from fastapi import APIRouter, Depends, Request

from api.deps import require_role
from api.routers.portfolio import rows, suppress
from greendash.db import audit, repo

router = APIRouter(prefix="/api/governance", tags=["governance"])

@router.get("")
@router.get("/")
@router.get("/audit")
def governance(request: Request, principal=Depends(require_role("AUDITOR", "EVALUATOR"))):
    ok, bad = audit.verify_chain()
    d = rows()
    abstain_rate = (d["status"] == "ABSTAIN").groupby(d["product"]).mean().round(4).to_dict()
    seg = (d.assign(rec=d["status"] == "RECOMMEND")
             .groupby(["product", "income_band"]).agg(customers=("customer_key", "nunique"), rec_rate=("rec", "mean"))
             .reset_index())
    return {"audit_chain_ok": ok, "first_bad_row": bad, "claims_blocked": repo.claims_blocked_total(),
            "audit_summary": repo.audit_summary(), "abstention_rate_by_product": abstain_rate,
            "recommend_rate_by_income_band": suppress(seg).to_dict("records"),
            "not_used_as_model_inputs": ["age", "income_band", "fine-grained postcode"]}
