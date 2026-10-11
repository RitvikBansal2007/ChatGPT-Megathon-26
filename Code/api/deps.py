from typing import Callable, Any
from fastapi import HTTPException, Depends, Header
from pydantic import BaseModel
from greendash.security.authz import verify_token

class Principal(BaseModel):
    role: str
    sub: str = "demo"
    customer_id: str | None = None
    display_name: str | None = None

def get_principal(authorization: str | None = Header(default=None)) -> Principal:
    if not authorization:
        raise HTTPException(status_code=401, detail="Authentication token required")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization header: must be Bearer <token>")
    token = parts[1]
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    role = payload.get("role", "CUSTOMER")
    sub = payload.get("sub", payload.get("customer_id", "demo"))
    cid = payload.get("customer_id")
    name = payload.get("display_name")
    return Principal(role=role, sub=sub, customer_id=cid, display_name=name)

def require_role(*roles: str) -> Callable:
    def _require_role(principal: Any = Depends(get_principal)):
        if roles and principal.role not in roles:
            raise HTTPException(status_code=403, detail=f"Forbidden for role {principal.role}")
        return principal
    return _require_role

def require_subject(principal: Any, customer_id: str):
    if principal.role == "CUSTOMER":
        effective_cid = getattr(principal, "customer_id", None) or getattr(principal, "sub", None)
        if effective_cid and effective_cid != customer_id:
            raise HTTPException(status_code=403, detail="Customers cannot access records of another customer")

def customer_key_for(customer_id: str) -> str:
    # return the key to be used to fetch from DB
    return customer_id


