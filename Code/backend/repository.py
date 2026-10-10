"""Repository layer for users and transactions, plus explicit CSV importers."""

import csv
import datetime
import io
import re
import uuid
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# The exact 8 categories from Code/config/categories.yaml
CANONICAL_CATEGORIES = frozenset({
    "Fuel",
    "Electricity",
    "Gas",
    "Public Transport",
    "Home Improvement",
    "Automotive",
    "Utilities",
    "Other",
})

DECIMAL_REGEX = re.compile(r"^-?\d+(\.\d+)?$")
DATE_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def validate_amount(amount: Union[str, int, float, Decimal]) -> str:
    """Validate amount and return it as an exact decimal string without floating-point distortion."""
    amt_str = str(amount).strip()
    if not DECIMAL_REGEX.match(amt_str):
        raise ValueError(f"Invalid monetary amount format: '{amount}'")
    try:
        Decimal(amt_str)
    except InvalidOperation:
        raise ValueError(f"Invalid decimal value: '{amount}'")
    return amt_str


def validate_category(category: Optional[str]) -> Optional[str]:
    """Validate category against canonical list or return None."""
    if category is None or category == "":
        return None
    if category not in CANONICAL_CATEGORIES:
        raise ValueError(f"Category '{category}' is not one of the canonical categories: {sorted(CANONICAL_CATEGORIES)}")
    return category


def validate_date(date_str: str) -> str:
    """Validate date format is YYYY-MM-DD and is a real calendar date (e.g. rejects 2026-02-31)."""
    if not isinstance(date_str, str):
        raise ValueError(f"Date must be a string, got {type(date_str).__name__}")
    d = date_str.strip()
    if not DATE_REGEX.match(d):
        raise ValueError(f"Invalid date format '{date_str}', expected YYYY-MM-DD")
    try:
        datetime.date.fromisoformat(d)
    except ValueError as e:
        raise ValueError(f"Invalid calendar date '{date_str}': {e}") from e
    return d


VALID_DEBIT_CREDIT = frozenset({"debit", "credit"})


def validate_debit_credit(val: Optional[str]) -> Optional[str]:
    """Validate debit_credit is 'debit', 'credit', or None."""
    if val is None or val == "":
        return None
    clean = str(val).strip().lower()
    if clean not in VALID_DEBIT_CREDIT:
        raise ValueError(f"Invalid debit_credit '{val}', expected 'debit' or 'credit'")
    return clean


# Privacy helper reusing the security team's existing module
def pseudonymise_identifier(raw_id: str, key: Optional[bytes] = None) -> str:
    """Helper delegating to the security module if pseudonymisation is requested."""
    try:
        from security.privacy import pseudonymise
        return pseudonymise(raw_id, key=key)
    except ImportError:
        import sys
        sys_path = Path(__file__).resolve().parent.parent
        if str(sys_path) not in sys.path:
            sys.path.insert(0, str(sys_path))
        from security.privacy import pseudonymise
        return pseudonymise(raw_id, key=key)


# User operations
def create_user(
    conn,
    user_id: str,
    role: str = "customer",
    account_status: str = "active",
) -> Dict[str, Any]:
    """Insert a user record."""
    if not user_id or not user_id.strip():
        raise ValueError("user_id cannot be empty")
    query = """
    INSERT INTO users (user_id, role, account_status)
    VALUES (?, ?, ?)
    """
    conn.execute(query, (user_id.strip(), role, account_status))
    return get_user(conn, user_id.strip())


def get_user(conn, user_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a user by user_id."""
    cursor = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id.strip(),))
    row = cursor.fetchone()
    return dict(row) if row else None


def list_users(conn) -> List[Dict[str, Any]]:
    """Retrieve all users ordered by created_at."""
    cursor = conn.execute("SELECT * FROM users ORDER BY created_at ASC")
    return [dict(row) for row in cursor.fetchall()]


# Transaction operations
def create_transaction(
    conn,
    transaction_id: str,
    user_id: str,
    date: str,
    description: str,
    amount: Union[str, Decimal],
    currency: Optional[str] = None,
    debit_credit: Optional[str] = None,
    category: Optional[str] = None,
    import_batch_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Insert a single transaction record with validated fields and foreign keys."""
    if not transaction_id or not str(transaction_id).strip():
        raise ValueError("transaction_id cannot be empty or whitespace-only")
    t_id = str(transaction_id).strip()

    if not user_id or not str(user_id).strip():
        raise ValueError("user_id cannot be empty or whitespace-only")
    u_id = str(user_id).strip()

    if not description or not str(description).strip():
        raise ValueError("Transaction description cannot be empty or whitespace-only")
    desc = str(description).strip()

    d_str = validate_date(date)
    amt_str = validate_amount(amount)
    cat = validate_category(category)
    dc = validate_debit_credit(debit_credit)
    curr = currency.strip() if currency and currency.strip() else None

    query = """
    INSERT INTO transactions (
        transaction_id, user_id, date, description, amount,
        currency, debit_credit, category, import_batch_id
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    conn.execute(
        query,
        (t_id, u_id, d_str, desc, amt_str, curr, dc, cat, import_batch_id),
    )
    return get_transaction(conn, t_id)


def get_transaction(conn, transaction_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a single transaction by ID."""
    cursor = conn.execute("SELECT * FROM transactions WHERE transaction_id = ?", (transaction_id.strip(),))
    row = cursor.fetchone()
    return dict(row) if row else None


def get_transactions_by_user(conn, user_id: str) -> List[Dict[str, Any]]:
    """Retrieve all transactions for a user ordered by date descending."""
    cursor = conn.execute(
        "SELECT * FROM transactions WHERE user_id = ? ORDER BY date DESC, transaction_id ASC",
        (user_id.strip(),),
    )
    return [dict(row) for row in cursor.fetchall()]


# Explicit CSV Importers with atomic savepoint protection
def import_raw_dataset_csv(
    conn,
    csv_source: Union[str, Path, io.StringIO],
    batch_id: Optional[str] = None,
) -> int:
    """Explicit importer for Code/data/raw/transactions.csv structure.
    
    Columns: transaction_id, customer_id, date, merchant_description, amount, debit_credit, true_category
    Currency is saved as NULL since the raw dataset does not supply a currency.
    Atomicity: Wrapped in a SAVEPOINT so that if any row is invalid, all rows are rolled back.
    """
    b_id = batch_id or f"raw_{uuid.uuid4().hex[:8]}"
    count = 0

    if isinstance(csv_source, (str, Path)) and not isinstance(csv_source, io.StringIO):
        f = open(csv_source, "r", encoding="utf-8")
        should_close = True
    else:
        f = csv_source
        should_close = False

    savepoint_name = f"sp_raw_{uuid.uuid4().hex[:8]}"
    conn.execute(f"SAVEPOINT {savepoint_name}")
    try:
        reader = csv.DictReader(f)
        required_cols = {"transaction_id", "customer_id", "date", "merchant_description", "amount"}
        if not required_cols.issubset(set(reader.fieldnames or [])):
            raise ValueError(f"Missing required columns in raw dataset CSV: {required_cols - set(reader.fieldnames or [])}")

        for row in reader:
            create_transaction(
                conn=conn,
                transaction_id=row["transaction_id"],
                user_id=row["customer_id"],
                date=row["date"],
                description=row["merchant_description"],
                amount=row["amount"],
                currency=None,  # Not present in raw dataset; preserve as NULL
                debit_credit=row.get("debit_credit"),
                category=row.get("true_category"),
                import_batch_id=b_id,
            )
            count += 1
        conn.execute(f"RELEASE SAVEPOINT {savepoint_name}")
    except Exception:
        conn.execute(f"ROLLBACK TO SAVEPOINT {savepoint_name}")
        conn.execute(f"RELEASE SAVEPOINT {savepoint_name}")
        raise
    finally:
        if should_close:
            f.close()

    return count


def import_simple_csv(
    conn,
    csv_source: Union[str, Path, io.StringIO],
    user_id: str,
    currency: Optional[str] = None,
    batch_id: Optional[str] = None,
) -> int:
    """Explicit importer for simple 3-column CSV: date, description, amount.
    
    Currency is saved as given (or NULL if omitted, never defaults to GBP).
    Atomicity: Wrapped in a SAVEPOINT so that if any row is invalid, all rows are rolled back.
    """
    b_id = batch_id or f"simple_{uuid.uuid4().hex[:8]}"
    count = 0

    if isinstance(csv_source, (str, Path)) and not isinstance(csv_source, io.StringIO):
        f = open(csv_source, "r", encoding="utf-8")
        should_close = True
    else:
        f = csv_source
        should_close = False

    savepoint_name = f"sp_simple_{uuid.uuid4().hex[:8]}"
    conn.execute(f"SAVEPOINT {savepoint_name}")
    try:
        reader = csv.DictReader(f)
        required_cols = {"date", "description", "amount"}
        if not required_cols.issubset(set(reader.fieldnames or [])):
            raise ValueError(f"Missing required columns in simple CSV: {required_cols - set(reader.fieldnames or [])}")

        for i, row in enumerate(reader, start=1):
            t_id = f"{b_id}_{i:05d}"
            create_transaction(
                conn=conn,
                transaction_id=t_id,
                user_id=user_id,
                date=row["date"],
                description=row["description"],
                amount=row["amount"],
                currency=currency,
                debit_credit=None,
                category=None,
                import_batch_id=b_id,
            )
            count += 1
        conn.execute(f"RELEASE SAVEPOINT {savepoint_name}")
    except Exception:
        conn.execute(f"ROLLBACK TO SAVEPOINT {savepoint_name}")
        conn.execute(f"RELEASE SAVEPOINT {savepoint_name}")
        raise
    finally:
        if should_close:
            f.close()

    return count
