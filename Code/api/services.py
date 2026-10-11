"""Customer packs for the API: load, attach a verified explanation, validate.

Explanations:
- Every pack carries a deterministic template explanation (set when the pack is built).
- When an LLM key is configured, an explanation can be generated at request time by
  greendash.llm.explain (gateway, guards, Claim-Check, PII minimisation) and cached.
- Whatever is returned has been through Claim-Check at response time. A cached
  explanation is re-checked on every read, so a stale or edited cache file cannot be
  served unchecked.
- The cache only ever stores explanations that were produced by the LLM and passed.
  Fallbacks are never cached, so a provider outage does not pin a template.
"""
import hashlib
import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from fastapi import HTTPException

from config.settings import settings
from greendash.contracts import CustomerOpportunities
from greendash.llm.claimcheck import check
from greendash.llm.explain import get_explanation, to_contract_explanation
from greendash.llm.templates import get_template

log = logging.getLogger("api.services")

# Locations are module constants so tests can point them at a temp directory.
PACKS_DIR = Path("out/packs")
CACHE_PACKS_DIR = Path("out/cache/packs")
EXPLANATION_CACHE_DIR = Path("out/cache/explanations")
FIXTURE_PACKS = Path("fixtures/status.json")
DECISIONS = Path("config/decisions.yaml")
MANIFEST = Path("out/run_manifest.json")

_KEY_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
_EXPLANATION_KEYS = {"sentences", "source", "claimcheck_status"}
_SENTENCE_KEYS = {"text", "fields", "check"}
_LLM_DIR = Path(__file__).resolve().parents[1] / "greendash" / "llm"


def _read_manifest() -> str:
    """The run manifest hash from out/run_manifest.json, or "unavailable"."""
    try:
        value = json.loads(MANIFEST.read_text()).get("manifest_hash")
        if isinstance(value, str) and value:
            return value
    except Exception:
        pass
    return "unavailable"


def _llm_configured() -> bool:
    return bool(settings.llm_api_key or os.environ.get("GEMINI_API_KEY"))


def _template_explanation(pid: Optional[str], status: Optional[str]) -> Dict[str, Any]:
    text = get_template(pid, status)
    return {"sentences": [{"text": text, "fields": [], "check": "TEMPLATE"}],
            "source": "template", "claimcheck_status": "FALLBACK"}


def _is_contract_explanation(expl: Any) -> bool:
    return (isinstance(expl, dict) and set(expl) == _EXPLANATION_KEYS
            and isinstance(expl.get("sentences"), list) and expl["sentences"]
            and all(isinstance(s, dict) and set(s) == _SENTENCE_KEYS for s in expl["sentences"])
            and expl.get("source") in ("llm", "template")
            and expl.get("claimcheck_status") in ("PASS", "FALLBACK"))


def _normalise_explanation(opp: Dict[str, Any]) -> Dict[str, Any]:
    """Make opp["explanation"] a valid contracts.Explanation dict.

    Accepts a contract explanation, a raw get_explanation() result (older cache files
    stored those, with extra keys the contract forbids), or nothing (template).
    """
    pid, status = opp.get("opportunity_id"), opp.get("status")
    expl = opp.get("explanation")
    if _is_contract_explanation(expl):
        return expl
    if isinstance(expl, dict) and "sentences" in expl and "claimcheck_status" in expl and "source" in expl:
        try:
            adapted = to_contract_explanation(expl)
            if _is_contract_explanation(adapted):
                return adapted
        except Exception:
            pass
    return _template_explanation(pid, status)


def _version_tag() -> str:
    """Changes when the prompt, model config or Claim-Check rules change."""
    h = hashlib.sha256()
    for path in (_LLM_DIR / "prompts" / "system_v2.txt", _LLM_DIR / "claimcheck.py",
                 Path(__file__).resolve().parents[1] / "config" / "llm.yaml"):
        try:
            h.update(path.read_bytes())
        except OSError:
            h.update(b"missing:" + path.name.encode())
    return h.hexdigest()[:16]


def _cache_path(customer_key: str, opp: Dict[str, Any], manifest_id: str) -> Path:
    facts = {k: opp.get(k) for k in ("opportunity_id", "status", "propensity", "confidence",
                                     "reason_codes", "impact", "eligibility")}
    digest = hashlib.sha256(json.dumps([facts, manifest_id, _version_tag()],
                                       sort_keys=True, default=str).encode()).hexdigest()[:24]
    return EXPLANATION_CACHE_DIR / f"{customer_key}_{opp.get('opportunity_id')}_{digest}.json"


def _passes_claim_check(opp: Dict[str, Any], expl: Dict[str, Any]) -> bool:
    try:
        result = check(opp, expl["sentences"])
    except Exception:
        return False
    return result.get("verdict") == "PASS"


NEUTRAL_TEXT = "Information for this option is not available right now."


def _enrich_explanation(opp: Dict[str, Any], customer_key: str, manifest_id: str) -> Dict[str, Any]:
    """Return opp with a valid explanation that has passed Claim-Check. Never raises.

    The check runs on whatever is about to be returned (template, cached or fresh).
    If even that fails, a fixed neutral sentence is used.
    """
    opp = _enrich_core(opp, customer_key, manifest_id)
    if not _passes_claim_check(opp, opp["explanation"]):
        opp["explanation"] = {"sentences": [{"text": NEUTRAL_TEXT, "fields": [], "check": "TEMPLATE"}],
                              "source": "template", "claimcheck_status": "FALLBACK"}
    return opp


def _enrich_core(opp: Dict[str, Any], customer_key: str, manifest_id: str) -> Dict[str, Any]:
    opp["explanation"] = _normalise_explanation(opp)
    if not _llm_configured() or not _KEY_RE.match(customer_key):
        return opp

    path = _cache_path(customer_key, opp, manifest_id)
    try:
        cached = json.loads(path.read_text()).get("contract_explanation")
        if _is_contract_explanation(cached) and cached["source"] == "llm" \
                and _passes_claim_check(opp, cached):
            opp["explanation"] = cached
            return opp
    except Exception:
        pass

    try:
        # customer_key is accepted by get_explanation for compatibility; it is never
        # sent to the model (the pack is minimised and identifiers are dropped).
        expl = to_contract_explanation(get_explanation(opp, customer_key=customer_key))
        if (_is_contract_explanation(expl) and expl["source"] == "llm"
                and expl["claimcheck_status"] == "PASS" and _passes_claim_check(opp, expl)):
            opp["explanation"] = expl
            try:
                EXPLANATION_CACHE_DIR.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps({"contract_explanation": expl}, indent=2))
            except OSError:
                log.warning("explanation cache write failed")
    except Exception:
        log.warning("explanation enrichment failed; using template")
    return opp


def _pack_file(key: str) -> Optional[Path]:
    order = (CACHE_PACKS_DIR, PACKS_DIR) if settings.DEMO_MODE == "cached" else (PACKS_DIR, CACHE_PACKS_DIR)
    for base in order:
        f = base / f"{key}.json"
        if f.exists():
            return f
    if settings.DEMO_MODE == "fixtures" and FIXTURE_PACKS.exists():
        return FIXTURE_PACKS
    return None


def load_customer_packs(key: str, display_id: str) -> CustomerOpportunities:
    if not _KEY_RE.match(key or ""):
        raise HTTPException(status_code=404, detail="Customer not found")
    f = _pack_file(key)
    if f is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    data = json.loads(f.read_text())
    cfg = yaml.safe_load(DECISIONS.read_text())
    manifest_id = _read_manifest()
    opportunities = [_enrich_explanation(v, key, manifest_id) for _, v in sorted(data.items())]
    return CustomerOpportunities.model_validate_json(json.dumps({
        "customer_id": display_id,
        "persona": None,
        "opportunities": opportunities,
        "cutoff_date": cfg["cutoff_date"],
        "outcome_window_days": cfg["outcome_window_days"],
        "run_manifest": manifest_id,
    }))
