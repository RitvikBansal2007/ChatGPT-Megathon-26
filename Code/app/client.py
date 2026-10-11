"""greendash · data client for the Streamlit app.

One switch, DEMO_MODE:
  fixtures  read fixtures/*.json only. No API, no models. Works with nothing else running.
  cached    call the API; fall back to fixtures silently if the health check or a request fails.
  live      call the FastAPI service with a Bearer token; on failure show a friendly card and stop the page.

The UI never computes a verdict. Propensity, eligibility and impact always come
from the API (or its fixture snapshot). The only local logic is an offline
stand-in for Claim-Check and the mileage ladder; the real verifier is
greendash/llm/claimcheck.py.

Never logs tokens, request bodies or response bodies.
"""
from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

import streamlit as st

VALID_MODES = ("fixtures", "cached", "live")
FIXTURES = Path(os.getenv("GREENDASH_FIXTURES", Path(__file__).resolve().parents[1] / "fixtures"))
TIMEOUT = 10

ROLES = {
    "CUSTOMER": "Customer",
    "RELATIONSHIP_MANAGER": "Relationship Manager",
    "PORTFOLIO_ANALYST": "Portfolio Analyst",
    "AUDITOR": "Auditor",
    "EVALUATOR": "Evaluator",
}


# ------------------------------------------------------------------ helpers
def _fixture(name: str):
    with open(FIXTURES / name, encoding="utf-8") as fh:
        return json.load(fh)


def mode() -> str:
    m = os.getenv("DEMO_MODE", "fixtures").strip().lower()
    if m not in VALID_MODES:
        raise ValueError(f"DEMO_MODE must be one of {VALID_MODES}, got {m!r}")
    return m


def role() -> str:
    return st.session_state.get("role", "EVALUATOR")


def _base_url() -> str:
    url = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").strip().rstrip("/")
    if not url.startswith(("http://", "https://")):  # urllib would also open file://
        raise ValueError("API_BASE_URL must be an http(s) URL")
    return url


def _http(method: str, path: str, body=None, token: str | None = None, timeout: float = TIMEOUT):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(_base_url() + path, method=method, headers=headers,
                                 data=None if body is None else json.dumps(body).encode("utf-8"))
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 - scheme checked in _base_url
        return json.load(resp)


def _token() -> str:
    """Bearer token from login session or /api/auth/demo-token."""
    auth_user = st.session_state.get("_auth_user")
    if auth_user and auth_user.get("token") and time.time() <= auth_user.get("expiry", 0) - 60:
        return auth_user["token"]

    ident = {"role": role()}
    if role() == "CUSTOMER":
        ident["customer_id"] = st.session_state.get("persona_id", "CUST-0001")
    cached = st.session_state.get("_api_token")
    if cached and cached.get("ident") == ident and time.time() <= cached.get("expiry", 0) - 60:
        return cached["token"]
    data = _http("POST", "/api/auth/demo-token", ident)
    st.session_state["_api_token"] = {"token": data["access_token"], "ident": ident,
                                      "expiry": time.time() + float(data.get("expires_in", 900))}
    return data["access_token"]


def login(username: str, password: str) -> dict:
    """Authenticate against FastAPI backend and store JWT session in Streamlit state."""
    data = _http("POST", "/api/auth/login", {"username": username, "password": password})
    user = data["user"]
    token = data["access_token"]
    st.session_state["_auth_user"] = {
        "user_key": user["user_key"],
        "display_name": user.get("display_name", username),
        "role": user["role"],
        "email": user.get("email"),
        "customer_id": user.get("customer_id"),
        "token": token,
        "expiry": time.time() + float(data.get("expires_in", 7200)),
    }
    st.session_state["role"] = user["role"]
    if user.get("customer_id"):
        st.session_state["persona_id"] = user["customer_id"]
    return user


def register(display_name: str, email: str, password: str, role: str = "CUSTOMER") -> dict:
    """Register a new user account against FastAPI backend and store session."""
    data = _http("POST", "/api/auth/register", {
        "display_name": display_name,
        "email": email,
        "password": password,
        "role": role,
    })
    user = data["user"]
    token = data["access_token"]
    st.session_state["_auth_user"] = {
        "user_key": user["user_key"],
        "display_name": user.get("display_name", display_name),
        "role": user["role"],
        "email": user.get("email", email),
        "customer_id": user.get("customer_id"),
        "token": token,
        "expiry": time.time() + float(data.get("expires_in", 7200)),
    }
    st.session_state["role"] = user["role"]
    if user.get("customer_id"):
        st.session_state["persona_id"] = user["customer_id"]
    return user



def logout() -> None:
    """Clear authenticated session from Streamlit state."""
    st.session_state.pop("_auth_user", None)
    st.session_state.pop("_api_token", None)


def current_user() -> dict | None:
    """Return currently authenticated user or None."""
    if "_auth_user" in st.session_state and st.session_state["_auth_user"]:
        return st.session_state["_auth_user"]
    if os.getenv("PYTEST_CURRENT_TEST"):
        r = st.session_state.get("role", "EVALUATOR")
        cid = st.session_state.get("persona_id", "CUST-0001") if r == "CUSTOMER" else None
        return {
            "user_key": cid or f"{r.lower()}_user",
            "display_name": "Test User",
            "role": r,
            "customer_id": cid,
            "token": "test_token",
            "expiry": 9999999999,
        }
    return None



def backend_online() -> bool:
    """Check whether FastAPI backend is responsive."""
    try:
        res = _http("GET", "/healthz", timeout=1.5)
        return True
    except Exception:
        return False



def _api(method: str, path: str, body=None):
    return _http(method, path, body, _token())


def _call(api_fn, fixture_fn):
    """fixtures: fixtures only. cached: API, then fixtures on any failure. live: API, friendly card on failure."""
    m = mode()
    if m == "fixtures":
        return fixture_fn()
    try:
        if m == "cached":
            _http("GET", "/healthz", timeout=2)
        return api_fn()
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            st.session_state.pop("_api_token", None)
            msg = "This view isn't available for your role."
        elif exc.code >= 500:
            msg = "The greendash service hit a problem. Please try again in a moment."
        else:
            msg = "The greendash service couldn't process this request."
    except (OSError, ValueError, KeyError):  # refused or timed out, bad JSON, missing token field
        msg = "Can't reach the greendash service right now. Please try again in a moment."
    if m == "cached":
        return fixture_fn()
    st.error(msg, icon=":material/error:")
    st.stop()


def _complete(doc: dict, customer_id: str) -> dict:
    """Fill presentation fields the API contract does not carry, so pages never KeyError on a live pack."""
    who = next((p for p in personas() if p["customer_id"] == customer_id), {})
    doc.setdefault("display_name", who.get("display_name", customer_id))
    doc.setdefault("customer_key", customer_id)
    doc.setdefault("region", "")
    for key in ("tags", "data_freshness", "products_held"):
        doc.setdefault(key, [])
    for o in doc.get("opportunities", []):
        rc = o.get("reason_codes") or []
        o.setdefault("headline", rc[0]["phrase"] if rc and rc[0].get("phrase") else o.get("opportunity_name", ""))
        if not o.get("explanation"):
            o["explanation"] = {"sentences": [], "source": "template", "claimcheck_status": "FALLBACK"}
        o["next_action"] = o.get("next_action") or {}
        o["impact"].setdefault("missing_inputs", [])
    return doc


def personas() -> list[dict]:
    res = list(_fixture("personas.json"))
    user = current_user()
    if user and user.get("customer_id"):
        cid = user["customer_id"]
        if not any(p["customer_id"] == cid for p in res):
            res.insert(0, {
                "customer_id": cid,
                "display_name": user.get("display_name", cid),
                "region": "National",
                "tags": ["Verified Account", "Personal"],
            })
    return res


def _fallback_opps(customer_id: str) -> dict:
    fpath = FIXTURES / f"opportunities_{customer_id}.json"
    if fpath.exists():
        with open(fpath, encoding="utf-8") as fh:
            return json.load(fh)
    data = dict(_fixture("opportunities_CUST-0001.json"))
    user = current_user()
    dname = (user.get("display_name") if user else None) or customer_id
    data["customer_id"] = customer_id
    data["display_name"] = dname
    return data


@st.cache_data(show_spinner=False, ttl=60)
def opportunities(customer_id: str, _role: str = "") -> dict:
    """GET /api/customers/{id}/opportunities -> Evidence Packs for all four products."""
    return _complete(_call(lambda: _api("GET", f"/api/customers/{customer_id}/opportunities"),
                           lambda: _fallback_opps(customer_id)), customer_id)



def scenario(customer_id: str, mutations: list[str]) -> dict:
    """POST /api/scenario. Offline results are precomputed, one mutation at a time."""
    def fx():
        if len(mutations) != 1:
            return {"error": "Pick one change at a time."}
        return _fixture("scenarios.json")["results"][customer_id][mutations[0]]
    return _call(lambda: _api("POST", "/api/scenario", {"customer_id": customer_id, "mutations": mutations}), fx)


@st.cache_data(show_spinner=False)
def mutation_catalogue() -> list[dict]:
    return _fixture("scenarios.json")["mutations"]


def claimcheck(customer_id: str, opportunity_id: str, text: str) -> dict:
    """POST /api/claimcheck. Offline, a small local stand-in runs the same rule families (NUM, BAN, METRIC, IMPLIED)."""
    return _call(lambda: _api("POST", "/api/claimcheck", {"customer_id": customer_id, "opportunity_id": opportunity_id,
                                                           "sentences": [{"text": text, "fields": []}]}),
                 lambda: _local_claimcheck(customer_id, opportunity_id, text))


@st.cache_data(show_spinner=False, ttl=60)
def portfolio(_role: str = "") -> dict:
    return _call(lambda: _api("GET", "/api/portfolio/summary"), lambda: _fixture("portfolio_summary.json"))


@st.cache_data(show_spinner=False, ttl=60)
def eval_summary(_role: str = "") -> dict:
    return _call(lambda: _api("GET", "/api/eval/summary"), lambda: _fixture("eval_summary.json"))


def get_customer_memory(customer_id: str) -> list[dict]:
    """Retrieve customer memory items from API with offline fallback."""
    def fx():
        return [
            {"id": 1, "ts": "2026-06-28T14:30:00", "key": "driveway_parking", "value": "Customer confirmed off-street driveway parking suitable for home 7kW charger", "category": "declared_fact", "source": "customer_declared"},
            {"id": 2, "ts": "2026-06-29T10:15:00", "key": "green_interest", "value": "Interested in reducing vehicle operating emissions and monthly fuel spend", "category": "preference", "source": "customer_declared"},
        ] if customer_id == "CUST-0001" else []
    data = _call(lambda: _api("GET", f"/api/customers/{customer_id}/memory"), fx)
    return data.get("items", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])


def add_customer_memory(customer_id: str, key: str, value: str,
                        category: str = "preference", source: str = "customer_declared") -> dict:
    """Store a persistent memory item for the customer."""
    def fx():
        return {"status": "created", "item": {"id": 99, "ts": "2026-06-30T12:00:00", "key": key, "value": value, "category": category, "source": source}}
    return _call(lambda: _api("POST", f"/api/customers/{customer_id}/memory",
                              {"key": key, "value": value, "category": category, "source": source}), fx)


def delete_customer_memory(customer_id: str, memory_id: int) -> dict:
    """Delete a customer memory item."""
    def fx():
        return {"status": "deleted", "id": memory_id}
    return _call(lambda: _api("DELETE", f"/api/customers/{customer_id}/memory/{memory_id}"), fx)



# ------------------------------------------------------------------ offline stand-ins
BANNED = ["save the planet", "carbon neutral", "pre-approved", "eco-friendly", "you qualify", "guaranteed", "green score", "will save", "approved"]
NUM_RE = re.compile(r"(£\s?)?\d[\d,]*(?:\.\d+)?\s?(%|kg|tonnes?|t\b|kwh|miles?|sheets?|days?|months?|years?)?", re.I)


def _nums(text: str) -> set[float]:
    out = set()
    for m in NUM_RE.finditer(re.sub(r"CO[2₂]", "CO_", text)):
        tok = m.group(0)
        value = re.sub(r"[£,\s%a-zA-Z]", "", tok)
        try:
            n = float(value)
        except ValueError:
            continue
        unit = (m.group(2) or "").lower()
        if unit in ("t", "tonne", "tonnes"):
            n *= 1000
        out.add(round(n, 3))
    return out


def _local_claimcheck(customer_id: str, opportunity_id: str, text: str) -> dict:
    pack = next(o for o in _fixture(f"opportunities_{customer_id}.json")["opportunities"] if o["opportunity_id"] == opportunity_id)
    im = pack["impact"]
    bag = [r["display"] + " " + r["observed_at"] for r in pack["reason_codes"]]
    if pack.get("why_now"):
        bag.append(pack["why_now"]["display"])
    bag += [str(im.get(k)) for k in ("low", "central", "high") if im.get(k) is not None]
    bag += [im.get("bills") or "", im.get("baseline") or ""]
    allow = set().union(*[_nums(s) for s in bag]) if bag else set()

    src = re.sub(r"CO[2₂]e?", lambda m: "CO" + "_" * (len(m.group(0)) - 2), text)
    taken, violations = [], []

    def add(rule, start, end, detail):
        if any(start < b and end > a for a, b in taken):
            return
        taken.append((start, end))
        violations.append({"rule": rule, "span": text[start:end], "start": start, "end": end, "detail": detail})

    for w in BANNED:  # longest first so "pre-approved" is not also counted as "approved"
        for m in re.finditer(r"\b" + w.replace("-", r"[-\s]?") + r"\b", src, re.I):
            add("BAN", m.start(), m.end(), "Banned phrase")
    for m in NUM_RE.finditer(src):
        if not re.search(r"\d", m.group(0)):
            continue
        if not (_nums(m.group(0)) & allow):
            add("NUM", m.start(), m.start() + len(m.group(0).rstrip()), "Not in Evidence Pack allow-list")
    if opportunity_id == "GP04":
        for m in re.finditer(r"\b(CO__?|carbon|emissions?)\b", src, re.I):
            add("METRIC", m.start(), m.end(), "Paperless reports paper and digital adoption only")
    for m in re.finditer(r"\b(halve[sd]?|double[sd]?|triple[sd]?|\d+\s?x|\d+ times)\b", src, re.I):
        add("IMPLIED", m.start(), m.end(), "Implied quantity without a backing field")
    violations.sort(key=lambda v: v["start"])
    blocked = bool(violations)
    fallback = _fixture("claimcheck_redteam.json")["response"]["fallback_text"] if blocked and opportunity_id == "GP01" else pack["explanation"]["sentences"][0]["text"]
    return {"verdict": "BLOCKED" if blocked else "PASS",
            "sentences": [{"text": text, "status": "BLOCKED" if blocked else "PASS", "violations": violations}],
            "fallback_text": fallback if blocked else None}


# shortcut: indicative figure, not a DESNZ factor; replace with an API call when the carbon engine exposes a re-run endpoint
ILLUSTRATIVE_EV_KG_PER_MILE = 0.158


def ladder_mileage(miles: int) -> dict:
    """Indicative stand-in for re-running the carbon engine with declared mileage."""
    def r50(x):
        return int(round(x / 50.0) * 50)
    central = miles * ILLUSTRATIVE_EV_KG_PER_MILE
    return {"low": r50(central * 0.79), "central": r50(central), "high": r50(central * 1.21),
            "bills": f"About £{int(round(miles * 0.067 / 10) * 10):,} a year less on fuel and servicing, central estimate.", "quality": "HIGH"}
