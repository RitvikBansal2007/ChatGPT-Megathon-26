from datetime import date
import math

def days_old(as_of: date | None, cutoff: date) -> int | None:
    return None if as_of is None else (cutoff - as_of).days

def recency_score(days: int | None, fresh: int = 60, stale: int = 365) -> float:
    if days is None:
        return 0.0
    if days <= fresh:
        return 1.0
    if days >= stale:
        return 0.0
    return 1.0 - (days - fresh) / (stale - fresh)

CRITICAL = {
    "GP01": ["annual_mileage", "vehicle_fuel_type"],
    "GP02": ["gas_kwh_12m"],
    "GP03": ["electricity_kwh_12m", "roof_suitability"],
    "GP04": ["paper_statements_12m"],
}

def critical_missing(row: dict, product_id: str) -> list[str]:
    return [f for f in CRITICAL[product_id]
            if row.get(f) is None or (isinstance(row.get(f), float) and math.isnan(row[f]))]
