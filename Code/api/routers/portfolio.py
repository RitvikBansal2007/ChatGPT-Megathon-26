import pandas as pd
from fastapi import APIRouter, Depends
from api.deps import require_role
from greendash.portfolio.summary import get_portfolio_summary

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
    return get_portfolio_summary()


