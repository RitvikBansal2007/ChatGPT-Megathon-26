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
    return {
        "tiles": tiles,
        "digital_adoption": "see GP04 packs (separate from carbon)",
        "labels": {"estimated": True, "synthetic_data": True},
        "customers_analysed": int(d["customer_key"].nunique()),
        "funnel": funnel,
        "by_region": suppress(by_region).to_dict("records"),
        "quadrant": d[d["status"] != "RULED_OUT"][["product", "propensity", "impact_central", "confidence"]]
                    .dropna().round(3).to_dict("records"),
        "demo_mode": settings.DEMO_MODE,
    }
