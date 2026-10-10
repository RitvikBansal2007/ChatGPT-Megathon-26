import hashlib
import json
from datetime import datetime, timezone

from greenproof.db.repo import connect

GENESIS = "0" * 64

def _canonical(rec: dict) -> str:
    return json.dumps(rec, sort_keys=True, separators=(",", ":"))

def _hash(prev_hash: str, rec: dict) -> str:
    return hashlib.sha256((prev_hash + _canonical(rec)).encode()).hexdigest()

def append(customer_key: str, product_id: str, verdict: str, rules_violated: list[str], source: str) -> str:
    rec = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "customer_key": customer_key, "product_id": product_id, "verdict": verdict,
        "rules_violated": json.dumps(rules_violated), "source": source,
    }
    with connect(read_only=False) as c:
        c.execute("BEGIN IMMEDIATE")
        row = c.execute("SELECT row_hash FROM claim_audit ORDER BY id DESC LIMIT 1").fetchone()
        prev = row["row_hash"] if row else GENESIS
        h = _hash(prev, rec)
        c.execute(
            "INSERT INTO claim_audit (ts, customer_key, product_id, verdict, rules_violated, source, prev_hash, row_hash) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (rec["ts"], customer_key, product_id, verdict, rec["rules_violated"], source, prev, h),
        )
        c.execute("COMMIT")
    return h

def verify_chain() -> tuple[bool, int | None]:
    prev = GENESIS
    with connect() as c:
        for r in c.execute("SELECT * FROM claim_audit ORDER BY id"):
            rec = {k: r[k] for k in ("ts", "customer_key", "product_id", "verdict", "rules_violated", "source")}
            if r["prev_hash"] != prev or r["row_hash"] != _hash(prev, rec):
                return False, r["id"]
            prev = r["row_hash"]
    return True, None
