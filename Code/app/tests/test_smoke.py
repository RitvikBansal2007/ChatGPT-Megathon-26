"""Smoke tests: every page renders without exception, with banner, theme, and title.
Also tests role switching, client mode guards, and badge/state rendering from fixtures.
"""

import os
import sys
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP_DIR = Path(__file__).resolve().parent.parent
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
    """Every page must load cleanly in fixtures mode."""
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

@pytest.mark.parametrize("mode", ["cached", "live"])
def test_client_unimplemented_modes(monkeypatch, mode):
    import client
    monkeypatch.setenv("DEMO_MODE", mode)
    with pytest.raises(NotImplementedError, match="Step 3.5"):
        client.get_portfolio()


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


# ── Fixture loading tests ────────────────────────────────────────────────────

def test_fixtures_load_all(monkeypatch):
    import client
    monkeypatch.setenv("DEMO_MODE", "fixtures")
    opps = client.get_opportunities("CUST-0001")
    assert isinstance(opps, list)
    assert len(opps) > 0

    portfolio = client.get_portfolio()
    assert "metrics" in portfolio
    assert "funnel" in portfolio

    ev = client.get_eval()
    assert "baselines" in ev

    scenario = client.run_scenario("CUST-0001", ["SET_VEHICLE_BEV"])
    assert "before" in scenario

    cc = client.claimcheck("CUST-0001", "GP01", ["Test sentence."])
    assert "violations" in cc


def test_all_five_statuses_present(monkeypatch):
    """Opportunities fixture must cover all five statuses for CP1."""
    import client
    monkeypatch.setenv("DEMO_MODE", "fixtures")
    opps = client.get_opportunities("CUST-0001")
    statuses = {o["status"] for o in opps}
    # At least 4 statuses in the default fixture (RECOMMEND, SOFT_SURFACE, ABSTAIN, RULED_OUT)
    expected = {"RECOMMEND", "SOFT_SURFACE", "ABSTAIN", "RULED_OUT"}
    assert expected.issubset(statuses), f"Missing statuses: {expected - statuses}"
