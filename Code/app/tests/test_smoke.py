"""Smoke tests for the greendash Streamlit app (offline, fixtures only)."""

import os
import re
import sys
from pathlib import Path

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

APP_DIR = Path(__file__).resolve().parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import client  # noqa: E402

PAGES = ["Home.py", "pages/1_Customer_Hub.py", "pages/2_Cockpit.py", "pages/3_Receipts.py"]
PERSONAS = [f"CUST-000{i}" for i in range(1, 9)]
PRODUCTS = ["GP01", "GP02", "GP03", "GP04"]
ALL_STATUSES = {"RECOMMEND", "SOFT_SURFACE", "ABSTAIN", "REVIEW", "RULED_OUT"}


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "fixtures")
    st.cache_data.clear()
    yield
    st.cache_data.clear()


def run(page, role="EVALUATOR", persona="CUST-0001"):
    at = AppTest.from_file(str(APP_DIR / page), default_timeout=30)
    at.session_state["role"] = role
    at.session_state["persona_id"] = persona
    return at.run()


def text_of(at):
    return " ".join(str(e.value) for kind in ("markdown", "caption", "title", "subheader", "header", "error", "warning", "info")
                    for e in getattr(at, kind))


# ── pages ────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("page", PAGES)
def test_page_renders(page):
    at = run(page)
    assert not at.exception, f"{page} raised: {at.exception}"
    assert "ML predicts." in text_of(at), f"{page}: core rule footer missing"


@pytest.mark.parametrize("page", PAGES)
def test_no_demo_wording_on_screen(page):
    visible = re.sub(r"<[^>]+>", " ", text_of(run(page)))
    assert not re.search(r"\bdemo\b|fixture|test account|DEMO_MODE", visible, re.I)


@pytest.mark.parametrize("persona", PERSONAS)
def test_hub_opens_every_pathway(persona):
    at = run("pages/1_Customer_Hub.py", persona=persona)
    assert not at.exception
    for gp in PRODUCTS:
        at.button(key=f"open-{gp}").click().run()
        assert not at.exception, f"{persona} {gp}: {at.exception}"


def test_role_gates_hide_pages():
    cockpit = run("pages/2_Cockpit.py", role="CUSTOMER")
    assert not cockpit.exception and "cannot open" in text_of(cockpit)
    receipts = run("pages/3_Receipts.py", role="RELATIONSHIP_MANAGER")
    assert not receipts.exception and "cannot open" in text_of(receipts)
    assert "cannot open" not in text_of(run("pages/2_Cockpit.py", role="PORTFOLIO_ANALYST"))


def test_receipts_labels_illustrative_figures():
    assert "Illustrative figures" in text_of(run("pages/3_Receipts.py"))


def test_live_mode_unreachable_shows_friendly_card(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "live")
    monkeypatch.setenv("API_BASE_URL", "http://127.0.0.1:9")  # nothing listens here
    at = run("pages/1_Customer_Hub.py")
    assert not at.exception
    assert any("Can't reach the greendash service" in e.value for e in at.error)


# ── client ───────────────────────────────────────────────────────────────────
def test_invalid_mode(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "bogus")
    with pytest.raises(ValueError, match="DEMO_MODE"):
        client.portfolio()


def test_cached_mode_falls_back_to_fixtures(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "cached")
    monkeypatch.setenv("API_BASE_URL", "http://127.0.0.1:9")
    assert client.portfolio()["tiles"]
    assert len(client.opportunities("CUST-0001")["opportunities"]) == 4


def test_every_persona_has_four_contract_shaped_cards():
    required = {"opportunity_id", "opportunity_name", "status", "propensity", "likelihood_band",
                "confidence", "eligibility", "reason_codes", "impact", "explanation", "next_action"}
    seen = set()
    for cid in PERSONAS:
        opps = client.opportunities(cid)["opportunities"]
        assert [o["opportunity_id"] for o in opps] == PRODUCTS
        for o in opps:
            assert not required - set(o), f"{cid} {o['opportunity_id']} missing {required - set(o)}"
            seen.add(o["status"])
    assert seen == ALL_STATUSES


def test_ruled_out_cards_have_a_reason_and_no_action():
    for cid in PERSONAS:
        for o in client.opportunities(cid)["opportunities"]:
            if o["status"] == "RULED_OUT":
                assert o.get("why_not", {}).get("rule"), f"{cid} {o['opportunity_id']}: no rule named"


def test_scenario_set_vehicle_bev_rules_out_ev_finance():
    res = client.scenario("CUST-0001", ["SET_VEHICLE_BEV"])
    assert res["before"]["GP01"]["status"] == "RECOMMEND"
    assert res["after"]["GP01"]["status"] == "RULED_OUT"
    assert res["invariance_ok"] is True


def test_claimcheck_blocks_the_fixed_fake_claim():
    res = client.claimcheck("CUST-0001", "GP01", "Switching will save you 4,000 kg a year and you're pre-approved.")
    assert res["verdict"] == "BLOCKED"
    assert sorted(v["rule"] for v in res["sentences"][0]["violations"]) == ["BAN", "BAN", "NUM"]
    assert res["fallback_text"]


def test_live_pack_without_presentation_fields_is_completed():
    """A pack shaped like the API contract (no headline/explanation/display_name) must still render."""
    doc = client._complete({"customer_id": "CUST-0001", "opportunities": [
        {"opportunity_id": "GP01", "opportunity_name": "EV Finance", "status": "SOFT_SURFACE", "impact": {"status": "NOT_APPLICABLE"},
         "reason_codes": [], "explanation": None, "next_action": None}]}, "CUST-0001")
    o = doc["opportunities"][0]
    assert doc["display_name"] == "Priya" and o["headline"] == "EV Finance"
    assert o["explanation"]["sentences"] == [] and o["next_action"] == {}
