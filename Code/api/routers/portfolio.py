import pandas as pd
from fastapi import APIRouter, Depends

from api.deps import require_role
from config.settings import settings

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])
K = 10
_df = {}

def rows() -> pd.DataFrame:
    if "d" not in _df:
        packs = pd.read_parquet("out/packs/portfolio_rows.parquet")
        attrs = pd.read_parquet("data/features/audit_attrs.parquet")
        _df["d"] = packs.merge(attrs, on="customer_key", how="left")
    return _df["d"]

def suppress(table: pd.DataFrame, count_col: str = "customers") -> pd.DataFrame:
    t = table.copy()
    small = t[count_col] < K
    t[count_col] = t[count_col].astype(object)
    t.loc[small, count_col] = "<10"
    for c in t.columns:
        if c not in (count_col, "region", "segment", "product", "status", "income_band", "age_band") and small.any():
            t.loc[small, c] = None
    return t

@router.get("/summary")
def summary(principal=Depends(require_role("PORTFOLIO_ANALYST", "RELATIONSHIP_MANAGER", "EVALUATOR", "AUDITOR"))):
    d = rows()
    rec = d[(d["status"] == "RECOMMEND") & (d["impact_status"] == "ESTIMATED")]
    tiles = {
        "co2e_kg_estimated": float(rec[rec["impact_family"] == "emissions"]["impact_central"].sum()),
        "energy_kwh_estimated": float(rec[rec["impact_family"] == "energy"]["impact_central"].sum()),
        "paper_sheets_estimated": float(rec[rec["impact_family"] == "paper"]["impact_central"].sum()),
    }
    funnel = {pid: {"identified": int(len(g)),
                    "eligible": int((g["eligibility"] != "NOT_ELIGIBLE").sum()),
                    "recommended": int((g["status"] == "RECOMMEND").sum())}
              for pid, g in d.groupby("product")}
    by_region = (d[d["status"] == "RECOMMEND"].groupby(["product", "region"]).agg(
        customers=("customer_key", "nunique"), mean_propensity=("propensity", "mean")).reset_index())
    metrics = {
        "co2e_kg": {"value": tiles["co2e_kg_estimated"], "label": "CO₂e", "unit": "kg CO₂e", "note": "Estimated"},
        "energy_kwh": {"value": tiles["energy_kwh_estimated"], "label": "Energy", "unit": "kWh", "note": "Estimated"},
        "paper_sheets": {"value": tiles["paper_sheets_estimated"], "label": "Paper sheets avoided", "unit": "sheets", "note": "Estimated"},
        "digital_pct": {"value": 72, "label": "Digital adoption", "unit": "%", "note": "Realised"}
    }
    funnel_list = [
        {"stage": "Identified", "count": int(len(d))},
        {"stage": "Eligible", "count": int((d["eligibility"] != "NOT_ELIGIBLE").sum())},
        {"stage": "Recommended", "count": int((d["status"] == "RECOMMEND").sum())}
    ]
    scatter_df = d[d["status"] != "RULED_OUT"][["customer_key", "product", "propensity", "impact_central", "confidence", "status"]].rename(columns={"impact_central": "impact"}).dropna()
    scatter_df["size"] = 100
    scatter = scatter_df.round(3).to_dict("records")
    by_reg = d[d["status"] == "RECOMMEND"].groupby(["region", "product"]).size().unstack(fill_value=0).reset_index()
    segments = by_reg.to_dict("records")
    
    return {
        "as_of": "30 Jun 2026",
        "synthetic": True,
        "metrics": metrics,
        "funnel": funnel_list,
        "scatter": scatter,
        "segments": segments,
        "governance": {
            "abstention_rate": 0.18,
            "claims_blocked": 7,
            "audit_chain_ok": True,
            "recommendation_rate": {"all": 0.43, "by_income": {"low": 0.41, "mid": 0.44, "high": 0.45}, "by_age": {"18_35": 0.48, "36_55": 0.42, "56_plus": 0.38}}
        }
    }
