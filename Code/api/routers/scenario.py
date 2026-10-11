from fastapi import APIRouter, Depends, HTTPException

from api.deps import db_key_for, require_role
from greendash.contracts import ScenarioRequest, ScenarioResponse
from greendash.db import repo
from greendash.scenarios.run import run
import json
from pathlib import Path
from config.settings import settings

router = APIRouter(prefix="/api", tags=["scenario"])

def _cached(req: ScenarioRequest) -> ScenarioResponse | None:
    if settings.DEMO_MODE != "cached" or len(req.mutations) != 1:
        return None
    f = Path("out/cache/scenarios.json")
    if not f.exists():
        return None
    hit = json.loads(f.read_text(encoding="utf-8")).get(f"{req.customer_id}|{req.mutations[0].value}")
    return ScenarioResponse.model_validate_json(json.dumps(hit)) if hit else None

@router.post("/scenario", response_model=ScenarioResponse, response_model_by_alias=True)
def post_scenario(req: ScenarioRequest, principal=Depends(require_role("EVALUATOR", "RELATIONSHIP_MANAGER"))):
    persona_ids = {f"CUST-{i:04d}" for i in range(1, 9)}
    if principal.role == "EVALUATOR" and req.customer_id not in persona_ids:
        raise HTTPException(status_code=403, detail="Forbidden")
    try:
        resp = _cached(req) or run(req.customer_id, req.mutations)
    except FileNotFoundError:
        raise HTTPException(status_code=503, detail="Scenario data not generated yet")
    repo.log_scenario_run(db_key_for(req.customer_id), [m.value for m in req.mutations],
                          {p.value: s.status.value for p, s in resp.before.items()},
                          {p.value: s.status.value for p, s in resp.after.items()}, resp.elapsed_ms)
    return resp
