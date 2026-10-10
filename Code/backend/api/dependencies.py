"""Reusable FastAPI dependencies and the authentication integration boundary."""

import sqlite3
from dataclasses import dataclass
from typing import Callable, Generator, Optional
from fastapi import Depends, Header, HTTPException, status

from backend.config import Settings, get_settings
from backend.db import get_connection


@dataclass(frozen=True)
class AuthenticatedUser:
    """Verified identity passed to route handlers after successful authentication."""

    user_id: str
    role: str = "customer"


# Pluggable authentication provider boundary for security module integration
_auth_provider: Optional[Callable[[str], AuthenticatedUser]] = None


def set_auth_provider(provider: Callable[[str], AuthenticatedUser]) -> None:
    """Register external JWT verification provider once implemented."""
    global _auth_provider
    _auth_provider = provider


def is_auth_configured() -> bool:
    """Return True if an authentication provider has been registered."""
    return _auth_provider is not None


def get_settings_dep() -> Settings:
    """Dependency returning application settings."""
    return Settings()


def get_db(settings: Settings = Depends(get_settings_dep)) -> Generator[sqlite3.Connection, None, None]:
    """Provide a database connection per request and guarantee commit and closure on completion."""
    conn = get_connection(settings.GREENPROOF_DB_PATH)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_current_user(
    authorization: Optional[str] = Header(None, description="Bearer token header"),
) -> AuthenticatedUser:
    """Extract and verify user identity.
    
    This is the strict security boundary:
    1. Rejects unauthenticated requests with HTTP 401.
    2. Never trusts unverified client-supplied user IDs.
    3. Delegates token verification to the registered auth provider once connected.
    """
    if not authorization or not authorization.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required: missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    parts = authorization.strip().split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization format: expected 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = parts[1]

    # If security module has registered an auth provider, invoke it
    if _auth_provider is not None:
        try:
            return _auth_provider(token)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            ) from e

    # If no auth provider is registered yet, fail closed
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication provider not configured; request denied",
        headers={"WWW-Authenticate": "Bearer"},
    )
