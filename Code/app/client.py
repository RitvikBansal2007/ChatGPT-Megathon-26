"""The single data gateway for the GreenDash UI.

Pages call these functions and nothing else for data. DEMO_MODE (env) picks
the source:

  fixtures (default)  read contract-shaped JSON from <repo>/fixtures/
  live                FastAPI at API_BASE_URL with a demo Bearer token; on any
                      failure show a friendly card and return empty data
  cached              same API, but silently fall back to fixtures when
                      /healthz or a request fails

Contract shapes mirror greendash/contracts.py (frozen by G1-A).

Rules:
- Never holds the LLM key
- Never logs tokens, request bodies or response bodies
- No network calls in fixtures mode
- Path-traversal guard on all IDs used in filenames
"""

from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import streamlit as st

VALID_MODES = ("fixtures", "cached", "live")
FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"

_SAFE_ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")

# Status → per-status fixture file name (G1-A's naming convention)
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


def _base_url() -> str:
    url = os.environ.get("API_BASE_URL", "http://127.0.0.1:8000").strip().rstrip("/")
    if not url.startswith(("http://", "https://")):  # urllib would also open file://
        raise ValueError("API_BASE_URL must be an http(s) URL")
    return url


def _http(method: str, path: str, body: Any = None, token: str | None = None,
          timeout: float = 10) -> Any:
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(
        _base_url() + path, method=method, headers=headers,
        data=None if body is None else json.dumps(body).encode("utf-8"),
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 - scheme checked in _base_url
        return json.load(resp)


def _identity(customer_id: str | None) -> dict:
    """Map the UI role label to the API's demo-token body."""
    role = st.session_state.get("role", "")
    if not role or role.startswith("Customer"):
        return {"role": "CUSTOMER", "customer_id": customer_id}
    return {"role": role.upper().replace(" ", "_")}


def _token(customer_id: str | None) -> str:
    ident = _identity(customer_id)
    cached = st.session_state.get("_api_token")
    if cached and cached["ident"] == ident and time.time() <= cached["expiry"] - 60:
        return cached["token"]
    data = _http("POST", "/api/auth/demo-token", ident)
    st.session_state["_api_token"] = {
        "token": data["access_token"],
        "expiry": time.time() + float(data.get("expires_in", 900)),
        "ident": ident,
    }
    return data["access_token"]


_USE_FIXTURES = object()


def _remote(method: str, path: str, body: Any = None, customer_id: str | None = None) -> Any:
    """Fetch from the API. Returns _USE_FIXTURES when the caller should read
    fixtures, or None after showing a friendly card (live mode failure)."""
    mode = demo_mode()
    if mode == "fixtures":
        return _USE_FIXTURES
    try:
        if mode == "cached":
            _http("GET", "/healthz", timeout=2)
        return _http(method, path, body, _token(customer_id))
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            st.session_state.pop("_api_token", None)
            msg = "This view isn't available for the current role. Switch role on Home and try again."
        elif exc.code >= 500:
            msg = "The GreenDash service hit a problem. Please try again in a moment."
        else:
            msg = "The GreenDash service couldn't process this request."
    except (OSError, ValueError, KeyError):  # refused/timeout, bad JSON, missing token field
        msg = "Can't reach the GreenDash service right now. Please try again in a moment."
    if mode == "cached":
        return _USE_FIXTURES
    st.error(msg, icon=":material/error:")
    return None


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
    cid = _safe_id(customer_id, "customer_id")
    live = _remote("GET", f"/api/customers/{cid}/opportunities", customer_id=cid)
    if live is not _USE_FIXTURES:
        return _unwrap_opportunities(live)

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
    _safe_id(customer_id, "customer_id")
    if not isinstance(mutations, (list, dict)):
        raise ValueError("mutations must be a list or dict")
    live = _remote("POST", "/api/scenario",
                   {"customer_id": customer_id, "mutations": mutations}, customer_id)
    if live is not _USE_FIXTURES:
        return live or {}
    return dict(_load("scenario_response"))


def claimcheck(customer_id: str, opportunity_id: str, sentences: list[str]) -> dict:
    """Claim-Check result. fixtures mode returns canned claimcheck_response.json."""
    _safe_id(customer_id, "customer_id")
    _safe_id(opportunity_id, "opportunity_id")
    if not isinstance(sentences, list) or not all(isinstance(s, str) for s in sentences):
        raise ValueError("sentences must be a list of strings")
    live = _remote("POST", "/api/claimcheck", {
        "customer_id": customer_id, "opportunity_id": opportunity_id,
        "sentences": [{"text": s, "fields": []} for s in sentences],  # API's SentenceIn shape
    }, customer_id)
    if live is not _USE_FIXTURES:
        return live or {}
    return dict(_load("claimcheck_response"))


def get_portfolio() -> dict:
    """k-anonymised portfolio aggregates for the Cockpit."""
    live = _remote("GET", "/api/portfolio/summary")
    if live is not _USE_FIXTURES:
        return live or {}
    return dict(_load("portfolio"))


def get_eval() -> dict:
    """Evaluation summary for the Receipts page."""
    live = _remote("GET", "/api/eval/summary")
    if live is not _USE_FIXTURES:
        return live or {}
    return dict(_load("eval"))
