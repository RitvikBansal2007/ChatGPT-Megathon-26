"""Production explainer: evidence pack -> verified explanation, or a deterministic template.

    pack -> greendash.llm.LLMGateway
              minimise (allow-list, PII rejected) -> guard_pre -> provider
              -> guard_post (strict JSON, PII, canary) -> Claim-Check per sentence
         -> {"explanation": str, ...}   (or the product/status template on ANY failure)

Contract notes:
- Fail closed. get_explanation never raises and never returns unverified model text.
  If the security modules or config cannot be loaded, the provider is never called.
- Model, temperature, token cap, timeout and retries come from config/llm.yaml.
- Fallback wording is the existing product/status template in templates.py.
- The result carries fixed-vocabulary codes only. No pack content, model output,
  prompt or exception text is placed in the result, in logs, or in audit fields.

Result keys:
    explanation        str   always a string (verified sentences joined, or the template)
    metrics_summary    str   "" (the gateway returns sentences only)
    source             str   "llm" | "template"
    claimcheck_status  str   PASS | PII_BLOCK | FALLBACK
                             | SECURITY_MODULE_UNAVAILABLE | SECURITY_CONFIG_ERROR
    fallback_reason    str|None  fixed code (INPUT_PII, CLAIMCHECK_FAIL, ...); None on PASS
    attempts           int   provider calls made (0 when nothing was sent)
    sentences          list  [{"text", "fields", "check"}] in contracts.Sentence shape;
                             "check" is PASS (verified) or TEMPLATE

Adapters (pure functions, no I/O):
    to_contract_explanation(result) -> dict valid for contracts.Explanation
    to_audit_args(result, customer_key, product_id) -> kwargs for db.audit.append
Nothing in this module writes to the audit log: see to_audit_args.
"""
import logging
import math
import os
from typing import Any, Dict, Mapping, Optional

from greendash.llm.templates import TEMPLATES, get_template

log = logging.getLogger("greendash.llm.explain")

STATUS_PASS = "PASS"
STATUS_PII_BLOCK = "PII_BLOCK"
STATUS_FALLBACK = "FALLBACK"
STATUS_MODULE_UNAVAILABLE = "SECURITY_MODULE_UNAVAILABLE"
STATUS_CONFIG_ERROR = "SECURITY_CONFIG_ERROR"

SOURCE_LLM = "llm"
SOURCE_TEMPLATE = "template"

_HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(_HERE, "..", "..", "config", "llm.yaml")
PROMPT_PATH = os.path.join(_HERE, "prompts", "system_v2.txt")

# Cost estimates for Gemini 1.5 Flash (as of mid-2024 pricing roughly)
# Input: $0.075 / 1M tokens -> ~£0.06
# Output: $0.30 / 1M tokens -> ~£0.24
COST_PER_1K_INPUT_GBP = 0.00006
COST_PER_1K_OUTPUT_GBP = 0.00024


class CostTracker:
    def __init__(self):
        self.total_cost_gbp = 0.0
        self.budget_limit = float(os.environ.get("LLM_BUDGET_GBP", 5.0))

    def add_cost(self, input_tokens, output_tokens):
        cost = (input_tokens / 1000.0) * COST_PER_1K_INPUT_GBP
        cost += (output_tokens / 1000.0) * COST_PER_1K_OUTPUT_GBP
        self.total_cost_gbp += cost

        if self.total_cost_gbp > self.budget_limit:
            raise Exception(f"BUDGET EXCEEDED: Total LLM cost £{self.total_cost_gbp:.4f} > £{self.budget_limit}")

    def get_total(self):
        return self.total_cost_gbp


tracker = CostTracker()


# ---- configuration -----------------------------------------------------------
class ConfigError(Exception):
    """config/llm.yaml is missing or invalid. The message is a fixed string."""


def _num(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def load_llm_config(path: Optional[str] = None) -> Dict[str, Any]:
    """Read and validate config/llm.yaml. Nothing is defaulted: a missing key is an error."""
    try:
        import yaml
        with open(path or CONFIG_PATH, "r", encoding="utf-8") as fh:
            raw = yaml.safe_load(fh)
    except Exception:
        raise ConfigError("llm config unreadable")
    if not isinstance(raw, dict):
        raise ConfigError("llm config invalid")
    model_id = raw.get("model_id")
    if not isinstance(model_id, str) or not model_id.strip():
        raise ConfigError("llm config invalid: model_id")
    temperature, max_tokens = raw.get("temperature"), raw.get("max_tokens")
    timeout, retries = raw.get("timeout_seconds"), raw.get("retries")
    if not _num(temperature) or not 0 <= temperature <= 2:
        raise ConfigError("llm config invalid: temperature")
    if not isinstance(max_tokens, int) or isinstance(max_tokens, bool) or max_tokens <= 0:
        raise ConfigError("llm config invalid: max_tokens")
    if not _num(timeout) or timeout <= 0:
        raise ConfigError("llm config invalid: timeout_seconds")
    if not isinstance(retries, int) or isinstance(retries, bool) or not 0 <= retries <= 5:
        raise ConfigError("llm config invalid: retries")
    return {"model_id": model_id.strip(), "temperature": float(temperature),
            "max_tokens": max_tokens, "timeout_seconds": float(timeout), "retries": retries}


# ---- deterministic templates ---------------------------------------------------
# Orchestrator display status (or eligibility verdict) -> templates.py status key.
# Unknown or missing statuses use PENDING, the one template that claims nothing.
_TEMPLATE_STATUS = {
    "RECOMMEND": "RECOMMEND",
    "SOFT_SURFACE": "PENDING",
    "REVIEW": "PENDING",
    "ABSTAIN": "PENDING",
    "RULED_OUT": "INELIGIBLE",
    "NOT_ELIGIBLE": "INELIGIBLE",
    "ELIGIBLE": "ELIGIBLE",
    "NEEDS_VERIFICATION": "PENDING",
    "INELIGIBLE": "INELIGIBLE",
    "PENDING": "PENDING",
    "REJECTED": "REJECTED",
}
_PLACEHOLDERS = {"fuel_spend": "[FUEL_SPEND]", "gas_kwh": "[GAS_KWH]", "elec_kwh": "[ELEC_KWH]"}

# Where each template figure may come from. A figure is used only if a pack field or a
# reason code's "metric" has exactly one of these names and a finite numeric value.
# Nothing is derived, converted or defaulted. fuel_spend has NO source on purpose: the
# only pack metric is avg_monthly_fuel_gbp (monthly) and the GP01 template text does not
# say "per month", so using it would misstate the figure. Add "avg_monthly_fuel_gbp"
# here once the template wording is confirmed. Until then GP01 RECOMMEND uses PENDING.
_TEMPLATE_SOURCES = {
    "fuel_spend": (),
    "gas_kwh": ("gas_kwh_12m", "gas_kwh"),
    "elec_kwh": ("electricity_kwh_12m", "elec_kwh"),
}


def _enum(pack: Mapping[str, Any], keys, allowed) -> Optional[str]:
    """First value under keys that is an exact member of allowed. Never free text."""
    for key in keys:
        value = pack.get(key)
        if isinstance(value, str) and value in allowed:
            return value
    return None


def _template_text(pack: Any) -> str:
    """The deterministic product/status template for this pack. Uses only enum-checked
    identifiers and finite numbers from the pack; no free text."""
    pack = pack if isinstance(pack, Mapping) else {}
    product = _enum(pack, ("product_id", "recommendation", "opportunity_id"), TEMPLATES)
    status = _enum(pack, ("status",), _TEMPLATE_STATUS)
    key = _TEMPLATE_STATUS.get(status, "PENDING")
    features = pack.get("evidence_features")
    reasons = [r for field in ("reason_codes", "reasons")
               for r in (pack.get(field) if isinstance(pack.get(field), (list, tuple)) else [])
               if isinstance(r, Mapping)]
    context = dict(_PLACEHOLDERS)
    for name, sources in _TEMPLATE_SOURCES.items():
        value = None
        for src in sources:
            value = pack.get(src)
            if value is None and isinstance(features, Mapping):
                value = features.get(src)
            if value is None:
                value = next((r.get("value") for r in reasons if r.get("metric") == src), None)
            if _num(value):
                break
        if _num(value):
            context[name] = f"{value:,.0f}"
    text = get_template(product, key, context)
    if any(token in text for token in _PLACEHOLDERS.values()):
        text = get_template(product, "PENDING", context)   # never show "[FUEL_SPEND]"
    return text


def _template_result(pack: Any, status: str, reason: Optional[str], attempts: int = 0) -> Dict[str, Any]:
    try:
        text = _template_text(pack)
    except Exception:
        text = "Status information is currently unavailable."
    log.warning("explain template status=%s reason=%s attempts=%d", status, reason, attempts)
    return {"explanation": text, "metrics_summary": "", "source": SOURCE_TEMPLATE,
            "claimcheck_status": status, "fallback_reason": reason, "attempts": attempts,
            "sentences": [{"text": text, "fields": [], "check": "TEMPLATE"}]}


# ---- adapters ---------------------------------------------------------------------
def to_contract_explanation(result: Mapping[str, Any]) -> Dict[str, Any]:
    """Shape of contracts.Explanation, which is what Opportunity.explanation and the UI
    claim stamp read. The contract's claimcheck_status is PASS | FALLBACK only, so
    PII_BLOCK and the SECURITY_* statuses are reported there as FALLBACK. The detailed
    status stays in result["claimcheck_status"] and in the audit verdict."""
    sentences = [{"text": s["text"], "fields": list(s.get("fields", [])), "check": s["check"]}
                 for s in result.get("sentences", [])]
    return {"sentences": sentences,
            "source": result["source"],
            "claimcheck_status": "PASS" if result["claimcheck_status"] == STATUS_PASS else "FALLBACK"}


def to_audit_args(result: Mapping[str, Any], customer_key: str, product_id: str) -> Dict[str, Any]:
    """Keyword arguments for greendash.db.audit.append (verdict is constrained there to
    PASS | BLOCKED | FALLBACK | PII_BLOCK; source to llm | template | red_team).

    rules_violated carries the fixed fallback reason code, never rule match text:
    the gateway does not expose which Claim-Check rules fired. customer_key must be
    the pseudonymous key, never a customer_id or name."""
    status = result["claimcheck_status"]
    verdict = status if status in (STATUS_PASS, STATUS_PII_BLOCK) else STATUS_FALLBACK
    reason = result.get("fallback_reason")
    return {"customer_key": customer_key, "product_id": product_id, "verdict": verdict,
            "rules_violated": [reason] if reason else [], "source": result["source"]}


# ---- provider -------------------------------------------------------------------
def _lazy_client():
    # Imported on first use so a rejected pack (or a test) never loads the SDK or key.
    from greendash.llm.client import get_client
    return get_client()


def _meter(response: Any, prompt_chars: int) -> None:
    from greendash.llm.gateway import NonRetryableProviderError
    try:
        usage = getattr(response, "usage_metadata", None)
        if usage:
            tracker.add_cost(usage.prompt_token_count, usage.candidates_token_count)
        else:
            tracker.add_cost(prompt_chars / 4, 100)
    except Exception:
        raise NonRetryableProviderError("budget")   # spend cap: no retry, template


class _Recording:
    """Provider wrapper that remembers the last raw reply, so the cited fields of an
    accepted reply can be recovered (the gateway returns sentence text only)."""

    def __init__(self, inner):
        self._inner, self.last = inner, None

    def generate(self, **kwargs):
        self.last = self._inner.generate(**kwargs)
        return self.last


def _build_provider(cfg: Mapping[str, Any]):
    from greendash.llm.providers import GeminiProvider
    return GeminiProvider(_lazy_client, model_id=cfg["model_id"],
                          temperature=cfg["temperature"], on_response=_meter)


# ---- public ---------------------------------------------------------------------
def get_explanation(evidence_pack, customer_key="dummy", canary_token=None, *,
                    provider=None, config=None):
    """Return the explanation result dict (see module docstring). Never raises.

    customer_key is accepted for backward compatibility and is never used or sent.
    canary_token: a valid gateway canary, or None / invalid to use a fresh random one.
    provider / config: injection points for tests; production passes neither.
    """
    try:
        if hasattr(evidence_pack, "model_dump"):      # contracts.Opportunity
            evidence_pack = evidence_pack.model_dump(mode="json")
        try:
            from greendash.llm.gateway import LLMGateway, SOURCE_LLM as GW_LLM
            from greendash.llm.guard import (INPUT_PII, CanaryError, generate_canary,
                                             guard_post, validate_canary)
        except ImportError:
            return _template_result(evidence_pack, STATUS_MODULE_UNAVAILABLE, "MODULE_UNAVAILABLE")

        try:
            cfg = dict(config) if config is not None else load_llm_config()
            with open(PROMPT_PATH, "r", encoding="utf-8") as fh:
                system_prompt = fh.read()
            try:
                canary = validate_canary(canary_token)
            except CanaryError:
                canary = generate_canary()
            recorder = _Recording(provider if provider is not None else _build_provider(cfg))
            gateway = LLMGateway(
                recorder,
                system_prompt=system_prompt, canary=canary,
                max_attempts=int(cfg["retries"]) + 1,
                max_tokens=int(cfg["max_tokens"]), timeout_s=float(cfg["timeout_seconds"]),
            )
        except Exception:
            return _template_result(evidence_pack, STATUS_CONFIG_ERROR, "CONFIG_ERROR")

        result = gateway.explain(evidence_pack)
        if result.source == GW_LLM:
            log.info("explain status=%s attempts=%d", STATUS_PASS, result.attempts)
            cited = [list(c) for _, c in guard_post(recorder.last, canary=canary)]
            if len(cited) != len(result.sentences):
                cited = [[] for _ in result.sentences]
            return {"explanation": " ".join(result.sentences), "metrics_summary": "",
                    "source": SOURCE_LLM, "claimcheck_status": STATUS_PASS,
                    "fallback_reason": None, "attempts": result.attempts,
                    "sentences": [{"text": t, "fields": f, "check": "PASS"}
                                  for t, f in zip(result.sentences, cited)]}
        status = STATUS_PII_BLOCK if result.reason == INPUT_PII else STATUS_FALLBACK
        return _template_result(evidence_pack, status, result.reason, result.attempts)
    except Exception:
        return _template_result(evidence_pack, STATUS_FALLBACK, "INTERNAL_ERROR")


if __name__ == "__main__":
    # Calls the real provider: needs GEMINI_API_KEY. Mock-provider tests live in
    # tests/unit/test_explain_integration.py.
    sample_pack = {
        "customer_id": "C123",
        "recommendation": "GP01",
        "confidence": 0.85,
        "reasons": [
            {"code": "HIGH_FUEL_SPEND", "value": 250}
        ]
    }
    print("Testing explainer...")
    res = get_explanation(sample_pack)
    print("Response:", res)
    print(f"Total Cost So Far: £{tracker.get_total():.6f}")
