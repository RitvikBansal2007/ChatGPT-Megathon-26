"""Transaction API endpoints using the repository layer and customer ownership enforcement."""

import io
import uuid
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from backend import repository
from backend.api.dependencies import AuthenticatedUser, get_current_user, get_db
from backend.api.schemas import (
    CSVImportResponse,
    TransactionCreate,
    TransactionListResponse,
    TransactionResponse,
)

router = APIRouter(prefix="/api/v1/transactions", tags=["transactions"])

MAX_CSV_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB maximum CSV upload size


@router.post(
    "",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new transaction",
)
def create_transaction_endpoint(
    payload: TransactionCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    conn=Depends(get_db),
):
    """Create a new transaction strictly scoped to the verified authenticated user."""
    # Ensure user record exists in database to satisfy foreign-key constraint
    if not repository.get_user(conn, current_user.user_id):
        repository.create_user(conn, user_id=current_user.user_id, role=current_user.role)

    t_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"
    try:
        tx = repository.create_transaction(
            conn=conn,
            transaction_id=t_id,
            user_id=current_user.user_id,  # Ownership strictly enforced from verified identity
            date=payload.date,
            description=payload.description,
            amount=payload.amount,
            currency=payload.currency,
            debit_credit=payload.debit_credit,
            category=payload.category,
        )
        return tx
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get(
    "",
    response_model=TransactionListResponse,
    summary="List transactions for the authenticated user",
)
def list_transactions_endpoint(
    current_user: AuthenticatedUser = Depends(get_current_user),
    conn=Depends(get_db),
):
    """Retrieve all transactions owned by the authenticated user."""
    txs = repository.get_transactions_by_user(conn, user_id=current_user.user_id)
    return {"transactions": txs, "count": len(txs)}


@router.get(
    "/{transaction_id}",
    response_model=TransactionResponse,
    summary="Retrieve a specific transaction",
)
def get_transaction_endpoint(
    transaction_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    conn=Depends(get_db),
):
    """Retrieve a single transaction. Returns 404 if not found or owned by another user."""
    tx = repository.get_transaction(conn, transaction_id)
    # Deny-by-default: return 404 so we do not disclose the existence of another customer's record
    if tx is None or tx["user_id"] != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )
    return tx


@router.post(
    "/import",
    response_model=CSVImportResponse,
    summary="Atomically import transactions from a simple 3‑column CSV file",
)
async def import_transactions_csv_endpoint(
    file: UploadFile = File(...),
    currency: Optional[str] = Form(None),
    current_user: AuthenticatedUser = Depends(get_current_user),
    conn=Depends(get_db),
):
    """Import CSV transactions atomically for the authenticated customer.
    
    Enforces a strict 5 MB file size limit and rolls back completely if any row fails validation.
    """
    # Ensure user record exists
    if not repository.get_user(conn, current_user.user_id):
        repository.create_user(conn, user_id=current_user.user_id, role=current_user.role)

    content = await file.read(MAX_CSV_SIZE_BYTES + 1)
    if len(content) > MAX_CSV_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Uploaded file exceeds maximum limit of {MAX_CSV_SIZE_BYTES // (1024*1024)} MB",
        )

    try:
        csv_text = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded CSV must be valid UTF-8 encoded text",
        )

    b_id = f"import_{uuid.uuid4().hex[:8]}"
    csv_stream = io.StringIO(csv_text)

    try:
        count = repository.import_simple_csv(
            conn=conn,
            csv_source=csv_stream,
            user_id=current_user.user_id,  # Scoped strictly to authenticated user
            currency=currency,
            batch_id=b_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"CSV validation failed: {e}",
        )
    return {"imported_count": count, "import_batch_id": b_id}


@router.post(
    "/import/raw",
    response_model=CSVImportResponse,
    summary="Import raw 7‑column CSV dataset (transaction_id, customer_id, date, merchant_description, amount, debit_credit, true_category)",
)
async def import_raw_csv_endpoint(
    current_user: AuthenticatedUser = Depends(get_current_user),
    conn=Depends(get_db),
):
    """Import the server‑side raw dataset CSV.

    This endpoint is protected; only an authenticated request can trigger the import.
    The CSV is read from the repository's data directory and imported atomically.
    """
    # Determine path to the raw CSV relative to the project root
    raw_csv_path = Path(__file__).resolve().parents[4] / "data" / "raw" / "transactions.csv"
    if not raw_csv_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Raw transactions CSV not found on server.",
        )
    batch_id = f"raw_{uuid.uuid4().hex[:8]}"
    try:
        count = repository.import_raw_dataset_csv(
            conn=conn,
            csv_source=str(raw_csv_path),
            batch_id=batch_id,
        )
        return {"imported_count": count, "import_batch_id": batch_id}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"CSV validation failed: {e}",
        )

