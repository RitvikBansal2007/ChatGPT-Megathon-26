"""Smoke tests aligned to real contracts.py (frozen by G1-A).

Opportunity shape: CustomerOpportunities wrapper with .opportunities list.
Fixture files: opps_recommend.json, opps_abstain.json, opps_review.json,
               opps_ruled_out.json, opps_soft_surface.json,
               claimcheck_response.json, scenario_response.json
"""

import os
import sys
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP_DIR  = Path(__file__).resolve().parent.parent
REPO_ROOT = APP_DIR.parent

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))


PAGES = [
    "Home.py",
    "pages/1_Customer_Hub.py",
    "pages/2_Cockpit.py",
    "pages/3_Receipts.py",
]


# ── Page render tests ────────────────────────────────────────────────────────

@pytest.mark.parametrize("page", PAGES)
def test_page_renders_without_exception(page):
    os.environ["DEMO_MODE"] = "fixtures"
    at = AppTest.from_file(str(APP_DIR / page), default_timeout=30).run()
    assert not at.exception, f"{page} raised: {at.exception}"
    assert any("Synthetic data – demo only" in m.value for m in at.markdown), \
        f"{page}: synthetic-data banner missing"
    assert at.title, f"{page}: page title missing"


def test_role_switcher_updates_session_state():
    os.environ["DEMO_MODE"] = "fixtures"
    at = AppTest.from_file(str(APP_DIR / "Home.py"), default_timeout=30).run()
    assert at.session_state["role"] == "Customer – Priya (GP01)"
    at.selectbox(key="_role_select").select("Auditor").run()
    assert not at.exception
    assert at.session_state["role"] == "Auditor"


# ── Client mode guard tests ──────────────────────────────────────────────────

def test_client_cached_falls_back_to_fixtures(monkeypatch):
    import client
    monkeypatch.setenv("DEMO_MODE", "cached")
    monkeypatch.setenv("API_BASE_URL", "http://127.0.0.1:9")  # nothing listens here
    assert "metrics" in client.get_portfolio()
    assert client.get_opportunities("CUST-0001")


def test_client_live_unreachable_returns_empty(monkeypatch):
    import client
    monkeypatch.setenv("DEMO_MODE", "live")
    monkeypatch.setenv("API_BASE_URL", "http://127.0.0.1:9")
    assert client.get_portfolio() == {}
    assert client.get_opportunities("CUST-0001") == []


def test_client_invalid_mode(monkeypatch):
    import client
    monkeypatch.setenv("DEMO_MODE", "bogus")
    with pytest.raises(ValueError, match="DEMO_MODE"):
        client.get_portfolio()


def test_client_path_traversal_guard(monkeypatch):
    import client
    monkeypatch.setenv("DEMO_MODE", "fixtures")
    with pytest.raises(ValueError):
        client.get_opportunities("../../etc/passwd")


# ── Contract-shape tests ─────────────────────────────────────────────────────

def test_opportunities_return_list(monkeypatch):
    import client
    monkeypatch.setenv("DEMO_MODE", "fixtures")
    opps = client.get_opportunities("CUST-0001")
    assert isinstance(opps, list)
    assert len(opps) > 0


def test_all_five_statuses_covered(monkeypatch):
    """One card per product per persona; the five demo personas cover all five statuses."""
    import client
    monkeypatch.setenv("DEMO_MODE", "fixtures")
    statuses = set()
    for cid in ("CUST-0001", "CUST-0002", "CUST-0003", "CUST-0004", "CUST-0005"):
        gp01 = [o for o in client.get_opportunities(cid) if o["opportunity_id"] == "GP01"]
        assert len(gp01) == 1, f"{cid}: expected one GP01 card, got {len(gp01)}"
        statuses.add(gp01[0]["status"])
    assert statuses == {"RECOMMEND", "SOFT_SURFACE", "ABSTAIN", "REVIEW", "RULED_OUT"}


def test_hub_opens_proof_card():
    """Regression: tiles must find their opportunity (keyed on opportunity_id)."""
    os.environ["DEMO_MODE"] = "fixtures"
    at = AppTest.from_file(str(APP_DIR / "pages/1_Customer_Hub.py"), default_timeout=30).run()
    at.button(key="tile_GP01").click().run()
    assert not at.exception
    assert not any("No opportunity data" in i.value for i in at.info)


def test_opportunity_has_required_contract_fields(monkeypatch):
    """Every opportunity must have the required fields from contracts.py."""
    import client
    monkeypatch.setenv("DEMO_MODE", "fixtures")
    opps = client.get_opportunities("CUST-0001")
    required = {"opportunity_id", "opportunity_name", "status", "propensity",
                "likelihood_band", "eligibility", "impact"}
    for opp in opps:
        missing = required - set(opp.keys())
        assert not missing, f"Opp {opp.get('opportunity_id')} missing fields: {missing}"


def test_claimcheck_contract_shape(monkeypatch):
    import client
    monkeypatch.setenv("DEMO_MODE", "fixtures")
    cc = client.claimcheck("CUST-0001", "GP01", ["Test sentence."])
    assert "verdict" in cc
    assert "sentences" in cc
    assert "fallback_text" in cc
    assert "blocked_total" in cc
    # Each sentence must have violations with rule + span
    for sent in cc.get("sentences", []):
        for v in sent.get("violations", []):
            assert "rule" in v
            assert "span" in v


def test_scenario_contract_shape(monkeypatch):
    import client
    monkeypatch.setenv("DEMO_MODE", "fixtures")
    sc = client.run_scenario("CUST-0001", ["SET_VEHICLE_BEV"])
    assert "before" in sc
    assert "after" in sc
    assert "diff" in sc
    assert "invariance_ok" in sc
    assert "elapsed_ms" in sc


def test_portfolio_and_eval_load(monkeypatch):
    import client
    monkeypatch.setenv("DEMO_MODE", "fixtures")
    portfolio = client.get_portfolio()
    assert "metrics" in portfolio
    ev = client.get_eval()
    assert "baselines" in ev
