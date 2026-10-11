from datetime import datetime, timezone, timedelta
import hashlib
import hmac
import os
import secrets
import jwt

from config.settings import settings

SECRET = getattr(settings, "jwt_secret", None) or os.getenv("JWT_SECRET", "greendash_super_secret_jwt_key_2026")

def hash_password(password: str) -> str:
    """Hash password using PBKDF2-HMAC-SHA256 with a unique salt."""
    salt = secrets.token_bytes(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return f"{salt.hex()}:{key.hex()}"

def verify_password(stored_hash: str, password: str) -> bool:
    """Verify password against stored salt:hash string."""
    try:
        salt_hex, key_hex = stored_hash.split(":", 1)
        salt = bytes.fromhex(salt_hex)
        key = bytes.fromhex(key_hex)
        new_key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
        return hmac.compare_digest(key, new_key)
    except Exception:
        return False

def issue_token(role: str, customer_id: str | None = None, sub: str | None = None,
                display_name: str | None = None, expires_minutes: int = 60) -> str:
    """Issue a signed JWT token with role, subject, and expiration."""
    now = datetime.now(timezone.utc)
    effective_sub = sub or customer_id or f"{role.lower()}_user"
    payload = {
        "sub": effective_sub,
        "role": role,
        "customer_id": customer_id,
        "display_name": display_name,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=expires_minutes)).timestamp()),
    }
    return jwt.encode(payload, SECRET, algorithm="HS256")

def verify_token(token: str) -> dict | None:
    """Verify a JWT token signature and expiry, returning payload dict or None."""
    try:
        return jwt.decode(token, SECRET, algorithms=["HS256"])
    except (jwt.PyJWTError, Exception):
        return None

def encrypt_feedback(data: str) -> str:
    """Obfuscate feedback notes for audit logging."""
    return f"enc_{secrets.token_hex(4)}_{hashlib.sha256(data.encode('utf-8')).hexdigest()[:16]}"

