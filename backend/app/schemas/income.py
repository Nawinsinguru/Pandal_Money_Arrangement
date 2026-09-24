from datetime import date, time
from decimal import Decimal

from pydantic import BaseModel, Field


class IncomeCreate(BaseModel):
    category: str = Field(
        pattern="^(sponsor|chanda|committee_member|other)$"
    )

    source_name: str = Field(
        min_length=2,
        max_length=200,
    )

    amount: Decimal = Field(
        gt=0,
        max_digits=12,
        decimal_places=2,
    )

    payment_method: str = Field(
        pattern="^(cash|upi|bank_transfer|cheque|other)$"
    )

    transaction_reference: str | None = Field(
        default=None,
        max_length=200,
    )

    transaction_date: date

    transaction_time: time

    proof_url: str = Field(
        min_length=1,
        max_length=500,
    )

    received_by: str

    notes: str | None = Field(
        default=None,
        max_length=1000,
    )


class IncomeResponse(BaseModel):
    id: str
    pandal_id: str
    category: str
    source_name: str
    amount: Decimal
    payment_method: str
    transaction_reference: str | None
    transaction_date: date
    transaction_time: time
    proof_url: str
    received_by: str
    notes: str | None
    created_by: str

class IncomeUpdate(BaseModel):
    category: str | None = Field(
        default=None,
        pattern="^(sponsor|chanda|committee_member|other)$"
    )

    source_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=200
    )

    amount: Decimal | None = Field(
        default=None,
        gt=0,
        max_digits=12,
        decimal_places=2
    )

    payment_method: str | None = Field(
        default=None,
        pattern="^(cash|upi|bank_transfer|cheque|other)$"
    )

    transaction_reference: str | None = Field(
        default=None,
        max_length=200
    )

    transaction_date: date | None = None
    transaction_time: time | None = None

    proof_url: str | None = Field(
        default=None,
        min_length=1,
        max_length=500
    )

    notes: str | None = Field(
        default=None,
        max_length=1000
    )