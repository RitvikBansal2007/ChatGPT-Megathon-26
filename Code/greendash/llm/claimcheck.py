"""Claim-Check, first slice: the NUM, FIELD and BAN rules.

Claim-Check is the output firewall for the explainer. It reads one sentence the LLM
wrote and compares it with facts the engines already produced. It is deterministic
(regexes and set lookups) and never asks a model whether a sentence is acceptable.

- NUM:   every number in the sentence must appear in the allow-list built from the
         engine's own display strings. Numbers are normalised first, so "1,400",
         "1400" and "1.4 t" all mean the same quantity.
- FIELD: every field the sentence cites (explicitly, or as a dotted path such as
         impact.hidden_field in the text) must exist in the evidence pack.
- BAN:   no phrase from the banned list (credit-decision wording, certainty claims,
         vague green claims) may appear.

All three rules compare against a normalised form of the sentence (textnorm.py:
NFKC, case folding, a small table of Cyrillic/Greek lookalike letters, no combining
or invisible marks). The sentence itself is never changed or returned; the
Violation.text field shows the matched text in that normalised form.

METRIC and VERDICT need the pack and run in check() (see _pack_rules).
Not implemented yet: PRODUCT, IMPLIED.
"""
import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, Iterable, List, Sequence

from greendash.llm.textnorm import normalise

# Rule IDs, in the order violations are reported.
NUM, FIELD, BAN = "NUM", "FIELD", "BAN"

# Phrases the explainer may never show. Sources: the research note ("guaranteed",
# "approved", "will save") and the banned-phrase reasons in eval/llm_eval/adversarial.yaml.
# Matching is case-insensitive and tolerant of hyphen/space variants, so
# "pre-approved", "Pre approved" and "preapproved" are the same phrase.
DEFAULT_BANNED_PHRASES = (
    "guaranteed",
    "pre-approved",
    "approved",
    "will save",
    "you qualify",
    "eco-friendly",
    "carbon neutral",
)


@dataclass(frozen=True)
class Violation:
    rule: str    # NUM, FIELD or BAN
    text: str    # the offending text as written in the sentence
    detail: str  # short plain-language reason, safe to show in an audit row


# A number: "4,000", "36", "0.35", optionally followed by a tonne unit.
# The lookbehind skips digits inside identifiers ("CO2e", "GP01", "reason_codes.0").
_NUMBER = re.compile(
    r"(?<![\w.])(\d{1,3}(?:,\d{3})+|\d+)(\.\d+)?(?:\s*(tonnes?|tons?|t)\b)?",
    re.IGNORECASE,
)

# A dotted field path such as impact.hidden_field or reason_codes.0
_FIELD_PATH = re.compile(r"(?<![\w.])([a-z_][a-z_0-9]*(?:\.[a-z_0-9]+)+)(?!\w)")


def _numbers_in(text: str) -> Dict[str, str]:
    """Map normalised value -> first matched text, for every number in text.

    Matching runs on the normalised form of the text (see textnorm.py), so fullwidth
    digits and commas are read as ordinary ones. The caller's text is not changed.
    """
    found: Dict[str, str] = {}
    for m in _NUMBER.finditer(normalise(text or "")):
        whole, frac, unit = m.group(1), m.group(2), m.group(3)
        value = Decimal(whole.replace(",", "") + (frac or ""))
        if unit:
            value *= 1000  # tonnes -> kg, so "1.4 t" == "1,400 kg"
        key = format(value.normalize(), "f")
        found.setdefault(key, m.group(0).strip())
    return found


def _check_numbers(sentence: str, allowed_numbers: Iterable[str]) -> List[Violation]:
    allowed = set()
    for entry in allowed_numbers:
        allowed.update(_numbers_in(str(entry)))
    return [
        Violation(NUM, raw, "number not in the engine's allowed figures")
        for key, raw in _numbers_in(sentence).items()
        if key not in allowed
    ]


def _check_fields(sentence: str, allowed_fields: Iterable[str],
                  cited_fields: Iterable[str]) -> List[Violation]:
    allowed = set(allowed_fields)
    roots = {f.split(".")[0] for f in allowed}
    out: List[Violation] = []
    seen = set()

    def flag(field: str, detail: str) -> None:
        if field not in allowed and field not in seen:
            seen.add(field)
            out.append(Violation(FIELD, field, detail))

    for field in cited_fields:
        flag(field, "cited field is not in the evidence pack")
    for m in _FIELD_PATH.finditer(normalise(sentence or "")):
        path = m.group(1)
        # Treat as a field reference only if it starts with a known root or has an
        # underscore, so abbreviations such as "e.g." are not mistaken for fields.
        if path.split(".")[0] in roots or "_" in path:
            flag(path, "field named in the text is not in the evidence pack")
    return out


# Separator between the words of a phrase: hyphens (ASCII and U+2010..U+2015) or spaces.
_SEPARATOR = "[-" + chr(0x2010) + "-" + chr(0x2015) + r"\s]*"


def _phrase_pattern(phrase: str) -> "re.Pattern[str]":
    # The phrase goes through the same normalisation as the sentence, so a banned
    # phrase written with lookalike letters in the list still matches.
    tokens = [re.escape(t) for t in re.split(r"[-\s]+", normalise(phrase.strip())) if t]
    return re.compile(r"\b" + _SEPARATOR.join(tokens) + r"\b", re.IGNORECASE)


def _check_banned(sentence: str, banned_phrases: Sequence[str]) -> List[Violation]:
    hits = []
    normalised = normalise(sentence or "")
    for phrase in banned_phrases:
        for m in _phrase_pattern(phrase).finditer(normalised):
            hits.append((m.start(), m.end(), m.group(0), phrase))
    # Longest match wins, and a span is reported once: "pre-approved" is one hit,
    # not two (it would otherwise also match "approved").
    hits.sort(key=lambda h: (h[0], -(h[1] - h[0])))
    out: List[Violation] = []
    last_end = -1
    for start, end, text, phrase in hits:
        if start >= last_end:
            out.append(Violation(BAN, text, f"banned phrase: {phrase}"))
            last_end = end
    return out


def check_sentence(
    sentence: str,
    *,
    allowed_numbers: Iterable[str],
    allowed_fields: Iterable[str],
    cited_fields: Iterable[str] = (),
    banned_phrases: Sequence[str] = DEFAULT_BANNED_PHRASES,
) -> List[Violation]:
    """Return every NUM, FIELD and BAN violation in one sentence (empty list = clean).

    allowed_numbers: engine display strings and values, e.g. "1,420 kg CO2e".
    allowed_fields:  field paths that exist in the evidence pack, e.g. "impact.display.central".
    cited_fields:    fields the model said it used (from its JSON output), if any.
    """
    return (
        _check_numbers(sentence, allowed_numbers)
        + _check_fields(sentence, allowed_fields, cited_fields)
        + _check_banned(sentence, banned_phrases)
    )

# Rules that need the pack itself, not only its numbers and fields.
_CARBON_WORDS = re.compile(r"\b(co2e?|carbon|emissions?|footprint|kg|tonnes?)\b", re.IGNORECASE)
_RECOMMENDING = re.compile(r"\b(recommend(?:ed|s)?|worth exploring|you should|great fit|ideal for you|go ahead)\b",
                           re.IGNORECASE)


def _pack_rules(text: str, pack: dict) -> list:
    """METRIC: paperless is reported in sheets, never as carbon.
    VERDICT: nothing may be recommended when the status is RULED_OUT or REVIEW."""
    out = []
    norm = normalise(text)
    if str(pack.get("opportunity_id") or pack.get("product_id")) == "GP04":
        hit = _CARBON_WORDS.search(norm)
        if hit:
            out.append({"rule": "METRIC", "span": hit.group(0), "detail": "paperless is reported in sheets, not as carbon"})
    if str(pack.get("status")) in ("RULED_OUT", "REVIEW"):
        hit = _RECOMMENDING.search(norm)
        if hit:
            out.append({"rule": "VERDICT", "span": hit.group(0), "detail": "no recommendation is allowed for this status"})
    return out


def check(pack, sentences):
    """Claim-Check a list of sentences against one evidence pack.

    The shape api/routers/claimcheck.py calls and fixtures/claimcheck_response.json
    documents:
        pack      contracts.Opportunity (or its dict), checked after minimisation
        sentences [{"text": str, "fields": [str]}]
        returns   {"verdict": PASS | BLOCKED | PII_BLOCK, "sentences": [{"text",
                   "status", "violations": [{"rule","span","detail"}]}],
                   "fallback_text": str | None}
    The verdict vocabulary is the one db.audit accepts. Never raises for bad input:
    a pack that cannot be minimised blocks every sentence.
    """
    from greendash.llm.gateway import _collect_facts      # lazy: gateway imports this module
    from greendash.llm.guard import INPUT_PII, GuardRejection, guard_pre
    from greendash.llm.minimise import minimise
    from greendash.llm.explain import _template_text

    plain = pack.model_dump(mode="json") if hasattr(pack, "model_dump") else pack
    items = [s if isinstance(s, dict) else {"text": str(s), "fields": []} for s in sentences]
    try:
        payload = minimise(plain)
        guard_pre(payload)
    except GuardRejection as err:
        verdict = "PII_BLOCK" if err.code == INPUT_PII else "BLOCKED"
        return {"verdict": verdict,
                "sentences": [{"text": str(i.get("text", "")), "status": "BLOCKED", "violations": []}
                              for i in items],
                "fallback_text": _template_text(plain)}
    except Exception:
        return {"verdict": "BLOCKED",
                "sentences": [{"text": str(i.get("text", "")), "status": "BLOCKED", "violations": []}
                              for i in items],
                "fallback_text": _template_text(plain)}

    numbers, fields = set(), set()
    _collect_facts(payload, "", numbers, fields)
    out, blocked = [], False
    for item in items:
        text = str(item.get("text", ""))
        cited = tuple(f for f in item.get("fields", []) if isinstance(f, str))
        try:
            found = check_sentence(text, allowed_numbers=numbers, allowed_fields=fields,
                                   cited_fields=cited)
            violations = [{"rule": v.rule, "span": v.text, "detail": v.detail} for v in found]
            violations += _pack_rules(text, plain)
        except Exception:
            violations = [{"rule": "ERROR", "span": "", "detail": "claim check could not run"}]
        blocked = blocked or bool(violations)
        out.append({"text": text, "status": "BLOCKED" if violations else "PASS",
                    "violations": violations})
    return {"verdict": "BLOCKED" if blocked else "PASS", "sentences": out,
            "fallback_text": _template_text(plain) if blocked else None}
