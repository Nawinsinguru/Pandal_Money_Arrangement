from datetime import date, time
from decimal import Decimal

from pydantic import BaseModel, Field


class CashExpenseCreate(BaseModel):
    given_to: str = Field(
        min_length=2,
        max_length=200,
    )

    given_date: date

    given_time: time

    location: str = Field(
        min_length=2,
        max_length=300,
    )

    organiser_known: bool

    purpose: str = Field(
        min_length=2,
        max_length=500,
    )


class ExpenseCreate(BaseModel):
    expense_type: str = Field(
        pattern="^(item|event)$"
    )

    item_name: str = Field(
        min_length=2,
        max_length=200,
    )

    amount: Decimal = Field(
        gt=0,
        max_digits=12,
        decimal_places=2,
    )

    spent_by: str

    payment_method: str = Field(
        pattern="^(cash|upi|bank_transfer|cheque|other)$"
    )

    expense_date: date

    expense_time: time

    proof_url: str = Field(
        min_length=1,
        max_length=500,
    )

    notes: str | None = Field(
        default=None,
        max_length=1000,
    )

    cash_details: CashExpenseCreate | None = None


class ExpenseResponse(BaseModel):
    id: str
    pandal_id: str
    expense_type: str
    item_name: str
    amount: Decimal
    spent_by: str
    payment_method: str
    expense_date: date
    expense_time: time
    proof_url: str
    notes: str | None
    created_by: str
    cash_details: CashExpenseCreate | None = None

class ExpenseUpdate(BaseModel):
    expense_type: str | None = Field(
        default=None,
        pattern="^(item|event)$"
    )

    item_name: str | None = Field(
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

    spent_by: str | None = None

    payment_method: str | None = Field(
        default=None,
        pattern="^(cash|upi|bank_transfer|cheque|other)$"
    )

    expense_date: date | None = None
    expense_time: time | None = None

    proof_url: str | None = Field(
        default=None,
        min_length=1,
        max_length=500
    )

    notes: str | None = Field(
        default=None,
        max_length=1000
    )

    cash_details: CashExpenseCreate | None = None