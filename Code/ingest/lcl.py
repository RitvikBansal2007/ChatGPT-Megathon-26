"""Summarise the Low Carbon London smart-meter file into a small profile the generator can use.

Input:  dataset/CC_LCL-FullData.csv (about 8 GB, half-hourly kWh per household; not in git).
Output: data/priors/lcl_profile.json (a few KB, committed), so the pipeline never needs the raw file.

Only aggregates leave this module: annual-consumption quantiles across households and a
12-month seasonality shape. No household ID or reading is written out.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "dataset" / "CC_LCL-FullData.csv"
OUT = ROOT / "data" / "priors" / "lcl_profile.json"
MIN_READINGS_PER_MONTH = 1200   # of about 1,440 half-hours: drop months with long gaps
QUANTILES = list(range(1, 100))


def build(source: Path = SOURCE, out: Path = OUT, chunksize: int = 4_000_000) -> dict:
    parts = []
    reader = pd.read_csv(source, header=0, names=["id", "tariff", "ts", "kwh"], usecols=["id", "ts", "kwh"],
                         dtype={"id": "category", "ts": "string"}, na_values=["Null"], skipinitialspace=True,
                         chunksize=chunksize)
    for i, chunk in enumerate(reader):
        chunk["kwh"] = pd.to_numeric(chunk["kwh"], errors="coerce")
        chunk = chunk.dropna(subset=["kwh"])
        chunk["ym"] = chunk["ts"].str.slice(0, 7)
        parts.append(chunk.groupby(["id", "ym"], observed=True)["kwh"].agg(["sum", "count"]).reset_index())
        print(f"chunk {i + 1}", file=sys.stderr, flush=True)
    monthly = pd.concat(parts).groupby(["id", "ym"], observed=True).sum().reset_index()
    monthly = monthly[monthly["count"] >= MIN_READINGS_PER_MONTH]
    monthly["month"] = monthly["ym"].str.slice(5, 7).astype(int)

    # A household's typical month-m consumption, then its year: only homes with all 12 months seen.
    typical = monthly.groupby(["id", "month"], observed=True)["sum"].mean().unstack("month").dropna()
    annual = typical.sum(axis=1)
    shape = (typical.div(annual, axis=0) * 12).mean()   # 1.0 = an average month

    profile = {
        "source": "Low Carbon London smart-meter trial (UK Power Networks), CC_LCL-FullData.csv",
        "households_used": int(len(annual)),
        "household_months_used": int(len(monthly)),
        "annual_elec_kwh_quantiles": {str(q): round(float(np.percentile(annual, q)), 1) for q in QUANTILES},
        "monthly_elec_seasonality": [round(float(shape[m]), 4) for m in range(1, 13)],
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(profile, indent=2, sort_keys=True))
    print(f"wrote {out}: {profile['households_used']} households")
    return profile


if __name__ == "__main__":
    build()
