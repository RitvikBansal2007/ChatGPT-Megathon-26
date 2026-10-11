from typing import Callable, Any
from fastapi import HTTPException, Depends
from pydantic import BaseModel

class Principal(BaseModel):
    role: str
    sub: str = "demo"

def get_principal() -> Principal:
    return Principal(role="CUSTOMER")

def require_role(*roles: str) -> Callable:
    def _require_role(principal: Any = Depends(get_principal)):
        if roles and principal.role not in roles:
            raise HTTPException(status_code=403, detail="Forbidden")
        return principal
    return _require_role

def require_subject(principal: Any, customer_id: str):
    pass

def customer_key_for(customer_id: str) -> str:
    # return the key to be used to fetch from DB
    return customer_id

