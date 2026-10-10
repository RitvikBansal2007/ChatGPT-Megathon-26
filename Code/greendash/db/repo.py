import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

from config.settings import settings

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
