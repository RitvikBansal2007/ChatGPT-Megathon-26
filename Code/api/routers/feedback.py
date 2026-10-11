from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel, ConfigDict, Field

from api.deps import db_key_for, require_role, require_subject
from greendash.db import repo
from greendash.security.authz import FeedbackEncryptionUnavailable, encrypt_feedback

CustomerId = Annotated[str, Path(pattern=r"^[A-Za-z0-9_-]{1,64}$")]

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
def post_feedback(customer_id: CustomerId, body: FeedbackIn, principal=Depends(require_role("CUSTOMER", "RELATIONSHIP_MANAGER"))):
    require_subject(principal, customer_id)
    try:
        enc = encrypt_feedback(body.note) if body.note else None
    except FeedbackEncryptionUnavailable:
        # Never store a free-text note unencrypted.
        raise HTTPException(status_code=503, detail="Feedback notes are temporarily unavailable")
    repo.add_feedback(db_key_for(customer_id), body.opportunity_id, body.kind, enc)
    return {"status": "recorded"}

@router.post("/opt-out")
def post_optout(customer_id: CustomerId, body: OptOutIn, principal=Depends(require_role("CUSTOMER", "RELATIONSHIP_MANAGER"))):
    require_subject(principal, customer_id)
    repo.set_optout(db_key_for(customer_id), body.opted_out)
    return {"status": "recorded", "opted_out": repo.is_opted_out(db_key_for(customer_id))}
