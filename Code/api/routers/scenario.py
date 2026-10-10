from fastapi import APIRouter, Depends, HTTPException

from api.deps import customer_key_for, require_role
from greenproof.contracts import ScenarioRequest, ScenarioResponse
from greenproof.db import repo
from greenproof.scenarios.run import run
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
    hit = json.loads(f.read_text()).get(f"{req.customer_id}|{req.mutations[0].value}")
    return ScenarioResponse.model_validate_json(json.dumps(hit)) if hit else None

@router.post("/scenario", response_model=ScenarioResponse, response_model_by_alias=True)
def post_scenario(req: ScenarioRequest, principal=Depends(require_role("EVALUATOR", "RELATIONSHIP_MANAGER"))):
    persona_ids = {f"CUST-{i:04d}" for i in range(1, 9)}
    if principal.role == "EVALUATOR" and req.customer_id not in persona_ids:
        raise HTTPException(status_code=403, detail="Forbidden")
    resp = _cached(req) or run(req.customer_id, req.mutations)
    repo.log_scenario_run(customer_key_for(req.customer_id), [m.value for m in req.mutations],
                          {p.value: s.status.value for p, s in resp.before.items()},
                          {p.value: s.status.value for p, s in resp.after.items()}, resp.elapsed_ms)
    return resp
