"""Pre- and post-LLM guards for the LLM gateway.

guard_pre  checks the minimised payload BEFORE anything is sent to a provider.
guard_post checks the provider's raw reply BEFORE any sentence is shown.

Both raise GuardRejection(code) on the first problem. The exception carries only a
short fixed code, never the offending text, so it is safe to log and audit.

What this is and is not: these are deterministic, heuristic filters (character
classes, size caps, regexes, a strict JSON shape). They reduce the chance that
hostile text reaches the model or that unexpected text reaches a customer. They do
not prove a prompt is safe, and a determined attacker may find wording that slips
past the injection patterns. The main defence remains that only allow-listed,
engine-produced fields are ever sent (see minimise.py).
"""
import json
import math
import re
import secrets
import unicodedata
from typing import Any, List, Mapping, Tuple

from greendash.carbon.units import SAFE as DISPLAY_SAFE
from greendash.llm.textnorm import normalise as normalise_text
from security.privacy import find_pii

# Size and shape limits.
MAX_PAYLOAD_CHARS = 4000
MAX_STRING_CHARS = 120
MAX_LIST_ITEMS = 20
MAX_DEPTH = 3
MAX_RAW_OUTPUT_CHARS = 4000
MAX_SENTENCES = 4
MAX_SENTENCE_CHARS = 240
MAX_CITED_FIELDS = 6

# Reason codes (fixed vocabulary; safe to log).
INPUT_PII = "INPUT_PII"
INPUT_INJECTION = "INPUT_INJECTION"
INPUT_UNSAFE = "INPUT_UNSAFE"
OUTPUT_SCHEMA = "OUTPUT_SCHEMA"
OUTPUT_PII = "OUTPUT_PII"
OUTPUT_CANARY = "OUTPUT_CANARY"
OUTPUT_UNSAFE = "OUTPUT_UNSAFE"


# The one output schema. guard_post enforces these exact keys and the gateway prompt
# shows the same example, so the validator and the prompt cannot drift apart.
RESPONSE_KEYS = frozenset({"sentences"})
SENTENCE_KEYS = frozenset({"text", "cited_fields"})
OUTPUT_SCHEMA_EXAMPLE = '{"sentences": [{"text": "...", "cited_fields": ["field.path"]}]}'


class GuardRejection(Exception):
    """A security check failed. Message is the code only, never data."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


# ---- canary ---------------------------------------------------------------
# The canary is a secret token planted in the system prompt. If it ever shows up in
# a reply, the prompt has leaked. A weak canary is worse than none: a one-letter
# canary matches almost every reply (blocking all output) and protects nothing.
#
# A canary is measured two ways, and must pass both:
#   - raw length: len(canary) in Unicode code points, as supplied;
#   - effective length: length of its comparison form (normalised, letters and
#     digits only: see canary_form), which is the form actually matched against replies.
MIN_CANARY_CHARS = 16
MIN_CANARY_DISTINCT = 6   # distinct characters in the comparison form

CANARY_MISSING = "CANARY_MISSING"
CANARY_TOO_SHORT = "CANARY_TOO_SHORT"
CANARY_INVALID = "CANARY_INVALID"


class CanaryError(ValueError):
    """The canary configuration is unusable. Message is a fixed code, never the canary."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def canary_form(text: str) -> str:
    """The form in which canaries and replies are compared.

    Normalised (see textnorm.py), then reduced to letters and digits only, so that
    changing the separators in a leaked canary ("-" to "_" or a space, say) cannot
    hide it. Letters from any script are kept; punctuation and whitespace are not.
    """
    return re.sub(r"[\W_]+", "", normalise_text(text))


def validate_canary(canary: Any) -> str:
    """Return the canary unchanged if it is usable, otherwise raise CanaryError.

    Never repairs, pads, trims or replaces a bad value.
    """
    if canary is None:
        raise CanaryError(CANARY_MISSING)
    if not isinstance(canary, str):
        raise CanaryError(CANARY_INVALID)
    if not canary.strip():
        raise CanaryError(CANARY_MISSING)
    if any(ch.isspace() for ch in canary) or _has_hidden_chars(canary):
        raise CanaryError(CANARY_INVALID)
    if len(canary) < MIN_CANARY_CHARS:
        raise CanaryError(CANARY_TOO_SHORT)
    form = canary_form(canary)
    if len(form) < MIN_CANARY_CHARS:
        raise CanaryError(CANARY_TOO_SHORT)
    if len(set(form)) < MIN_CANARY_DISTINCT:
        raise CanaryError(CANARY_INVALID)
    return canary


def generate_canary() -> str:
    """A fresh random canary (128 bits). Call this explicitly; nothing does it silently."""
    for _ in range(8):
        candidate = "CANARY-" + secrets.token_hex(16)
        try:
            return validate_canary(candidate)
        except CanaryError:
            continue
    raise CanaryError(CANARY_INVALID)  # unreachable in practice


# A string value may only use plain letters, digits and light punctuation. This
# excludes quotes, angle brackets, braces, backticks and newlines, so a value cannot
# break out of the <evidence_pack> delimiter or the JSON around it.
_VALUE_RE = re.compile(
    r"^[A-Za-z0-9 _.,:()/%\u00a3\u2013\-]{1," + str(MAX_STRING_CHARS) + r"}$"
)
_KEY_RE = re.compile(r"^[a-z_][a-z_0-9]{0,47}$")
_FIELD_RE = re.compile(r"^[a-z_][a-z_0-9]{0,47}(\.[a-z_0-9]{1,48}){0,3}$")

# Wording that tries to give the model instructions. Applied to normalised text
# (NFKC, lower case, whitespace and underscores collapsed to single spaces).
_INJECTION = [re.compile(p) for p in (
    r"\b(ignore|disregard|forget|override|bypass)\b.{0,30}"
    r"\b(rules?|instructions?|prompts?|polic(y|ies)|guidelines?|above|previous)\b",
    r"\b(system|developer) (prompt|message|instructions?)\b",
    r"\b(reveal|show|print|repeat|output|leak)\b.{0,20}"
    r"\b(prompt|instructions?|rules?|canary|secret|keys?)\b",
    r"\byou are now\b",
    r"\bact as\b",
    r"\bpretend\b",
    r"\bjailbreak\b",
    r"\bdeveloper mode\b",
    r"\bnew instructions?\b",
    r"\b(system|assistant|user|human) ?:",
    r"evidence pack ?>",
)]


def _normalise(text: str) -> str:
    # Shared security normalisation (NFKC, confusable folding, case folding, no
    # combining or invisible marks), then whitespace and underscores collapsed.
    return re.sub(r"[\s_]+", " ", normalise_text(text))


def _has_hidden_chars(text: str) -> bool:
    # Cc = control characters, Cf = invisible format characters (zero-width, BOM, bidi).
    return any(unicodedata.category(c) in ("Cc", "Cf") for c in text)


def _check_string(text: str) -> None:
    if _has_hidden_chars(text) or not _VALUE_RE.match(text):
        raise GuardRejection(INPUT_UNSAFE)
    flat = _normalise(text)
    if any(p.search(flat) for p in _INJECTION):
        raise GuardRejection(INPUT_INJECTION)


def _walk(value: Any, depth: int, in_display: bool = False) -> None:
    if depth > MAX_DEPTH:
        raise GuardRejection(INPUT_UNSAFE)
    if isinstance(value, bool) or value is None:
        return
    if isinstance(value, int):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise GuardRejection(INPUT_UNSAFE)
        return
    if isinstance(value, str):
        _check_string(value)
        if in_display and not DISPLAY_SAFE.match(value):
            raise GuardRejection(INPUT_UNSAFE)
        return
    if isinstance(value, (list, tuple)):
        if len(value) > MAX_LIST_ITEMS:
            raise GuardRejection(INPUT_UNSAFE)
        for item in value:
            _walk(item, depth + 1, in_display)
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str) or not _KEY_RE.match(key):
                raise GuardRejection(INPUT_UNSAFE)
            _walk(item, depth + 1, in_display or key == "display")
        return
    raise GuardRejection(INPUT_UNSAFE)  # any other type (objects, bytes, sets, ...)


def guard_pre(payload: Mapping[str, Any]) -> None:
    """Reject the payload (raise GuardRejection) unless it is safe to send."""
    _walk(payload, 0)
    try:
        blob = json.dumps(payload, sort_keys=True)
    except (TypeError, ValueError):
        raise GuardRejection(INPUT_UNSAFE)
    if len(blob) > MAX_PAYLOAD_CHARS:
        raise GuardRejection(INPUT_UNSAFE)
    if find_pii(blob):
        raise GuardRejection(INPUT_PII)


def guard_post(raw: Any, *, canary: str) -> List[Tuple[str, Tuple[str, ...]]]:
    """Validate a provider reply and return [(sentence, cited_fields), ...].

    The reply must be exactly: {"sentences": [{"text": str, "cited_fields": [str]}]}
    with no other keys, within the size limits, free of PII, URLs, markup and the
    canary token.
    """
    validate_canary(canary)   # raises CanaryError; checking is never silently skipped
    if not isinstance(raw, str) or len(raw) > MAX_RAW_OUTPUT_CHARS:
        raise GuardRejection(OUTPUT_SCHEMA)
    # Compare canary and text in the same normalised form.
    needle = canary_form(canary)
    if needle in canary_form(raw):
        raise GuardRejection(OUTPUT_CANARY)

    try:
        data = json.loads(raw)
    except (ValueError, RecursionError):
        raise GuardRejection(OUTPUT_SCHEMA)
    if not isinstance(data, dict) or set(data) != RESPONSE_KEYS:
        raise GuardRejection(OUTPUT_SCHEMA)
    items = data["sentences"]
    if not isinstance(items, list) or not 1 <= len(items) <= MAX_SENTENCES:
        raise GuardRejection(OUTPUT_SCHEMA)

    result: List[Tuple[str, Tuple[str, ...]]] = []
    for item in items:
        if not isinstance(item, dict) or set(item) != SENTENCE_KEYS:
            raise GuardRejection(OUTPUT_SCHEMA)
        text, cited = item["text"], item["cited_fields"]
        if not isinstance(text, str) or not 1 <= len(text.strip()) <= MAX_SENTENCE_CHARS:
            raise GuardRejection(OUTPUT_SCHEMA)
        if (not isinstance(cited, list) or len(cited) > MAX_CITED_FIELDS
                or not all(isinstance(c, str) and _FIELD_RE.match(c) for c in cited)):
            raise GuardRejection(OUTPUT_SCHEMA)
        if _has_hidden_chars(text) or re.search(r"[<>{}`]|https?:|www\.|\]\(", text, re.I):
            raise GuardRejection(OUTPUT_UNSAFE)
        # Re-check the decoded text: JSON escapes can hide a canary from the raw scan.
        if needle in canary_form(text):
            raise GuardRejection(OUTPUT_CANARY)
        if find_pii(text):
            raise GuardRejection(OUTPUT_PII)
        result.append((text.strip(), tuple(cited)))
    return result
