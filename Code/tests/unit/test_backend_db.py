"""Unit tests for the GreenProof backend database, repository layer, and CSV validation."""

import io
import os
import sqlite3
import sys
from pathlib import Path
import pytest

# Ensure Code directory is on sys.path
CODE_ROOT = Path(__file__).resolve().parent.parent.parent
if str(CODE_ROOT) not in sys.path:
    sys.path.insert(0, str(CODE_ROOT))

from backend.db import get_connection, apply_schema, db_session
from backend import repository


@pytest.fixture
def mem_db():
    """Create a freshly initialized in-memory database with foreign keys active."""
    conn = get_connection(":memory:")
    apply_schema(conn)
    yield conn
    conn.close()


def test_schema_tables_and_indexes_exist(mem_db):
    """Verify users and transactions tables and indexes are created on the active connection."""
    cur = mem_db.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {r["name"] for r in cur.fetchall()}
    assert "users" in tables
    assert "transactions" in tables

    idx_cur = mem_db.execute("SELECT name FROM sqlite_master WHERE type='index'")
    indexes = {r["name"] for r in idx_cur.fetchall()}
    assert "idx_transactions_user_id" in indexes
    assert "idx_transactions_date" in indexes
    assert "idx_transactions_category" in indexes
    assert "idx_transactions_batch" in indexes


def test_user_creation_and_retrieval(mem_db):
    """Verify user creation, uniqueness, and querying."""
    user = repository.create_user(mem_db, "CUST-0001", role="customer", account_status="active")
    assert user["user_id"] == "CUST-0001"
    assert user["role"] == "customer"
    assert user["account_status"] == "active"
    assert user["created_at"] is not None

    fetched = repository.get_user(mem_db, "CUST-0001")
    assert fetched == user

    # Empty user_id must be rejected
    with pytest.raises(ValueError, match="user_id cannot be empty"):
        repository.create_user(mem_db, "   ")


def test_foreign_key_on_delete_restrict(mem_db):
    """Verify ON DELETE RESTRICT prevents deleting a user with active transactions."""
    repository.create_user(mem_db, "CUST-0001")
    repository.create_transaction(
        mem_db,
        transaction_id="TXN-001",
        user_id="CUST-0001",
        date="2026-06-01",
        description="Electric Company",
        amount="50.00",
    )

    # Deleting user must fail because transactions reference it with ON DELETE RESTRICT
    with pytest.raises(sqlite3.IntegrityError):
        mem_db.execute("DELETE FROM users WHERE user_id = 'CUST-0001'")


def test_foreign_key_rejects_nonexistent_user(mem_db):
    """Verify foreign keys prevent inserting transaction for non-existent user."""
    with pytest.raises(sqlite3.IntegrityError):
        repository.create_transaction(
            mem_db,
            transaction_id="TXN-002",
            user_id="NONEXISTENT_USER",
            date="2026-06-01",
            description="Merchant",
            amount="25.50",
        )


def test_amount_precision_preservation_no_float_rounding(mem_db):
    """Verify monetary amounts are saved as exact decimal strings with zero floating-point rounding."""
    repository.create_user(mem_db, "CUST-0001")
    raw_amount = "113.10423866418128"
    tx = repository.create_transaction(
        mem_db,
        transaction_id="TXN-003",
        user_id="CUST-0001",
        date="2026-06-01",
        description="Council Tax",
        amount=raw_amount,
    )
    assert tx["amount"] == raw_amount
    assert isinstance(tx["amount"], str)


def test_invalid_amount_rejected(mem_db):
    """Verify non-numeric monetary amounts raise ValueError."""
    repository.create_user(mem_db, "CUST-0001")
    for bad_amt in ["abc", "$12.50", "12,50", "12.34.56"]:
        with pytest.raises(ValueError, match="Invalid monetary amount format"):
            repository.create_transaction(
                mem_db,
                transaction_id=f"TXN-BAD-{bad_amt}",
                user_id="CUST-0001",
                date="2026-06-01",
                description="Invalid",
                amount=bad_amt,
            )


def test_real_calendar_date_validation(mem_db):
    """Verify impossible calendar dates like 2026-02-31 are rejected."""
    repository.create_user(mem_db, "CUST-0001")
    
    # Valid leap day in 2024
    repository.create_transaction(
        mem_db,
        transaction_id="TXN-LEAP",
        user_id="CUST-0001",
        date="2024-02-29",
        description="Valid Leap Day",
        amount="10.00",
    )

    # Impossible dates
    for bad_date in ["2026-02-31", "2026-04-31", "2026-13-01", "2026-00-10", "invalid-date"]:
        with pytest.raises(ValueError):
            repository.create_transaction(
                mem_db,
                transaction_id=f"TXN-DATE-{bad_date}",
                user_id="CUST-0001",
                date=bad_date,
                description="Bad Date",
                amount="10.00",
            )


def test_currency_preservation_no_implicit_gbp(mem_db):
    """Verify currency is NULL unless explicitly provided."""
    repository.create_user(mem_db, "CUST-0001")
    tx_no_curr = repository.create_transaction(
        mem_db,
        transaction_id="TXN-005",
        user_id="CUST-0001",
        date="2026-06-01",
        description="Unknown currency",
        amount="10.00",
    )
    assert tx_no_curr["currency"] is None

    tx_with_curr = repository.create_transaction(
        mem_db,
        transaction_id="TXN-006",
        user_id="CUST-0001",
        date="2026-06-01",
        description="Explicit EUR",
        amount="10.00",
        currency="EUR",
    )
    assert tx_with_curr["currency"] == "EUR"


def test_canonical_categories_enforcement(mem_db):
    """Verify only the 8 canonical categories from Code/config/categories.yaml are permitted."""
    repository.create_user(mem_db, "CUST-0001")
    for valid_cat in repository.CANONICAL_CATEGORIES:
        tx = repository.create_transaction(
            mem_db,
            transaction_id=f"TXN-CAT-{valid_cat}",
            user_id="CUST-0001",
            date="2026-06-01",
            description="Valid Category",
            amount="10.00",
            category=valid_cat,
        )
        assert tx["category"] == valid_cat

    with pytest.raises(ValueError, match="is not one of the canonical categories"):
        repository.create_transaction(
            mem_db,
            transaction_id="TXN-INVALID-CAT",
            user_id="CUST-0001",
            date="2026-06-01",
            description="Bad Category",
            amount="10.00",
            category="NonExistentCategory",
        )


def test_raw_dataset_csv_import(mem_db):
    """Verify explicit import of the 7-column raw dataset format."""
    repository.create_user(mem_db, "CUST-0001")
    csv_data = io.StringIO(
        "transaction_id,customer_id,date,merchant_description,amount,debit_credit,true_category\n"
        "TXN-000001,CUST-0001,2025-07-13,PAYPAL *COUNCIL TAX 803 GLASGOW,113.10423866418128,debit,Utilities\n"
        "TXN-000002,CUST-0001,2025-12-30,BRITISH GAS DUAL BRISTOL,204.5482374954356,debit,Utilities\n"
    )
    imported = repository.import_raw_dataset_csv(mem_db, csv_data, batch_id="batch_01")
    assert imported == 2

    txs = repository.get_transactions_by_user(mem_db, "CUST-0001")
    assert len(txs) == 2
    # Verify no implicit GBP: raw dataset has no currency column
    assert txs[0]["currency"] is None
    assert txs[0]["category"] == "Utilities"


def test_simple_csv_import(mem_db):
    """Verify explicit import of the 3-column simple CSV format."""
    repository.create_user(mem_db, "CUST-0002")
    csv_data = io.StringIO(
        "date,description,amount\n"
        "2026-01-15,Supermarket,45.20\n"
        "2026-01-16,Coffee Shop,3.50\n"
    )
    imported = repository.import_simple_csv(
        mem_db,
        csv_data,
        user_id="CUST-0002",
        currency="GBP",
        batch_id="batch_simple_01",
    )
    assert imported == 2

    txs = repository.get_transactions_by_user(mem_db, "CUST-0002")
    assert len(txs) == 2
    assert txs[0]["currency"] == "GBP"


def test_atomic_rollback_on_csv_error_leaves_zero_rows(mem_db):
    """Verify an invalid row in a batch causes rollback so ZERO rows from that batch remain."""
    repository.create_user(mem_db, "CUST-0003")
    bad_csv = io.StringIO(
        "date,description,amount\n"
        "2026-01-15,Valid Row 1,10.00\n"
        "2026-02-31,Invalid Impossible Date,25.00\n"
    )
    with pytest.raises(ValueError):
        repository.import_simple_csv(mem_db, bad_csv, user_id="CUST-0003", batch_id="batch_fail")

    # Verify that zero rows from that batch were persisted
    txs = repository.get_transactions_by_user(mem_db, "CUST-0003")
    assert len(txs) == 0


def test_privacy_pseudonymise_delegation():
    """Verify optional helper delegating to the security module."""
    # When PSEUDONYM_KEY is provided, it returns a 16-character hex pseudonym
    os.environ["PSEUDONYM_KEY"] = "test_secret_key_12345"
    try:
        pseudo = repository.pseudonymise_identifier("CUST-0001")
        assert isinstance(pseudo, str)
        assert len(pseudo) == 16
    finally:
        os.environ.pop("PSEUDONYM_KEY", None)


def test_empty_or_whitespace_description_rejected(mem_db):
    """Verify empty or whitespace-only descriptions raise ValueError."""
    repository.create_user(mem_db, "CUST-0001")
    for bad_desc in ["", "   ", "\t\n"]:
        with pytest.raises(ValueError, match="description cannot be empty or whitespace-only"):
            repository.create_transaction(
                mem_db,
                transaction_id=f"TXN-DESC-{hash(bad_desc)}",
                user_id="CUST-0001",
                date="2026-06-01",
                description=bad_desc,
                amount="15.00",
            )


def test_duplicate_transaction_id_rejected(mem_db):
    """Verify inserting duplicate transaction IDs raises sqlite3.IntegrityError."""
    repository.create_user(mem_db, "CUST-0001")
    repository.create_transaction(
        mem_db,
        transaction_id="TXN-DUP-001",
        user_id="CUST-0001",
        date="2026-06-01",
        description="First attempt",
        amount="20.00",
    )
    with pytest.raises(sqlite3.IntegrityError):
        repository.create_transaction(
            mem_db,
            transaction_id="TXN-DUP-001",
            user_id="CUST-0001",
            date="2026-06-02",
            description="Duplicate attempt",
            amount="30.00",
        )


def test_invalid_debit_credit_rejected(mem_db):
    """Verify invalid debit_credit values are rejected."""
    repository.create_user(mem_db, "CUST-0001")
    with pytest.raises(ValueError, match="Invalid debit_credit"):
        repository.create_transaction(
            mem_db,
            transaction_id="TXN-DC-BAD",
            user_id="CUST-0001",
            date="2026-06-01",
            description="Merchant",
            amount="10.00",
            debit_credit="transfer",
        )

    # Valid values
    tx_debit = repository.create_transaction(
        mem_db,
        transaction_id="TXN-DC-DEBIT",
        user_id="CUST-0001",
        date="2026-06-01",
        description="Debit Merchant",
        amount="10.00",
        debit_credit="debit",
    )
    assert tx_debit["debit_credit"] == "debit"


def test_empty_transaction_and_user_ids_rejected(mem_db):
    """Verify empty or whitespace-only transaction_id or user_id are rejected."""
    repository.create_user(mem_db, "CUST-0001")
    with pytest.raises(ValueError, match="transaction_id cannot be empty"):
        repository.create_transaction(
            mem_db,
            transaction_id="   ",
            user_id="CUST-0001",
            date="2026-06-01",
            description="Merchant",
            amount="10.00",
        )

    with pytest.raises(ValueError, match="user_id cannot be empty"):
        repository.create_transaction(
            mem_db,
            transaction_id="TXN-OK",
            user_id="   ",
            date="2026-06-01",
            description="Merchant",
            amount="10.00",
        )
