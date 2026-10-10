import csv
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional

ROOT = Path(__file__).resolve().parent.parent.parent

@dataclass(frozen=True)
class CarbonEstimate:
    status: str # ESTIMATED, INSUFFICIENT_DATA, NOT_APPLICABLE
    low: float = 0.0
    central: float = 0.0
    high: float = 0.0
    formula: str = ""
    missing_inputs: Optional[List[str]] = None

def load_factors():
    out = {}
    path = ROOT / "config" / "factors.csv"
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            out[r["activity"]] = float(r["kg_co2e_per_unit"])
    return out

def estimate(features: dict, product_id: str, factors: dict):
    if product_id == "GP01":
        if not features.get("has_car"):
            return CarbonEstimate(status="NOT_APPLICABLE")
        if features.get("annual_mileage") is None:
            return CarbonEstimate(status="INSUFFICIENT_DATA", missing_inputs=["annual_mileage"])
        
        from .formulas import ev_switch
        ice_factor = factors.get("car_petrol_average", 0.26472)
        grid_factor = factors.get("grid_electricity", 0.20707)
        kwh_per_mile = 0.3 # assumption
        
        saved, form = ev_switch(features["annual_mileage"], ice_factor, kwh_per_mile, grid_factor)
        return CarbonEstimate(status="ESTIMATED", low=saved*0.85, central=saved, high=saved*1.15, formula=form)
        
    elif product_id == "GP02":
        if not features.get("home_owner"):
            return CarbonEstimate(status="NOT_APPLICABLE")
        if features.get("gas_kwh") is None:
            return CarbonEstimate(status="INSUFFICIENT_DATA", missing_inputs=["gas_kwh"])
        
        from .formulas import green_home_efficiency
        gas_factor = factors.get("natural_gas", 0.18254)
        
        kwh_saved, saved, form = green_home_efficiency(features["gas_kwh"], 0.15, gas_factor)
        return CarbonEstimate(status="ESTIMATED", low=saved*0.5, central=saved, high=saved*2.0, formula=form)
        
    elif product_id == "GP03":
        if not features.get("home_owner"):
            return CarbonEstimate(status="NOT_APPLICABLE")
        if features.get("roof_suitability") == "unknown":
            return CarbonEstimate(status="INSUFFICIENT_DATA", missing_inputs=["roof_suitability"])
            
        from .formulas import solar_install
        grid_factor = factors.get("grid_electricity", 0.20707)
        kwh, saved, form = solar_install(4.0, 950.0, grid_factor)
        return CarbonEstimate(status="ESTIMATED", low=saved*0.9, central=saved, high=saved*1.1, formula=form)
        
    elif product_id == "GP04":
        if features.get("paper_statements_12m") is None:
            return CarbonEstimate(status="INSUFFICIENT_DATA", missing_inputs=["paper_statements_12m"])
        
        from .formulas import paperless
        sheets, form = paperless(features["paper_statements_12m"], 3)
        return CarbonEstimate(status="ESTIMATED", low=sheets, central=sheets, high=sheets, formula=form)
        
    return CarbonEstimate(status="NOT_APPLICABLE")
