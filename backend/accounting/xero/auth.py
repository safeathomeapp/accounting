"""OAuth 2.0 authentication for Xero."""
import secrets
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
import hashlib
import base64
import requests
from urllib.parse import urlencode

XERO_AUTH_URL = "https://login.xero.com/identity/connect/authorize"
XERO_TOKEN_URL = "https://identity.xero.com/connect/token"
XERO_REVOKE_URL = "https://identity.xero.com/connect/revoke"
XERO_SCOPES = [
    "offline_access",
    "accounting.transactions",
    "accounting.contacts",
    "accounting.settings",
]

def generate_pkce_pair() -> Tuple[str, str]:
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("utf-8").rstrip("=")
    challenge = base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest()).decode("utf-8").rstrip("=")
    return code_verifier, challenge

def generate_state() -> str:
    return secrets.token_urlsafe(32)

class XeroAuth:
    """Handles OAuth 2.0 authentication with Xero."""
    
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        if not client_id or not client_secret or not redirect_uri:
            raise ValueError("client_id, client_secret, and redirect_uri are required")
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.tokens = {}
        self.pkce_state = {}
    
    def get_authorization_url(self, state: Optional[str] = None) -> Tuple[str, str]:
        if state is None:
            state = generate_state()
        code_verifier, code_challenge = generate_pkce_pair()
        self.pkce_state[state] = {"code_verifier": code_verifier, "created_at": datetime.now()}
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": " ".join(XERO_SCOPES),
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
        auth_url = f"{XERO_AUTH_URL}?{urlencode(params)}"
        return auth_url, state
    
    def exchange_code_for_token(self, code: str, state: str) -> Dict:
        if state not in self.pkce_state:
            raise ValueError(f"Invalid state parameter: {state}")
        pkce_data = self.pkce_state[state]
        code_verifier = pkce_data["code_verifier"]
        if datetime.now() - pkce_data["created_at"] > timedelta(minutes=10):
            del self.pkce_state[state]
            raise ValueError("Authorization request expired")
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code_verifier": code_verifier,
        }
        response = requests.post(XERO_TOKEN_URL, data=data, timeout=30)
        response.raise_for_status()
        token_data = response.json()
        del self.pkce_state[state]
        self.tokens = {
            "access_token": token_data["access_token"],
            "refresh_token": token_data["refresh_token"],
            "expires_at": datetime.now() + timedelta(seconds=token_data["expires_in"]),
            "tenant_id": token_data.get("Xero-tenant-id"),
        }
        return token_data
    
    def get_access_token(self) -> Optional[str]:
        if not self.tokens:
            return None
        if datetime.now() >= self.tokens.get("expires_at", datetime.now()):
            try:
                self.refresh_access_token()
            except Exception:
                return None
        return self.tokens.get("access_token")
    
    def refresh_access_token(self) -> Dict:
        if not self.tokens.get("refresh_token"):
            raise ValueError("No refresh token available")
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.tokens["refresh_token"],
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        response = requests.post(XERO_TOKEN_URL, data=data, timeout=30)
        response.raise_for_status()
        token_data = response.json()
        self.tokens["access_token"] = token_data["access_token"]
        self.tokens["refresh_token"] = token_data.get("refresh_token", self.tokens["refresh_token"])
        self.tokens["expires_at"] = datetime.now() + timedelta(seconds=token_data["expires_in"])
        return token_data
    
    def get_tenant_id(self) -> Optional[str]:
        return self.tokens.get("tenant_id")
    
    def is_authenticated(self) -> bool:
        try:
            token = self.get_access_token()
            return token is not None
        except Exception:
            return False
    
    def revoke_token(self) -> bool:
        if not self.tokens.get("refresh_token"):
            return False
        data = {"token": self.tokens["refresh_token"], "client_id": self.client_id}
        try:
            response = requests.post(XERO_REVOKE_URL, data=data, timeout=30)
            response.raise_for_status()
            self.tokens = {}
            return True
        except requests.exceptions.RequestException:
            return False
