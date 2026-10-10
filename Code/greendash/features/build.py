from __future__ import annotations

from datetime import date
import pandas as pd

from greendash.features.conflicts import conflict_flags
from greendash.features.freshness import CRITICAL, critical_missing, days_old, recency_score

MODEL_EXCLUDED = {"age", "income_band", "region", "postcode"}

def build_features(raw: dict[str, pd.DataFrame], cutoff: date) -> tuple[pd.DataFrame, pd.DataFrame]:
    cut = pd.Timestamp(cutoff)
    start12 = cut - pd.DateOffset(months=12)
    start90 = cut - pd.Timedelta(days=90)

    cust = raw["customers"].copy()
    tx = raw["transactions"]
    tx = tx[(tx["date"] < cut) & (tx["date"] >= start12)]
    veh = raw["vehicles"]
    en = raw["energy"]
    en = en[(en["month"] < cut.to_period("M").to_timestamp()) & (en["month"] >= start12)]
    dg = raw["digital"]
    dg = dg[(dg["month"] < cut.to_period("M").to_timestamp()) & (dg["month"] >= start12)]
    pr = raw["products"]
    pr = pr[pr["start_date"] < cut]

    out = cust[["customer_id", "customer_key", "is_persona", "home_owner", "digital_usage",
                "sustainability_preference", "epc_band", "roof_suitability", "existing_solar",
                "accessibility_paper_need"]].set_index("customer_id")

    debit = tx[tx["debit_credit"] == "D"]
    if "category" not in debit.columns:
        debit = debit.assign(category="Other")
    fuel = debit[debit["category"] == "Fuel"]
    g = fuel.groupby("customer_id")
    out["avg_monthly_fuel_gbp"] = (g["amount"].sum() / 12).reindex(out.index)
    out["fuel_txn_count_90d"] = fuel[fuel["date"] >= start90].groupby("customer_id").size().reindex(out.index).fillna(0)
    out["history_months"] = tx.groupby("customer_id")["date"].agg(lambda s: (s.max() - s.min()).days / 30.4).reindex(out.index)
    out["as_of_transactions"] = tx.groupby("customer_id")["date"].max().reindex(out.index)

    owned = veh[veh["status"] == "owned"].sort_values("vehicle_age")
    first = owned.groupby("customer_id").first()
    out["has_vehicle_record"] = out.index.isin(veh["customer_id"])
    out["vehicle_sold"] = out.index.isin(veh[veh["status"] == "sold"]["customer_id"]) & ~out.index.isin(owned["customer_id"])
    out["vehicle_fuel_type"] = first["fuel_type"].reindex(out.index)
    out["vehicle_age"] = first["vehicle_age"].reindex(out.index)
    out["annual_mileage"] = first["annual_mileage"].reindex(out.index)
    out["second_vehicle"] = (owned.groupby("customer_id").size().reindex(out.index).fillna(0) > 1)
    out["as_of_vehicle"] = veh.groupby("customer_id")["updated_at"].max().reindex(out.index)

    e = en.groupby("customer_id")
    out["electricity_kwh_12m"] = e["electricity_kwh"].sum(min_count=1).reindex(out.index)
    out["gas_kwh_12m"] = e["gas_kwh"].sum(min_count=1).reindex(out.index)
    out["as_of_energy"] = e["month"].max().reindex(out.index)

    d = dg.groupby("customer_id")
    out["paper_statements_12m"] = d["paper_statements"].sum(min_count=1).reindex(out.index)
    out["digital_statements_12m"] = d["digital_statements"].sum(min_count=1).reindex(out.index)
    tot = out["paper_statements_12m"] + out["digital_statements_12m"]
    out["digital_share"] = (out["digital_statements_12m"] / tot).where(tot > 0)
    out["as_of_digital"] = d["month"].max().reindex(out.index)

    cf = pr[pr["product"] == "car_finance"].groupby("customer_id")["end_date"].max()
    out["car_finance_end_date"] = cf.reindex(out.index)
    out["days_to_car_finance_end"] = (out["car_finance_end_date"] - cut).dt.days
    mg = pr[pr["product"] == "mortgage"].groupby("customer_id")["start_date"].max()
    out["days_since_mortgage_start"] = (cut - mg.reindex(out.index)).dt.days

    out = out.reset_index()

    rows = out.to_dict("records")
    for r in rows:
        for src in ("transactions", "vehicle", "energy", "digital"):
            d_old = days_old(None if pd.isna(r[f"as_of_{src}"]) else r[f"as_of_{src}"].date(), cutoff)
            r[f"recency_{src}"] = recency_score(d_old)
        r["conflict_flags"] = conflict_flags(r)
        r["fuel_ev_conflict"] = "BEV_RECORD_BUT_FUEL_SPEND" in r["conflict_flags"]
        for pid in CRITICAL:
            miss = critical_missing(r, pid)
            r[f"critical_missing_{pid}"] = miss
            r[f"completeness_{pid}"] = 1 - len(miss) / len(CRITICAL[pid])
    feats = pd.DataFrame(rows)

    audit = cust[["customer_key", "age", "income_band", "region"]].copy()
    return feats, audit
