"""Privacy and security helpers for the data lane.

- scrub_text: redact common PII patterns from free text before it is stored or sent anywhere.
- find_pii: detect (not redact) PII, for gates and tests.
- pseudonymise: keyed, deterministic pseudonym for identifiers (key from environment, never in code).
- llm_payload: strict allowlist builder so only non-identifying, task-relevant fields
  can ever reach a language model. Unknown keys are dropped, not passed through.
"""
import hashlib
import hmac
import os
import re

PATTERNS = {
    "EMAIL": re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}"),
    "IBAN": re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b"),
    "CARD": re.compile(r"\b(?:\d[ \-]?){13,19}\b"),
    "SORT_CODE": re.compile(r"\b\d{2}-\d{2}-\d{2}\b"),
    "ACCOUNT_NO": re.compile(r"\b\d{8}\b"),
    "NI_NUMBER": re.compile(r"\b[A-CEGHJ-PR-TW-Z]{2}\s?\d{2}\s?\d{2}\s?\d{2}\s?[A-D]\b", re.I),
    "PHONE": re.compile(r"(?<!\d)(?:\+44|0)\s?\d{3,4}\s?\d{3}\s?\d{3,4}(?!\d)"),
    "POSTCODE": re.compile(r"\b[A-Z]{1,2}\d[A-Z\d]?\s?\d[A-Z]{2}\b"),
}

# Fields that may be shown to a model. Everything else is dropped.
LLM_ALLOWED_FIELDS = frozenset({
    "product_id", "status", "metric_family", "formula", "missing_inputs", "display",
    "age_band", "income_band", "region", "home_owner", "has_car", "fuel_type",
    "epc_band", "roof_suitability", "existing_solar",
    "annual_mileage", "gas_kwh", "paper_statements_12m",
    # Model-side explanation inputs. Only ever filled by greendash.llm.minimise, which keeps
    # reasons to {code, value} pairs and confidence to a number in [0, 1].
    "reasons", "confidence",
})
# Never allowed, even if someone adds them to the allowlist by mistake.
LLM_FORBIDDEN_FIELDS = frozenset({
    "customer_id", "name", "email", "phone", "address", "postcode", "account_number",
    "sort_code", "iban", "card_number", "date_of_birth", "merchant_description",
    "accessibility_paper_need", "balance",
})
assert not (LLM_ALLOWED_FIELDS & LLM_FORBIDDEN_FIELDS)


def _luhn(digits: str) -> bool:
    total, alt = 0, False
    for ch in reversed(digits):
        d = int(ch)
        if alt:
            d = d * 2 - 9 if d * 2 > 9 else d * 2
        total += d
        alt = not alt
    return total % 10 == 0


def find_pii(text: str) -> list:
    hits = []
    for name, pat in PATTERNS.items():
        for m in pat.finditer(text or ""):
            if name == "CARD":
                digits = re.sub(r"\D", "", m.group())
                if not (13 <= len(digits) <= 19 and _luhn(digits)):
                    continue
            hits.append(name)
    return hits


def scrub_text(text: str) -> str:
    out = text or ""
    for name, pat in PATTERNS.items():
        if name == "CARD":
            out = pat.sub(lambda m: "[CARD]" if _luhn(re.sub(r"\D", "", m.group())) else m.group(), out)
        else:
            out = pat.sub(f"[{name}]", out)
    return out


def pseudonymise(value: str, key: bytes = None) -> str:
    """HMAC-SHA256 pseudonym. Key comes from env PSEUDONYM_KEY; no default key exists."""
    key = key or os.environ.get("PSEUDONYM_KEY", "").encode()
    if not key:
        raise RuntimeError("PSEUDONYM_KEY is not set; refusing to pseudonymise without a key")
    return hmac.new(key, value.encode(), hashlib.sha256).hexdigest()[:16]


def age_band(age: int) -> str:
    lo = (int(age) // 10) * 10
    return f"{lo}-{lo + 9}"


def llm_payload(fields: dict) -> dict:
    """Allowlist filter. Drops unknown/forbidden keys and scrubs any string value."""
    out = {}
    for k, v in fields.items():
        if k in LLM_FORBIDDEN_FIELDS or k not in LLM_ALLOWED_FIELDS:
            continue
        out[k] = _clean(v)
    return out


def _clean(v):
    if isinstance(v, str):
        return scrub_text(v)
    if isinstance(v, dict):
        return {k: _clean(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_clean(x) for x in v]
    return v
