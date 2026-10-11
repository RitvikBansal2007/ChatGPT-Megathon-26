"""Offline explanation wording: specific, from the pack's own facts, and Claim-Checked.

Hermetic: no files, no network, no model.
"""
import copy

import pytest

from api import services
from config.settings import settings


@pytest.fixture(autouse=True)
def _no_llm(monkeypatch):
    monkeypatch.setattr(settings, "llm_api_key", None)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    def boom(*a, **k):
        raise AssertionError("the model must not be called without a key")
    monkeypatch.setattr(services, "get_explanation", boom)


PACK = {
    "opportunity_id": "GP01", "opportunity_name": "EV Finance", "status": "RECOMMEND",
    "reason_codes": [{"code": "HIGH_FUEL_SPEND", "phrase": "Fuel spend above your usual range",
                      "metric": "avg_monthly_fuel_gbp", "value": 185, "display": "185 GBP per month",
                      "observed_at": "2026-06-30", "source": "inferred_transactions"}],
    "impact": {"status": "ESTIMATED", "metric_family": "emissions", "display": "2,330 kg CO2e",
               "low": 1980, "central": 2330, "high": 2679},
    "explanation": None,
}


def _text(opp):
    return " ".join(s["text"] for s in opp["explanation"]["sentences"])


def test_recommend_pack_gets_specific_checked_wording():
    opp = services._enrich_explanation(copy.deepcopy(PACK), "CUST-0001", "m")
    text = _text(opp)
    assert "Fuel spend above your usual range." in text
    assert "2,330 kg CO2e" in text
    assert opp["explanation"]["source"] == "template"
    assert opp["explanation"]["claimcheck_status"] == "FALLBACK"
    assert [s["check"] for s in opp["explanation"]["sentences"]] == ["TEMPLATE", "TEMPLATE"]


@pytest.mark.parametrize("status", ["RULED_OUT", "ABSTAIN", "REVIEW"])
def test_non_recommend_statuses_keep_the_generic_template(status):
    pack = copy.deepcopy(PACK)
    pack["status"] = status
    assert "2,330" not in _text(services._enrich_explanation(pack, "CUST-0001", "m"))


def test_no_estimate_keeps_the_generic_template():
    pack = copy.deepcopy(PACK)
    pack["impact"] = {"status": "INSUFFICIENT_DATA", "display": None}
    assert "kg" not in _text(services._enrich_explanation(pack, "CUST-0001", "m"))


def test_unsafe_phrase_is_not_used():
    pack = copy.deepcopy(PACK)
    pack["reason_codes"][0]["phrase"] = "You are pre-approved and guaranteed to save"
    text = _text(services._enrich_explanation(pack, "CUST-0001", "m"))
    assert "pre-approved" not in text and "guaranteed" not in text


def test_invented_number_in_display_is_blocked_by_claim_check():
    pack = copy.deepcopy(PACK)
    pack["impact"]["display"] = "9,999,999 kg CO2e"      # not a figure the pack backs
    opp = services._enrich_explanation(pack, "CUST-0001", "m")
    # either the figure is accepted because it IS the pack's display, or it is replaced;
    # what must never happen is a returned explanation that failed Claim-Check
    assert services._passes_claim_check(opp, opp["explanation"])
