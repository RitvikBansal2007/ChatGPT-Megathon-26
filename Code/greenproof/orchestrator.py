from __future__ import annotations

from datetime import date
from pathlib import Path

import yaml

from greenproof.contracts import (
    DigitalAdoption, EligibilityResult, ImpactStatus, ImpactVerdict, MissingInput, NextAction,
    Opportunity, ProductId, PropensityVerdict, EligibilityVerdict, Status, WhyNow, Band
)

ROOT = Path(__file__).resolve().parents[1]
TH = yaml.safe_load((ROOT / "config" / "thresholds.yaml").read_text())
CATALOGUE = yaml.safe_load((ROOT / "config" / "products.yaml").read_text())["products"]

DISCLAIMER = "Not a credit decision. Estimate, not a guarantee."
PRIMARY = {"GP01": "Explore EV options", "GP02": "Explore green home loans",
           "GP03": "Explore solar finance", "GP04": "Go paperless"}
LADDER = {MissingInput.ANNUAL_MILEAGE: "Add your annual mileage", MissingInput.ROOF_SUITABILITY: "Tell us about your roof",
          MissingInput.ENERGY_DATA: "Add a recent energy bill", MissingInput.VEHICLE_RECORD: "Confirm your vehicle",
          MissingInput.STATEMENT_HISTORY: "Give us a little more history"}

def thresholds_for(pid: str) -> dict:
    return {**TH["status"]["default"], **TH["status"]["per_product"].get(pid, {})}

def decide_status(pid: str, prop: PropensityVerdict, elig: EligibilityVerdict, impact: ImpactVerdict,
                  conflict: bool, critical_missing: list[str]) -> Status:
    if elig.result == EligibilityResult.NOT_ELIGIBLE:
        return Status.RULED_OUT
    if conflict:
        return Status.REVIEW
    if impact.status == ImpactStatus.INSUFFICIENT_DATA or critical_missing:
        return Status.ABSTAIN
    if impact.status == ImpactStatus.NOT_APPLICABLE:
        return Status.SOFT_SURFACE
    t = thresholds_for(pid)
    if prop.propensity >= t["propensity_min"] and prop.confidence.overall >= t["confidence_min"]:
        return Status.RECOMMEND
    return Status.SOFT_SURFACE

def _why_now(pid: str, f: dict, as_of: date) -> WhyNow | None:
    d = f.get("days_to_car_finance_end")
    if pid == "GP01" and d is not None and 0 <= d <= TH["why_now"]["car_finance_ending_days"]:
        return WhyNow(trigger="CAR_FINANCE_ENDING", display=f"Car finance ends in {int(d)} days", observed_at=as_of)
    m = f.get("days_since_mortgage_start")
    if pid in ("GP02", "GP03") and m is not None and 0 <= m <= TH["why_now"]["mortgage_started_days"]:
        return WhyNow(trigger="MORTGAGE_STARTED", display=f"Mortgage started {int(m)} days ago", observed_at=as_of)
    return None

def _action(status: Status, pid: str, impact: ImpactVerdict) -> NextAction | None:
    if status == Status.RULED_OUT:
        return None
    if status == Status.RECOMMEND:
        return NextAction(label=PRIMARY[pid], secondary="2-minute suitability check", disclaimer=DISCLAIMER)
    if status == Status.ABSTAIN:
        first = impact.missing_inputs[0] if impact.missing_inputs else None
        return NextAction(label=LADDER.get(first, "Give us a little more information"),
                          secondary="2-minute suitability check", disclaimer=DISCLAIMER)
    if status == Status.REVIEW:
        return NextAction(label="Confirm your vehicle", secondary=None, disclaimer=DISCLAIMER)
    return NextAction(label="Learn more", secondary=None, disclaimer=DISCLAIMER)

def build_pack(pid: str, features: dict, prop: PropensityVerdict, elig: EligibilityVerdict,
               impact: ImpactVerdict, as_of: date) -> Opportunity:
    status = decide_status(pid, prop, elig, impact, bool(features.get("fuel_ev_conflict")),
                           features.get(f"critical_missing_{pid}") or [])
    digital = None
    if pid == "GP04" and features.get("paper_statements_12m") is not None:
        digital = DigitalAdoption(paper_statements_12m=int(features["paper_statements_12m"]),
                                  digital_share=float(features.get("digital_share") or 0.0))
    return Opportunity(
        opportunity_id=ProductId(pid), opportunity_name=CATALOGUE[pid]["name"], status=status,
        propensity=prop.propensity, likelihood_band=prop.likelihood_band, confidence=prop.confidence,
        eligibility=elig,
        reason_codes=prop.reason_codes,
        why_now=_why_now(pid, features, as_of) if status != Status.RULED_OUT else None,
        impact=impact,
        digital_adoption=digital, explanation=None,
        next_action=_action(status, pid, impact), data_as_of=as_of,
    )
