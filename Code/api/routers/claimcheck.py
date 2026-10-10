from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field

from api.deps import customer_key_for, require_role
from greendash.db import audit, repo
from greendash.llm.claimcheck import check
from api.services import load_customer_packs

router = APIRouter(prefix="/api", tags=["claimcheck"])

class SentenceIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(max_length=300)
    fields: list[str] = Field(default_factory=list, max_length=10)

class ClaimCheckIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    customer_id: str = Field(pattern=r"^CUST-\d{4}$")
    opportunity_id: str = Field(pattern=r"^GP0[1-4]$")
    sentences: list[SentenceIn] = Field(max_length=5)

@router.post("/claimcheck")
def post_claimcheck(body: ClaimCheckIn, principal=Depends(require_role("EVALUATOR", "RELATIONSHIP_MANAGER", "SERVICE"))):
    key = customer_key_for(body.customer_id)
    pack = next(o for o in load_customer_packs(key, body.customer_id).opportunities
                if o.opportunity_id.value == body.opportunity_id)
    result = check(pack, [s.model_dump() for s in body.sentences])
    violated = [v["rule"] for s in result.get("sentences", []) for v in s.get("violations", [])]
    audit.append(key, body.opportunity_id, result.get("verdict", "PASS"), violated, "red_team")
    result["blocked_total"] = repo.claims_blocked_total()
    return result
