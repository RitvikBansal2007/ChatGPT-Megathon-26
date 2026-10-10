from typing import Literal
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict

from config.settings import settings
from greendash.security.authz import issue_token

router = APIRouter(prefix="/api/auth", tags=["auth"])

class DemoTokenIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: Literal["CUSTOMER", "RELATIONSHIP_MANAGER", "PORTFOLIO_ANALYST", "AUDITOR", "EVALUATOR"]
    customer_id: str | None = None

@router.post("/demo-token")
def demo_token(body: DemoTokenIn):
    if settings.ENV != "demo":
        raise HTTPException(status_code=404)
    return {"access_token": issue_token(body.role, body.customer_id), "token_type": "bearer", "expires_in": 900}
