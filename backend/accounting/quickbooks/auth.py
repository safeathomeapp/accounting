"""OAuth 2.0 authentication for QuickBooks Online."""
import secrets
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
import requests
from urllib.parse import urlencode

QBO_AUTH_URL = "https://appcenter.intuit.com/connect/oauth2"
QBO_TOKEN_URL = "https://quickbooks.api.intuit.com/v2/oauth2/tokens/bearer"
QBO_REVOKE_URL = "https://developer.api.intuit.com/v2/oauth2/tokens/revoke"
QBO_SCOPES = ["com.intuit.quickbooks.accounting"]


def generate_state() -> str:
    """Generate random state parameter for CSRF protection."""
    return secrets.token_urlsafe(32)


class QuickBooksAuth:
    """Handles OAuth 2.0 authentication with QuickBooks Online."""

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        if not client_id or not client_secret or not redirect_uri:
            raise ValueError("client_id, client_secret, and redirect_uri are required")
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.tokens = {}
        self.state_store = {}

    def get_authorization_url(self, state: Optional[str] = None) -> Tuple[str, str]:
        """Get authorization URL for user redirect."""
        if state is None:
            state = generate_state()
        self.state_store[state] = {"created_at": datetime.now()}
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "scope": " ".join(QBO_SCOPES),
            "redirect_uri": self.redirect_uri,
            "state": state,
        }
        auth_url = f"{QBO_AUTH_URL}?{urlencode(params)}"
        return auth_url, state

    def exchange_code_for_token(self, code: str, state: str) -> Dict:
        """Exchange authorization code for access and refresh tokens."""
        if state not in self.state_store:
            raise ValueError(f"Invalid state parameter: {state}")

        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
        }
        auth = (self.client_id, self.client_secret)
        response = requests.post(QBO_TOKEN_URL, data=data, auth=auth, timeout=30)
        response.raise_for_status()
        token_data = response.json()
        del self.state_store[state]

        self.tokens = {
            "access_token": token_data["access_token"],
            "refresh_token": token_data["refresh_token"],
            "expires_at": datetime.now()
            + timedelta(seconds=token_data.get("expires_in", 3600)),
            "realm_id": token_data.get("x_refresh_token_expires_in"),
        }
        return token_data

    def get_access_token(self) -> Optional[str]:
        """Get current access token, refreshing if needed."""
        if not self.tokens:
            return None
        expires_at = self.tokens.get("expires_at")
        if expires_at and datetime.now() >= expires_at:
            try:
                self.refresh_access_token()
            except Exception:
                return None
        return self.tokens.get("access_token")

    def refresh_access_token(self) -> Dict:
        """Refresh access token using refresh token."""
        if not self.tokens.get("refresh_token"):
            raise ValueError("No refresh token available")
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.tokens["refresh_token"],
        }
        auth = (self.client_id, self.client_secret)
        response = requests.post(QBO_TOKEN_URL, data=data, auth=auth, timeout=30)
        response.raise_for_status()
        token_data = response.json()

        self.tokens["access_token"] = token_data["access_token"]
        self.tokens["refresh_token"] = token_data.get(
            "refresh_token", self.tokens["refresh_token"]
        )
        self.tokens["expires_at"] = datetime.now() + timedelta(
            seconds=token_data.get("expires_in", 3600)
        )
        return token_data

    def get_realm_id(self) -> Optional[str]:
        """Get QB realm ID (company ID)."""
        return self.tokens.get("realm_id")

    def is_authenticated(self) -> bool:
        """Check if currently authenticated."""
        try:
            token = self.get_access_token()
            return token is not None
        except Exception:
            return False

    def revoke_token(self) -> bool:
        """Revoke refresh token (logout)."""
        if not self.tokens.get("refresh_token"):
            return False
        data = {"token": self.tokens["refresh_token"]}
        auth = (self.client_id, self.client_secret)
        try:
            response = requests.post(QBO_REVOKE_URL, data=data, auth=auth, timeout=30)
            response.raise_for_status()
            self.tokens = {}
            return True
        except requests.exceptions.RequestException:
            return False
