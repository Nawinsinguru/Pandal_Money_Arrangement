from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
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
    tags=["Dashboard"]
)


@router.get("/{pandal_id}/dashboard")
def get_dashboard_summary(
    pandal_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Check that the pandal exists
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

    # Check that the current user belongs to this pandal
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

    # -----------------------------------------
    # TOTAL INCOME
    # -----------------------------------------

    total_received = (
        db.query(
            func.coalesce(
                func.sum(IncomeTransaction.amount),
                0
            )
        )
        .filter(
            IncomeTransaction.pandal_id == pandal_id
        )
        .scalar()
    )

    # -----------------------------------------
    # INCOME BREAKDOWN
    # -----------------------------------------

    income_rows = (
        db.query(
            IncomeTransaction.category,
            func.coalesce(
                func.sum(IncomeTransaction.amount),
                0
            )
        )
        .filter(
            IncomeTransaction.pandal_id == pandal_id
        )
        .group_by(
            IncomeTransaction.category
        )
        .all()
    )

    income_breakdown = {
        "sponsor": Decimal("0.00"),
        "chanda": Decimal("0.00"),
        "committee_member": Decimal("0.00"),
        "other": Decimal("0.00"),
    }

    for category, amount in income_rows:
        if category in income_breakdown:
            income_breakdown[category] = amount

    # -----------------------------------------
    # TOTAL EXPENSE
    # -----------------------------------------

    total_spent = (
        db.query(
            func.coalesce(
                func.sum(ExpenseTransaction.amount),
                0
            )
        )
        .filter(
            ExpenseTransaction.pandal_id == pandal_id
        )
        .scalar()
    )

    # -----------------------------------------
    # EXPENSE BREAKDOWN
    # -----------------------------------------

    expense_rows = (
        db.query(
            ExpenseTransaction.expense_type,
            func.coalesce(
                func.sum(ExpenseTransaction.amount),
                0
            )
        )
        .filter(
            ExpenseTransaction.pandal_id == pandal_id
        )
        .group_by(
            ExpenseTransaction.expense_type
        )
        .all()
    )

    expense_breakdown = {
        "item": Decimal("0.00"),
        "event": Decimal("0.00"),
    }

    for expense_type, amount in expense_rows:
        if expense_type in expense_breakdown:
            expense_breakdown[expense_type] = amount

    # -----------------------------------------
    # REMAINING BUDGET
    # -----------------------------------------

    remaining_budget = total_received - total_spent

    return {
        "pandal_id": str(pandal_id),

        "total_received": total_received,
        "total_spent": total_spent,
        "remaining_budget": remaining_budget,

        "income_breakdown": income_breakdown,

        "expense_breakdown": expense_breakdown,
    }