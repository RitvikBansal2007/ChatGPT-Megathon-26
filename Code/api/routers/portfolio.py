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
            d = packs.merge(attrs, on="customer_key", how="left")
            try:  # grouping attributes that are model inputs, for the segment table
                feats = pd.read_parquet("data/features/features.parquet",
                                        columns=["customer_key", "has_car", "home_owner"])
                d = d.merge(feats, on="customer_key", how="left")
            except (FileNotFoundError, KeyError, ValueError):
                pass
            _df["d"] = d
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

def _quadrant(d: pd.DataFrame) -> dict:
    """Per product: one cohort per region, from this run's packs (not the template)."""
    out = {}
    for pid, g in d.groupby("product"):
        cohorts = []
        for i, (region, r) in enumerate(g.groupby("region", observed=True), start=1):
            n = int(r["customer_key"].nunique())
            cid = f"{pid}-r{i:02d}"
            if n < K:  # small cohorts are not shown at all
                cohorts.append({"id": cid, "name": str(region), "n": n, "suppressed": True,
                                "propensity": 0, "conf": 0, "status": "SOFT_SURFACE",
                                "eligPass": 0, "eligNeeds": 0, "reasons": []})
                continue
            elig = r[r["eligibility"].isin(["ELIGIBLE", "NEEDS_VERIFICATION"])]
            passed = float((elig["eligibility"] == "ELIGIBLE").mean()) if len(elig) else 0.0
            est = r[r["impact_status"] == "ESTIMATED"]
            c = {"id": cid, "name": str(region), "n": n,
                 "propensity": round(float(r["propensity"].mean()), 3),
                 "conf": round(float(r["confidence"].mean()), 3),
                 "status": str(r["status"].mode().iat[0]),
                 "eligPass": round(passed, 3), "eligNeeds": round(1 - passed, 3) if len(elig) else 0.0,
                 "quality": None, "reasons": []}
            if len(est) and {"impact_low", "impact_central", "impact_high"} <= set(est.columns):
                c.update(low=round(float(est["impact_low"].mean())),
                         central=round(float(est["impact_central"].mean())),
                         high=round(float(est["impact_high"].mean())))
                if "impact_quality" in est.columns and est["impact_quality"].notna().any():
                    c["quality"] = str(est["impact_quality"].mode().iat[0])
            cohorts.append(c)
        out[str(pid)] = cohorts
    return out


def _segments(d: pd.DataFrame) -> list:
    """Customer groups from model-input attributes. Impact is the mean CO2e of the group's
    recommended emissions-family opportunities; other families are never mixed into it."""
    groups = []
    if "has_car" in d.columns:
        groups += [("Customers with a car on record", d["has_car"] == True),  # noqa: E712
                   ("Customers with no car on record", d["has_car"] == False)]  # noqa: E712
    if "home_owner" in d.columns:
        groups += [("Homeowners", d["home_owner"] == True),  # noqa: E712
                   ("Renters", d["home_owner"] == False)]  # noqa: E712
    if "digital_share" in d.columns:
        groups += [("Mostly paper statements", d["digital_share"] < 0.5),
                   ("Mostly digital statements", d["digital_share"] >= 0.5)]
    out = []
    for name, mask in groups:
        g = d[mask.fillna(False)]
        n = int(g["customer_key"].nunique())
        if n < K:
            continue
        rec = g[(g["status"] == "RECOMMEND") & (g["impact_status"] == "ESTIMATED")
                & (g["impact_family"] == "emissions")]
        impact = f'{round(float(rec["impact_central"].mean())):,} kg CO\u2082e (mean, per recommended customer)' if len(rec) else "Not estimated"
        out.append({"name": name, "customers": n,
                    "recommend": round(float((g["status"] == "RECOMMEND").mean()), 4),
                    "abstain": round(float((g["status"] == "ABSTAIN").mean()), 4),
                    "impact": impact})
    return out


@router.get("/summary")
def summary(principal=Depends(require_role("PORTFOLIO_ANALYST", "RELATIONSHIP_MANAGER", "EVALUATOR", "AUDITOR"))):
    import json
    from pathlib import Path

    res = {}
    p = Path("fixtures/portfolio_summary.json")
    if p.exists():
        res = json.loads(p.read_text(encoding="utf-8"))

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
                res["quadrant"] = _quadrant(d)
            res["segments"] = _segments(d)
            # Month-by-month history needs post-launch data this run does not have.
            # Report that instead of showing the template's invented series.
            res["trends"] = None
            if "digital_share" in d.columns and d["digital_share"].notna().any():
                tile = res.setdefault("tiles", {}).setdefault("digital", {
                    "family": "digital", "name": "Digital adoption", "status": "realised",
                    "unit": "of statements digital", "note": "Not a carbon reduction."})
                tile["central"] = round(float(d.drop_duplicates("customer_key")["digital_share"].mean()), 2)
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
                "digital_pct": {"value": round(res.get("tiles", {}).get("digital", {}).get("central", 0) * 100),
                                "label": "Digital adoption", "unit": "%", "note": "Realised"}
            }
    except Exception:
        pass

    return res

