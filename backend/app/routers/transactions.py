from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user

from app.models.user import User
from app.models.member import PandalMember
from app.models.pandal import Pandal
from app.models.income import IncomeTransaction
from app.models.expense import ExpenseTransaction


router = APIRouter(
    prefix="/pandals",
    tags=["Transactions"]
)


@router.get("/{pandal_id}/transactions")
def get_transaction_history(
    pandal_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Check pandal
    pandal = (
        db.query(Pandal)
        .filter(Pandal.id == pandal_id)
        .first()
    )

    if pandal is None:
        raise HTTPException(
            status_code=404,
            detail="Pandal not found."
        )

    # Check membership
    membership = (
        db.query(PandalMember)
        .filter(
            PandalMember.pandal_id == pandal_id,
            PandalMember.user_id == current_user.id,
        )
        .first()
    )

    if membership is None:
        raise HTTPException(
            status_code=403,
            detail="You are not a member of this Pandal."
        )

    transactions = []

    # -----------------------------------------
    # INCOME TRANSACTIONS
    # -----------------------------------------

    incomes = (
        db.query(IncomeTransaction)
        .filter(
            IncomeTransaction.pandal_id == pandal_id
        )
        .all()
    )

    for income in incomes:
        transactions.append(
            {
                "id": str(income.id),
                "transaction_type": "income",
                "category": income.category,
                "description": income.source_name,
                "amount": income.amount,
                "signed_amount": income.amount,
                "payment_method": income.payment_method,
                "date": income.transaction_date,
                "time": income.transaction_time,
                "proof_url": income.proof_url,
                "user_id": str(income.created_by),
                "reference": income.transaction_reference,
                "notes": income.notes,
            }
        )

    # -----------------------------------------
    # EXPENSE TRANSACTIONS
    # -----------------------------------------

    expenses = (
        db.query(ExpenseTransaction)
        .filter(
            ExpenseTransaction.pandal_id == pandal_id
        )
        .all()
    )

    for expense in expenses:
        transactions.append(
            {
                "id": str(expense.id),
                "transaction_type": "expense",
                "category": expense.expense_type,
                "description": expense.item_name,
                "amount": expense.amount,
                "signed_amount": -expense.amount,
                "payment_method": expense.payment_method,
                "date": expense.expense_date,
                "time": expense.expense_time,
                "proof_url": expense.proof_url,
                "user_id": str(expense.created_by),
                "reference": None,
                "notes": expense.notes,
            }
        )

    # -----------------------------------------
    # SORT BY DATE + TIME
    # -----------------------------------------

    transactions.sort(
        key=lambda transaction: (
            transaction["date"],
            transaction["time"],
        ),
        reverse=True,
    )

    return transactions