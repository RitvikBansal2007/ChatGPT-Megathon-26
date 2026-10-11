"""Bearer-token issue/verify and feedback-note encryption.

Tokens are HS256 JWTs signed with settings.jwt_secret. The algorithm is pinned on
verify (a token cannot choose its own), and exp, role and sub are required claims.
The secret itself is validated in config.settings (see Settings._validate_secrets).
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt

from config.settings import settings

ROLES = frozenset({"CUSTOMER", "RELATIONSHIP_MANAGER", "PORTFOLIO_ANALYST", "AUDITOR", "EVALUATOR"})
ALGORITHM = "HS256"
DEFAULT_TTL_SECONDS = 900
REQUIRED_CLAIMS = ["exp", "role", "sub"]


class FeedbackEncryptionUnavailable(Exception):
    """DATA_KEY is missing or invalid, so a free-text note cannot be stored safely."""


def encrypt_feedback(data: str) -> str:
    """Encrypt a free-text feedback note with AES-256-GCM (security/crypto.py).

    Fails closed: if the key is missing or unusable this raises
    FeedbackEncryptionUnavailable instead of storing the note in a readable form.
    The note is bound to the context "feedback.note". Only a fixed message is raised;
    neither the note nor key material appears in the exception.
    """
    try:
        from security.crypto import encrypt_field, load_keyring
        keyring = load_keyring({"DATA_KEY": settings.data_key,
                                "DATA_KEY_OLD": settings.data_key_old})
        return encrypt_field(data, context="feedback.note", keyring=keyring)
    except Exception:
        raise FeedbackEncryptionUnavailable("feedback encryption unavailable") from None


def issue_token(
    role: str,
    customer_id: Optional[str] = None,
    expires_in: int = DEFAULT_TTL_SECONDS,
    secret: Optional[str] = None,
) -> str:
    """Sign a short-lived token. Only a known role may be issued."""
    if role not in ROLES:
        raise ValueError("unknown role")
    now = datetime.now(timezone.utc)
    payload = {
        "role": role,
        "sub": customer_id or "",
        "iat": now,
        "exp": now + timedelta(seconds=expires_in),
    }
    return jwt.encode(payload, secret or settings.jwt_secret, algorithm=ALGORITHM)


def verify_token(token: str, secret: Optional[str] = None) -> dict:
    """Return the claims of a valid token, or raise a jwt.PyJWTError subclass.

    Rejects: bad signature, expired, malformed, missing exp/role/sub, unknown role.
    """
    claims = jwt.decode(
        token,
        secret or settings.jwt_secret,
        algorithms=[ALGORITHM],
        options={"require": REQUIRED_CLAIMS},
    )
    if claims.get("role") not in ROLES:
        raise jwt.InvalidTokenError("unknown role")
    if not isinstance(claims.get("sub"), str):
        raise jwt.InvalidTokenError("invalid subject")
    return claims
