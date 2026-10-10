"""The single data gateway for the GreenDash UI.

Pages call these functions and nothing else for data. DEMO_MODE (env) picks
the source:

  fixtures (default)  read contract-shaped JSON from <repo>/fixtures/
  cached / live       not implemented yet (Step 3.5)

Contract shapes mirror greenproof/contracts.py (frozen by Akshit, G1-A).

Rules:
- Never holds the LLM key
- Never logs request or response bodies
- No network calls in fixtures mode
- Path-traversal guard on all IDs used in filenames
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

VALID_MODES = ("fixtures", "cached", "live")
FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"

_SAFE_ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")

# Status → per-status fixture file name (Akshit's naming convention)
_STATUS_FIXTURES = {
    "RECOMMEND":    "opps_recommend",
    "SOFT_SURFACE": "opps_soft_surface",
    "ABSTAIN":      "opps_abstain",
    "REVIEW":       "opps_review",
    "RULED_OUT":    "opps_ruled_out",
}

# Customer → which status fixture to load first for that persona
_CUSTOMER_STATUS_MAP = {
    "CUST-0001": "RECOMMEND",    # Priya — EV RECOMMEND
    "CUST-0002": "REVIEW",       # Marcus — REVIEW
    "CUST-0003": "RULED_OUT",    # Aisha — all RULED_OUT
    "CUST-0004": "SOFT_SURFACE", # Fatima — SOFT_SURFACE
}


def demo_mode() -> str:
    """Return DEMO_MODE env, validated."""
    mode = os.environ.get("DEMO_MODE", "fixtures").strip().lower()
    if mode not in VALID_MODES:
        raise ValueError(f"DEMO_MODE must be one of {VALID_MODES}, got {mode!r}")
    return mode


def _require_fixtures() -> None:
    if demo_mode() != "fixtures":
        raise NotImplementedError("Coming in Step 3.5")


def _safe_id(value: str, field: str) -> str:
    if not isinstance(value, str) or not _SAFE_ID.match(value):
        raise ValueError(f"invalid {field}")
    return value


def _load(name: str) -> Any:
    path = FIXTURES_DIR / f"{name}.json"
    if not path.is_file():
        raise FileNotFoundError(f"fixture not found: fixtures/{name}.json")
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def _unwrap_opportunities(data: Any) -> list[dict]:
    """Handle both the wrapper shape (CustomerOpportunities) and plain lists."""
    if isinstance(data, dict) and "opportunities" in data:
        return list(data["opportunities"])
    if isinstance(data, list):
        return data
    return []


# ── Public API ────────────────────────────────────────────────────────────────

def get_opportunities(customer_id: str) -> list[dict]:
    """Return opportunity list for one customer.

    Loading order:
    1. fixtures/opportunities_<customer_id>.json   (per-customer override)
    2. Status-based fixture from _CUSTOMER_STATUS_MAP + all other status fixtures
       combined into one list (covers all five status examples for the demo)
    3. fixtures/opportunities.json                 (legacy fallback)
    """
    _require_fixtures()
    cid = _safe_id(customer_id, "customer_id")

    # 1. Per-customer override
    per_cust = FIXTURES_DIR / f"opportunities_{cid}.json"
    if per_cust.is_file():
        return _unwrap_opportunities(_load(f"opportunities_{cid}"))

    # 2. Combine all 5 per-status fixtures → one opportunity per product
    #    Primary status from _CUSTOMER_STATUS_MAP; the rest fill the other products
    opps: list[dict] = []
    primary_status = _CUSTOMER_STATUS_MAP.get(cid, "RECOMMEND")
    seen_products: set[str] = set()

    # Load primary status first so it sorts top
    primary_file = _STATUS_FIXTURES[primary_status]
    try:
        primary_opps = _unwrap_opportunities(_load(primary_file))
        for o in primary_opps:
            pid = o.get("opportunity_id", "")
            if pid not in seen_products:
                opps.append(o)
                seen_products.add(pid)
    except FileNotFoundError:
        pass

    # Fill remaining products with the other status fixtures
    for status, fname in _STATUS_FIXTURES.items():
        if status == primary_status:
            continue
        try:
            for o in _unwrap_opportunities(_load(fname)):
                pid = o.get("opportunity_id", "")
                if pid not in seen_products:
                    opps.append(o)
                    seen_products.add(pid)
        except FileNotFoundError:
            pass

    if opps:
        return opps

    # 3. Legacy fallback
    legacy = _load("opportunities") if (FIXTURES_DIR / "opportunities.json").is_file() else []
    return _unwrap_opportunities(legacy)


def run_scenario(customer_id: str, mutations: list[str] | list[dict] | dict) -> dict:
    """Scenario Lab result. fixtures mode returns canned scenario_response.json."""
    _require_fixtures()
    _safe_id(customer_id, "customer_id")
    if not isinstance(mutations, (list, dict)):
        raise ValueError("mutations must be a list or dict")
    return dict(_load("scenario_response"))


def claimcheck(customer_id: str, opportunity_id: str, sentences: list[str]) -> dict:
    """Claim-Check result. fixtures mode returns canned claimcheck_response.json."""
    _require_fixtures()
    _safe_id(customer_id, "customer_id")
    _safe_id(opportunity_id, "opportunity_id")
    if not isinstance(sentences, list) or not all(isinstance(s, str) for s in sentences):
        raise ValueError("sentences must be a list of strings")
    return dict(_load("claimcheck_response"))


def get_portfolio() -> dict:
    """k-anonymised portfolio aggregates for the Cockpit."""
    _require_fixtures()
    return dict(_load("portfolio"))


def get_eval() -> dict:
    """Evaluation summary for the Receipts page."""
    _require_fixtures()
    return dict(_load("eval"))
