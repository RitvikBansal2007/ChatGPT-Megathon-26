import json
import statistics as st
import time
from datetime import date

import pandas as pd

from greendash.carbon.engine import load_factors
from greendash.contracts import Mutation
from greendash.packs import evaluate_customer
from greendash.scenarios.run import run

CUT = date(2026, 6, 30)

def pct(xs, q):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(q * len(xs)))]

def main() -> None:
    feats = pd.read_parquet("data/features/features.parquet")
    f = load_factors()
    pack_ms = []
    for rec in feats.head(300).to_dict("records"):
        t = time.perf_counter()
        evaluate_customer(rec, f, CUT)
        pack_ms.append((time.perf_counter() - t) * 1000 / 4)
    run("CUST-0001", [Mutation.REMOVE_MILEAGE])
    scen_ms = []
    for m in Mutation:
        t = time.perf_counter()
        run("CUST-0001", [m])
        scen_ms.append((time.perf_counter() - t) * 1000)
    out = {"pack_ms_p50": round(st.median(pack_ms), 1), "pack_ms_p95": round(pct(pack_ms, 0.95), 1),
           "scenario_ms_p50": round(st.median(scen_ms)), "scenario_ms_max": round(max(scen_ms)),
           "targets": {"pack_ms": 50, "scenario_ms": 1000}}
    json.dump(out, open("out/latency.json", "w"), indent=1)
    print(out)

if __name__ == "__main__":
    main()
