from fastapi import APIRouter, Depends

from api.deps import customer_key_for, require_role, require_subject
from api.services import load_customer_packs
from greendash.contracts import CustomerPacks

router = APIRouter(prefix="/api/customers/{customer_id}", tags=["opportunities"])

@router.get("/opportunities", response_model=CustomerPacks, response_model_by_alias=True)
def get_opportunities(customer_id: str, principal=Depends(require_role("CUSTOMER", "RELATIONSHIP_MANAGER", "EVALUATOR"))):
    require_subject(principal, customer_id)
    return load_customer_packs(customer_key_for(customer_id), customer_id)
