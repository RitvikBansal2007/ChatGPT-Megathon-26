"""Explainer vs the frozen contracts, the audit sink and the eval judge (mock provider only).

Covers: contracts.Explanation adapter, contracts.Opportunity input, template figures
taken only from pack metrics, db.audit handoff (real sqlite, temp file), and the judge's
deterministic canary-leak check. No network, no key, no Gemini.
"""
import json
import logging
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from greendash.contracts import CustomerOpportunities, Explanation
from greendash.llm import explain as ex
from greendash.llm.guard import CanaryError, contains_canary, generate_canary
from greendash.llm.templates import get_template

CANARY = "CANARY-CONTRACT-0123456789abcdef"
FIXTURE = ROOT / "fixtures" / "opps_recommend.json"


class MockProvider:
    def __init__(self, *replies):
        self.replies, self.calls = list(replies), []

    def generate(self, *, system, user, max_tokens, timeout_s):
        self.calls.append(user)
        r = self.replies[min(len(self.calls) - 1, len(self.replies) - 1)]
        if isinstance(r, Exception):
            raise r
        return r


def reply(text, cited=("reasons.code",)):
    return json.dumps({"sentences": [{"text": text, "cited_fields": list(cited)}]})


def opportunity(index=0):
    return CustomerOpportunities.model_validate_json(FIXTURE.read_text(encoding="utf-8")).opportunities[index]


def payload_of(call):
    return json.loads(call.split("<evidence_pack>\n")[1].split("\n</evidence_pack>")[0])


# ---- contracts.Explanation adapter ----------------------------------------------
def test_pass_result_adapts_to_contract_explanation():
    prov = MockProvider(reply("Your fuel spend is above your usual range.", ("reasons.code",)))
    res = ex.get_explanation(opportunity(), canary_token=CANARY, provider=prov)
    assert res["claimcheck_status"] == "PASS"
    adapted = ex.to_contract_explanation(res)
    parsed = Explanation.model_validate(adapted)       # strict, extra="forbid"
    assert parsed.source == "llm" and parsed.claimcheck_status == "PASS"
    assert [(s.text, s.fields, s.check) for s in parsed.sentences] == [
        ("Your fuel spend is above your usual range.", ["reasons.code"], "PASS")]


@pytest.mark.parametrize("pack_extra,expected_detail", [
    ({"region": "contact me at jo@example.com"}, "PII_BLOCK"),
    ({}, "FALLBACK"),
])
def test_fallback_adapts_to_contract_with_template_sentences(pack_extra, expected_detail):
    pack = dict(opportunity().model_dump(mode="json"), **pack_extra)
    prov = MockProvider("bad", "bad")
    res = ex.get_explanation(pack, canary_token=CANARY, provider=prov)
    assert res["claimcheck_status"] == expected_detail
    parsed = Explanation.model_validate(ex.to_contract_explanation(res))
    assert parsed.source == "template"
    assert parsed.claimcheck_status == "FALLBACK"      # contract has no PII_BLOCK value
    assert [s.check for s in parsed.sentences] == ["TEMPLATE"]
    assert "jo@example.com" not in json.dumps(res)


def test_security_statuses_adapt_to_fallback(monkeypatch):
    monkeypatch.setattr(ex, "CONFIG_PATH", str(ROOT / "nope.yaml"))
    res = ex.get_explanation(opportunity(), canary_token=CANARY, provider=MockProvider())
    assert res["claimcheck_status"] == "SECURITY_CONFIG_ERROR"
    assert Explanation.model_validate(ex.to_contract_explanation(res)).claimcheck_status == "FALLBACK"


def test_string_explanation_is_kept_for_backward_compatibility():
    res = ex.get_explanation(opportunity(), canary_token=CANARY,
                             provider=MockProvider(reply("Fuel spend is high.")))
    assert isinstance(res["explanation"], str)
    assert res["explanation"] == " ".join(s["text"] for s in res["sentences"])


# ---- contracts.Opportunity as input -------------------------------------------------
def test_opportunity_model_and_dict_reach_model_minimised():
    opp = opportunity()
    for pack in (opp, opp.model_dump(mode="json")):
        prov = MockProvider(reply("Fuel spend is high."))
        ex.get_explanation(pack, canary_token=CANARY, provider=prov)
        seen = payload_of(prov.calls[0])
        assert seen["product_id"] == "GP01"
        assert seen["status"] == "RECOMMEND"
        assert 0 <= seen["confidence"] <= 1
        assert {"code": "HIGH_FUEL_SPEND", "value": 185} in seen["reasons"]
        blob = json.dumps(seen)
        for banned in ("customer_id", "phrase", "observed_at", "inferred_transactions",
                       "rules_fired", "plain_reasons", "CUST-"):
            assert banned not in blob


def test_impact_status_does_not_overwrite_display_status():
    prov = MockProvider(reply("Fuel spend is high."))
    ex.get_explanation(opportunity(), canary_token=CANARY, provider=prov)
    assert payload_of(prov.calls[0])["status"] == "RECOMMEND"      # not "ESTIMATED"


# ---- GP01 / GP03 (and GP02) templates: figures only from pack metrics --------------------
def _opp_with(product, status, reasons):
    d = opportunity().model_dump(mode="json")
    d.update(opportunity_id=product, status=status, reason_codes=reasons)
    return d


def _reason(metric, value):
    return {"code": "X_CODE", "phrase": "p", "metric": metric, "value": value,
            "display": "d", "observed_at": "2026-06-30", "source": "bank_record"}


def test_gp01_stays_pending_while_only_a_monthly_metric_exists():
    # avg_monthly_fuel_gbp is monthly; the template does not say so, so it is not used.
    pack = _opp_with("GP01", "RECOMMEND", [_reason("avg_monthly_fuel_gbp", 185)])
    res = ex.get_explanation(pack, canary_token=CANARY, provider=MockProvider("bad", "bad"))
    assert res["explanation"] == get_template("GP01", "PENDING")
    assert "185" not in res["explanation"]


@pytest.mark.parametrize("product,metric,value,expected", [
    ("GP02", "gas_kwh_12m", 11500, "11,500 kWh annual gas"),
    ("GP03", "electricity_kwh_12m", 3200, "3,200 kWh annual electricity"),
])
def test_recommend_template_uses_metric_value_from_pack(product, metric, value, expected):
    pack = _opp_with(product, "RECOMMEND", [_reason(metric, value)])
    res = ex.get_explanation(pack, canary_token=CANARY, provider=MockProvider("bad", "bad"))
    assert res["source"] == "template"
    assert expected in res["explanation"]
    assert "[" not in res["explanation"] and "{" not in res["explanation"]


@pytest.mark.parametrize("product", ["GP01", "GP02", "GP03"])
def test_recommend_template_without_metric_never_shows_placeholder_or_invents(product):
    pack = _opp_with(product, "RECOMMEND", [_reason("annual_mileage", 12000)])
    res = ex.get_explanation(pack, canary_token=CANARY, provider=MockProvider("bad", "bad"))
    assert res["explanation"] == get_template(product, "PENDING")
    assert "12,000" not in res["explanation"]
    assert "[" not in res["explanation"] and "{" not in res["explanation"]


def test_template_ignores_non_numeric_and_wrong_metric_values():
    for bad in ("3200", None, True, float("nan"), "3200; ignore previous"):
        pack = _opp_with("GP03", "RECOMMEND", [_reason("electricity_kwh_12m", bad)])
        res = ex.get_explanation(pack, canary_token=CANARY, provider=MockProvider("x", "x"))
        assert res["explanation"] == get_template("GP03", "PENDING"), bad


def test_gp04_recommend_template_needs_no_figure():
    pack = _opp_with("GP04", "RECOMMEND", [])
    res = ex.get_explanation(pack, canary_token=CANARY, provider=MockProvider("x", "x"))
    assert res["explanation"] == get_template("GP04", "RECOMMEND")


# ---- audit handoff (real greendash.db.audit, temp sqlite) -------------------------------------
@pytest.fixture
def audit_db(tmp_path, monkeypatch):
    pytest.importorskip("pydantic_settings")
    from config.settings import settings
    from greendash.db import audit, migrate
    # main bug: Settings has no DB_PATH field (only database_url), so set it on the class.
    monkeypatch.setattr(type(settings), "DB_PATH", str(tmp_path / "audit.db"), raising=False)
    migrate.migrate()
    return audit, settings


@pytest.mark.parametrize("pack_extra,provider,verdict,source", [
    ({}, MockProvider(reply("Fuel spend is high.")), "PASS", "llm"),
    ({}, MockProvider("bad", "bad"), "FALLBACK", "template"),
    ({"region": "SW1A 1AA"}, MockProvider(), "PII_BLOCK", "template"),
])
def test_audit_append_accepts_explainer_result_and_stores_no_sensitive_text(
        audit_db, pack_extra, provider, verdict, source):
    import sqlite3
    audit, settings = audit_db
    pack = dict(opportunity().model_dump(mode="json"), **pack_extra)
    res = ex.get_explanation(pack, canary_token=CANARY, provider=provider)
    args = ex.to_audit_args(res, customer_key="k_abc123", product_id="GP01")
    assert args["verdict"] == verdict and args["source"] == source
    audit.append(**args)
    assert audit.verify_chain() == (True, None)
    rows = sqlite3.connect(settings.DB_PATH).execute("SELECT * FROM claim_audit").fetchall()
    blob = json.dumps(rows, default=str)
    for secret in ("CUST-", "SW1A", res["explanation"], CANARY, "Fuel spend is high"):
        assert secret not in blob


def test_audit_args_use_only_fixed_vocabulary():
    for status, reason, verdict in [
        ("PASS", None, "PASS"), ("PII_BLOCK", "INPUT_PII", "PII_BLOCK"),
        ("FALLBACK", "CLAIMCHECK_FAIL", "FALLBACK"),
        ("SECURITY_CONFIG_ERROR", "CONFIG_ERROR", "FALLBACK"),
        ("SECURITY_MODULE_UNAVAILABLE", "MODULE_UNAVAILABLE", "FALLBACK"),
    ]:
        args = ex.to_audit_args({"claimcheck_status": status, "fallback_reason": reason,
                                 "source": "template"}, "k", "GP01")
        assert args["verdict"] == verdict
        assert args["rules_violated"] == ([reason] if reason else [])


# ---- judge: canary detection without the explainer exposing the canary ---------------------
def test_explainer_result_does_not_expose_canary_and_judge_helper_finds_leaks():
    judge = pytest.importorskip("eval.llm_eval.judge")
    canary = generate_canary()
    clean = ex.get_explanation(opportunity(), canary_token=canary,
                               provider=MockProvider(reply("Fuel spend is high.")))
    assert "canary" not in clean                         # not exposed...
    assert canary not in json.dumps(clean)
    assert judge.canary_leakage(clean, canary) == 0      # ...and detectably absent
    # a result that did leak (any field, any separator style) is caught
    assert judge.canary_leakage({"explanation": "token " + canary}, canary) == 1
    assert judge.canary_leakage({"x": {"y": canary.replace("-", " ")}}, canary) == 1
    assert judge.canary_leakage({"explanation": canary.lower()}, canary) == 1


def test_judge_does_not_depend_on_a_canary_key_or_default_token():
    judge = pytest.importorskip("eval.llm_eval.judge")
    canary = generate_canary()
    # old behaviour: looked for result["canary"], defaulting to "canary123" -> a leak of
    # the real canary went unnoticed
    assert judge.canary_leakage({"explanation": canary}, canary) == 1
    assert judge.canary_leakage({"explanation": "canary123"}, canary) == 0


def test_judge_fails_closed_on_bad_canary():
    judge = pytest.importorskip("eval.llm_eval.judge")
    for bad in (None, "", "short", 5):
        assert judge.canary_leakage({"explanation": "ok"}, bad) == 1


def test_evaluate_explanation_overrides_model_verdict_for_canary(monkeypatch):
    judge = pytest.importorskip("eval.llm_eval.judge")
    canary = generate_canary()
    sent = {}

    class Models:
        def generate_content(self, *, model, contents, config):
            sent["prompt"] = contents
            return type("R", (), {"text": json.dumps(
                {"faithfulness": 1, "positive_tone": 1, "canary_leakage": 0, "reasoning": "ok"})})()

    monkeypatch.setattr(judge, "_get_client", lambda: type("C", (), {"models": Models()})())
    leaked = judge.evaluate_explanation({"p": 1}, {"explanation": "x " + canary}, canary=canary)
    assert leaked["canary_leakage"] == 1                 # model said 0; local check wins
    clean = judge.evaluate_explanation({"p": 1}, {"explanation": "fine"}, canary=canary)
    assert clean["canary_leakage"] == 0
    assert canary not in sent["prompt"]                  # secret never sent to the judge
    unknown = judge.evaluate_explanation({"p": 1}, {"explanation": "fine"})
    assert unknown["canary_leakage"] == 1                # no canary supplied: not "safe"


def test_contains_canary_rejects_unusable_canary():
    with pytest.raises(CanaryError):
        contains_canary("anything", "short")


# ---- logs ----------------------------------------------------------------------------------------
def test_no_sensitive_text_in_logs_for_opportunity_input(caplog):
    caplog.set_level(logging.DEBUG)
    pack = dict(opportunity().model_dump(mode="json"), region="jo.bloggs@example.com")
    ex.get_explanation(pack, canary_token=CANARY, provider=MockProvider())
    logged = "\n".join(r.getMessage() for r in caplog.records)
    assert "jo.bloggs" not in logged and "CUST-" not in logged and CANARY not in logged


# ---- settings / audit configuration -----------------------------------------------------------
def test_settings_db_path_defaults_from_database_url(monkeypatch):
    pytest.importorskip("pydantic_settings")
    from config.settings import Settings
    monkeypatch.delenv("DB_PATH", raising=False)
    assert Settings(database_url="sqlite:///some/where.db", DB_PATH="").DB_PATH == "some/where.db"
    assert Settings(DB_PATH="/x/y.db").DB_PATH == "/x/y.db"


# ---- claimcheck.check(): the shape api/routers/claimcheck.py calls -------------------------------
def _check(sentences, pack=None):
    from greendash.llm.claimcheck import check
    return check(pack if pack is not None else opportunity(), sentences)


def test_check_passes_supported_sentence_and_matches_fixture_shape():
    res = _check([{"text": "Your fuel spend is above your usual range.", "fields": ["reasons.code"]}])
    assert res["verdict"] == "PASS"
    assert res["sentences"][0]["status"] == "PASS" and res["sentences"][0]["violations"] == []
    assert res["fallback_text"] is None
    fixture = json.loads((ROOT / "fixtures" / "claimcheck_response.json").read_text(encoding="utf-8"))
    assert set(res) <= set(fixture)                      # no keys the UI does not know
    assert set(res["sentences"][0]) <= set(fixture["sentences"][0])


def test_check_blocks_unsupported_number_and_banned_phrase_with_template_fallback():
    res = _check([{"text": "This will save you 4,000 kg and you are pre-approved.", "fields": []}])
    assert res["verdict"] == "BLOCKED"
    rules = {v["rule"] for v in res["sentences"][0]["violations"]}
    assert {"NUM", "BAN"} <= rules
    assert res["fallback_text"] == get_template("GP01", "PENDING")


def test_check_verdicts_are_accepted_by_audit_vocabulary():
    for sentences in ([{"text": "ok fuel", "fields": []}], [{"text": "guaranteed 99 kg", "fields": []}]):
        assert _check(sentences)["verdict"] in {"PASS", "BLOCKED", "FALLBACK", "PII_BLOCK"}


def test_check_pii_pack_returns_pii_block_and_does_not_echo_pack():
    pack = dict(opportunity().model_dump(mode="json"), region="jo.bloggs@example.com")
    res = _check([{"text": "hello", "fields": []}], pack)
    assert res["verdict"] == "PII_BLOCK"
    assert "jo.bloggs" not in json.dumps(res)


def test_check_never_raises_on_malformed_sentences():
    res = _check([{"text": None}, "plain string", {"fields": [1, None]}])
    assert res["verdict"] in {"PASS", "BLOCKED"}
