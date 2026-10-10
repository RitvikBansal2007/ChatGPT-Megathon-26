"""Unit tests for the GreenProof FastAPI application and transaction endpoints."""

import io
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

CODE_ROOT = Path(__file__).resolve().parent.parent.parent
if str(CODE_ROOT) not in sys.path:
    sys.path.insert(0, str(CODE_ROOT))

from backend.api.app import create_app
from backend.api.dependencies import AuthenticatedUser, get_current_user, get_db
from backend.config import Settings
from backend.db import apply_schema, get_connection


@pytest.fixture
def app_and_db(tmp_path):
    """Fixture providing a test application with an isolated SQLite database."""
    db_file = str(tmp_path / "test_api.db")
    # Initialize schema
    conn = get_connection(db_file)
    apply_schema(conn)
    conn.close()

    test_settings = Settings(
        ENVIRONMENT="test",
        GREENPROOF_DB_PATH=db_file,
        AUTH_ENABLED=False,
        CORS_ORIGINS=["http://localhost:3000"],
    )
    test_app = create_app(test_settings)
    from backend.api.dependencies import get_settings_dep
    test_app.dependency_overrides[get_settings_dep] = lambda: test_settings
    return test_app, db_file


@pytest.fixture
def client(app_and_db):
    """TestClient without authentication overrides."""
    test_app, _ = app_and_db
    return TestClient(test_app)


@pytest.fixture
def authed_client(app_and_db):
    """TestClient with dependency override for AuthenticatedUser('CUST-0001')."""
    test_app, _ = app_and_db
    test_app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(
        user_id="CUST-0001", role="customer"
    )
    yield TestClient(test_app)
    test_app.dependency_overrides.clear()


# Application & Health Tests
def test_health_endpoint(client):
    """Verify /health returns 200 with environment information."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["environment"] == "test"


def test_ready_endpoint(client):
    """Verify /ready checks database connectivity safely."""
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_production_startup_fails_without_auth_provider():
    """Verify production mode refuses to start without an active authentication provider."""
    prod_settings = Settings(
        ENVIRONMENT="production",
        AUTH_ENABLED=True,
        JWT_SECRET_KEY="a" * 32,
        CORS_ORIGINS=["https://app.greenproof.io"],
    )
    with pytest.raises(RuntimeError, match="Production startup failed: authentication is mandatory"):
        create_app(prod_settings)


# Authentication Boundary Tests
def test_unauthenticated_request_rejected(client):
    """Verify protected endpoints return 401 when no authorization header is supplied."""
    resp_get = client.get("/api/v1/transactions")
    assert resp_get.status_code == 401
    assert "Authentication required" in resp_get.json()["detail"]

    resp_post = client.post(
        "/api/v1/transactions",
        json={"date": "2026-06-01", "description": "Coffee", "amount": "3.50"},
    )
    assert resp_post.status_code == 401


def test_malformed_auth_header_rejected(client):
    """Verify malformed authorization headers return 401."""
    resp = client.get("/api/v1/transactions", headers={"Authorization": "InvalidTokenHeader"})
    assert resp.status_code == 401
    assert "expected 'Bearer <token>'" in resp.json()["detail"]


# Transaction Schema Validation Tests
def test_create_transaction_success(authed_client):
    """Verify valid transaction creation scoped to the authenticated customer."""
    payload = {
        "date": "2026-06-01",
        "description": "Green Energy Provider",
        "amount": "85.50",
        "currency": "GBP",
        "debit_credit": "debit",
        "category": "Electricity",
    }
    response = authed_client.post("/api/v1/transactions", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["user_id"] == "CUST-0001"
    assert data["amount"] == "85.50"
    assert data["category"] == "Electricity"
    assert data["transaction_id"].startswith("TXN-")


def test_create_transaction_invalid_date(authed_client):
    """Verify impossible calendar date (e.g., 2026-02-31) is rejected with 422."""
    payload = {
        "date": "2026-02-31",
        "description": "Invalid Date Store",
        "amount": "10.00",
    }
    response = authed_client.post("/api/v1/transactions", json=payload)
    assert response.status_code == 422


def test_create_transaction_empty_description(authed_client):
    """Verify empty or whitespace-only description is rejected with 422."""
    for bad_desc in ["", "   "]:
        payload = {
            "date": "2026-06-01",
            "description": bad_desc,
            "amount": "10.00",
        }
        response = authed_client.post("/api/v1/transactions", json=payload)
        assert response.status_code == 422


def test_create_transaction_invalid_amount(authed_client):
    """Verify non-numeric amount is rejected with 422."""
    payload = {
        "date": "2026-06-01",
        "description": "Store",
        "amount": "not_an_amount",
    }
    response = authed_client.post("/api/v1/transactions", json=payload)
    assert response.status_code == 422


def test_create_transaction_invalid_category(authed_client):
    """Verify non-canonical category is rejected with 422."""
    payload = {
        "date": "2026-06-01",
        "description": "Store",
        "amount": "10.00",
        "category": "NonCanonicalCategory",
    }
    response = authed_client.post("/api/v1/transactions", json=payload)
    assert response.status_code == 422


def test_create_transaction_unexpected_extra_field(authed_client):
    """Verify extra/unexpected fields are forbidden and rejected with 422."""
    payload = {
        "date": "2026-06-01",
        "description": "Store",
        "amount": "10.00",
        "user_id": "HACKER-ATTEMPT",  # Forbidden extra field
    }
    response = authed_client.post("/api/v1/transactions", json=payload)
    assert response.status_code == 422


# Customer Ownership & Scoping Tests
def test_customer_isolation_and_scoping(app_and_db):
    """Verify Customer A cannot retrieve Customer B's transaction (returns 404)."""
    test_app, _ = app_and_db

    # 1. Create transaction as Customer A
    test_app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(user_id="CUST-AAAA")
    client_a = TestClient(test_app)
    create_res = client_a.post(
        "/api/v1/transactions",
        json={"date": "2026-06-01", "description": "Customer A Txn", "amount": "100.00"},
    )
    assert create_res.status_code == 201
    txn_id = create_res.json()["transaction_id"]

    # Customer A lists their transactions -> sees 1
    list_a = client_a.get("/api/v1/transactions")
    assert list_a.status_code == 200
    assert list_a.json()["count"] == 1

    # 2. Switch identity to Customer B
    test_app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(user_id="CUST-BBBB")
    client_b = TestClient(test_app)

    # Customer B lists their transactions -> sees 0
    list_b = client_b.get("/api/v1/transactions")
    assert list_b.status_code == 200
    assert list_b.json()["count"] == 0

    # Customer B attempts to retrieve Customer A's transaction directly by ID -> returns 404
    get_res = client_b.get(f"/api/v1/transactions/{txn_id}")
    assert get_res.status_code == 404
    assert get_res.json()["detail"] == "Transaction not found"

    test_app.dependency_overrides.clear()


# CSV Import & Atomic Rollback Tests
def test_csv_import_success(authed_client):
    """Verify atomic CSV import succeeds for valid rows and scopes to current user."""
    csv_content = (
        "date,description,amount\n"
        "2026-01-10,Grocery Store,45.20\n"
        "2026-01-11,Train Ticket,12.50\n"
    )
    files = {"file": ("txns.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    response = authed_client.post("/api/v1/transactions/import", files=files, data={"currency": "GBP"})
    assert response.status_code == 200
    data = response.json()
    assert data["imported_count"] == 2
    assert "import_batch_id" in data

    # Verify transactions are present in list
    list_res = authed_client.get("/api/v1/transactions")
    assert list_res.json()["count"] == 2


def test_csv_import_atomic_rollback_on_bad_row(authed_client):
    """Verify that a malformed row causes complete rollback with ZERO rows persisted."""
    bad_csv = (
        "date,description,amount\n"
        "2026-01-10,Good Row 1,10.00\n"
        "2026-02-31,Impossible Date Row 2,20.00\n"
    )
    files = {"file": ("bad_txns.csv", io.BytesIO(bad_csv.encode("utf-8")), "text/csv")}
    response = authed_client.post("/api/v1/transactions/import", files=files)
    assert response.status_code == 422
    assert "CSV validation failed" in response.json()["detail"]

    # Verify zero rows were saved
    list_res = authed_client.get("/api/v1/transactions")
    assert list_res.json()["count"] == 0


def test_csv_import_oversized_rejected(authed_client):
    """Verify uploads exceeding the maximum bounded size are rejected with 413."""
    from backend.api.routers.transactions import MAX_CSV_SIZE_BYTES
    oversized = b"a" * (MAX_CSV_SIZE_BYTES + 10)
    files = {"file": ("huge.csv", io.BytesIO(oversized), "text/csv")}
    response = authed_client.post("/api/v1/transactions/import", files=files)
    assert response.status_code == 413
