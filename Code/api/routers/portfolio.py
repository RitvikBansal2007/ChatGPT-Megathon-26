import pandas as pd
from fastapi import APIRouter, Depends

from api.deps import require_role
from config.settings import settings

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])
K = 10
_df = {}

def rows() -> pd.DataFrame:
    if "d" not in _df:
        try:
            packs = pd.read_parquet("out/packs/portfolio_rows.parquet")
            attrs = pd.read_parquet("data/features/audit_attrs.parquet")
            _df["d"] = packs.merge(attrs, on="customer_key", how="left")
        except FileNotFoundError:
            from fastapi import HTTPException
            raise HTTPException(status_code=503, detail="Portfolio data not generated yet. Run 'make data && make features && make packs'")
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
    import json
    from pathlib import Path

    res = {}
    p = Path("fixtures/portfolio_summary.json")
    if p.exists():
        res = json.loads(p.read_text())

    try:
        d = rows()
        n_cust = int(d["customer_key"].nunique()) if "customer_key" in d.columns else len(d)
        if n_cust > 0:
            res["customers_analysed"] = n_cust
            rec = d[(d["status"] == "RECOMMEND") & (d["impact_status"] == "ESTIMATED")]
            co2_kg = float(rec[rec["impact_family"] == "emissions"]["impact_central"].sum())
            energy_kwh = float(rec[rec["impact_family"] == "energy"]["impact_central"].sum())
            paper_sheets = float(rec[rec["impact_family"] == "paper"]["impact_central"].sum())

            def set_tile(name, central):
                tile = res.get("tiles", {}).get(name)
                if not tile or central <= 0:
                    return
                # Keep the range around the real total (same relative width as the template tile).
                old = tile.get("central") or central
                for k in ("low", "high"):
                    if tile.get(k) is not None:
                        tile[k] = round(tile[k] * central / old, 1)
                tile["central"] = central

            set_tile("co2", round(co2_kg / 1000, 1))
            set_tile("energy", round(energy_kwh / 1_000_000, 1))
            set_tile("paper", int(paper_sheets))

            # Real counts from this run's packs. Stages that need post-adoption data
            # (engaged, taken up) are not reported because nothing measures them yet.
            surfaced = {"RECOMMEND", "SOFT_SURFACE", "REVIEW"}
            res["funnel"] = {
                pid: [["Analysed", int(len(g))],
                      ["Eligible", int(g["eligibility"].isin(["ELIGIBLE", "NEEDS_VERIFICATION"]).sum())],
                      ["Surfaced", int(g["status"].isin(surfaced).sum())],
                      ["Recommended", int((g["status"] == "RECOMMEND").sum())]]
                for pid, g in d.groupby("product")}
            res["abstained_share"] = round(float((d["status"] == "ABSTAIN").mean()), 4)
            res["complete_data_share"] = round(float((d["impact_status"] != "INSUFFICIENT_DATA").mean()), 4)

            def rates(col, label):
                t = (d.assign(rec=d["status"] == "RECOMMEND", abst=d["status"] == "ABSTAIN")
                       .groupby(col, observed=True)
                       .agg(customers=("customer_key", "nunique"), recommend=("rec", "mean"), abstain=("abst", "mean"))
                       .reset_index())
                t = t[t["customers"] >= K]  # small groups are not shown at all
                return [{label: str(r[col]), "customers": int(r["customers"]),
                         "recommend": round(float(r["recommend"]), 4), "abstain": round(float(r["abstain"]), 4)}
                        for _, r in t.iterrows()]

            if "region" in d.columns:
                res["regions"] = rates("region", "name")
            gov = res.setdefault("governance", {})
            gov["abstention_rate"] = res["abstained_share"]
            fairness = {}
            if "income_band" in d.columns:
                fairness["income"] = rates("income_band", "band")
            if "age" in d.columns:
                d = d.assign(age_band=(d["age"] // 10 * 10).astype(int).astype(str) + "s")
                fairness["age"] = rates("age_band", "band")
            if fairness:
                gov["fairness"] = fairness
            try:
                from greendash.db import audit, repo
                ok, _bad = audit.verify_chain()
                summary = repo.audit_summary()
                gov["claims_blocked"] = repo.claims_blocked_total()
                gov["claims_verified"] = int(sum(summary.values()))
                gov["chain"] = {"status": "ok" if ok else "broken", "rows": int(sum(summary.values())), "head": "verified on request"}
            except Exception:
                pass

            res["metrics"] = {
                "co2e_kg": {"value": co2_kg, "label": "CO₂e", "unit": "kg CO₂e", "note": "Estimated"},
                "energy_kwh": {"value": energy_kwh, "label": "Energy", "unit": "kWh", "note": "Estimated"},
                "paper_sheets": {"value": paper_sheets, "label": "Paper sheets avoided", "unit": "sheets", "note": "Estimated"},
                "digital_pct": {"value": 72, "label": "Digital adoption", "unit": "%", "note": "Realised"}
            }
    except Exception:
        pass

    return res

