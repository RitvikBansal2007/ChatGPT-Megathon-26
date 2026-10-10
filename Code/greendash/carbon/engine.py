import csv
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional

import yaml

from . import units
from .formulas import ev_switch, green_home_efficiency, solar_install, paperless

ROOT = Path(__file__).resolve().parent.parent.parent


@dataclass(frozen=True)
class CarbonEstimate:
    status: str  # ESTIMATED, INSUFFICIENT_DATA, NOT_APPLICABLE
    low: float = 0.0
    central: float = 0.0
    high: float = 0.0
    formula: str = ""
    missing_inputs: Optional[List[str]] = None
    display: Optional[dict] = None


def load_factors(path=None):
    out = {}
    path = path or ROOT / "config" / "factors.csv"
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            out[r["activity"]] = float(r["kg_co2e_per_unit"])
    return out


def load_assumptions(path=None):
    path = path or ROOT / "config" / "assumptions.yaml"
    with open(path) as f:
        return yaml.safe_load(f)


def _a(assumptions, key, field="value"):
    return float(assumptions[key][field])


def estimate(features: dict, product_id: str, factors: dict, assumptions: dict = None):
    """Deterministic estimate. Every number comes from factors.csv or assumptions.yaml."""
    assumptions = assumptions if assumptions is not None else load_assumptions()

    if product_id == "GP01":
        if features.get("annual_mileage") is None:
            return CarbonEstimate(status="INSUFFICIENT_DATA", missing_inputs=["annual_mileage"])
        if features.get("annual_mileage", 0) <= 0 and features.get("fuel_spend_last_6m", 0) <= 0:
            return CarbonEstimate(status="NOT_APPLICABLE")
        if features.get("fuel_type") == "bev":
            return CarbonEstimate(status="NOT_APPLICABLE")
        ice_key = "car_diesel_average" if features.get("fuel_type") == "diesel" else "car_petrol_average"
        miles = features["annual_mileage"]
        # Uncertain input is annual miles: +/-15% when only one value exists.
        args = (factors[ice_key], _a(assumptions, "ev_kwh_per_mile"), factors["grid_electricity"])
        central, form = ev_switch(miles, *args)
        low, _ = ev_switch(miles * 0.85, *args)
        high, _ = ev_switch(miles * 1.15, *args)
        return _done(low, central, high, form, "kg")

    if product_id == "GP02":
        if not features.get("home_owner"):
            return CarbonEstimate(status="NOT_APPLICABLE")
        if features.get("gas_kwh") is None:
            return CarbonEstimate(status="INSUFFICIENT_DATA", missing_inputs=["gas_kwh"])
        g = assumptions["gp02_reduction_fraction"]
        gas = factors["natural_gas"]
        res = [green_home_efficiency(features["gas_kwh"], float(g[k]), gas)
               for k in ("value_low", "value_central", "value_high")]
        return _done(res[0][1], res[1][1], res[2][1], res[1][2], "kg")

    if product_id == "GP03":
        if not features.get("home_owner"):
            return CarbonEstimate(status="NOT_APPLICABLE")
        if features.get("roof_suitability") is None or features.get("roof_suitability") == "unknown":
            return CarbonEstimate(status="INSUFFICIENT_DATA", missing_inputs=["roof_suitability"])
        if features.get("roof_suitability") == "unsuitable" or features.get("existing_solar"):
            return CarbonEstimate(status="NOT_APPLICABLE")
        kwp = _a(assumptions, "gp03_kwp_sizing")
        yield_ = _a(assumptions, "gp03_kwh_per_kwp")
        grid = factors["grid_electricity"]
        # Uncertain input is yield per kWp: +/-10%.
        central = solar_install(kwp, yield_, grid)
        low = solar_install(kwp, yield_ * 0.9, grid)
        high = solar_install(kwp, yield_ * 1.1, grid)
        return _done(low[1], central[1], high[1], central[2], "kg")

    if product_id == "GP04":
        if features.get("accessibility_paper_need"):
            return CarbonEstimate(status="NOT_APPLICABLE")
        if features.get("paper_statements_12m") is None:
            return CarbonEstimate(status="INSUFFICIENT_DATA", missing_inputs=["paper_statements_12m"])
        sheets, form = paperless(features["paper_statements_12m"],
                                 _a(assumptions, "sheets_per_statement"))
        # Paper family only. Never CO2e.
        return CarbonEstimate(status="ESTIMATED", low=sheets, central=sheets, high=sheets,
                              formula=form, display={"central": units.fmt_sheets(sheets)})

    return CarbonEstimate(status="NOT_APPLICABLE")


def _done(low, central, high, form, kind):
    return CarbonEstimate(
        status="ESTIMATED", low=low, central=central, high=high, formula=form,
        display={"central": units.fmt_kg(central), "range": units.fmt_range_kg(low, high)},
    )
