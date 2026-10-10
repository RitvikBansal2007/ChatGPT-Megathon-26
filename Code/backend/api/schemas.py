"""Pydantic request and response schemas for the GreenProof API."""

import datetime
import re
from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.repository import CANONICAL_CATEGORIES, DECIMAL_REGEX, DATE_REGEX


class TransactionCreate(BaseModel):
    """Payload for creating a new transaction."""

    model_config = ConfigDict(extra="forbid")

    date: str = Field(..., description="Transaction date in YYYY-MM-DD format")
    description: str = Field(..., min_length=1, max_length=255, description="Merchant description")
    amount: str = Field(..., description="Exact monetary amount as a decimal string")
    currency: Optional[str] = Field(default=None, description="ISO 4217 currency code if known")
    debit_credit: Optional[Literal["debit", "credit"]] = Field(
        default=None, description="Whether transaction is a debit or credit"
    )
    category: Optional[str] = Field(
        default=None, description="One of the 8 canonical categories or None"
    )

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        d = v.strip()
        if not DATE_REGEX.match(d):
            raise ValueError(f"Invalid date format '{v}', expected YYYY-MM-DD")
        try:
            datetime.date.fromisoformat(d)
        except ValueError as e:
            raise ValueError(f"Invalid calendar date '{v}': {e}") from e
        return d

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("description cannot be empty or whitespace-only")
        return cleaned

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: str) -> str:
        cleaned = str(v).strip()
        if not DECIMAL_REGEX.match(cleaned):
            raise ValueError(f"Invalid monetary amount format: '{v}'")
        return cleaned

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return None
        cleaned = v.strip()
        if cleaned not in CANONICAL_CATEGORIES:
            raise ValueError(
                f"Category '{v}' is not one of the canonical categories: {sorted(CANONICAL_CATEGORIES)}"
            )
        return cleaned

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return None
        cleaned = v.strip().upper()
        if not re.match(r"^[A-Z]{3}$", cleaned):
            raise ValueError(f"Invalid currency code '{v}', expected 3-letter ISO code")
        return cleaned


class TransactionResponse(BaseModel):
    """Response representation of a transaction."""

    model_config = ConfigDict(from_attributes=True)

    transaction_id: str
    user_id: str
    date: str
    description: str
    amount: str
    currency: Optional[str] = None
    debit_credit: Optional[str] = None
    category: Optional[str] = None
    import_batch_id: Optional[str] = None
    created_at: str


class TransactionListResponse(BaseModel):
    """List response for a customer's transactions."""

    transactions: List[TransactionResponse]
    count: int


class CSVImportResponse(BaseModel):
    """Response returned upon successful atomic CSV ingestion."""

    imported_count: int
    import_batch_id: str


class HealthResponse(BaseModel):
    """Response returned by the health check endpoint."""

    status: str
    environment: str
