"""Unit tests for validated backend configuration."""

import os
import sys
from pathlib import Path
import pytest
from pydantic import ValidationError

CODE_ROOT = Path(__file__).resolve().parent.parent.parent
if str(CODE_ROOT) not in sys.path:
    sys.path.insert(0, str(CODE_ROOT))

from backend.config import Settings, get_settings


def test_valid_development_configuration():
    """1. Valid development configuration defaults."""
    s = get_settings(ENVIRONMENT="development")
    assert s.ENVIRONMENT == "development"
    assert s.AUTH_ENABLED is False
    assert s.JWT_SECRET_KEY is None
    assert s.RATE_LIMIT_PER_MINUTE == 60
    assert "http://localhost:3000" in s.CORS_ORIGINS


def test_valid_test_configuration():
    """2. Valid test configuration with custom values."""
    s = get_settings(
        ENVIRONMENT="test",
        GREENPROOF_DB_PATH=":memory:",
        RATE_LIMIT_PER_MINUTE=100,
    )
    assert s.ENVIRONMENT == "test"
    assert s.GREENPROOF_DB_PATH == ":memory:"
    assert s.RATE_LIMIT_PER_MINUTE == 100


def test_unsupported_environment_rejected():
    """3. Unsupported environment values are rejected."""
    with pytest.raises(ValidationError) as exc_info:
        get_settings(ENVIRONMENT="staging")
    assert "ENVIRONMENT" in str(exc_info.value)


def test_invalid_rate_limits_rejected():
    """4. Zero, negative, and invalid rate limits are rejected."""
    for bad_limit in [0, -1, -50]:
        with pytest.raises(ValidationError) as exc_info:
            get_settings(RATE_LIMIT_PER_MINUTE=bad_limit)
        assert "RATE_LIMIT_PER_MINUTE" in str(exc_info.value)


def test_valid_cors_origins_parsed():
    """5. Valid CORS origins as list or comma-separated string."""
    s_list = get_settings(CORS_ORIGINS=["https://app.greenproof.io", "http://localhost:8080"])
    assert s_list.CORS_ORIGINS == ["https://app.greenproof.io", "http://localhost:8080"]

    s_str = get_settings(CORS_ORIGINS="https://app.greenproof.io, http://localhost:8080")
    assert s_str.CORS_ORIGINS == ["https://app.greenproof.io", "http://localhost:8080"]


def test_malformed_cors_origins_rejected():
    """6. Malformed CORS origins (missing scheme, path included, invalid host) are rejected."""
    bad_origins = [
        "ftp://app.greenproof.io",
        "app.greenproof.io",
        "https://app.greenproof.io/some/path",
        "://invalid",
    ]
    for bad in bad_origins:
        with pytest.raises(ValidationError) as exc_info:
            get_settings(CORS_ORIGINS=[bad])
        assert "CORS_ORIGINS" in str(exc_info.value)


def test_production_refuses_inadequate_jwt_secret():
    """7. Production refuses to enable authentication without an adequate secret."""
    # When AUTH_ENABLED is True, secret must exist and be >= 32 chars
    with pytest.raises(ValidationError, match="JWT_SECRET_KEY is required"):
        get_settings(ENVIRONMENT="production", AUTH_ENABLED=True, JWT_SECRET_KEY=None)

    with pytest.raises(ValidationError, match="at least 32 characters"):
        get_settings(
            ENVIRONMENT="production",
            AUTH_ENABLED=True,
            JWT_SECRET_KEY="too_short_secret_value",
            CORS_ORIGINS=["https://app.greenproof.io"],
        )

    with pytest.raises(ValidationError, match="placeholder or insecure secret"):
        get_settings(
            ENVIRONMENT="production",
            AUTH_ENABLED=True,
            JWT_SECRET_KEY="secret",
            CORS_ORIGINS=["https://app.greenproof.io"],
        )


def test_production_requires_auth_enabled():
    """Production strictly refuses to start if AUTH_ENABLED is False."""
    with pytest.raises(ValidationError, match="Production environment requires AUTH_ENABLED=True"):
        get_settings(
            ENVIRONMENT="production",
            AUTH_ENABLED=False,
            CORS_ORIGINS=["https://app.greenproof.io"],
        )


def test_production_rejects_wildcard_cors():
    """8. Production does not silently permit all CORS origins."""
    with pytest.raises(ValidationError, match="CORS_ORIGINS must not allow wildcard"):
        get_settings(
            ENVIRONMENT="production",
            AUTH_ENABLED=True,
            JWT_SECRET_KEY="a" * 32,
            CORS_ORIGINS=["*"],
        )


def test_production_rejects_empty_cors():
    """Production requires explicitly configured CORS origins."""
    with pytest.raises(ValidationError, match="CORS_ORIGINS must be explicitly configured in production"):
        get_settings(
            ENVIRONMENT="production",
            AUTH_ENABLED=True,
            JWT_SECRET_KEY="a" * 32,
            CORS_ORIGINS=[],
        )


def test_jwt_secret_never_exposed():
    """9. JWT secret values never appear in validation errors, logs, or string representations."""
    secret_value = "super_secure_production_secret_key_32chars!"
    s = get_settings(
        ENVIRONMENT="development",
        JWT_SECRET_KEY=secret_value,
    )
    # Check repr and str do not reveal the secret
    assert secret_value not in repr(s)
    assert secret_value not in str(s)
    assert "super_secure" not in repr(s)


def test_database_path_configuration(tmp_path):
    """10. Database path configuration works correctly."""
    custom_db = str(tmp_path / "custom.db")
    s = get_settings(GREENPROOF_DB_PATH=custom_db)
    assert s.GREENPROOF_DB_PATH == custom_db


def test_loading_configuration_does_not_create_file(tmp_path):
    """11. Loading configuration does not create a database file."""
    non_existent_db = tmp_path / "never_created.db"
    assert not non_existent_db.exists()
    s = get_settings(GREENPROOF_DB_PATH=str(non_existent_db))
    assert s.GREENPROOF_DB_PATH == str(non_existent_db)
    assert not non_existent_db.exists()


def test_environment_variable_overrides_isolated(monkeypatch, tmp_path):
    """12. Environment variables can be overridden in tests without leaking state."""
    custom_path = str(tmp_path / "env_test.db")
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("GREENPROOF_DB_PATH", custom_path)
    monkeypatch.setenv("RATE_LIMIT_PER_MINUTE", "200")

    s = Settings()
    assert s.ENVIRONMENT == "test"
    assert s.GREENPROOF_DB_PATH == custom_path
    assert s.RATE_LIMIT_PER_MINUTE == 200
