"""Build the 130 perturbed Evidence-Pack-shaped fixtures for the LLM explainer eval.

Deterministic: every random choice derives from numpy.random.default_rng(42).
Output: eval/llm_eval/packs.json
Plan: 8 personas x 4 products = 32 baseline packs, plus 98 perturbed packs
(5 perturbation types, each at least 15 times) = exactly 130.
"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from greendash.carbon.engine import estimate, load_factors  # noqa: E402
from greendash.carbon import units  # noqa: E402
from security.privacy import llm_payload  # noqa: E402

OUT = Path(__file__).resolve().parent / "packs.json"
PRODUCTS = ["GP01", "GP02", "GP03", "GP04"]
PERTURBATIONS = ["missing_field", "conflict", "ruled_out", "abstain", "stale"]
TOTAL = 130
BASELINE = 32

# Designed outcomes per persona and product (PRD Appendix A). Where the PRD is
# silent the default is SOFT_SURFACE.
PERSONAS = {
    "CUST-0001": dict(home_owner=True, has_car=True, fuel_type="petrol", annual_mileage=11500,
                      gas_kwh=11500, roof_suitability="suitable", paper_statements_12m=12),
    "CUST-0002": dict(home_owner=True, has_car=True, fuel_type="bev", annual_mileage=8000,
                      gas_kwh=None, roof_suitability="suitable", paper_statements_12m=12),
    "CUST-0003": dict(home_owner=True, has_car=True, fuel_type="bev", annual_mileage=6000,
                      gas_kwh=9000, roof_suitability="suitable", paper_statements_12m=0,
                      existing_solar=True),
    "CUST-0004": dict(home_owner=True, has_car=True, fuel_type="petrol", annual_mileage=None,
                      gas_kwh=None, roof_suitability="unknown", paper_statements_12m=12),
    "CUST-0005": dict(home_owner=True, has_car=False, fuel_type=None, annual_mileage=None,
                      gas_kwh=16000, roof_suitability="suitable", paper_statements_12m=12),
    "CUST-0006": dict(home_owner=True, has_car=True, fuel_type="petrol", annual_mileage=9000,
                      gas_kwh=11000, roof_suitability="unknown", paper_statements_12m=12),
    "CUST-0007": dict(home_owner=False, has_car=False, fuel_type=None, annual_mileage=None,
                      gas_kwh=6000, roof_suitability="unknown", paper_statements_12m=12),
    "CUST-0008": dict(home_owner=True, has_car=True, fuel_type="petrol", annual_mileage=7000,
                      gas_kwh=9000, roof_suitability="suitable", paper_statements_12m=12,
                      accessibility_paper_need=True),
}

DESIGNED = {
    ("CUST-0001", "GP01"): "RECOMMEND", ("CUST-0001", "GP04"): "RECOMMEND",
    ("CUST-0002", "GP01"): "REVIEW", ("CUST-0002", "GP02"): "ABSTAIN",
    ("CUST-0003", "GP01"): "RULED_OUT", ("CUST-0003", "GP03"): "RULED_OUT",
    ("CUST-0003", "GP04"): "RULED_OUT",
    ("CUST-0004", "GP01"): "ABSTAIN", ("CUST-0004", "GP02"): "ABSTAIN",
    ("CUST-0004", "GP03"): "ABSTAIN", ("CUST-0004", "GP04"): "RECOMMEND",
    ("CUST-0005", "GP02"): "RECOMMEND",
    ("CUST-0006", "GP03"): "ABSTAIN",
    ("CUST-0007", "GP02"): "RULED_OUT", ("CUST-0007", "GP03"): "RULED_OUT",
    ("CUST-0007", "GP04"): "RECOMMEND",
    ("CUST-0008", "GP04"): "RULED_OUT",
}

METRIC_FAMILY = {"GP01": "co2e", "GP02": "kwh", "GP03": "kwh", "GP04": "paper"}
REQUIRED_FIELD = {"GP01": "annual_mileage", "GP02": "gas_kwh", "GP03": "roof_suitability",
                  "GP04": "paper_statements_12m"}


def impact_strings(est, product):
    """Display strings come ONLY from units.py (LLM-safe regex)."""
    if est.status != "ESTIMATED":
        return {}
    if product == "GP04":
        return {"central": units.fmt_sheets(est.central)}
    if product in ("GP01", "GP02", "GP03"):
        return {"central": units.fmt_kg(est.central),
                "range": units.fmt_range_kg(est.low, est.high)}
    return {}


def make_pack(pack_id, cust, product, features, expected, perturbation, factors):
    est = estimate(features, product, factors)
    return {
        "pack_id": pack_id,
        "customer_id": cust,
        "product_id": product,
        "perturbation": perturbation,
        "expected_status": expected,
        "metric_family": METRIC_FAMILY[product],
        "carbon": {
            "status": est.status,
            "formula": est.formula,
            "missing_inputs": est.missing_inputs or [],
            "display": impact_strings(est, product),
        },
        # Only allowlisted, non-identifying fields (security.privacy.llm_payload).
        "evidence_features": dict(sorted(llm_payload(
            {k: v for k, v in features.items() if v is not None}).items())),
        "flags": sorted(k.lstrip("_") for k in features if k.startswith("_") and k != "_freshness"),
        "data_freshness": features.get("_freshness", "fresh"),
    }


def apply(perturbation, product, features, expected):
    """Return (features, expected_status) after the perturbation."""
    f = dict(features)
    if perturbation == "missing_field":
        f[REQUIRED_FIELD[product]] = None
        return f, "ABSTAIN"
    if perturbation == "conflict":
        f["_conflict"] = True
        return f, "REVIEW"
    if perturbation == "ruled_out":
        f["_not_eligible"] = True
        return f, "RULED_OUT"
    if perturbation == "abstain":
        f[REQUIRED_FIELD[product]] = None
        f["_critical_missing"] = True
        return f, "ABSTAIN"
    if perturbation == "stale":
        f["_freshness"] = "stale"
        return f, "ABSTAIN"
    raise ValueError(perturbation)


def build():
    rng = np.random.default_rng(42)
    factors = load_factors()
    packs = []
    base = []
    for cust, feats in PERSONAS.items():
        for product in PRODUCTS:
            expected = DESIGNED.get((cust, product), "SOFT_SURFACE")
            base.append((cust, product, feats, expected))
            packs.append(make_pack(f"P{len(packs) + 1:03d}", cust, product, feats,
                                   expected, "none", factors))
    assert len(packs) == BASELINE

    n_perturbed = TOTAL - BASELINE  # 98
    # Guarantee >= 15 per type first (75), then fill the remaining 23 randomly.
    plan = [p for p in PERTURBATIONS for _ in range(15)]
    extra = rng.choice(PERTURBATIONS, size=n_perturbed - len(plan))
    plan += [str(e) for e in extra]
    plan = [plan[i] for i in rng.permutation(len(plan))]
    for pert in plan:
        cust, product, feats, expected = base[int(rng.integers(0, len(base)))]
        pf, pe = apply(pert, product, feats, expected)
        packs.append(make_pack(f"P{len(packs) + 1:03d}", cust, product, pf, pe, pert, factors))

    assert len(packs) == TOTAL
    counts = {p: sum(1 for k in packs if k["perturbation"] == p) for p in PERTURBATIONS}
    assert all(c >= 15 for c in counts.values()), counts
    with open(OUT, "w") as fh:
        json.dump({"seed": 42, "total": len(packs), "perturbation_counts": counts,
                   "packs": packs}, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"wrote {OUT} ({len(packs)} packs) {counts}")


if __name__ == "__main__":
    build()
