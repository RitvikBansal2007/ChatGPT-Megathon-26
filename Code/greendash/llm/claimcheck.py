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

Not implemented yet: VERDICT, METRIC, PRODUCT, IMPLIED.
"""
import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, Iterable, List, Sequence

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
    """Map normalised value -> first raw text, for every number in text."""
    found: Dict[str, str] = {}
    for m in _NUMBER.finditer(text or ""):
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
    for m in _FIELD_PATH.finditer(sentence or ""):
        path = m.group(1)
        # Treat as a field reference only if it starts with a known root or has an
        # underscore, so abbreviations such as "e.g." are not mistaken for fields.
        if path.split(".")[0] in roots or "_" in path:
            flag(path, "field named in the text is not in the evidence pack")
    return out


def _phrase_pattern(phrase: str) -> "re.Pattern[str]":
    tokens = [re.escape(t) for t in re.split(r"[-\s]+", phrase.strip().lower()) if t]
    return re.compile(r"\b" + r"[-‐-―\s]*".join(tokens) + r"\b", re.IGNORECASE)


def _check_banned(sentence: str, banned_phrases: Sequence[str]) -> List[Violation]:
    hits = []
    for phrase in banned_phrases:
        for m in _phrase_pattern(phrase).finditer(sentence or ""):
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
