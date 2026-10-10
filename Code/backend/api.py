# FastAPI application exposing transaction endpoints

"""FastAPI API layer for GreenProof backend.

Provides a GET /transactions endpoint that optionally filters transactions by
`user_id`. The endpoint uses the repository layer which already implements
validation, atomic CSV imports, and foreign‑key enforcement.

CORS settings are drawn from the validated `Settings` model defined in
`backend/config.py`. In production the settings enforce safe defaults, while
in development a permissive default is applied.
"""

from fastapi import FastAPI, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional

from backend.config import get_settings, Settings
from backend.db import db_session
from backend import repository

# ---------------------------------------------------------------------------
# Pydantic model for transaction responses
# ---------------------------------------------------------------------------

class Transaction(BaseModel):
    transaction_id: str = Field(..., description="Unique identifier of the transaction")
    user_id: str = Field(..., description="Identifier of the user owning the transaction")
    date: str = Field(..., description="Transaction date in ISO YYYY‑MM‑DD format")
    description: str = Field(..., description="Human‑readable description of the transaction")
    amount: str = Field(..., description="Exact monetary amount as stored in the DB (string)")
    currency: Optional[str] = Field(None, description="Currency code, e.g. 'EUR', or null")
    debit_credit: Optional[str] = Field(
        None, description="Either 'debit', 'credit', or null if unspecified"
    )
    category: Optional[str] = Field(None, description="Canonical category name or null")
    import_batch_id: Optional[str] = Field(
        None, description="Batch identifier when the transaction originates from a CSV import"
    )

    class Config:
        orm_mode = True

# ---------------------------------------------------------------------------
# Dependency that supplies a SQLite connection per request
# ---------------------------------------------------------------------------

def get_db(settings: Settings = Depends(get_settings)):
    """Yield a database connection using the configured DB path.

    The `db_session` context manager handles commit/rollback and closes the
    connection after the request.
    """
    with db_session(settings.GREENPROOF_DB_PATH) as conn:
        yield conn

# ---------------------------------------------------------------------------
# FastAPI app creation with CORS configuration from settings
# ---------------------------------------------------------------------------

def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="GreenProof API", version="0.1.0")

    # Apply CORS middleware – the Settings validator guarantees origins are
    # well‑formed URLs or the wildcard '*'. Production disallows the wildcard.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/transactions", response_model=List[Transaction])
    def list_transactions(
        user_id: Optional[str] = Query(
            None,
            description="If supplied, only transactions belonging to this user are returned",
        ),
        db=Depends(get_db),
    ):
        """Return all transactions, optionally filtered by `user_id`."""
        if user_id:
            return repository.get_transactions_by_user(db, user_id)
        # No filter – return everything ordered by date descending.
        cur = db.execute(
            "SELECT * FROM transactions ORDER BY date DESC, transaction_id ASC"
        )
        return [dict(row) for row in cur.fetchall()]

    return app

# Export a module‑level app instance for `uvicorn`.
app = create_app()
