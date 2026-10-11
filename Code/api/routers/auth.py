from typing import Literal
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, ConfigDict, Field

from config.settings import settings
from greendash.security.authz import issue_token
from greendash.db import repo
from api.deps import get_principal, Principal

router = APIRouter(prefix="/api/auth", tags=["auth"])

class LoginIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=100)

class DemoTokenIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: Literal["CUSTOMER", "RELATIONSHIP_MANAGER", "PORTFOLIO_ANALYST", "AUDITOR", "EVALUATOR"]
    customer_id: str | None = None

@router.post("/login")
def login(body: LoginIn):
    user = repo.authenticate_user(body.username, body.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username/email or password")
    
    cid = user["user_key"] if user["role"] == "CUSTOMER" else None
    token = issue_token(
        role=user["role"],
        customer_id=cid,
        sub=user["user_key"],
        display_name=user.get("display_name"),
        expires_minutes=120,
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": 7200,
        "user": {
            "user_key": user["user_key"],
            "role": user["role"],
            "email": user.get("email"),
            "display_name": user.get("display_name"),
            "customer_id": cid,
        },
    }

@router.post("/demo-token")
def demo_token(body: DemoTokenIn):
    user = repo.get_user(body.customer_id or body.role.lower())
    dname = user["display_name"] if user else None
    token = issue_token(
        role=body.role,
        customer_id=body.customer_id,
        sub=body.customer_id or f"{body.role.lower()}_user",
        display_name=dname,
        expires_minutes=120,
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": 7200,
        "role": body.role,
        "customer_id": body.customer_id,
        "display_name": dname,
    }

@router.get("/me")
def me(principal: Principal = Depends(get_principal)):
    return {
        "sub": principal.sub,
        "role": principal.role,
        "customer_id": principal.customer_id,
        "display_name": principal.display_name,
    }

@router.get("/users")
def get_users():
    return {"users": repo.list_users()}

