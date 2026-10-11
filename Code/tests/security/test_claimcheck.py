import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from greendash.llm.claimcheck import check_sentence

ADVERSARIAL = yaml.safe_load((ROOT / "eval/llm_eval/adversarial.yaml").read_text())
CASES = {c["id"]: c for c in ADVERSARIAL}
SLICE_RULES = {"NUM", "FIELD", "BAN"}  # the rules implemented so far

# A small stand-in evidence pack: what the engines said about one EV customer.
ALLOWED_NUMBERS = ["1,420 kg CO2e", "1,100 to 1,800 kg CO2e per year", "12,000 miles", "2026"]
ALLOWED_FIELDS = ["status", "impact.display.central", "impact.display.range", "reason_codes.0"]


def run(sentence, **kw):
    kw.setdefault("allowed_numbers", ALLOWED_NUMBERS)
    kw.setdefault("allowed_fields", ALLOWED_FIELDS)
    return check_sentence(sentence, **kw)


def rules(violations):
    return [v.rule for v in violations]


def slice_of(case_id):
    return [r for r in CASES[case_id]["expected_violations"] if r in SLICE_RULES]


# ---- the red-team string -------------------------------------------------

def test_red_team_string_is_exactly_num_ban_ban():
    case = CASES["ADV01"]
    # Pinned from Architecture.md section 4A.10 test 6, not only read from the YAML.
    assert case["expected_violations"] == ["NUM", "BAN", "BAN"]
    got = run(case["sentence"])
    assert rules(got) == ["NUM", "BAN", "BAN"]
    assert [v.text for v in got if v.rule == "NUM"] == ["4,000"]
    assert {v.text.lower() for v in got if v.rule == "BAN"} == {"will save", "pre-approved"}


# ---- adversarial cases that exercise only these three rules ---------------

@pytest.mark.parametrize("case_id", ["ADV02", "ADV03", "ADV05", "ADV10", "ADV11", "ADV12",
                                     "ADV17", "ADV18"])
def test_adversarial_cases_match_expected_rules(case_id):
    got = run(CASES[case_id]["sentence"])
    assert rules(got) == slice_of(case_id)


# ---- NUM -----------------------------------------------------------------

@pytest.mark.parametrize("sentence", [
    "Your estimate is 1,420 kg CO2e.",
    "Your estimate is 1420 kg CO2e.",
    "That is about 1.42 t CO2e a year.",           # 1.42 t == 1,420 kg
    "The range is 1,100 to 1,800 kg CO2e per year.",
    "Based on 12,000 miles in 2026.",
])
def test_allowed_numbers_pass_in_any_notation(sentence):
    assert run(sentence) == []


def test_other_tonne_figure_is_flagged():
    assert rules(run("That is about 1.5 t CO2e a year.")) == ["NUM"]


def test_invented_number_is_reported_once_per_value():
    got = run("You could save 900 kg, and again 900 kg next year.")
    assert rules(got) == ["NUM"]


def test_identifiers_with_digits_are_not_numbers():
    assert run("GP01 EV Finance is estimated at 1,420 kg CO2e.") == []


def test_number_glued_to_unit_is_still_checked():
    assert rules(run("Expect 4,000kg a year.")) == ["NUM"]


# ---- FIELD ---------------------------------------------------------------

def test_cited_field_must_exist():
    assert run("Based on your status.", cited_fields=["status"]) == []
    got = run("Based on your status.", cited_fields=["impact.secret_score"])
    assert rules(got) == ["FIELD"]


def test_unknown_dotted_path_in_text_is_flagged_but_known_one_is_not():
    assert run("See impact.display.central for the figure.") == []
    assert rules(run("See impact.display.hidden for the figure.")) == ["FIELD"]


def test_abbreviations_are_not_fields():
    assert run("Costs vary, e.g. by tariff.") == []


# ---- BAN -----------------------------------------------------------------

@pytest.mark.parametrize("sentence", [
    "This is GUARANTEED.",
    "You are Pre Approved.",
    "You are preapproved.",
    "You're pre‑approved.",       # non-breaking hyphen
])
def test_banned_phrases_match_case_and_hyphen_variants(sentence):
    assert rules(run(sentence)) == ["BAN"]


def test_pre_approved_is_one_hit_not_two():
    assert rules(run("Your credit is pre-approved.")) == ["BAN"]


def test_similar_but_allowed_wording_passes():
    assert run("This could reduce your emissions, and it is not a credit decision.") == []
    assert run("An unapproved change is not part of this estimate.") == []


def test_custom_ban_list_is_respected():
    assert run("A cheap option.", banned_phrases=["cheap"]) != []
    assert run("You are pre-approved.", banned_phrases=["cheap"]) == []


# ---- general -------------------------------------------------------------

def test_clean_sentence_has_no_violations():
    s = ("Your fuel spend suggests an EV could cut about 1,420 kg CO2e a year "
         "(estimate, not a guarantee).")
    assert run(s) == []


def test_checks_are_deterministic():
    s = CASES["ADV01"]["sentence"]
    assert run(s) == run(s)


def test_metric_and_verdict_rules_use_the_pack():
    from greendash.llm.claimcheck import _pack_rules
    assert [v["rule"] for v in _pack_rules("Going paperless cuts your carbon footprint.", {"opportunity_id": "GP04", "status": "RECOMMEND"})] == ["METRIC"]
    assert _pack_rules("Going paperless avoids paper sheets.", {"opportunity_id": "GP04", "status": "RECOMMEND"}) == []
    assert [v["rule"] for v in _pack_rules("This looks worth exploring.", {"opportunity_id": "GP01", "status": "RULED_OUT"})] == ["VERDICT"]
    assert _pack_rules("This looks worth exploring.", {"opportunity_id": "GP01", "status": "RECOMMEND"}) == []
