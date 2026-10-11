from typing import Literal
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field, model_validator

from config.settings import settings
from greendash.security.authz import issue_token

router = APIRouter(prefix="/api/auth", tags=["auth"])

class DemoTokenIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: Literal["CUSTOMER", "RELATIONSHIP_MANAGER", "PORTFOLIO_ANALYST", "AUDITOR", "EVALUATOR"]
    customer_id: str | None = Field(default=None, pattern=r"^CUST-\d{4}$")

    @model_validator(mode="after")
    def _customer_requires_subject(self):
        if self.role == "CUSTOMER" and not self.customer_id:
            raise ValueError("CUSTOMER tokens require a customer_id")
        return self

@router.post("/demo-token")
def demo_token(body: DemoTokenIn):
    if settings.ENV != "demo":
        raise HTTPException(status_code=404)
    return {"access_token": issue_token(body.role, body.customer_id), "token_type": "bearer", "expires_in": 900}
