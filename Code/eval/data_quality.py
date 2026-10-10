"""Data-quality gates owned by the data lane. Prints PASS/FAIL and writes out/data_quality.json.

Gates: schema conformance, foreign-key integrity, take-up base rates, single-feature
AUC < 0.80, persona raw-signal facts, same-seed determinism (sha256), PII scan.
Pure numpy/pandas (rank-based AUC), no network.
"""
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pandera.pandas as pa

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "out" / "data_quality.json"

BASE_RATE_RANGES = {"take_up_GP01": (0.04, 0.08), "take_up_GP02": (0.03, 0.06),
                    "take_up_GP03": (0.02, 0.05), "take_up_GP04": (0.15, 0.25)}
# Take-up is conditional on eligibility; the target is the rate among eligible customers.
EXPECTED_TABLES = ["customers", "vehicles", "energy_usage", "transactions", "digital_usage",
                   "products", "green_products", "emissions_factors",
                   "take_up_labels", "transaction_labels"]
PII = re.compile(r"@|\b\d{10,}\b|\b[A-Z]{1,2}\d[A-Z\d]? ?\d[A-Z]{2}\b")


def load():
    return {n: pd.read_parquet(RAW / f"{n}.parquet") for n in EXPECTED_TABLES}


def auc(y: np.ndarray, x: np.ndarray) -> float:
    """Mann-Whitney AUC using average ranks (ties handled)."""
    pos = y == 1
    n1, n0 = pos.sum(), (~pos).sum()
    if n1 == 0 or n0 == 0:
        return 0.5
    ranks = pd.Series(x).rank(method="average").to_numpy()
    return float((ranks[pos].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def gate_schema(t):
    schemas = {
        "customers": pa.DataFrameSchema({
            "customer_id": pa.Column(str, unique=True),
            "age": pa.Column(int, pa.Check.in_range(18, 120)),
            "income_band": pa.Column(str),
            "region": pa.Column(str),
            "home_owner": pa.Column(bool),
            "digital_usage": pa.Column(float, pa.Check.in_range(0, 1)),
            "sustainability_preference": pa.Column(float, pa.Check.in_range(0, 1)),
            "roof_suitability": pa.Column(str, pa.Check.isin(["suitable", "unsuitable", "unknown"])),
        }, strict=False),
        "vehicles": pa.DataFrameSchema({
            "customer_id": pa.Column(str),
            "fuel_type": pa.Column(str, pa.Check.isin(["petrol", "diesel", "hybrid", "bev"])),
            "annual_mileage": pa.Column(int, pa.Check.gt(0)),
        }, strict=False),
        "energy_usage": pa.DataFrameSchema({
            "customer_id": pa.Column(str),
            "electricity_kwh": pa.Column(float, pa.Check.ge(0)),
            "gas_kwh": pa.Column(float, pa.Check.ge(0)),
        }, strict=False),
        "transactions": pa.DataFrameSchema({
            "transaction_id": pa.Column(str, unique=True),
            "customer_id": pa.Column(str),
            "amount": pa.Column(float, pa.Check.gt(0)),
        }, strict=False),
        "take_up_labels": pa.DataFrameSchema({
            "customer_id": pa.Column(str, unique=True),
            **{c: pa.Column(int, pa.Check.isin([0, 1])) for c in BASE_RATE_RANGES},
        }, strict=False),
    }
    bad = {}
    for name, schema in schemas.items():
        try:
            schema.validate(t[name], lazy=True)
        except pa.errors.SchemaErrors as e:
            bad[name] = int(len(e.failure_cases))
    return not bad, {"tables_checked": len(schemas), "failures": bad}


def gate_fk(t):
    ids = set(t["customers"]["customer_id"])
    orphans = {}
    for name in ["vehicles", "energy_usage", "transactions", "digital_usage",
                 "products", "take_up_labels"]:
        orphans[name] = int((~t[name]["customer_id"].isin(ids)).sum())
    orphans["transaction_labels"] = int(
        (~t["transaction_labels"]["transaction_id"].isin(t["transactions"]["transaction_id"])).sum())
    return sum(orphans.values()) == 0, orphans


def eligibility(t):
    c = t["customers"]
    return {
        "take_up_GP01": c["customer_id"].isin(t["vehicles"]["customer_id"]),
        "take_up_GP02": c["home_owner"],
        "take_up_GP03": c["home_owner"],
        "take_up_GP04": c["digital_usage"] < 0.5,
    }


def gate_base_rates(t):
    lab = t["take_up_labels"].set_index("customer_id").loc[t["customers"]["customer_id"]]
    elig = eligibility(t)
    res, ok = {}, True
    for col, (lo, hi) in BASE_RATE_RANGES.items():
        rate_all = float(lab[col].mean())
        mask = elig[col].to_numpy()
        rate_elig = float(lab[col].to_numpy()[mask].mean()) if mask.any() else 0.0
        # Base rate is defined among eligible customers (not-eligible rows are forced to 0).
        within = lo <= rate_elig <= hi
        ok &= within
        res[col] = {"rate_all": round(rate_all, 4), "rate_eligible": round(rate_elig, 4),
                    "target": [lo, hi], "in_range": bool(within)}
    return ok, res


def gate_auc(t):
    c = t["customers"].set_index("customer_id")
    lab = t["take_up_labels"].set_index("customer_id").loc[c.index]
    veh = t["vehicles"].drop_duplicates("customer_id").set_index("customer_id").reindex(c.index)
    energy = t["energy_usage"].groupby("customer_id")[["electricity_kwh", "gas_kwh"]].mean() \
        .reindex(c.index)
    X = pd.DataFrame({
        "age": c["age"], "digital_usage": c["digital_usage"],
        "sustainability_preference": c["sustainability_preference"],
        "home_owner": c["home_owner"].astype(int),
        "existing_solar": c["existing_solar"].astype(int),
        "vehicle_age": veh["vehicle_age"], "annual_mileage": veh["annual_mileage"],
        "electricity_kwh": energy["electricity_kwh"], "gas_kwh": energy["gas_kwh"],
    })
    worst, ok, detail = 0.0, True, {}
    elig = eligibility(t)
    for col in BASE_RATE_RANGES:
        # Eligibility is a product rule, so AUC is measured within the eligible population.
        m = elig[col].to_numpy()
        y = lab[col].to_numpy()[m]
        best = 0.0
        for f in X.columns:
            a = auc(y, X[f].fillna(0).to_numpy()[m])
            a = max(a, 1 - a)
            best = max(best, a)
        detail[col] = round(best, 4)
        worst = max(worst, best)
    return worst < 0.80, {"max_single_feature_auc": detail}


def gate_personas(t):
    c = t["customers"].set_index("customer_id")
    v = t["vehicles"].set_index("customer_id")
    facts = {
        "CUST-0001_petrol_8y": bool(v.loc["CUST-0001", "fuel_type"] == "petrol"
                                    and v.loc["CUST-0001", "vehicle_age"] == 8),
        "CUST-0002_bev_record": bool(v.loc["CUST-0002", "fuel_type"] == "bev"),
        "CUST-0003_bev_solar_paperless": bool(v.loc["CUST-0003", "fuel_type"] == "bev"
                                              and c.loc["CUST-0003", "existing_solar"]
                                              and c.loc["CUST-0003", "digital_usage"] == 1.0),
        "CUST-0004_short_history_paper": bool(c.loc["CUST-0004", "digital_usage"] == 0.0),
        "CUST-0005_homeowner_epc_D": bool(c.loc["CUST-0005", "home_owner"]
                                          and c.loc["CUST-0005", "epc_band"] == "D"),
        "CUST-0006_roof_unknown": bool(c.loc["CUST-0006", "roof_suitability"] == "unknown"),
        "CUST-0007_renter_paper": bool((not c.loc["CUST-0007", "home_owner"])
                                       and c.loc["CUST-0007", "digital_usage"] < 0.5),
        "CUST-0008_accessibility": bool(c.loc["CUST-0008", "accessibility_paper_need"]),
    }
    n = sum(facts.values())
    return n == 8, {"raw_signal_facts_matched": f"{n} of 8", "facts": facts}


def sha_dir():
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(RAW.glob("*.parquet"))}


def gate_determinism():
    before = sha_dir()
    bak = ROOT / "out" / "_raw_backup"
    if bak.exists():
        shutil.rmtree(bak)
    shutil.copytree(RAW, bak)
    try:
        subprocess.run([sys.executable, "-m", "greendash.generator.run"], cwd=ROOT, check=True,
                       capture_output=True)
        after = sha_dir()
    finally:
        shutil.rmtree(RAW)
        shutil.move(str(bak), str(RAW))
    diffs = sorted(k for k in before if before[k] != after.get(k))
    manifest = hashlib.sha256(json.dumps(before, sort_keys=True).encode()).hexdigest()
    return not diffs, {"manifest_sha256": manifest, "files": len(before), "differing_files": diffs}


def gate_pii(t):
    hits = 0
    for name, df in t.items():
        for col in df.select_dtypes(include=["object", "string"]):
            hits += int(df[col].astype(str).str.contains(PII).sum()) if name not in ("customers",) \
                or col != "postcode" else 0
    return hits == 0, {"hits": hits}


def main():
    t = load()
    gates = [
        ("Schema conformance (pandera)", "100%", lambda: gate_schema(t)),
        ("Foreign-key integrity", "0 orphans", lambda: gate_fk(t)),
        ("Take-up base rates", "inside target ranges", lambda: gate_base_rates(t)),
        ("Single-feature AUC", "< 0.80", lambda: gate_auc(t)),
        ("Persona raw-signal facts", "8 of 8", lambda: gate_personas(t)),
        ("Same seed, two runs", "identical sha256", gate_determinism),
        ("PII scan on public data", "0 hits", lambda: gate_pii(t)),
    ]
    report, all_ok = [], True
    for name, thr, fn in gates:
        ok, detail = fn()
        all_ok &= bool(ok)
        report.append({"gate": name, "threshold": thr, "result": "PASS" if ok else "FAIL",
                       "detail": detail})
        print(f"{'PASS' if ok else 'FAIL'}  {name}  [{thr}]")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"all_pass": all_ok, "gates": report}, indent=2, sort_keys=True,
                              default=str) + "\n")
    print(f"wrote {OUT}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
