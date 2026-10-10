from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field

from api.deps import customer_key_for, require_role, require_subject
from greenproof.db import repo
from greenproof.security.authz import encrypt_feedback

router = APIRouter(prefix="/api/customers/{customer_id}", tags=["feedback"])

class FeedbackIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    opportunity_id: str = Field(pattern=r"^GP0[1-4]$")
    kind: Literal["NOT_RELEVANT", "THIS_IS_WRONG", "REMIND_LATER"]
    note: str | None = Field(default=None, max_length=500)

class OptOutIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    opted_out: bool

@router.post("/feedback")
def post_feedback(customer_id: str, body: FeedbackIn, principal=Depends(require_role("CUSTOMER", "RELATIONSHIP_MANAGER"))):
    require_subject(principal, customer_id)
    enc = encrypt_feedback(body.note) if body.note else None
    repo.add_feedback(customer_key_for(customer_id), body.opportunity_id, body.kind, enc)
    return {"status": "recorded"}

@router.post("/opt-out")
def post_optout(customer_id: str, body: OptOutIn, principal=Depends(require_role("CUSTOMER", "RELATIONSHIP_MANAGER"))):
    require_subject(principal, customer_id)
    repo.set_optout(customer_key_for(customer_id), body.opted_out)
    return {"status": "recorded", "opted_out": repo.is_opted_out(customer_key_for(customer_id))}
