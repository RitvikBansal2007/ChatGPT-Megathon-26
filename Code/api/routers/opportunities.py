from typing import Literal
from fastapi import APIRouter, Depends, Path, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from api.deps import customer_key_for, require_role, require_subject
from api.services import load_customer_packs
from greendash.contracts import CustomerOpportunities
from greendash.db import repo

router = APIRouter(prefix="/api/customers/{customer_id}", tags=["opportunities"])

class MemoryIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    key: str = Field(min_length=1, max_length=100)
    value: str = Field(min_length=1, max_length=500)
    category: Literal["preference", "declared_fact", "interaction", "goal", "agent_note"] = "preference"
    source: Literal["customer_declared", "rm_note", "feedback", "system_inferred"] = "customer_declared"

@router.get("/opportunities", response_model=CustomerOpportunities, response_model_by_alias=True)
def get_opportunities(
    customer_id: str = Path(pattern=r"^[A-Za-z0-9_-]{1,64}$"),
    principal=Depends(require_role("CUSTOMER", "RELATIONSHIP_MANAGER", "EVALUATOR"))
):
    require_subject(principal, customer_id)
    return load_customer_packs(customer_key_for(customer_id), customer_id)

@router.get("/memory")
def get_memory(
    customer_id: str = Path(pattern=r"^[A-Za-z0-9_-]{1,64}$"),
    principal=Depends(require_role("CUSTOMER", "RELATIONSHIP_MANAGER", "EVALUATOR"))
):
    require_subject(principal, customer_id)
    return {
        "customer_id": customer_id,
        "items": repo.get_customer_memory(customer_id)
    }

@router.post("/memory")
def add_memory(
    body: MemoryIn,
    customer_id: str = Path(pattern=r"^[A-Za-z0-9_-]{1,64}$"),
    principal=Depends(require_role("CUSTOMER", "RELATIONSHIP_MANAGER", "EVALUATOR"))
):
    require_subject(principal, customer_id)
    item = repo.add_customer_memory(
        customer_key=customer_id,
        key=body.key,
        value=body.value,
        category=body.category,
        source=body.source,
    )
    return {"status": "created", "item": item}

@router.delete("/memory/{memory_id}")
def delete_memory(
    memory_id: int,
    customer_id: str = Path(pattern=r"^[A-Za-z0-9_-]{1,64}$"),
    principal=Depends(require_role("CUSTOMER", "RELATIONSHIP_MANAGER", "EVALUATOR"))
):
    require_subject(principal, customer_id)
    success = repo.delete_customer_memory(customer_id, memory_id)
    if not success:
        raise HTTPException(status_code=404, detail="Memory item not found")
    return {"status": "deleted", "id": memory_id}

