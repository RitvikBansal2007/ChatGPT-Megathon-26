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
from typing import Any, Dict, Mapping

from greendash.llm.guard import INPUT_PII, GuardRejection
from security.privacy import LLM_ALLOWED_FIELDS, find_pii, llm_payload

# Fields lifted out of pack["carbon"] into the flat dict.
_CARBON_FIELDS = ("formula", "missing_inputs", "display", "status")


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
    return flat


def minimise(pack: Mapping[str, Any]) -> Dict[str, Any]:
    """Return the allow-listed payload, or raise GuardRejection(INPUT_PII)."""
    flat = flatten_pack(pack)
    candidate = {k: v for k, v in flat.items() if k in LLM_ALLOWED_FIELDS}
    if find_pii(json.dumps(candidate, default=str)):
        raise GuardRejection(INPUT_PII)
    return llm_payload(flat)
