"""API authentication, authorization, feedback encryption and explanation serving.

Hermetic: packs are written to a temp directory, the explainer is mocked, no network,
no Gemini, no generated pipeline artifacts required.
"""
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from api import services
from api.main import app
from config.settings import DEFAULT_JWT_SECRET, Settings, settings
from greendash.contracts import CustomerOpportunities
from greendash.llm.claimcheck import check
from greendash.llm.templates import TEMPLATES, get_template
from greendash.security.authz import issue_token

@pytest.fixture(autouse=True)
def _real_auth():
    """These tests exercise real token validation, so no dependency override may be active."""
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


STRONG = "x" * 8 + "Kq7Zp2Lw9Rt4Vb6Nm1Cx3Hs5Jd8Fg0Ua"          # 41 chars, not a placeholder
PERSONA = "CUST-0001"


def client(role=None, sub=PERSONA, **token_kw):
    headers = {}
    if role is not None:
        headers["Authorization"] = "Bearer " + issue_token(role, sub, **token_kw)
    return TestClient(app, headers=headers)


# ---- token validation -----------------------------------------------------------------
def test_missing_token_is_401_with_challenge():
    r = TestClient(app).get(f"/api/customers/{PERSONA}/opportunities")
    assert r.status_code == 401
    assert r.headers.get("www-authenticate", "").lower().startswith("bearer")


@pytest.mark.parametrize("header", ["Bearer", "Bearer ", "Basic abc", "Token abc", "Bearer not.a.jwt"])
def test_malformed_authorization_is_401(header):
    r = TestClient(app, headers={"Authorization": header}).get("/api/eval/summary")
    assert r.status_code == 401


def test_expired_token_is_401():
    r = client("EVALUATOR", expires_in=-10).get("/api/eval/summary")
    assert r.status_code == 401 and "expired" in r.json()["detail"].lower()


def test_wrong_signature_is_401():
    token = issue_token("EVALUATOR", PERSONA, secret="a-completely-different-secret-0123456789")
    r = TestClient(app, headers={"Authorization": f"Bearer {token}"}).get("/api/eval/summary")
    assert r.status_code == 401 and "signature" in r.json()["detail"].lower()


def _forge(payload, key=None, alg="HS256"):
    return jwt.encode(payload, key if key is not None else settings.jwt_secret, algorithm=alg)


def test_token_without_exp_is_rejected():
    token = _forge({"role": "EVALUATOR", "sub": PERSONA})          # validly signed, no exp
    r = TestClient(app, headers={"Authorization": f"Bearer {token}"}).get("/api/eval/summary")
    assert r.status_code == 401


def test_token_with_unknown_role_is_rejected():
    exp = datetime.now(timezone.utc) + timedelta(minutes=5)
    token = _forge({"role": "ROOT", "sub": PERSONA, "exp": exp})
    r = TestClient(app, headers={"Authorization": f"Bearer {token}"}).get("/api/eval/summary")
    assert r.status_code == 401


def test_token_without_role_is_401_not_500():
    exp = datetime.now(timezone.utc) + timedelta(minutes=5)
    token = _forge({"sub": PERSONA, "exp": exp})
    r = TestClient(app, headers={"Authorization": f"Bearer {token}"}).get("/api/eval/summary")
    assert r.status_code == 401


def test_alg_none_token_is_rejected():
    exp = int((datetime.now(timezone.utc) + timedelta(minutes=5)).timestamp())
    token = jwt.encode({"role": "AUDITOR", "sub": "", "exp": exp}, key=None, algorithm="none")
    r = TestClient(app, headers={"Authorization": f"Bearer {token}"}).get("/api/governance/audit")
    assert r.status_code == 401


def test_other_hmac_algorithm_is_rejected():
    exp = datetime.now(timezone.utc) + timedelta(minutes=5)
    token = _forge({"role": "AUDITOR", "sub": "", "exp": exp}, alg="HS512")
    r = TestClient(app, headers={"Authorization": f"Bearer {token}"}).get("/api/governance/audit")
    assert r.status_code == 401


def test_issue_token_refuses_unknown_role():
    with pytest.raises(ValueError):
        issue_token("ROOT", PERSONA)


# ---- role and subject enforcement ---------------------------------------------------------
def test_customer_token_forbidden_on_evaluator_endpoint():
    assert client("CUSTOMER").get("/api/eval/summary").status_code == 403


def test_staff_role_allowed_on_eval_endpoint():
    assert client("EVALUATOR").get("/api/eval/summary").status_code == 200


def test_analyst_cannot_open_scenario_lab():
    r = client("PORTFOLIO_ANALYST").post("/api/scenario", json={"customer_id": PERSONA, "mutations": ["SELL_CAR"]})
    assert r.status_code == 403


def test_governance_is_open_to_auditor_and_evaluator_only():
    # The UI grants the Governance tab to exactly these two roles (app/components/shell.py).
    for role in ("CUSTOMER", "RELATIONSHIP_MANAGER", "PORTFOLIO_ANALYST"):
        assert client(role).get("/api/governance/audit").status_code == 403, role
    for role in ("AUDITOR", "EVALUATOR"):
        # Allowed past authorization. The body needs a migrated DB and generated data, so
        # a server error is fine here; 401/403 is not.
        token = issue_token(role, "")
        c = TestClient(app, headers={"Authorization": f"Bearer {token}"}, raise_server_exceptions=False)
        assert c.get("/api/governance/audit").status_code not in (401, 403), role


def test_demo_token_requires_a_customer_id_for_customers(monkeypatch):
    monkeypatch.setattr(settings, "ENV", "demo")
    c = TestClient(app)
    assert c.post("/api/auth/demo-token", json={"role": "CUSTOMER"}).status_code == 422
    assert c.post("/api/auth/demo-token", json={"role": "CUSTOMER", "customer_id": "x' OR 1=1"}).status_code == 422
    assert c.post("/api/auth/demo-token", json={"role": "EVALUATOR"}).status_code == 200


def test_keys_in_dotenv_are_read_through_settings(tmp_path):
    env = tmp_path / ".env"
    env.write_text("GEMINI_API_KEY=from-dotenv\nDATA_KEY=abc\nDATA_KEY_OLD=def\n")
    s = Settings(_env_file=str(env))
    assert s.llm_api_key == "from-dotenv" and s.data_key == "abc" and s.data_key_old == "def"


def test_customer_cannot_read_another_customers_opportunities():
    r = client("CUSTOMER", sub="CUST-0002").get(f"/api/customers/{PERSONA}/opportunities")
    assert r.status_code == 403


def test_customer_token_without_subject_is_forbidden():
    r = client("CUSTOMER", sub="").get(f"/api/customers/{PERSONA}/opportunities")
    assert r.status_code == 403


def test_bad_customer_id_is_422():
    r = client("EVALUATOR").get("/api/customers/CUST-0001'%3B%20DROP%20TABLE%20users--/opportunities")
    assert r.status_code == 422


# ---- demo token and settings ---------------------------------------------------------------
def test_demo_token_disabled_unless_env_is_demo(monkeypatch):
    for env in ("development", "production", "", "Demo "):
        monkeypatch.setattr(settings, "ENV", env)
        r = TestClient(app).post("/api/auth/demo-token", json={"role": "CUSTOMER", "customer_id": PERSONA})
        assert r.status_code == 404, env


def test_demo_token_enabled_in_demo_env(monkeypatch):
    monkeypatch.setattr(settings, "ENV", "demo")
    r = TestClient(app).post("/api/auth/demo-token", json={"role": "CUSTOMER", "customer_id": PERSONA})
    assert r.status_code == 200 and r.json()["access_token"]


def test_default_env_is_development_not_demo():
    assert Settings(_env_file=None).ENV == "development"


@pytest.mark.parametrize("env", ["production", "Production", " PROD ", "demo", "staging", "", "prod-eu"])
def test_deployed_envs_refuse_placeholder_secret(env):
    with pytest.raises(ValueError, match="placeholder or insecure JWT secret"):
        Settings(_env_file=None, ENV=env, jwt_secret=DEFAULT_JWT_SECRET)


@pytest.mark.parametrize("secret", ["", "short", "secret", "changeme", "a" * 31,
                                    "super_secret_key_for_hackathon_demo"])
def test_deployed_env_refuses_weak_secrets(secret):
    with pytest.raises(ValueError):
        Settings(_env_file=None, ENV="production", jwt_secret=secret)


def test_deployed_env_accepts_strong_secret():
    assert Settings(_env_file=None, ENV="production", jwt_secret=STRONG).ENV == "production"


@pytest.mark.parametrize("env", ["development", "dev", "test", "TEST"])
def test_local_envs_may_use_placeholder(env):
    assert Settings(_env_file=None, ENV=env, jwt_secret=DEFAULT_JWT_SECRET)


# ---- feedback: encryption fails closed, body is required -----------------------------------
@pytest.fixture
def captured_feedback(monkeypatch):
    rows = []
    monkeypatch.setattr("api.routers.feedback.repo.add_feedback",
                        lambda *a: rows.append(a))
    return rows


def _fb(note):
    return {"opportunity_id": "GP01", "kind": "THIS_IS_WRONG", "note": note}


def test_feedback_note_is_stored_encrypted(monkeypatch, captured_feedback):
    from security.crypto import generate_key
    monkeypatch.setattr(settings, "data_key", generate_key())
    note = "my phone is 07700 900123 please call"
    r = client("CUSTOMER").post(f"/api/customers/{PERSONA}/feedback", json=_fb(note))
    assert r.status_code == 200
    stored = captured_feedback[0][3]
    assert stored.startswith("gd1.") and "07700" not in stored and "please call" not in stored


def test_feedback_note_refused_when_key_missing(monkeypatch, captured_feedback):
    monkeypatch.setattr(settings, "data_key", "")
    r = client("CUSTOMER").post(f"/api/customers/{PERSONA}/feedback", json=_fb("secret note"))
    assert r.status_code == 503
    assert captured_feedback == []                      # nothing stored in the clear
    assert "secret note" not in r.text


def test_feedback_without_note_needs_no_key(monkeypatch, captured_feedback):
    monkeypatch.setattr(settings, "data_key", "")
    r = client("CUSTOMER").post(f"/api/customers/{PERSONA}/feedback", json=_fb(None))
    assert r.status_code == 200 and captured_feedback[0][3] is None


def test_feedback_requires_a_body():
    r = client("CUSTOMER").post(f"/api/customers/{PERSONA}/feedback")
    assert r.status_code == 422


def test_feedback_for_another_customer_is_forbidden(captured_feedback):
    r = client("CUSTOMER", sub="CUST-0002").post(f"/api/customers/{PERSONA}/feedback", json=_fb(None))
    assert r.status_code == 403 and captured_feedback == []


# ---- explanations served by the API --------------------------------------------------------
def _packs(tmp_path, monkeypatch, manifest=None):
    src = json.loads((ROOT / "fixtures" / "opps_recommend.json").read_text())
    opps = CustomerOpportunities.model_validate_json(json.dumps(src)).opportunities
    packs = {o.opportunity_id.value: o.model_dump(mode="json") for o in opps}
    for p in packs.values():
        p["explanation"] = None
    pdir = tmp_path / "packs"
    pdir.mkdir()
    (pdir / f"{PERSONA}.json").write_text(json.dumps(packs))
    monkeypatch.setattr(services, "PACKS_DIR", pdir)
    monkeypatch.setattr(services, "CACHE_PACKS_DIR", tmp_path / "nocache")
    monkeypatch.setattr(services, "EXPLANATION_CACHE_DIR", tmp_path / "expl")
    monkeypatch.setattr(services, "DECISIONS", ROOT / "config" / "decisions.yaml")
    mp = tmp_path / "run_manifest.json"
    if manifest is not None:
        mp.write_text(json.dumps(manifest))
    monkeypatch.setattr(services, "MANIFEST", mp)
    monkeypatch.setattr(services, "FIXTURE_PACKS", tmp_path / "nofixture.json")
    return packs


def _llm_result(text="Your fuel spend has run above your usual level."):
    return {"explanation": text, "metrics_summary": "", "source": "llm",
            "claimcheck_status": "PASS", "fallback_reason": None, "attempts": 1,
            "sentences": [{"text": text, "fields": ["reasons.code"], "check": "PASS"}]}


def _no_llm(monkeypatch):
    monkeypatch.setattr(settings, "llm_api_key", None)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    def boom(*a, **k):
        raise AssertionError("explainer must not be called without a key")
    monkeypatch.setattr(services, "get_explanation", boom)


def _get(role="CUSTOMER", sub=PERSONA):
    return client(role, sub).get(f"/api/customers/{PERSONA}/opportunities")


def test_template_explanation_without_key(tmp_path, monkeypatch):
    _packs(tmp_path, monkeypatch)
    _no_llm(monkeypatch)
    r = _get()
    assert r.status_code == 200
    for opp in r.json()["opportunities"]:
        e = opp["explanation"]
        assert e["source"] == "template" and e["claimcheck_status"] == "FALLBACK"
        assert e["sentences"] and e["sentences"][0]["check"] == "TEMPLATE"


def test_manifest_comes_from_manifest_hash_not_a_constant(tmp_path, monkeypatch):
    _packs(tmp_path, monkeypatch, manifest={"manifest_hash": "sha256:" + "ab" * 32})
    _no_llm(monkeypatch)
    assert _get().json()["run_manifest"] == "sha256:" + "ab" * 32


def test_manifest_unavailable_is_reported_honestly(tmp_path, monkeypatch):
    _packs(tmp_path, monkeypatch)             # no manifest file
    _no_llm(monkeypatch)
    assert _get().json()["run_manifest"] == "unavailable"


def test_raw_explainer_result_in_pack_is_normalised(tmp_path, monkeypatch):
    packs = _packs(tmp_path, monkeypatch)
    for p in packs.values():                   # what the old cache step wrote into packs
        p["explanation"] = {**_llm_result(), "claimcheck_status": "PII_BLOCK", "source": "template"}
    (tmp_path / "packs" / f"{PERSONA}.json").write_text(json.dumps(packs))
    _no_llm(monkeypatch)
    r = _get()
    assert r.status_code == 200
    e = r.json()["opportunities"][0]["explanation"]
    assert set(e) == {"sentences", "source", "claimcheck_status"} and e["claimcheck_status"] == "FALLBACK"


def test_llm_explanation_is_served_and_cached(tmp_path, monkeypatch):
    _packs(tmp_path, monkeypatch)
    monkeypatch.setattr(settings, "llm_api_key", "test-key")
    calls = []

    def fake(opp, customer_key):
        calls.append(customer_key)
        return _llm_result()
    monkeypatch.setattr(services, "get_explanation", fake)
    first_opps = _get().json()["opportunities"]
    llm_idx = [i for i, o in enumerate(first_opps) if o["explanation"]["source"] == "llm"]
    assert llm_idx, "at least one pack should accept the LLM sentence"
    for i in llm_idx:
        assert first_opps[i]["explanation"]["claimcheck_status"] == "PASS"
    n = len(calls)
    second_opps = _get().json()["opportunities"]
    # Packs that passed are served from cache; packs that fell back are re-asked.
    assert len(calls) - n == len(first_opps) - len(llm_idx)
    for i in llm_idx:
        assert second_opps[i]["explanation"] == first_opps[i]["explanation"]
    cached = next((tmp_path / "expl").glob("*.json")).read_text()
    assert "attempts" not in cached and "fallback_reason" not in cached   # contract only


def test_tampered_cache_entry_is_not_served(tmp_path, monkeypatch):
    _packs(tmp_path, monkeypatch)
    monkeypatch.setattr(settings, "llm_api_key", "test-key")
    monkeypatch.setattr(services, "get_explanation", lambda opp, customer_key: _llm_result())
    _get()
    for f in (tmp_path / "expl").glob("*.json"):
        d = json.loads(f.read_text())
        d["contract_explanation"]["sentences"][0]["text"] = "This is guaranteed to save you 99 kg."
        f.write_text(json.dumps(d))
    monkeypatch.setattr(services, "get_explanation",
                        lambda opp, customer_key: (_ for _ in ()).throw(RuntimeError("down")))
    r = _get()
    assert r.status_code == 200
    for opp in r.json()["opportunities"]:
        assert "guaranteed" not in json.dumps(opp["explanation"])
        assert opp["explanation"]["source"] == "template"


def test_failed_claim_check_never_reaches_the_customer(tmp_path, monkeypatch):
    _packs(tmp_path, monkeypatch)
    monkeypatch.setattr(settings, "llm_api_key", "test-key")
    bad = _llm_result("You will definitely save 4,000 kg and are pre-approved.")
    monkeypatch.setattr(services, "get_explanation", lambda opp, customer_key: bad)
    r = _get()
    for opp in r.json()["opportunities"]:
        assert "pre-approved" not in json.dumps(opp["explanation"])
        assert opp["explanation"]["source"] == "template"
    assert not (tmp_path / "expl").exists() or not list((tmp_path / "expl").glob("*.json"))


def test_fallbacks_are_not_cached(tmp_path, monkeypatch):
    _packs(tmp_path, monkeypatch)
    monkeypatch.setattr(settings, "llm_api_key", "test-key")
    down = {"explanation": "x", "sentences": [{"text": "x", "fields": [], "check": "TEMPLATE"}],
            "source": "template", "claimcheck_status": "FALLBACK", "fallback_reason": "PROVIDER_ERROR",
            "attempts": 2, "metrics_summary": ""}
    monkeypatch.setattr(services, "get_explanation", lambda opp, customer_key: down)
    assert _get().status_code == 200
    assert not (tmp_path / "expl").exists() or not list((tmp_path / "expl").glob("*.json"))


def test_unsafe_customer_key_is_404(tmp_path, monkeypatch):
    _packs(tmp_path, monkeypatch)
    with pytest.raises(Exception) as exc:
        services.load_customer_packs("../etc/passwd", "CUST-0001")
    assert getattr(exc.value, "status_code", None) == 404


@pytest.mark.parametrize("pid", sorted(TEMPLATES))
def test_every_template_passes_claim_check(pid):
    pack = {"opportunity_id": pid, "status": "RECOMMEND"}
    for status, text in TEMPLATES[pid].items():
        assert check(pack, [{"text": get_template(pid, status), "fields": []}])["verdict"] == "PASS", (pid, status)


def test_cache_step_does_not_write_raw_explainer_results_into_packs():
    src = (ROOT / "greendash" / "cache.py").read_text(encoding="utf-8")
    assert "get_explanation" not in src


# ---- request limits, refusal logging, headers ---------------------------------------------
def test_rate_limit_returns_429_then_recovers(monkeypatch):
    from api import main
    monkeypatch.setitem(main.LIMITS, "", 3)
    main._hits.clear()
    codes = [TestClient(app).get("/healthz").status_code for _ in range(5)]
    assert codes == [200, 200, 200, 429, 429]
    main._hits.clear()
    assert TestClient(app).get("/healthz").status_code == 200


def test_oversized_body_is_refused_before_any_handler():
    r = client("EVALUATOR").post("/api/claimcheck", content=b"x" * (70 * 1024),
                                 headers={"Content-Type": "application/json"})
    assert r.status_code == 413


def test_refusals_are_logged_without_token_or_body(caplog):
    import logging
    caplog.set_level(logging.WARNING, logger="api.access")
    r = TestClient(app, headers={"Authorization": "Bearer secret-token-value"}).get("/api/eval/summary")
    assert r.status_code == 401
    line = "\n".join(rec.getMessage() for rec in caplog.records)
    assert "status=401" in line and "/api/eval/summary" in line and "secret-token-value" not in line


def test_every_response_carries_security_headers():
    r = TestClient(app).get("/healthz")
    assert r.headers["x-content-type-options"] == "nosniff" and r.headers["cache-control"] == "no-store"


def test_evaluator_is_limited_to_demo_personas():
    assert client("EVALUATOR").get("/api/customers/CUST-0100/opportunities").status_code == 403
