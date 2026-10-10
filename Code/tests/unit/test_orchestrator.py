import pytest
from greenproof.contracts import *
from greenproof.orchestrator import decide_status

def prop(p=0.8, c=0.9):
    cp = ConfidenceParts(overall=c, completeness=c, recency=c, stability=c, in_distribution=c)
    return PropensityVerdict(propensity=p, likelihood_band=Band.HIGH, confidence=cp, reason_codes=[])

def elig(r=EligibilityResult.ELIGIBLE):
    return EligibilityVerdict(result=r, rules_fired=[], rules_version="rules-1.0", plain_reasons=[])

def imp(s=ImpactStatus.ESTIMATED):
    return ImpactVerdict(status=s)

def test_rule1_beats_everything():
    assert decide_status("GP01", prop(), elig(EligibilityResult.NOT_ELIGIBLE), imp(ImpactStatus.INSUFFICIENT_DATA), True, ["x"]) == Status.RULED_OUT

def test_rule2_conflict_beats_abstain():
    assert decide_status("GP01", prop(), elig(), imp(ImpactStatus.INSUFFICIENT_DATA), True, []) == Status.REVIEW

def test_rule3_insufficient_data_abstains_even_with_high_propensity():
    assert decide_status("GP01", prop(0.99), elig(), imp(ImpactStatus.INSUFFICIENT_DATA), False, []) == Status.ABSTAIN

def test_rule3_missing_critical_feature_abstains():
    assert decide_status("GP01", prop(), elig(), imp(), False, ["annual_mileage"]) == Status.ABSTAIN

def test_rule4_recommend_needs_both_thresholds():
    assert decide_status("GP01", prop(0.82, 0.88), elig(), imp(), False, []) == Status.RECOMMEND
    assert decide_status("GP01", prop(0.82, 0.40), elig(), imp(), False, []) == Status.SOFT_SURFACE
    assert decide_status("GP01", prop(0.20, 0.90), elig(), imp(), False, []) == Status.SOFT_SURFACE

def test_needs_verification_is_not_ruled_out():
    assert decide_status("GP02", prop(), elig(EligibilityResult.NEEDS_VERIFICATION), imp(), False, []) == Status.RECOMMEND

def test_not_applicable_never_recommends():
    assert decide_status("GP02", prop(), elig(), imp(ImpactStatus.NOT_APPLICABLE), False, []) == Status.SOFT_SURFACE
