"""Field-level authenticated encryption (AES-256-GCM) for sensitive values.

Use this to protect individual sensitive values (for example a postcode or a
persona name) before they are written to a file or database.

Design, in plain terms:
- AES-256-GCM is an "authenticated" cipher: it hides the value AND detects any
  change to it. A tampered value fails to decrypt instead of returning garbage.
- Every value gets its own random 96-bit nonce ("number used once"), so encrypting
  the same text twice gives different output.
- Each value is bound to a `context` string (for example "customers.postcode").
  A value copied into a different column fails to decrypt, so ciphertexts cannot
  be silently swapped between fields.
- The token carries a short key id so the key can be rotated: new data uses the
  current key, old data still decrypts with a retired key.
- The cipher itself comes from the `cryptography` package. Nothing is hand-rolled.

Token format:   gd1.<key_id>.<urlsafe-base64(nonce + ciphertext + tag)>

Limitations (not hidden):
- Encrypting values does not protect a machine that is already compromised: the key
  is in process memory while in use, and Python cannot reliably wipe it.
- Equal context + equal key never repeats a nonce in practice (random 96-bit), but
  GCM is only safe for a bounded number of messages per key (about 2**32). That is
  far above this project's size; rotate keys long before that in production.
- The key comes from an environment variable. Where that variable lives (a local
  .env, a secret manager) is a deployment decision outside this module.
- This module does not log. Errors carry a fixed code only, never data.
"""
import base64
import binascii
import hashlib
import os
from typing import Dict, Iterable, Mapping, Optional

TOKEN_PREFIX = "gd1"
KEY_BYTES = 32            # AES-256
NONCE_BYTES = 12          # 96-bit nonce, as recommended for GCM
MAX_FIELD_BYTES = 64 * 1024

ENV_CURRENT_KEY = "DATA_KEY"
ENV_OLD_KEYS = "DATA_KEY_OLD"   # optional, comma separated, decrypt-only

# Fixed error codes (safe to log or show).
UNAVAILABLE = "UNAVAILABLE"
KEY_MISSING = "KEY_MISSING"
KEY_INVALID = "KEY_INVALID"
BAD_FORMAT = "BAD_FORMAT"
UNKNOWN_KEY = "UNKNOWN_KEY"
DECRYPT_FAILED = "DECRYPT_FAILED"
TOO_LARGE = "TOO_LARGE"


class CryptoError(Exception):
    """A crypto operation failed. The message is a fixed code, never data."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def _b64decode(text: str) -> bytes:
    # Strict: unknown characters are an error, not silently skipped (the default
    # behaviour of base64 decoding). Accepts both the standard and URL-safe alphabets.
    cleaned = text.strip().replace("-", "+").replace("_", "/")
    return base64.b64decode(cleaned + "=" * (-len(cleaned) % 4), validate=True)


def _key_id(key: bytes) -> str:
    # A short fingerprint, not the key. SHA-256 cannot be run backwards to the key.
    return "k" + hashlib.sha256(key).hexdigest()[:8]


def _parse_key(text: str) -> bytes:
    try:
        key = _b64decode(text)
    except (binascii.Error, ValueError):
        raise CryptoError(KEY_INVALID)
    if len(key) != KEY_BYTES or len(set(key)) == 1:
        # Wrong length, or an obvious placeholder such as 32 zero bytes.
        raise CryptoError(KEY_INVALID)
    return key


def generate_key() -> str:
    """A fresh random key, base64 encoded, suitable for DATA_KEY."""
    return base64.urlsafe_b64encode(os.urandom(KEY_BYTES)).decode("ascii")


class KeyRing:
    """The current encryption key plus any retired keys kept for decryption."""

    def __init__(self, current: str, retired: Iterable[str] = ()):
        current_key = _parse_key(current)
        self._keys: Dict[str, bytes] = {_key_id(current_key): current_key}
        self._current_id = _key_id(current_key)
        for old in retired:
            old_key = _parse_key(old)
            self._keys.setdefault(_key_id(old_key), old_key)

    @property
    def current_id(self) -> str:
        return self._current_id

    def _get(self, key_id: str) -> bytes:
        key = self._keys.get(key_id)
        if key is None:
            raise CryptoError(UNKNOWN_KEY)
        return key

    def __repr__(self) -> str:  # never show key material
        return f"<KeyRing current={self._current_id} keys={len(self._keys)}>"

    __str__ = __repr__


def load_keyring(env: Optional[Mapping[str, str]] = None) -> KeyRing:
    """Build a KeyRing from DATA_KEY (and optional DATA_KEY_OLD). Fails closed."""
    env = os.environ if env is None else env
    current = env.get(ENV_CURRENT_KEY, "")
    if not current.strip():
        raise CryptoError(KEY_MISSING)
    retired = [p for p in env.get(ENV_OLD_KEYS, "").split(",") if p.strip()]
    return KeyRing(current, retired)


def _aesgcm(key: bytes):
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    except ImportError:
        raise CryptoError(UNAVAILABLE)
    return AESGCM(key)


def _context_bytes(context: str) -> bytes:
    if not isinstance(context, str) or not context:
        raise ValueError("context must be a non-empty string")
    return context.encode("utf-8")


def encrypt_field(plaintext: str, *, context: str, keyring: KeyRing) -> str:
    """Encrypt one text value. `context` names the field, e.g. "customers.postcode"."""
    if not isinstance(plaintext, str):
        raise TypeError("plaintext must be str")
    data = plaintext.encode("utf-8")
    if len(data) > MAX_FIELD_BYTES:
        raise CryptoError(TOO_LARGE)
    aad = _context_bytes(context)
    nonce = os.urandom(NONCE_BYTES)
    blob = nonce + _aesgcm(keyring._get(keyring.current_id)).encrypt(nonce, data, aad)
    body = base64.urlsafe_b64encode(blob).decode("ascii")
    return f"{TOKEN_PREFIX}.{keyring.current_id}.{body}"


def decrypt_field(token: str, *, context: str, keyring: KeyRing) -> str:
    """Decrypt a token made by encrypt_field. Any failure raises CryptoError."""
    aad = _context_bytes(context)
    if not isinstance(token, str):
        raise CryptoError(BAD_FORMAT)
    parts = token.split(".")
    if len(parts) != 3 or parts[0] != TOKEN_PREFIX:
        raise CryptoError(BAD_FORMAT)
    key = keyring._get(parts[1])
    try:
        blob = _b64decode(parts[2])
    except (binascii.Error, ValueError):
        raise CryptoError(BAD_FORMAT)
    if len(blob) < NONCE_BYTES + 16:       # nonce + 16-byte authentication tag
        raise CryptoError(BAD_FORMAT)
    try:
        data = _aesgcm(key).decrypt(blob[:NONCE_BYTES], blob[NONCE_BYTES:], aad)
        return data.decode("utf-8")
    except CryptoError:
        raise
    except Exception:
        # Wrong key, wrong context or tampering: deliberately indistinguishable.
        raise CryptoError(DECRYPT_FAILED)
