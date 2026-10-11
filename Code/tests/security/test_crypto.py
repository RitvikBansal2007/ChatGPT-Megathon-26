import base64
import sys
from pathlib import Path

import pytest

pytest.importorskip("cryptography", reason="field encryption needs the 'cryptography' package")
from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from security import crypto  # noqa: E402
from security.crypto import (  # noqa: E402
    CryptoError, KeyRing, decrypt_field, encrypt_field, generate_key, load_keyring,
)

CTX = "customers.postcode"


@pytest.fixture
def ring():
    return KeyRing(generate_key())


def code_of(fn, *a, **kw):
    with pytest.raises(CryptoError) as info:
        fn(*a, **kw)
    return info.value.code


# ---- round trip and format ------------------------------------------------

@pytest.mark.parametrize("value", ["SW1A 1AA", "", "café – £100", "x" * 5000])
def test_round_trip(ring, value):
    token = encrypt_field(value, context=CTX, keyring=ring)
    assert decrypt_field(token, context=CTX, keyring=ring) == value


def test_same_value_encrypts_differently_each_time(ring):
    a = encrypt_field("SW1A 1AA", context=CTX, keyring=ring)
    b = encrypt_field("SW1A 1AA", context=CTX, keyring=ring)
    assert a != b


def test_token_does_not_contain_the_plaintext(ring):
    token = encrypt_field("SW1A 1AA", context=CTX, keyring=ring)
    assert "SW1A" not in token and token.startswith("gd1." + ring.current_id + ".")


def test_token_is_standard_aes_256_gcm(ring):
    """Decrypt with the library directly: proves the format is plain AES-GCM."""
    token = encrypt_field("hello", context=CTX, keyring=ring)
    _, _, body = token.split(".")
    blob = base64.urlsafe_b64decode(body + "=" * (-len(body) % 4))
    key = ring._keys[ring.current_id]
    assert len(key) == 32
    assert AESGCM(key).decrypt(blob[:12], blob[12:], CTX.encode()) == b"hello"


# ---- authentication: tamper, context, key ---------------------------------

def test_tampered_ciphertext_is_rejected(ring):
    token = encrypt_field("SW1A 1AA", context=CTX, keyring=ring)
    head, body = token.rsplit(".", 1)
    raw = bytearray(base64.urlsafe_b64decode(body + "=" * (-len(body) % 4)))
    raw[-1] ^= 0x01
    forged = head + "." + base64.urlsafe_b64encode(bytes(raw)).decode()
    assert code_of(decrypt_field, forged, context=CTX, keyring=ring) == crypto.DECRYPT_FAILED


def test_value_cannot_be_moved_to_another_field(ring):
    token = encrypt_field("SW1A 1AA", context="customers.postcode", keyring=ring)
    assert code_of(decrypt_field, token, context="customers.name", keyring=ring) \
        == crypto.DECRYPT_FAILED


def test_wrong_key_is_rejected():
    token = encrypt_field("secret", context=CTX, keyring=KeyRing(generate_key()))
    assert code_of(decrypt_field, token, context=CTX, keyring=KeyRing(generate_key())) \
        == crypto.UNKNOWN_KEY


@pytest.mark.parametrize("bad", ["", "nonsense", "gd1.k1", "gd2.k1.AAAA", "gd1.k.!!!!", None, 5])
def test_malformed_tokens_are_rejected(ring, bad):
    assert code_of(decrypt_field, bad, context=CTX, keyring=ring) in (
        crypto.BAD_FORMAT, crypto.UNKNOWN_KEY)


def test_truncated_token_is_rejected(ring):
    token = encrypt_field("abc", context=CTX, keyring=ring)
    assert code_of(decrypt_field, token[:-8], context=CTX, keyring=ring) in (
        crypto.BAD_FORMAT, crypto.DECRYPT_FAILED)


# ---- key rotation ---------------------------------------------------------

def test_rotation_old_data_still_decrypts_and_new_data_uses_new_key():
    old_key, new_key = generate_key(), generate_key()
    old_token = encrypt_field("before", context=CTX, keyring=KeyRing(old_key))
    ring = KeyRing(new_key, retired=[old_key])
    assert decrypt_field(old_token, context=CTX, keyring=ring) == "before"
    new_token = encrypt_field("after", context=CTX, keyring=ring)
    assert new_token.split(".")[1] == ring.current_id != old_token.split(".")[1]
    # A ring without the retired key can no longer read old data.
    assert code_of(decrypt_field, old_token, context=CTX, keyring=KeyRing(new_key)) \
        == crypto.UNKNOWN_KEY


# ---- key loading fails closed --------------------------------------------

def test_load_keyring_from_env():
    key, old = generate_key(), generate_key()
    ring = load_keyring({"DATA_KEY": key, "DATA_KEY_OLD": old + ", "})
    token = encrypt_field("v", context=CTX, keyring=ring)
    assert decrypt_field(token, context=CTX, keyring=ring) == "v"


@pytest.mark.parametrize("env,expected", [
    ({}, crypto.KEY_MISSING),
    ({"DATA_KEY": "   "}, crypto.KEY_MISSING),
    ({"DATA_KEY": "not base64 !!"}, crypto.KEY_INVALID),
    ({"DATA_KEY": base64.b64encode(b"short").decode()}, crypto.KEY_INVALID),
    ({"DATA_KEY": base64.b64encode(bytes(32)).decode()}, crypto.KEY_INVALID),   # placeholder
    ({"DATA_KEY": generate_key(), "DATA_KEY_OLD": "bad"}, crypto.KEY_INVALID),
])
def test_bad_or_missing_keys_fail_closed(env, expected):
    assert code_of(load_keyring, env) == expected


def test_stray_characters_are_rejected_not_skipped(ring):
    """Base64 decoding is strict: junk is an error, never silently ignored."""
    good = generate_key()
    dirty = good[:10] + "!" + good[10:]
    assert code_of(load_keyring, {"DATA_KEY": dirty}) == crypto.KEY_INVALID
    token = encrypt_field("v", context=CTX, keyring=ring)
    head, body = token.rsplit(".", 1)
    forged = head + "." + body[:6] + "!" + body[6:]
    assert code_of(decrypt_field, forged, context=CTX, keyring=ring) == crypto.BAD_FORMAT


def test_generated_keys_are_32_random_bytes():
    a, b = generate_key(), generate_key()
    assert a != b
    assert len(base64.urlsafe_b64decode(a + "=" * (-len(a) % 4))) == 32


# ---- no leaks -------------------------------------------------------------

def test_keyring_repr_and_str_do_not_show_key_material():
    key = generate_key()
    ring = KeyRing(key)
    shown = repr(ring) + str(ring)
    raw = ring._keys[ring.current_id]
    # No encoding of the key may appear: base64 text, raw bytes repr, or hex.
    for leaked in (key, key[:10], repr(raw), str(raw), raw.hex(), raw.hex()[:16]):
        assert leaked not in shown
    assert ring.current_id in shown


def test_errors_carry_only_fixed_codes(ring):
    marker = "PLAINTEXT-MARKER-VALUE"
    token = encrypt_field(marker, context=CTX, keyring=ring)
    for fn, args in (
        (decrypt_field, (token[:-4] + "AAAA",)),
        (decrypt_field, ("gd1.k00000000." + token.split(".")[2],)),
    ):
        with pytest.raises(CryptoError) as info:
            fn(*args, context=CTX, keyring=ring)
        assert marker not in str(info.value) and info.value.code == str(info.value)


# ---- input validation -----------------------------------------------------

def test_input_validation(ring):
    with pytest.raises(TypeError):
        encrypt_field(b"bytes", context=CTX, keyring=ring)
    with pytest.raises(TypeError):
        encrypt_field(None, context=CTX, keyring=ring)
    with pytest.raises(ValueError):
        encrypt_field("x", context="", keyring=ring)
    assert code_of(encrypt_field, "x" * (crypto.MAX_FIELD_BYTES + 1), context=CTX,
                   keyring=ring) == crypto.TOO_LARGE


def test_missing_library_fails_with_a_clear_code(ring, monkeypatch):
    monkeypatch.setitem(sys.modules, "cryptography.hazmat.primitives.ciphers.aead", None)
    assert code_of(encrypt_field, "x", context=CTX, keyring=ring) == crypto.UNAVAILABLE
