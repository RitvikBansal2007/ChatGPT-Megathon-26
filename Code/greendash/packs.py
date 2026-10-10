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

from greendash.contracts import ImpactVerdict, ImpactStatus, MetricFamily, MissingInput
def evaluate_customer(features_row: dict, factors: dict, as_of: date) -> dict:
    packs = {}
    for pid in PRODUCTS:
        carbon = estimate(features_row, pid, factors)
        impact = ImpactVerdict(
            status=ImpactStatus(carbon.status),
            metric_family=MetricFamily.PAPER if pid == "GP04" else MetricFamily.EMISSIONS,
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
    cutoff = date.fromisoformat(yaml.safe_load(open("config/decisions.yaml"))["cutoff_date"])
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
                         "impact_central": o.impact.central})
    pd.DataFrame(rows).to_parquet(OUT / "portfolio_rows.parquet", index=False)
    print("packs:", len(rows))

if __name__ == "__main__":
    main()
