import json
from pathlib import Path
from fastapi import APIRouter, Depends
from api.deps import require_role

router = APIRouter(prefix="/api/eval", tags=["eval"])

@router.get("/summary")
def eval_summary(principal=Depends(require_role("EVALUATOR", "PORTFOLIO_ANALYST", "AUDITOR", "RELATIONSHIP_MANAGER"))):
    p = Path("out/eval_summary.json")
    return json.loads(p.read_text()) if p.exists() else {"status": "not generated yet"}
