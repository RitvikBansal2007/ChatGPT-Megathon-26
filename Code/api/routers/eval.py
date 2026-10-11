import json
from pathlib import Path
from fastapi import APIRouter, Depends
from api.deps import require_role

router = APIRouter(prefix="/api/eval", tags=["eval"])

@router.get("/summary")
def eval_summary(principal=Depends(require_role("EVALUATOR", "PORTFOLIO_ANALYST", "AUDITOR", "RELATIONSHIP_MANAGER"))):
    for p in (Path("out/eval_summary.json"), Path("fixtures/eval_summary.json"), Path("fixtures/eval.json")):
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
    return {"status": "not generated yet"}
