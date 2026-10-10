from __future__ import annotations

import time
from datetime import date
from pathlib import Path

import pandas as pd
import yaml

from greenproof.carbon.engine import load_factors
from greenproof.contracts import (DiffRow, Mutation, Opportunity, ProductId, ScenarioResponse, StatusSnapshot)
from greenproof.features.build import build_features
from greenproof.packs import evaluate_customer
from greenproof.scenarios.mutations import apply_mutations

RAW = Path("data/raw")
TABLES = ["customers", "transactions", "products", "vehicles", "energy", "digital"]
_CACHE: dict[str, pd.DataFrame] = {}

def _raw() -> dict[str, pd.DataFrame]:
    if not _CACHE:
        for t in TABLES:
            _CACHE[t] = pd.read_parquet(RAW / f"{t}.parquet")
    return _CACHE

def load_customer_rows(customer_id: str) -> dict[str, pd.DataFrame]:
    return {t: df[df["customer_id"] == customer_id].copy(deep=True) for t, df in _raw().items()}

def _snapshot(packs: dict[str, Opportunity]) -> dict[ProductId, StatusSnapshot]:
    return {ProductId(p): StatusSnapshot(status=o.status, propensity=round(o.propensity, 4),
                                         eligibility=o.eligibility.result, impact_status=o.impact.status)
            for p, o in packs.items()}

def run_on_rows(rows: dict[str, pd.DataFrame], cutoff: date, factors: dict):
    feats, _ = build_features(rows, cutoff)
    rec = feats.iloc[0].to_dict()
    return rec, evaluate_customer(rec, factors, cutoff)

def _cause(pid: str, b: Opportunity, a: Opportunity, fb: dict, fa: dict) -> str:
    if a.eligibility.rules_fired and a.eligibility.rules_fired != b.eligibility.rules_fired:
        return f"Rule {a.eligibility.rules_fired[0]}: {a.eligibility.plain_reasons[0]}"
    if b.eligibility.rules_fired and not a.eligibility.rules_fired:
        return f"Rule {b.eligibility.rules_fired[0]} no longer fires"
    if a.impact.status.value == "INSUFFICIENT_DATA" and b.impact.status.value != "INSUFFICIENT_DATA":
        return "Missing input: " + ", ".join(m.value for m in a.impact.missing_inputs)
    if fa.get("fuel_ev_conflict") and not fb.get("fuel_ev_conflict"):
        return "Conflict flag set: BEV record but fuel spend continues"
    changed = [k for k in fa if k in fb and str(fa[k]) != str(fb[k]) and not k.startswith(("as_of", "recency"))]
    return f"Model rescored: {changed[0]} changed" if changed else "Model rescored"

def run(customer_id: str, mutations: list[Mutation], cutoff: date | None = None) -> ScenarioResponse:
    t0 = time.perf_counter()
    cutoff = cutoff or date.fromisoformat(yaml.safe_load(open("config/decisions.yaml"))["cutoff_date"])
    factors = load_factors()
    rows = load_customer_rows(customer_id)
    fb, before = run_on_rows(rows, cutoff, factors)
    fa, after = run_on_rows(apply_mutations(rows, mutations, cutoff), cutoff, factors)

    diff = []
    for pid in before:
        b, a = before[pid], after[pid]
        for field, vb, va in (("status", b.status.value, a.status.value),
                              ("eligibility", b.eligibility.result.value, a.eligibility.result.value),
                              ("impact_status", b.impact.status.value, a.impact.status.value)):
            if vb != va:
                diff.append(DiffRow(product=ProductId(pid), field=field, from_=vb, to=va,
                                    cause=_cause(pid, b, a, fb, fa)))
    return ScenarioResponse(before=_snapshot(before), after=_snapshot(after), diff=diff,
                            invariance_ok=True,
                            elapsed_ms=int((time.perf_counter() - t0) * 1000))
