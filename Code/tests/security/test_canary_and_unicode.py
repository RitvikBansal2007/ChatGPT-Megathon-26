"""Regression tests: canary validation and Unicode evasion resistance.

Non-ASCII characters are always built with chr(), never typed, so lookalike letters
cannot hide in this file.
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from greendash.llm import guard, textnorm
from greendash.llm.claimcheck import DEFAULT_BANNED_PHRASES, check_sentence
from greendash.llm.gateway import LLMGateway, SOURCE_FALLBACK, SOURCE_LLM
from greendash.llm.guard import (
    CANARY_INVALID, CANARY_MISSING, CANARY_TOO_SHORT, MIN_CANARY_CHARS, CanaryError,
    generate_canary, guard_post, validate_canary,
)

CANARY = "CANARY-UNICODE-0123456789"

PACK = {
    "product_id": "GP01", "metric_family": "co2e",
    "carbon": {"status": "ESTIMATED", "formula": "annual_miles x petrol factor", "missing_inputs": [],
               "display": {"central": "2,330 kg CO2e", "range": "1,980 to 2,679 kg CO2e per year"}},
    "evidence_features": {"annual_mileage": 11500, "fuel_type": "petrol", "has_car": True},
}
GOOD = json.dumps({"sentences": [{
    "text": "An electric car could cut about 2,330 kg CO2e a year, which is an estimate.",
    "cited_fields": ["display.central"]}]})


class CountingProvider:
    def __init__(self, *replies):
        self.replies = list(replies)
        self.calls = 0

    def generate(self, **kw):
        self.calls += 1
        return self.replies.pop(0) if self.replies else GOOD


def say(text):
    return json.dumps({"sentences": [{"text": text, "cited_fields": []}]})


def code_of(fn, *a, **kw):
    with pytest.raises(CanaryError) as info:
        fn(*a, **kw)
    return info.value.code


def rules(sentence, **kw):
    kw.setdefault("allowed_numbers", ["2,330 kg CO2e"])
    kw.setdefault("allowed_fields", ["display.central"])
    return [v.rule for v in check_sentence(sentence, **kw)]


# Test-local lookalike table (independent of the module's table, so a mistake there
# is not mirrored here): Latin letter -> Cyrillic letter that looks identical.
LATIN_TO_CYR = {"a": 0x430, "e": 0x435, "o": 0x43E, "p": 0x440, "c": 0x441, "y": 0x443,
                "x": 0x445, "i": 0x456, "s": 0x455, "h": 0x4BB, "d": 0x501, "k": 0x43A,
                "j": 0x458, "q": 0x51B, "w": 0x51D}
LATIN_UP_TO_CYR = {"A": 0x410, "B": 0x412, "E": 0x415, "K": 0x41A, "M": 0x41C, "H": 0x41D,
                   "O": 0x41E, "P": 0x420, "C": 0x421, "T": 0x422, "X": 0x425, "Y": 0x423}


def cyrillic(text, only_first=False):
    out, done = [], False
    for ch in text:
        cp = LATIN_TO_CYR.get(ch) or LATIN_UP_TO_CYR.get(ch)
        if cp and not (only_first and done):
            out.append(chr(cp))
            done = True
        else:
            out.append(ch)
    return "".join(out)


def fullwidth(text):
    return "".join(chr(0x3000) if c == " " else chr(ord(c) + 0xFEE0) if "!" <= c <= "~" else c
                   for c in text)


# ======================= canary validation =================================

@pytest.mark.parametrize("length,expected", [
    (1, CANARY_TOO_SHORT), (8, CANARY_TOO_SHORT), (MIN_CANARY_CHARS - 1, CANARY_TOO_SHORT),
    (MIN_CANARY_CHARS, None), (MIN_CANARY_CHARS + 1, None), (64, None),
])
def test_canary_length_boundary(length, expected):
    value = ("abcdefghijklmnopqrstuvwxyz0123456789" * 3)[:length]
    assert len(value) == length
    if expected is None:
        assert validate_canary(value) == value          # returned unchanged
    else:
        assert code_of(validate_canary, value) == expected


def test_minimum_is_sixteen():
    assert MIN_CANARY_CHARS == 16


@pytest.mark.parametrize("value", [None, "", "   ", "\t\n"])
def test_missing_or_blank_canary_is_rejected(value):
    assert code_of(validate_canary, value) == CANARY_MISSING


@pytest.mark.parametrize("value", [
    12345678901234567, b"abcdefghijklmnopqrst", ["abcdefghijklmnopqrst"],
    " abcdefghijklmnopqrst", "abcdefghijklmnopqrst ", "abcdefghijkl mnopqrst",
    "abcdefghijkl\x00mnopqrst", "abcdefghijkl" + chr(0x200B) + "mnopqrst",
    "a" * 20, "ab" * 10, "abcde" * 4,                  # fewer than 6 distinct characters
])
def test_invalid_canary_is_rejected(value):
    assert code_of(validate_canary, value) == CANARY_INVALID


def test_effective_length_counts_not_just_raw_length():
    # 21 raw characters, but only 11 once separators are ignored in matching.
    assert code_of(validate_canary, "a_b_c_d_e_f_g_h_i_j_k") == CANARY_TOO_SHORT
    assert code_of(validate_canary, "a-b-c-d-e-f-g-h-i-j-k-l") == CANARY_TOO_SHORT
    # 17 raw, exactly 16 effective: allowed.
    assert validate_canary("abcdefgh_ijklmnop") == "abcdefgh_ijklmnop"


def test_error_never_contains_the_canary():
    weak = "short-secret-1"
    err = None
    try:
        validate_canary(weak)
    except CanaryError as e:
        err = e
    assert err is not None
    assert weak not in str(err) and weak not in repr(err) and str(err) == err.code


def test_generate_canary_is_valid_random_and_explicit():
    a, b = generate_canary(), generate_canary()
    assert a != b and validate_canary(a) == a and len(a) >= 32


# ---- gateway boundary: nothing is sent when the canary is bad --------------

@pytest.mark.parametrize("bad,expected", [
    ("a", CANARY_TOO_SHORT), ("ab", CANARY_TOO_SHORT), ("x" * 15, CANARY_TOO_SHORT),
    ("", CANARY_MISSING), (None, CANARY_MISSING), ("a" * 20, CANARY_INVALID),
])
def test_bad_canary_stops_gateway_before_any_provider_call(bad, expected):
    provider = CountingProvider(GOOD)
    assert code_of(LLMGateway, provider, canary=bad) == expected
    assert provider.calls == 0


def test_omitted_canary_is_an_error_not_a_generated_replacement():
    provider = CountingProvider(GOOD)
    assert code_of(LLMGateway, provider) == CANARY_MISSING
    assert provider.calls == 0


def test_valid_canary_works_exactly_as_before():
    provider = CountingProvider(GOOD)
    result = LLMGateway(provider, canary=CANARY).explain(PACK)
    assert result.source == SOURCE_LLM and result.reason is None and result.attempts == 1
    assert result.sentences[0].startswith("An electric car")


def test_explicitly_generated_canary_is_accepted():
    result = LLMGateway(CountingProvider(GOOD), canary=generate_canary()).explain(PACK)
    assert result.source == SOURCE_LLM


def test_guard_post_no_longer_skips_the_check_for_an_empty_canary():
    assert code_of(guard_post, GOOD, canary="") == CANARY_MISSING
    assert code_of(guard_post, GOOD, canary="short") == CANARY_TOO_SHORT


# ---- leak detection survives the same evasions ------------------------------

def test_canary_leak_is_detected_in_fullwidth_mixed_case_and_lookalike_form():
    variants = [
        fullwidth(CANARY),
        CANARY.lower(),
        CANARY.swapcase(),
        cyrillic(CANARY),
        CANARY.replace("-", "_"),
        CANARY.replace("-", " "),
        CANARY.replace("-", "."),
        CANARY.replace("-", ""),
    ]
    for leaked in variants:
        with pytest.raises(guard.GuardRejection) as info:
            guard_post(say(f"Reference {leaked}."), canary=CANARY)
        assert info.value.code == guard.OUTPUT_CANARY, leaked.encode("ascii", "backslashreplace")


def test_unrelated_text_does_not_trigger_the_canary_check():
    assert guard_post(say("An ordinary sentence about 2,330 kg CO2e."), canary=CANARY)


# ======================= Unicode evasion: banned phrases ===================

@pytest.mark.parametrize("phrase", DEFAULT_BANNED_PHRASES)
def test_plain_banned_phrases_are_still_blocked(phrase):
    assert rules(f"This is {phrase} for you.") == ["BAN"]


@pytest.mark.parametrize("phrase", DEFAULT_BANNED_PHRASES)
def test_cyrillic_lookalike_variants_are_blocked(phrase):
    full, first = cyrillic(phrase), cyrillic(phrase, only_first=True)
    assert full != phrase and first != phrase            # the substitution really happened
    assert full.isascii() is False and first.isascii() is False
    assert rules(f"This is {full} for you.") == ["BAN"]
    assert rules(f"This is {first} for you.") == ["BAN"]


@pytest.mark.parametrize("phrase", DEFAULT_BANNED_PHRASES)
def test_fullwidth_and_mixed_case_variants_are_blocked(phrase):
    assert rules(f"This is {fullwidth(phrase)} for you.") == ["BAN"]
    assert rules(f"This is {phrase.upper()} for you.") == ["BAN"]
    assert rules(f"This is {phrase.title()} for you.") == ["BAN"]
    assert rules(f"This is {fullwidth(phrase.upper())} for you.") == ["BAN"]


def test_capital_cyrillic_lookalikes_are_blocked():
    # ECO-FRIENDLY with Cyrillic capital E, C, O
    word = chr(0x415) + chr(0x421) + chr(0x41E) + "-FRIENDLY"
    assert rules(f"A {word} choice.") == ["BAN"]


def test_greek_lookalike_is_blocked():
    omicron = chr(0x3BF)
    assert rules(f"Your loan is appr{omicron}ved.") == ["BAN"]


def test_zero_width_and_combining_marks_do_not_hide_a_phrase():
    assert rules("Your loan is appro" + chr(0x200B) + "ved.") == ["BAN"]
    assert rules("Your loan is approve" + chr(0x301) + "d.") == ["BAN"]
    assert rules("Your loan is app" + chr(0xAD) + "roved.") == ["BAN"]    # soft hyphen


def test_variants_in_the_banned_list_itself_are_normalised():
    assert rules("This is cheap.", banned_phrases=[cyrillic("cheap")]) == ["BAN"]


# ---- numbers and fields use the same normalisation --------------------------

def test_fullwidth_numbers_are_read_as_numbers():
    assert rules("About " + fullwidth("2,330") + " kg CO2e.") == []        # equals the allowed figure
    assert rules("About " + fullwidth("4,000") + " kg CO2e.") == ["NUM"]   # invented figure


def test_mixed_case_field_path_is_still_checked():
    assert rules("See Display.Central.", allowed_fields=["display.central"]) == []
    assert rules("See Impact.Hidden_Field.", allowed_fields=["display.central"]) == ["FIELD"]


# ======================= benign Unicode stays allowed ======================

@pytest.mark.parametrize("sentence", [
    "A caf" + chr(0xE9) + " r" + chr(0xE9) + "sum" + chr(0xE9) + " na" + chr(0xEF) + "ve plan.",
    "Cost about " + chr(0xA3) + "2,330 a year, roughly 2,330 kg CO2e.",
    "Well done " + chr(0x2014) + " this is a good start " + chr(0x2713) + ".",
    # Real Russian: "Hello, this is an estimate" (no banned phrase)
    "".join(map(chr, [0x41F, 0x440, 0x438, 0x432, 0x435, 0x442])) + ", "
    + "".join(map(chr, [0x44D, 0x442, 0x43E])) + " "
    + "".join(map(chr, [0x43E, 0x446, 0x435, 0x43D, 0x43A, 0x430])) + ".",
    # Real Greek: "Good morning world"
    "".join(map(chr, [0x39A, 0x3B1, 0x3BB, 0x3B7, 0x3BC, 0x3AD, 0x3C1, 0x3B1])) + " "
    + "".join(map(chr, [0x3BA, 0x3CC, 0x3C3, 0x3BC, 0x3B5])) + ".",
    "".join(map(chr, [0x3053, 0x308C, 0x306F, 0x898B, 0x7A4D, 0x3082, 0x308A, 0x3067, 0x3059])) + ".",
    "An unapproved change and a disapproved request are not offers.",
    "It is a guarantee-free estimate.",
])
def test_benign_unicode_text_is_not_blocked(sentence):
    assert rules(sentence) == []


# ======================= display text is preserved =========================

def test_normalisation_does_not_change_user_facing_text():
    original = "A caf" + chr(0xE9) + " style estimate: about 2,330 kg CO2e a year."
    before = original
    assert rules(original) == []
    assert original == before                                   # strings are immutable, but be explicit
    result = LLMGateway(CountingProvider(say(original)), canary=CANARY).explain(PACK)
    assert result.source == SOURCE_LLM
    assert result.sentences == (original,)                      # byte-for-byte, accents intact


def test_lookalike_in_reply_triggers_fallback_through_the_gateway():
    sneaky = "Your loan is " + cyrillic("approved") + "."
    provider = CountingProvider(say(sneaky), say(sneaky))
    result = LLMGateway(provider, canary=CANARY).explain(PACK)
    assert result.source == SOURCE_FALLBACK and result.reason == "CLAIMCHECK_FAIL"
    assert provider.calls == 2
    assert all(sneaky not in s for s in result.sentences)


# ======================= the mapping itself ================================

def test_mapping_is_small_explicit_and_only_targets_ascii_letters():
    table = textnorm.CONFUSABLES
    assert 0 < len(table) <= 80
    assert all(cp > 127 for cp in table)                         # ASCII is never altered
    assert all(len(v) == 1 and v.isascii() and v.isalpha() for v in table.values())


def test_unmapped_letters_are_not_transliterated():
    word = "".join(map(chr, [0x43F, 0x440, 0x438, 0x432, 0x435, 0x442]))   # Russian "privet"
    out = textnorm.normalise(word)
    assert any(ord(c) > 127 for c in out)                        # i, v, t etc. remain Cyrillic
    assert out != "privet"


def test_normalise_is_idempotent_and_handles_empty():
    for text in ("", "Approved", fullwidth("approved"), cyrillic("approved")):
        once = textnorm.normalise(text)
        assert textnorm.normalise(once) == once
    assert textnorm.normalise("") == "" and textnorm.normalise(None) == ""


# ======================= canary lifecycle (gateway side) ===================
# These lock the contract the explainer relies on: ONE canary per gateway, the same
# value is placed in the prompt and used for leak detection, it is stable across
# retries, and it is never returned or logged.

import logging
import re

_HEX_CANARY = re.compile(r"CANARY-[0-9a-f]{32}")


class RecordingProvider:
    """Records each system prompt, and can reply with the canary found in it."""

    def __init__(self, leak=False):
        self.leak = leak
        self.systems = []

    def generate(self, *, system, user, max_tokens, timeout_s):
        self.systems.append(system)
        if self.leak:
            return say("Reference " + _HEX_CANARY.search(system).group(0) + ".")
        return GOOD


def test_prompt_canary_is_the_one_used_for_leak_detection():
    provider = RecordingProvider(leak=True)
    result = LLMGateway(provider, canary=generate_canary()).explain(PACK)
    assert result.source == SOURCE_FALLBACK and result.reason == guard.OUTPUT_CANARY
    assert len(provider.systems) == 2                      # retried once, then fell back


def test_canary_is_stable_across_retries_and_requests():
    provider = RecordingProvider(leak=True)
    gateway = LLMGateway(provider, canary=generate_canary())
    gateway.explain(PACK)
    gateway.explain(PACK)
    found = [_HEX_CANARY.search(s).group(0) for s in provider.systems]
    assert len(found) == 4 and len(set(found)) == 1        # 2 attempts x 2 requests, one value


def test_each_gateway_has_its_own_canary():
    a, b = RecordingProvider(), RecordingProvider()
    LLMGateway(a, canary=generate_canary()).explain(PACK)
    LLMGateway(b, canary=generate_canary()).explain(PACK)
    assert _HEX_CANARY.search(a.systems[0]).group(0) != _HEX_CANARY.search(b.systems[0]).group(0)


def test_canary_is_never_in_the_result_or_the_logs(caplog):
    caplog.set_level(logging.DEBUG)
    provider = RecordingProvider(leak=True)
    result = LLMGateway(provider, canary=generate_canary()).explain(PACK)
    canary = _HEX_CANARY.search(provider.systems[0]).group(0)
    shown = repr(result) + json.dumps(result.to_legacy_dict())
    logged = "\n".join(r.getMessage() for r in caplog.records)
    assert canary not in shown and canary not in logged
    assert "reason=OUTPUT_CANARY" in logged                # the code is logged, never the value
