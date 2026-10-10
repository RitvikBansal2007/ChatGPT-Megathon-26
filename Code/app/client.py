"""The single data gateway for the GreenDash UI.

Pages call these functions and nothing else for data. DEMO_MODE (env) picks
the source:

  fixtures (default)  read contract-shaped JSON from <repo>/fixtures/<name>.json
  cached / live       not implemented yet (Step 3.5)

Rules: this module never holds the LLM key, never logs request or response
bodies, and makes no network calls in fixtures mode.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

VALID_MODES = ("fixtures", "cached", "live")
FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"

# Fixture names per call. Opportunities try a per-customer file first.
_OPPORTUNITIES = "opportunities"
_SCENARIO = "scenario"
_CLAIMCHECK = "claimcheck"
_PORTFOLIO = "portfolio"
_EVAL = "eval"

_SAFE_ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def demo_mode() -> str:
    """Return DEMO_MODE, read at call time so tests can change it."""
    mode = os.environ.get("DEMO_MODE", "fixtures").strip().lower()
    if mode not in VALID_MODES:
        raise ValueError(f"DEMO_MODE must be one of {VALID_MODES}, got {mode!r}")
    return mode


def _require_fixtures() -> None:
    if demo_mode() != "fixtures":
        raise NotImplementedError("Coming in Step 3.5")


def _safe_id(value: str, field: str) -> str:
    """Ids become part of a file name, so allow only simple tokens (no path traversal)."""
    if not isinstance(value, str) or not _SAFE_ID.match(value):
        raise ValueError(f"invalid {field}")
    return value


def _load(name: str) -> Any:
    path = FIXTURES_DIR / f"{name}.json"
    if not path.is_file():
        raise FileNotFoundError(f"fixture not found: fixtures/{name}.json")
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


# --------------------------------------------------------------------------
# Public API
# --------------------------------------------------------------------------
def get_opportunities(customer_id: str) -> list[dict]:
    """Opportunity cards for one customer.

    Looks for fixtures/opportunities_<customer_id>.json, then falls back to
    fixtures/opportunities.json (either a list, or a dict keyed by customer id).
    """
    _require_fixtures()
    cid = _safe_id(customer_id, "customer_id")
    per_customer = FIXTURES_DIR / f"{_OPPORTUNITIES}_{cid}.json"
    data = _load(f"{_OPPORTUNITIES}_{cid}") if per_customer.is_file() else _load(_OPPORTUNITIES)
    if isinstance(data, dict):
        data = data.get(cid, [])
    return list(data)


def run_scenario(customer_id: str, mutations: list[dict] | dict) -> dict:
    """Scenario Lab result. Fixtures mode returns the canned response; inputs are only validated."""
    _require_fixtures()
    _safe_id(customer_id, "customer_id")
    if not isinstance(mutations, (list, dict)):
        raise ValueError("mutations must be a list or dict")
    return dict(_load(_SCENARIO))


def claimcheck(customer_id: str, opportunity_id: str, sentences: list[str]) -> dict:
    """Claim-Check result for candidate sentences. Fixtures mode returns the canned response."""
    _require_fixtures()
    _safe_id(customer_id, "customer_id")
    _safe_id(opportunity_id, "opportunity_id")
    if not isinstance(sentences, list) or not all(isinstance(s, str) for s in sentences):
        raise ValueError("sentences must be a list of strings")
    return dict(_load(_CLAIMCHECK))


def get_portfolio() -> dict:
    """k-anonymised portfolio aggregates for the Cockpit."""
    _require_fixtures()
    return dict(_load(_PORTFOLIO))


def get_eval() -> dict:
    """Evaluation summary for the Receipts page."""
    _require_fixtures()
    return dict(_load(_EVAL))
