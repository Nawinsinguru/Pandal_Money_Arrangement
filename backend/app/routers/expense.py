from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user

from app.models.user import User
from app.models.member import PandalMember
from app.models.pandal import Pandal
from app.models.expense import ExpenseTransaction
from app.models.cash import CashExpenseDetail
from app.models.audit import AuditLog

from app.schemas.expense import (
    ExpenseCreate,
    ExpenseResponse,
    ExpenseUpdate,
)


router = APIRouter(
    prefix="/pandals",
    tags=["Expenses"],
)


def get_pandal_membership(
    pandal_id: str,
    user_id,
    db: Session,
):
    return (
        db.query(PandalMember)
        .filter(
            PandalMember.pandal_id == pandal_id,
            PandalMember.user_id == user_id,
        )
        .first()
    )


@router.post(
    "/{pandal_id}/expenses",
    response_model=ExpenseResponse,
)
def create_expense(
    pandal_id: str,
    data: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 1. Check Pandal
    pandal = (
        db.query(Pandal)
        .filter(Pandal.id == pandal_id)
        .first()
    )

    if pandal is None:
        raise HTTPException(
            status_code=404,
            detail="Pandal not found.",
        )

    # 2. Check current user's membership
    membership = get_pandal_membership(
        pandal_id,
        current_user.id,
        db,
    )

    if membership is None:
        raise HTTPException(
            status_code=403,
            detail="You are not a member of this Pandal.",
        )

    # 3. Only organiser and cashier can add expenses
    if membership.role not in ("admin", "cashier"):
        raise HTTPException(
            status_code=403,
            detail="Only the organiser or cashier can add expenses.",
        )

    # 4. Validate spent_by user
    spent_by_user = (
        db.query(User)
        .filter(User.id == data.spent_by)
        .first()
    )

    if spent_by_user is None:
        raise HTTPException(
            status_code=404,
            detail="Spent-by user not found.",
        )

    spent_by_membership = get_pandal_membership(
        pandal_id,
        spent_by_user.id,
        db,
    )

    if spent_by_membership is None:
        raise HTTPException(
            status_code=400,
            detail="Spent-by user is not a member of this Pandal.",
        )

    # 5. Validate cash-specific information
    if data.payment_method == "cash" and data.cash_details is None:
        raise HTTPException(
            status_code=400,
            detail="Cash details are required for cash expenses.",
        )

    if data.payment_method != "cash" and data.cash_details is not None:
        raise HTTPException(
            status_code=400,
            detail="Cash details can only be provided for cash expenses.",
        )

    # 6. Create expense
    expense = ExpenseTransaction(
        pandal_id=pandal.id,
        expense_type=data.expense_type,
        item_name=data.item_name,
        amount=data.amount,
        spent_by=spent_by_user.id,
        payment_method=data.payment_method,
        expense_date=data.expense_date,
        expense_time=data.expense_time,
        proof_url=data.proof_url,
        notes=data.notes,
        created_by=current_user.id,
    )

    db.add(expense)
    db.flush()

    # 7. Create cash details when applicable
    if data.payment_method == "cash":

        cash_detail = CashExpenseDetail(
            expense_id=expense.id,
            given_to=data.cash_details.given_to,
            given_date=data.cash_details.given_date,
            given_time=data.cash_details.given_time,
            location=data.cash_details.location,
            organiser_known=data.cash_details.organiser_known,
            purpose=data.cash_details.purpose,
        )

        db.add(cash_detail)

    db.commit()
    db.refresh(expense)

    return ExpenseResponse(
        id=str(expense.id),
        pandal_id=str(expense.pandal_id),
        expense_type=expense.expense_type,
        item_name=expense.item_name,
        amount=expense.amount,
        spent_by=str(expense.spent_by),
        payment_method=expense.payment_method,
        expense_date=expense.expense_date,
        expense_time=expense.expense_time,
        proof_url=expense.proof_url,
        notes=expense.notes,
        created_by=str(expense.created_by),
        cash_details=data.cash_details,
    )

@router.get("/{pandal_id}/expenses")
def get_expense_transactions(
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

    # Check that current user belongs to this pandal
    membership = get_pandal_membership(
        pandal_id,
        current_user.id,
        db
    )

    if membership is None:
        raise HTTPException(
            status_code=403,
            detail="You are not a member of this Pandal."
        )

    # Get expenses
    expenses = (
        db.query(ExpenseTransaction)
        .filter(
            ExpenseTransaction.pandal_id == pandal_id
        )
        .order_by(
            ExpenseTransaction.expense_date.desc(),
            ExpenseTransaction.expense_time.desc()
        )
        .all()
    )

    result = []

    for expense in expenses:
        cash_detail = (
            db.query(CashExpenseDetail)
            .filter(
                CashExpenseDetail.expense_id == expense.id
            )
            .first()
        )

        result.append(
            {
                "id": str(expense.id),
                "pandal_id": str(expense.pandal_id),
                "expense_type": expense.expense_type,
                "item_name": expense.item_name,
                "amount": expense.amount,
                "spent_by": str(expense.spent_by),
                "payment_method": expense.payment_method,
                "expense_date": expense.expense_date,
                "expense_time": expense.expense_time,
                "proof_url": expense.proof_url,
                "notes": expense.notes,
                "created_by": str(expense.created_by),
                "cash_details": (
                    {
                        "given_to": cash_detail.given_to,
                        "given_date": cash_detail.given_date,
                        "given_time": cash_detail.given_time,
                        "location": cash_detail.location,
                        "organiser_known": cash_detail.organiser_known,
                        "purpose": cash_detail.purpose,
                    }
                    if cash_detail
                    else None
                ),
            }
        )

    return result

@router.put("/{pandal_id}/expenses/{expense_id}")
def update_expense(
    pandal_id: str,
    expense_id: str,
    data: ExpenseUpdate,
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

    # Check current user's membership
    membership = get_pandal_membership(
        pandal_id,
        current_user.id,
        db
    )

    if membership is None:
        raise HTTPException(
            status_code=403,
            detail="You are not a member of this Pandal."
        )

    # Only organiser and cashier can update
    if membership.role not in ("admin", "cashier"):
        raise HTTPException(
            status_code=403,
            detail="Only the organiser or cashier can update expenses."
        )

    # Find expense
    expense = (
        db.query(ExpenseTransaction)
        .filter(
            ExpenseTransaction.id == expense_id,
            ExpenseTransaction.pandal_id == pandal_id,
        )
        .first()
    )

    if expense is None:
        raise HTTPException(
            status_code=404,
            detail="Expense transaction not found."
        )

    # Fields supplied by client
    update_data = data.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="No fields provided for update."
        )

    # -----------------------------------------
    # VALIDATE SPENT-BY USER
    # -----------------------------------------

    if "spent_by" in update_data:
        spent_by_user = (
            db.query(User)
            .filter(User.id == update_data["spent_by"])
            .first()
        )

        if spent_by_user is None:
            raise HTTPException(
                status_code=404,
                detail="Spent-by user not found."
            )

        spent_by_membership = get_pandal_membership(
            pandal_id,
            spent_by_user.id,
            db
        )

        if spent_by_membership is None:
            raise HTTPException(
                status_code=400,
                detail="Spent-by user is not a member of this Pandal."
            )

    # -----------------------------------------
    # DETERMINE FINAL PAYMENT METHOD
    # -----------------------------------------

    final_payment_method = update_data.get(
        "payment_method",
        expense.payment_method
    )

    cash_details_provided = "cash_details" in update_data

    # Cash requires cash details
    if final_payment_method == "cash":
        if cash_details_provided:
            if update_data["cash_details"] is None:
                raise HTTPException(
                    status_code=400,
                    detail="Cash details are required for cash expenses."
                )
        else:
            existing_cash_detail = (
                db.query(CashExpenseDetail)
                .filter(
                    CashExpenseDetail.expense_id == expense.id
                )
                .first()
            )

            if existing_cash_detail is None:
                raise HTTPException(
                    status_code=400,
                    detail="Cash details are required for cash expenses."
                )

    # Non-cash cannot have cash details
    if final_payment_method != "cash":
        if cash_details_provided and update_data["cash_details"] is not None:
            raise HTTPException(
                status_code=400,
                detail="Cash details can only be provided for cash expenses."
            )

    # -----------------------------------------
    # CAPTURE OLD VALUES
    # -----------------------------------------

    old_data = {}

    for field in update_data:
        if field == "cash_details":
            existing_cash_detail = (
                db.query(CashExpenseDetail)
                .filter(
                    CashExpenseDetail.expense_id == expense.id
                )
                .first()
            )

            if existing_cash_detail:
                old_data["cash_details"] = {
                    "given_to": existing_cash_detail.given_to,
                    "given_date": existing_cash_detail.given_date.isoformat(),
                    "given_time": existing_cash_detail.given_time.isoformat(),
                    "location": existing_cash_detail.location,
                    "organiser_known": existing_cash_detail.organiser_known,
                    "purpose": existing_cash_detail.purpose,
                }
            else:
                old_data["cash_details"] = None

        else:
            old_value = getattr(expense, field)

            if hasattr(old_value, "isoformat"):
                old_value = old_value.isoformat()
            elif old_value is not None:
                old_value = str(old_value)

            old_data[field] = old_value

    # -----------------------------------------
    # UPDATE EXPENSE
    # -----------------------------------------

    for field, value in update_data.items():
        if field != "cash_details":
            setattr(expense, field, value)

    # -----------------------------------------
    # UPDATE CASH DETAILS
    # -----------------------------------------

    existing_cash_detail = (
        db.query(CashExpenseDetail)
        .filter(
            CashExpenseDetail.expense_id == expense.id
        )
        .first()
    )

    if final_payment_method == "cash":
        if cash_details_provided:
            cash_data = update_data["cash_details"]

            if existing_cash_detail:
                existing_cash_detail.given_to = cash_data.given_to
                existing_cash_detail.given_date = cash_data.given_date
                existing_cash_detail.given_time = cash_data.given_time
                existing_cash_detail.location = cash_data.location
                existing_cash_detail.organiser_known = cash_data.organiser_known
                existing_cash_detail.purpose = cash_data.purpose
            else:
                cash_detail = CashExpenseDetail(
                    expense_id=expense.id,
                    given_to=cash_data.given_to,
                    given_date=cash_data.given_date,
                    given_time=cash_data.given_time,
                    location=cash_data.location,
                    organiser_known=cash_data.organiser_known,
                    purpose=cash_data.purpose,
                )

                db.add(cash_detail)

    else:
        if existing_cash_detail:
            db.delete(existing_cash_detail)

    # -----------------------------------------
    # CAPTURE NEW VALUES
    # -----------------------------------------

    new_data = {}

    for field in update_data:
        if field == "cash_details":
            if final_payment_method == "cash":
                cash_detail = (
                    db.query(CashExpenseDetail)
                    .filter(
                        CashExpenseDetail.expense_id == expense.id
                    )
                    .first()
                )

                if cash_detail:
                    new_data["cash_details"] = {
                        "given_to": cash_detail.given_to,
                        "given_date": cash_detail.given_date.isoformat(),
                        "given_time": cash_detail.given_time.isoformat(),
                        "location": cash_detail.location,
                        "organiser_known": cash_detail.organiser_known,
                        "purpose": cash_detail.purpose,
                    }
                else:
                    new_data["cash_details"] = None
            else:
                new_data["cash_details"] = None

        else:
            new_value = getattr(expense, field)

            if hasattr(new_value, "isoformat"):
                new_value = new_value.isoformat()
            elif new_value is not None:
                new_value = str(new_value)

            new_data[field] = new_value

    # -----------------------------------------
    # AUDIT LOG
    # -----------------------------------------

    audit_log = AuditLog(
        pandal_id=pandal.id,
        user_id=current_user.id,
        action="UPDATE",
        entity_type="expense",
        entity_id=expense.id,
        old_data=str(old_data),
        new_data=str(new_data),
    )

    db.add(audit_log)

    db.commit()
    db.refresh(expense)

    # Get final cash details
    final_cash_detail = (
        db.query(CashExpenseDetail)
        .filter(
            CashExpenseDetail.expense_id == expense.id
        )
        .first()
    )

    return {
        "message": "Expense transaction updated successfully.",
        "id": str(expense.id),
        "pandal_id": str(expense.pandal_id),
        "expense_type": expense.expense_type,
        "item_name": expense.item_name,
        "amount": expense.amount,
        "spent_by": str(expense.spent_by),
        "payment_method": expense.payment_method,
        "expense_date": expense.expense_date,
        "expense_time": expense.expense_time,
        "proof_url": expense.proof_url,
        "notes": expense.notes,
        "created_by": str(expense.created_by),
        "cash_details": (
            {
                "given_to": final_cash_detail.given_to,
                "given_date": final_cash_detail.given_date,
                "given_time": final_cash_detail.given_time,
                "location": final_cash_detail.location,
                "organiser_known": final_cash_detail.organiser_known,
                "purpose": final_cash_detail.purpose,
            }
            if final_cash_detail
            else None
        ),
    }