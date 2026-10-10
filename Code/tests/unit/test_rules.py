import pytest
from greendash.contracts import EligibilityResult as E
from greendash.rules.engine import evaluate

BASE = dict(vehicle_fuel_type="petrol", second_vehicle=False, has_vehicle_record=True, fuel_ev_conflict=False, vehicle_sold=False,
            home_owner=True, existing_solar=False, roof_suitability="suitable",
            paper_statements_12m=12, accessibility_paper_need=False)

def f(**kw): return {**BASE, **kw}

def test_priya_is_eligible_for_ev():
    assert evaluate(f(), "GP01").result == E.ELIGIBLE

def test_existing_bev_is_ruled_out():
    v = evaluate(f(vehicle_fuel_type="BEV"), "GP01")
    assert v.result == E.NOT_ELIGIBLE and v.rules_fired == ["GP01-R1"]

def test_bev_with_fuel_spend_needs_verification_not_ruled_out():
    v = evaluate(f(vehicle_fuel_type="BEV", fuel_ev_conflict=True), "GP01")
    assert v.result == E.NEEDS_VERIFICATION and v.rules_fired == ["GP01-R3"]

def test_sold_car_retires_the_ev_suggestion():
    v = evaluate(f(vehicle_sold=True, has_vehicle_record=True), "GP01")
    assert v.result == E.NOT_ELIGIBLE and v.rules_fired == ["GP01-R4"]

def test_bev_with_second_vehicle_is_not_ruled_out():
    assert evaluate(f(vehicle_fuel_type="BEV", second_vehicle=True), "GP01").result == E.ELIGIBLE

@pytest.mark.parametrize("pid,rule", [("GP02", "GP02-R1"), ("GP03", "GP03-R1")])
def test_renter_is_ruled_out(pid, rule):
    v = evaluate(f(home_owner=False), pid)
    assert v.result == E.NOT_ELIGIBLE and v.rules_fired == [rule]

def test_existing_solar_and_unsuitable_roof():
    assert evaluate(f(existing_solar=True), "GP03").rules_fired == ["GP03-R2"]
    assert evaluate(f(roof_suitability="unsuitable"), "GP03").rules_fired == ["GP03-R3"]

def test_unknown_ownership_needs_verification():
    assert evaluate(f(home_owner=None), "GP02").result == E.NEEDS_VERIFICATION

def test_missing_roof_does_not_rule_out():
    assert evaluate(f(roof_suitability=None), "GP03").result == E.ELIGIBLE

def test_paperless_rules():
    assert evaluate(f(paper_statements_12m=0), "GP04").rules_fired == ["GP04-R1"]
    assert evaluate(f(accessibility_paper_need=True), "GP04").rules_fired == ["GP04-R2"]

def test_every_product_has_a_plain_reason_for_every_rule():
    from greendash.rules.engine import _load
    for p in _load()["products"].values():
        for r in p["rules"]:
            assert r["plain"] and r["id"]
