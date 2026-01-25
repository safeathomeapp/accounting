"""
Module: config
Purpose: Application configuration and settings management
Dependencies: pydantic, pydantic-settings, cryptography

This module loads and validates all configuration from environment variables.
Uses Pydantic Settings for type-safe configuration management.

Environment Variables (from .env):
- ENVIRONMENT: development, staging, production
- DEBUG: True/False
- DATABASE_URL: PostgreSQL connection string
- SECRET_KEY: JWT secret key
- ENCRYPTION_KEY: Fernet encryption key for sensitive data
- CLAUDE_API_KEY: Anthropic Claude API key
- XERO_CLIENT_ID, XERO_CLIENT_SECRET: Xero OAuth credentials
- QB_CLIENT_ID, QB_CLIENT_SECRET: QuickBooks OAuth credentials
- And many more...

Example:
    from backend.config import settings, EncryptionManager

    # Access settings
    print(settings.database_url)
    print(settings.debug)

    # Use encryption
    enc = EncryptionManager(settings.encryption_key)
    encrypted = enc.encrypt("sensitive data")

Author: Claude Code
Created: November 23, 2025
Last Modified: November 23, 2025
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from cryptography.fernet import Fernet
import os
from typing import Optional


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Uses Pydantic BaseSettings for automatic validation and type coercion.
    All environment variables are defined here with defaults.

    Attributes:
        # Application
        environment: Current environment (development, staging, production)
        debug: Enable debug mode
        app_name: Application name
        app_version: Application version

        # Database
        database_url: PostgreSQL connection string
        db_echo: Echo SQL queries (for debugging)

        # Security
        secret_key: JWT secret key (generate with: python -c "import secrets; print(secrets.token_urlsafe(32))")
        encryption_key: Fernet encryption key (generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
        jwt_algorithm: JWT algorithm
        jwt_expiration_hours: JWT token expiration

        # Claude API
        claude_api_key: Anthropic API key
        claude_model: Which Claude model to use
        claude_max_tokens: Max tokens per request
        claude_monthly_budget_gbp: Budget limit
        claude_alert_threshold_gbp: Alert when approaching budget

        # Xero
        xero_client_id: OAuth client ID
        xero_client_secret: OAuth client secret
        xero_redirect_uri: OAuth callback URL
        xero_scope: OAuth scopes

        # QuickBooks
        qb_client_id: OAuth client ID
        qb_client_secret: OAuth client secret
        qb_redirect_uri: OAuth callback URL
        qb_environment: sandbox or production

        # Server
        host: Server host
        port: Server port
        reload: Auto-reload on code changes

        # Logging
        log_level: Logging level

        # API Rate Limiting
        rate_limit_per_minute: Default rate limit
        claude_rate_limit_per_minute: Claude API rate limit

        # Caching
        cache_enabled: Enable caching
        cache_ttl_seconds: Cache TTL

        # CORS
        cors_origins: Allowed CORS origins

        # Timezone
        timezone: Application timezone
        locale: Application locale
        currency: Default currency

    Example:
        >>> from backend.config import settings
        >>> print(settings.environment)
        'development'
        >>> print(settings.database_url)
        'postgresql://user:pass@localhost/db'
    """

    # Application Settings
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = os.getenv("DEBUG", "True").lower() == "true"
    app_name: str = "Multi-Platform AI Practice Management"
    app_version: str = "2.0.0-alpha"

    # Database
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/accountancy_dev"
    )
    db_echo: bool = False  # Set to True for SQL debugging

    # Security
    secret_key: str = os.getenv(
        "SECRET_KEY",
        "change-me-in-production-generate-with-python-c-import-secrets"
    )
    encryption_key: str = os.getenv(
        "ENCRYPTION_KEY",
        "change-me-in-production-generate-with-fernet"
    )
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    # Claude API
    claude_api_key: str = os.getenv("CLAUDE_API_KEY", "")
    claude_model: str = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")
    claude_max_tokens: int = int(os.getenv("CLAUDE_MAX_TOKENS", "4096"))
    claude_monthly_budget_gbp: float = float(os.getenv("CLAUDE_MONTHLY_BUDGET_GBP", "30.00"))
    claude_alert_threshold_gbp: float = float(os.getenv("CLAUDE_ALERT_THRESHOLD_GBP", "25.00"))

    # Xero
    xero_client_id: str = os.getenv("XERO_CLIENT_ID", "")
    xero_client_secret: str = os.getenv("XERO_CLIENT_SECRET", "")
    xero_redirect_uri: str = os.getenv("XERO_REDIRECT_URI", "http://localhost:8000/auth/xero/callback")
    xero_scope: str = os.getenv(
        "XERO_SCOPE",
        "offline_access accounting.transactions accounting.contacts accounting.settings"
    )
    xero_tenant_id: Optional[str] = os.getenv("XERO_TENANT_ID", None)

    # QuickBooks
    qb_client_id: str = os.getenv("QB_CLIENT_ID", "")
    qb_client_secret: str = os.getenv("QB_CLIENT_SECRET", "")
    qb_redirect_uri: str = os.getenv("QB_REDIRECT_URI", "http://localhost:8000/auth/quickbooks/callback")
    qb_environment: str = os.getenv("QB_ENVIRONMENT", "sandbox")
    qb_company_id: Optional[str] = os.getenv("QB_COMPANY_ID", None)

    # Server
    host: str = os.getenv("HOST", "localhost")
    port: int = int(os.getenv("PORT", "8000"))
    reload: bool = os.getenv("RELOAD", "True").lower() == "true"

    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_file: str = os.getenv("LOG_FILE", "logs/app.log")

    # API Rate Limiting
    rate_limit_per_minute: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    claude_rate_limit_per_minute: int = int(os.getenv("CLAUDE_RATE_LIMIT_PER_MINUTE", "50"))

    # Caching
    cache_enabled: bool = os.getenv("CACHE_ENABLED", "True").lower() == "true"
    cache_ttl_seconds: int = int(os.getenv("CACHE_TTL_SECONDS", "3600"))

    # CORS
    # Hardcoded defaults (not sensitive, safe to keep here)
    # Excluded from environment loading using Field
    cors_origins: list = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:3001",
            "http://localhost:3002",
            "http://localhost:5173",
            "http://localhost:8080",
            "http://localhost:8000",
        ],
        exclude=True
    )

    # Timezone & Locale
    timezone: str = os.getenv("TIMEZONE", "Europe/London")
    locale: str = os.getenv("LOCALE", "en_GB")
    currency: str = os.getenv("CURRENCY", "GBP")

    class Config:
        """Pydantic config."""
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from .env

    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment.lower() == "production"

    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment.lower() == "development"


# Global settings instance
settings = Settings()


class EncryptionManager:
    """
    Handles encryption and decryption of sensitive data.

    Uses Fernet (symmetric encryption) from cryptography library.
    Ensures sensitive data like API tokens are encrypted at rest.

    Attributes:
        cipher: Fernet cipher instance

    Example:
        >>> from backend.config import EncryptionManager
        >>> manager = EncryptionManager(settings.encryption_key)
        >>> encrypted = manager.encrypt("secret")
        >>> decrypted = manager.decrypt(encrypted)
        >>> assert decrypted == "secret"

    Note:
        - Generate key with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
        - Store key in .env ENCRYPTION_KEY
        - Never commit .env to git
    """

    def __init__(self, key: str) -> None:
        """
        Initialize encryption manager.

        Args:
            key: Fernet encryption key (base64-encoded)

        Raises:
            ValueError: If key is invalid
        """
        try:
            self.cipher = Fernet(key.encode())
        except Exception as e:
            raise ValueError(f"Invalid encryption key: {e}")

    def encrypt(self, value: str) -> bytes:
        """
        Encrypt a string value.

        Args:
            value: Plain text string to encrypt

        Returns:
            Encrypted bytes

        Example:
            >>> encrypted = manager.encrypt("my secret")
        """
        return self.cipher.encrypt(value.encode())

    def decrypt(self, encrypted_value: bytes) -> str:
        """
        Decrypt an encrypted value.

        Args:
            encrypted_value: Encrypted bytes

        Returns:
            Decrypted string

        Example:
            >>> decrypted = manager.decrypt(encrypted_bytes)
        """
        return self.cipher.decrypt(encrypted_value).decode()


# Global encryption manager instance
encryption_manager = EncryptionManager(settings.encryption_key)
