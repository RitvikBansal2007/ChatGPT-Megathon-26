import json
from datetime import date
from pathlib import Path

import yaml

from greendash.carbon.engine import load_factors
from greendash.contracts import Mutation
from greendash.scenarios.mutations import apply_mutations
from greendash.scenarios.run import load_customer_rows, run_on_rows

CUT = date(2026, 6, 30)
CASES = Path(__file__).with_name("cases.yaml")

def packs_for(case: dict) -> dict:
    rows = load_customer_rows(case["persona"])
    rows = apply_mutations(rows, [Mutation(m) for m in case.get("mutations", [])], CUT)
    _, packs = run_on_rows(rows, CUT, load_factors())
    return packs

def check(case: dict) -> list[str]:
    packs, fails = packs_for(case), []
    for pid, exp in case["expected"].items():
        o = packs[pid]
        if "status" in exp and o.status.value != exp["status"]:
            fails.append(f"{pid}: status {o.status.value} != {exp['status']}")
        if "not_status" in exp and o.status.value == exp["not_status"]:
            fails.append(f"{pid}: status must not be {exp['not_status']}")
        if "rule" in exp and exp["rule"] not in o.eligibility.rules_fired:
            fails.append(f"{pid}: rule {exp['rule']} not in {o.eligibility.rules_fired}")
        if "impact_status" in exp and o.impact.status.value != exp["impact_status"]:
            fails.append(f"{pid}: impact {o.impact.status.value} != {exp['impact_status']}")
        if "recency_max" in exp and o.confidence.recency > exp["recency_max"]:
            fails.append(f"{pid}: recency {o.confidence.recency:.2f} > {exp['recency_max']}")
    return fails

def run_all(write: bool = True) -> list[dict]:
    cases = yaml.safe_load(CASES.read_text())
    results = []
    for c in cases:
        fails = check(c)
        results.append({"id": c["id"], "tag": c["tag"], "persona": c["persona"],
                        "mutations": c.get("mutations", []), "passed": not fails, "failures": fails})
    if write:
        Path("out").mkdir(exist_ok=True)
        Path("out/scenario_results.json").write_text(json.dumps(results, indent=1, sort_keys=True))
    return results
