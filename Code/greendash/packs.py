import json
from datetime import date
from pathlib import Path

import pandas as pd
import yaml

from greendash.carbon.engine import estimate, load_factors
from greendash.models.score import score
from greendash.orchestrator import build_pack
from greendash.rules.engine import evaluate

PRODUCTS = ["GP01", "GP02", "GP03", "GP04"]
OUT = Path("out/packs")

from greendash.contracts import Band, ImpactVerdict, ImpactStatus, MetricFamily, MissingInput

# What each estimate is measured against and which published factors it uses (config/factors.csv, assumptions.yaml).
IMPACT_CONTEXT = {
    "GP01": ("Your current car, same yearly mileage", ["DESNZ 2024: average car, per mile", "DESNZ 2024: UK grid electricity, per kWh"]),
    "GP02": ("Your gas use over the last 12 months", ["DESNZ 2024: natural gas, per kWh", "Energy Saving Trust: heating upgrade savings"]),
    "GP03": ("Grid electricity for the same amount generated", ["DESNZ 2024: UK grid electricity, per kWh", "JRC PVGIS: yearly yield per kWp"]),
    "GP04": ("Paper statements over the last 12 months", ["Sheets per statement (config/assumptions.yaml)"]),
}


def impact_quality(low: float, central: float, high: float) -> Band:
    """How tight the estimate is: half the range as a share of the central value.

    Up to 10% is HIGH, up to 25% is MEDIUM, wider is LOW. The widths come from the carbon
    engine's own uncertainty on its main input, so this never depends on the ML score.
    """
    if not central:
        return Band.LOW
    half_width = (high - low) / (2 * abs(central))
    return Band.HIGH if half_width <= 0.10 else Band.MEDIUM if half_width <= 0.25 else Band.LOW


def evaluate_customer(features_row: dict, factors: dict, as_of: date) -> dict:
    packs = {}
    for pid in PRODUCTS:
        carbon = estimate(features_row, pid, factors)
        estimated = carbon.status == "ESTIMATED"
        impact = ImpactVerdict(
            status=ImpactStatus(carbon.status),
            metric_family=MetricFamily.PAPER if pid == "GP04" else MetricFamily.EMISSIONS,
            unit=("sheets a year" if pid == "GP04" else "kg CO2e a year") if estimated else None,
            baseline=IMPACT_CONTEXT[pid][0] if estimated else None,
            horizon="12 months" if estimated else None,
            factor_refs=IMPACT_CONTEXT[pid][1] if estimated else [],
            quality=impact_quality(carbon.low, carbon.central, carbon.high) if estimated else None,
            low=carbon.low if carbon.status == "ESTIMATED" else None,
            central=carbon.central if carbon.status == "ESTIMATED" else None,
            high=carbon.high if carbon.status == "ESTIMATED" else None,
            formula=carbon.formula if carbon.status == "ESTIMATED" else None,
            display=carbon.display.get("central") if carbon.display else None,
            missing_inputs=[MissingInput("energy_data" if m == "gas_kwh" else "statement_history" if m == "paper_statements_12m" else m) for m in carbon.missing_inputs] if carbon.missing_inputs else []
        )
        packs[pid] = build_pack(pid, features_row, score(features_row, pid), evaluate(features_row, pid),
                                impact, as_of)
    return packs

def main() -> None:
    cutoff = date.fromisoformat(yaml.safe_load(open("config/decisions.yaml", encoding="utf-8"))["cutoff_date"])
    feats = pd.read_parquet("data/features/features.parquet")
    factors = load_factors()
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for rec in feats.sort_values("customer_id").to_dict("records"):
        packs = evaluate_customer(rec, factors, cutoff)
        (OUT / f"{rec['customer_id']}.json").write_text(
            json.dumps({p: json.loads(o.model_dump_json(by_alias=True)) for p, o in packs.items()}, sort_keys=True))
        for pid, o in packs.items():
            rows.append({"customer_key": rec["customer_key"], "product": pid, "status": o.status.value,
                         "propensity": o.propensity, "confidence": o.confidence.overall,
                         "eligibility": o.eligibility.result.value, "impact_status": o.impact.status.value,
                         "impact_family": o.impact.metric_family.value if o.impact.metric_family else None,
                         "impact_central": o.impact.central,
                         "impact_low": o.impact.low, "impact_high": o.impact.high,
                         "impact_quality": o.impact.quality.value if o.impact.quality else None,
                         "digital_share": rec.get("digital_share")})
    pd.DataFrame(rows).to_parquet(OUT / "portfolio_rows.parquet", index=False)
    print("packs:", len(rows))

if __name__ == "__main__":
    main()
