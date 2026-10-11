"""Data minimisation for the LLM gateway.

Turns an evidence pack into the small payload a provider is allowed to see.

The allow-list itself lives in security/privacy.py (LLM_ALLOWED_FIELDS /
LLM_FORBIDDEN_FIELDS, applied by llm_payload). This module adds two things the
existing helper does not do:

1. It flattens the pack shape produced today (fields nested under "carbon" and
   "evidence_features") into the flat shape llm_payload expects. Without this,
   llm_payload would drop those nested objects entirely.
2. It rejects PII instead of quietly scrubbing it. llm_payload replaces an email
   with "[EMAIL]" and carries on; here a hit means the pack is wrong, so the
   gateway refuses to call the model at all (fail closed).
"""
import json
import math
import re
from typing import Any, Dict, List, Mapping

from greendash.llm.guard import INPUT_PII, GuardRejection
from security.privacy import LLM_ALLOWED_FIELDS, find_pii, llm_payload

# Fields lifted out of pack["carbon"] into the flat dict.
_CARBON_FIELDS = ("formula", "missing_inputs", "display", "status")
_IMPACT_FIELDS = ("formula", "missing_inputs", "display")

# Explanation inputs from the scoring contract: {"recommendation", "confidence",
# "reasons": [{"code", "value", ...}]}. Only the shapes below ever pass.
_PRODUCT_RE = re.compile(r"^GP0[1-4]$")
_REASON_CODE_RE = re.compile(r"^[A-Z][A-Z0-9_]{1,47}$")
MAX_REASONS = 5   # top reasons are listed first; the rest are dropped


def _is_number(value: Any) -> bool:
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value))


def _clean_reasons(raw: Any) -> List[Dict[str, Any]]:
    """Keep only {"code": UPPER_SNAKE, "value": number}. Extra keys (feature names,
    SHAP values, identifiers) are dropped. A code that looks like PII rejects the
    pack; any other malformed entry is dropped."""
    if not isinstance(raw, (list, tuple)):
        return []
    out: List[Dict[str, Any]] = []
    for item in raw:
        if len(out) >= MAX_REASONS:
            break
        if not isinstance(item, Mapping):
            continue
        code = item.get("code")
        if not isinstance(code, str):
            continue
        if find_pii(code):
            raise GuardRejection(INPUT_PII)
        if not _REASON_CODE_RE.match(code):
            continue
        entry: Dict[str, Any] = {"code": code}
        if _is_number(item.get("value")):
            entry["value"] = item["value"]
        out.append(entry)
    return out


def flatten_pack(pack: Mapping[str, Any]) -> Dict[str, Any]:
    """Flatten the current evidence-pack shape. Flat mappings pass through unchanged."""
    flat: Dict[str, Any] = dict(pack)
    features = pack.get("evidence_features")
    if isinstance(features, Mapping):
        flat.update(features)
    carbon = pack.get("carbon")
    if isinstance(carbon, Mapping):
        for key in _CARBON_FIELDS:
            if key in carbon:
                flat[key] = carbon[key]
    # contracts.Opportunity carries the same facts under "impact". Its "status" is the
    # impact status, not the display status, so it is not lifted over pack["status"].
    impact = pack.get("impact")
    if isinstance(impact, Mapping):
        for key in _IMPACT_FIELDS:
            if impact.get(key) is not None:
                flat[key] = impact[key]
    return flat


def _contract_fields(pack: Mapping[str, Any], flat: Dict[str, Any]) -> None:
    """Map the scoring contract onto the allow-listed flat shape (in place)."""
    if not (isinstance(flat.get("product_id"), str) and _PRODUCT_RE.match(flat["product_id"])):
        for key in ("recommendation", "opportunity_id"):
            rec = pack.get(key)
            if isinstance(rec, str) and _PRODUCT_RE.match(rec):
                flat["product_id"] = rec
                break
    flat.pop("reasons", None)
    flat.pop("confidence", None)
    # "reasons" (flat scoring contract) or "reason_codes" (contracts.Opportunity).
    reasons = _clean_reasons(pack.get("reasons") or pack.get("reason_codes"))
    if reasons:
        flat["reasons"] = reasons
    confidence = pack.get("confidence")
    if isinstance(confidence, Mapping):          # contracts.ConfidenceParts
        confidence = confidence.get("overall")
    if _is_number(confidence) and 0 <= confidence <= 1:
        flat["confidence"] = confidence


def minimise(pack: Mapping[str, Any]) -> Dict[str, Any]:
    """Return the allow-listed payload, or raise GuardRejection(INPUT_PII)."""
    flat = flatten_pack(pack)
    _contract_fields(pack, flat)
    candidate = {k: v for k, v in flat.items() if k in LLM_ALLOWED_FIELDS}
    if find_pii(json.dumps(candidate, default=str)):
        raise GuardRejection(INPUT_PII)
    return llm_payload(flat)
