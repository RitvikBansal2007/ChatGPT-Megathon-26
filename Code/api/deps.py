from typing import Callable, Any
from fastapi import HTTPException
from pydantic import BaseModel

class Principal(BaseModel):
    role: str

def require_role(*roles: str) -> Callable:
    def _require_role():
        return Principal(role=roles[0] if roles else "CUSTOMER")
    return _require_role

def require_subject(principal: Principal, customer_id: str):
    pass

def customer_key_for(customer_id: str) -> str:
    # return the key to be used to fetch from DB
    return customer_id

