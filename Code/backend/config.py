"""Validated application configuration using Pydantic Settings."""

import re
from pathlib import Path
from typing import List, Literal, Optional, Union
from urllib.parse import urlparse

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_DB_PATH = str(Path(__file__).resolve().parent / "greenproof.db")
INSECURE_SECRETS = frozenset({
    "secret", "changeme", "password", "jwt_secret", "jwt_secret_key",
    "123456", "admin", "default", "your_secret_here"
})


class Settings(BaseSettings):
    """Central configuration for GreenProof backend."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ENVIRONMENT: Literal["development", "test", "production"] = "development"
    GREENPROOF_DB_PATH: str = Field(default=DEFAULT_DB_PATH)
    AUTH_ENABLED: bool = False
    JWT_SECRET_KEY: Optional[SecretStr] = None
    CORS_ORIGINS: Union[List[str], str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"]
    )
    RATE_LIMIT_PER_MINUTE: int = Field(default=60)

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """Parse comma-separated origins or validate list of origins."""
        if isinstance(v, str):
            origins = [item.strip() for item in v.split(",") if item.strip()]
        elif isinstance(v, (list, tuple)):
            origins = [str(item).strip() for item in v if str(item).strip()]
        else:
            raise ValueError("CORS_ORIGINS must be a comma-separated string or list of origins")

        validated = []
        for orig in origins:
            if orig == "*":
                validated.append(orig)
                continue
            parsed = urlparse(orig)
            if not parsed.scheme or parsed.scheme not in ("http", "https"):
                raise ValueError(f"Invalid CORS origin scheme: '{orig}'")
            if not parsed.netloc:
                raise ValueError(f"Invalid CORS origin host: '{orig}'")
            if parsed.path and parsed.path != "":
                raise ValueError(f"CORS origin must not contain a path: '{orig}'")
            validated.append(orig)

        return validated

    @field_validator("RATE_LIMIT_PER_MINUTE")
    @classmethod
    def validate_rate_limit(cls, v: int) -> int:
        """Rate limit must be a positive integer."""
        if v <= 0:
            raise ValueError("RATE_LIMIT_PER_MINUTE must be a positive integer greater than zero")
        return v

    @model_validator(mode="after")
    def validate_security_invariants(self) -> "Settings":
        """Enforce production security rules and JWT requirements without leaking secrets."""
        # Enforce production security rules
        if self.ENVIRONMENT == "production":
            if not self.AUTH_ENABLED:
                raise ValueError("Production environment requires AUTH_ENABLED=True")
            if "*" in self.CORS_ORIGINS:
                raise ValueError("CORS_ORIGINS must not allow wildcard '*' in production")
            if not self.CORS_ORIGINS:
                raise ValueError("CORS_ORIGINS must be explicitly configured in production")

        # When authentication is enabled, enforce strong JWT secret
        if self.AUTH_ENABLED:
            if self.JWT_SECRET_KEY is None:
                raise ValueError("JWT_SECRET_KEY is required when authentication is enabled")
            secret_val = self.JWT_SECRET_KEY.get_secret_value()
            if secret_val.lower() in INSECURE_SECRETS:
                raise ValueError("JWT_SECRET_KEY cannot use known placeholder or insecure secret")
            if len(secret_val) < 32:
                raise ValueError("JWT_SECRET_KEY must be at least 32 characters long")

        return self

    def __repr__(self) -> str:
        """Safe representation hiding any sensitive fields."""
        return (
            f"Settings(ENVIRONMENT='{self.ENVIRONMENT}', "
            f"GREENPROOF_DB_PATH='{self.GREENPROOF_DB_PATH}', "
            f"AUTH_ENABLED={self.AUTH_ENABLED}, "
            f"CORS_ORIGINS={self.CORS_ORIGINS}, "
            f"RATE_LIMIT_PER_MINUTE={self.RATE_LIMIT_PER_MINUTE})"
        )

    def __str__(self) -> str:
        return self.__repr__()


def get_settings(**kwargs) -> Settings:
    """Instantiate and return settings without accessing filesystem database."""
    return Settings(**kwargs)
