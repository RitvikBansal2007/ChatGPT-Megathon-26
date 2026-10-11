import json
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

from config.settings import settings
from greendash.security.authz import hash_password, verify_password

def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

@contextmanager
def connect(read_only: bool = True):
    mode = "ro" if read_only else "rw"
    conn = sqlite3.connect(f"file:{settings.DB_PATH}?mode={mode}", uri=True, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
    finally:
        conn.close()

def log_scenario_run(customer_key: str, mutations: list[str], before: dict, after: dict, elapsed_ms: int) -> None:
    with connect(read_only=False) as c:
        c.execute(
            "INSERT INTO scenario_runs (ts, customer_key, mutations, before_status, after_status, elapsed_ms) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (_now(), customer_key, json.dumps(mutations), json.dumps(before), json.dumps(after), elapsed_ms),
        )

def add_feedback(customer_key: str, product_id: str, kind: str, note_enc: bytes | None) -> None:
    with connect(read_only=False) as c:
        c.execute(
            "INSERT INTO feedback (ts, customer_key, product_id, kind, note_enc) VALUES (?, ?, ?, ?, ?)",
            (_now(), customer_key, product_id, kind, note_enc),
        )

def set_optout(customer_key: str, opted_out: bool) -> None:
    with connect(read_only=False) as c:
        c.execute(
            "INSERT INTO optouts (customer_key, opted_out, updated_at) VALUES (?, ?, ?) "
            "ON CONFLICT(customer_key) DO UPDATE SET opted_out = excluded.opted_out, updated_at = excluded.updated_at",
            (customer_key, int(opted_out), _now()),
        )

def is_opted_out(customer_key: str) -> bool:
    with connect() as c:
        row = c.execute("SELECT opted_out FROM optouts WHERE customer_key = ?", (customer_key,)).fetchone()
    return bool(row["opted_out"]) if row else False

def claims_blocked_total() -> int:
    with connect() as c:
        return c.execute(
            "SELECT COUNT(*) AS n FROM claim_audit WHERE verdict IN ('BLOCKED','FALLBACK','PII_BLOCK')"
        ).fetchone()["n"]

def audit_summary() -> dict:
    with connect() as c:
        rows = c.execute("SELECT verdict, COUNT(*) AS n FROM claim_audit GROUP BY verdict").fetchall()
    return {r["verdict"]: r["n"] for r in rows}

# ------------------------------------------------------------------ users & auth
DEMO_PERSONAS = [
    ("CUST-0001", "CUSTOMER", "priya@greenproof.bank", "Priya Sharma"),
    ("CUST-0002", "CUSTOMER", "marcus@greenproof.bank", "Marcus Chen"),
    ("CUST-0003", "CUSTOMER", "aisha@greenproof.bank", "Aisha Patel"),
    ("CUST-0004", "CUSTOMER", "tom@greenproof.bank", "Tom Wilson"),
    ("CUST-0005", "CUSTOMER", "dave@greenproof.bank", "Dave Evans"),
    ("CUST-0006", "CUSTOMER", "sam@greenproof.bank", "Sam Taylor"),
    ("CUST-0007", "CUSTOMER", "elena@greenproof.bank", "Elena Rossi"),
    ("CUST-0008", "CUSTOMER", "jordan@greenproof.bank", "Jordan Smith"),
    ("rm_user", "RELATIONSHIP_MANAGER", "rm@greenproof.bank", "Sarah Jenkins (RM)"),
    ("analyst_user", "PORTFOLIO_ANALYST", "analyst@greenproof.bank", "Alex Morgan (Portfolio Analyst)"),
    ("auditor_user", "AUDITOR", "auditor@greenproof.bank", "Hannah Scott (Auditor)"),
    ("evaluator_user", "EVALUATOR", "evaluator@greenproof.bank", "Dr. James Clark (Evaluator)"),
]

def ensure_seeded_users() -> None:
    with connect(read_only=False) as c:
        count = c.execute("SELECT COUNT(*) AS n FROM users").fetchone()["n"]
        if count == 0:
            default_hash = hash_password("password123")
            for ukey, role, email, dname in DEMO_PERSONAS:
                c.execute(
                    "INSERT INTO users (user_key, role, email, display_name, password_hash, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (ukey, role, email, dname, default_hash, _now()),
                )

def get_user(identifier: str) -> dict | None:
    ensure_seeded_users()
    with connect() as c:
        row = c.execute(
            "SELECT user_key, role, email, display_name, password_hash, created_at FROM users "
            "WHERE user_key = ? OR lower(email) = lower(?)",
            (identifier, identifier),
        ).fetchone()
        if not row:
            # Check prefix match for personas (e.g. 'priya' -> CUST-0001)
            row = c.execute(
                "SELECT user_key, role, email, display_name, password_hash, created_at FROM users "
                "WHERE lower(display_name) LIKE lower(?)",
                (f"%{identifier}%",),
            ).fetchone()
        if row:
            return dict(row)
    return None

def authenticate_user(username_or_email: str, password: str) -> dict | None:
    user = get_user(username_or_email)
    if not user:
        return None
    if verify_password(user["password_hash"], password):
        user_copy = dict(user)
        user_copy.pop("password_hash", None)
        return user_copy
    return None

def list_users() -> list[dict]:
    ensure_seeded_users()
    with connect() as c:
        rows = c.execute("SELECT user_key, role, email, display_name, created_at FROM users ORDER BY rowid").fetchall()
        return [dict(r) for r in rows]

def register_user(email: str, password: str, display_name: str, role: str = "CUSTOMER") -> dict:
    ensure_seeded_users()
    clean_email = email.strip().lower()
    clean_name = display_name.strip()
    if not clean_email or "@" not in clean_email:
        raise ValueError("A valid email address is required")
    if not clean_name:
        raise ValueError("Full name is required")
    if len(password) < 6:
        raise ValueError("Password must be at least 6 characters")

    with connect(read_only=False) as c:
        existing = c.execute("SELECT user_key FROM users WHERE lower(email) = ?", (clean_email,)).fetchone()
        if existing:
            raise ValueError(f"An account with email {clean_email} already exists")

        if role == "CUSTOMER":
            # Assign next available CUST-000X
            last_cust = c.execute("SELECT user_key FROM users WHERE user_key LIKE 'CUST-%' ORDER BY user_key DESC LIMIT 1").fetchone()
            if last_cust:
                try:
                    num = int(last_cust["user_key"].split("-")[1]) + 1
                    user_key = f"CUST-{num:04d}"
                except Exception:
                    user_key = f"CUST-{secrets.token_hex(2).upper()}"
            else:
                user_key = "CUST-0009"
        else:
            base_key = clean_email.split("@")[0].replace(".", "_")
            user_key = f"{base_key}_{role.lower()}"

        pw_hash = hash_password(password)
        now_str = _now()
        c.execute(
            "INSERT INTO users (user_key, role, email, display_name, password_hash, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (user_key, role, clean_email, clean_name, pw_hash, now_str),
        )
        return {
            "user_key": user_key,
            "role": role,
            "email": clean_email,
            "display_name": clean_name,
            "created_at": now_str,
            "customer_id": user_key if role == "CUSTOMER" else None,
        }


# ------------------------------------------------------------------ customer memory
INITIAL_MEMORIES = [
    ("CUST-0001", "driveway_parking", "Customer confirmed off-street driveway parking suitable for home 7kW charger", "declared_fact", "customer_declared"),
    ("CUST-0001", "green_interest", "Interested in reducing vehicle operating emissions and monthly fuel spend", "preference", "customer_declared"),
    ("CUST-0002", "home_renovation", "Planning loft insulation and solar heating renovation in Q3 2026", "goal", "rm_note"),
    ("CUST-0003", "transit_preference", "Relies entirely on London transit and cycling; no vehicle owned or planned", "preference", "customer_declared"),
    ("CUST-0004", "digital_native", "Prefers paperless billing; opted in to digital communications across all accounts", "preference", "system_inferred"),
    ("CUST-0006", "energy_bill_concern", "Reported high winter gas bills; requested heat pump grant information", "interaction", "rm_note"),
]

def ensure_seeded_memory() -> None:
    with connect(read_only=False) as c:
        count = c.execute("SELECT COUNT(*) AS n FROM customer_memory").fetchone()["n"]
        if count == 0:
            for ckey, key, val, cat, src in INITIAL_MEMORIES:
                c.execute(
                    "INSERT INTO customer_memory (ts, customer_key, key, value, category, source) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (_now(), ckey, key, val, cat, src),
                )

def get_customer_memory(customer_key: str) -> list[dict]:
    ensure_seeded_memory()
    with connect() as c:
        rows = c.execute(
            "SELECT id, ts, customer_key, key, value, category, source FROM customer_memory "
            "WHERE customer_key = ? ORDER BY id DESC",
            (customer_key,),
        ).fetchall()
        return [dict(r) for r in rows]

def add_customer_memory(customer_key: str, key: str, value: str,
                        category: str = "preference", source: str = "customer_declared") -> dict:
    ensure_seeded_memory()
    now_str = _now()
    with connect(read_only=False) as c:
        cursor = c.execute(
            "INSERT INTO customer_memory (ts, customer_key, key, value, category, source) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (now_str, customer_key, key, value, category, source),
        )
        return {
            "id": cursor.lastrowid,
            "ts": now_str,
            "customer_key": customer_key,
            "key": key,
            "value": value,
            "category": category,
            "source": source,
        }

def delete_customer_memory(customer_key: str, memory_id: int) -> bool:
    with connect(read_only=False) as c:
        cursor = c.execute(
            "DELETE FROM customer_memory WHERE customer_key = ? AND id = ?",
            (customer_key, memory_id),
        )
        return cursor.rowcount > 0

