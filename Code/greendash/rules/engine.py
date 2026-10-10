from functools import lru_cache
from pathlib import Path
import math

import yaml

from greenproof.contracts import EligibilityResult, EligibilityVerdict

CONFIG = Path(__file__).resolve().parents[2] / "config" / "products.yaml"

@lru_cache(maxsize=1)
def _load() -> dict:
    return yaml.safe_load(CONFIG.read_text())

def _missing(v) -> bool:
    return v is None or (isinstance(v, float) and math.isnan(v))

def _test(cond: dict, features: dict) -> bool:
    v = features.get(cond["field"])
    op = cond["op"]
    if op == "is_null":
        return _missing(v)
    if op == "not_null":
        return not _missing(v)
    if _missing(v):
        return False
    t = cond.get("value")
    return {
        "eq": lambda: v == t, "ne": lambda: v != t,
        "gt": lambda: v > t, "ge": lambda: v >= t,
        "lt": lambda: v < t, "le": lambda: v <= t,
        "in": lambda: v in t,
    }[op]()

def _fires(when: dict, features: dict) -> bool:
    if "all" in when:
        return all(_test(c, features) for c in when["all"])
    if "any" in when:
        return any(_test(c, features) for c in when["any"])
    raise ValueError("rule needs 'all' or 'any'")

def evaluate(features: dict, product_id: str) -> EligibilityVerdict:
    cfg = _load()
    rules = cfg["products"][product_id]["rules"]
    fired = [r for r in rules if _fires(r["when"], features)]
    if any(r["result"] == "NOT_ELIGIBLE" for r in fired):
        result = EligibilityResult.NOT_ELIGIBLE
    elif any(r["result"] == "NEEDS_VERIFICATION" for r in fired):
        result = EligibilityResult.NEEDS_VERIFICATION
    else:
        result = EligibilityResult.ELIGIBLE
    decisive = [r for r in fired if r["result"] == result.value] or []
    return EligibilityVerdict(
        result=result,
        rules_fired=[r["id"] for r in decisive],
        rules_version=cfg["rules_version"],
        plain_reasons=[r["plain"] for r in decisive],
    )
