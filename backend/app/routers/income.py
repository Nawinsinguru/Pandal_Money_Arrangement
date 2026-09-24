from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.audit import AuditLog
from app.models.income import IncomeTransaction
from app.models.member import PandalMember
from app.models.pandal import Pandal
from app.models.user import User
from app.schemas.income import IncomeCreate, IncomeResponse, IncomeUpdate


router = APIRouter(prefix="/pandals", tags=["Income"])


def get_pandal_membership(pandal_id: str, user_id, db: Session):
    return (
        db.query(PandalMember)
        .filter(
            PandalMember.pandal_id == pandal_id,
            PandalMember.user_id == user_id,
        )
        .first()
    )


def income_response(income: IncomeTransaction) -> IncomeResponse:
    return IncomeResponse(
        id=str(income.id),
        pandal_id=str(income.pandal_id),
        category=income.category,
        source_name=income.source_name,
        amount=income.amount,
        payment_method=income.payment_method,
        transaction_reference=income.transaction_reference,
        transaction_date=income.transaction_date,
        transaction_time=income.transaction_time,
        proof_url=income.proof_url,
        received_by=str(income.received_by),
        notes=income.notes,
        created_by=str(income.created_by),
    )


@router.post("/{pandal_id}/income", response_model=IncomeResponse)
def create_income(
    pandal_id: str,
    data: IncomeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    pandal = db.query(Pandal).filter(Pandal.id == pandal_id).first()
    if pandal is None:
        raise HTTPException(status_code=404, detail="Pandal not found.")

    membership = get_pandal_membership(pandal_id, current_user.id, db)
    if membership is None:
        raise HTTPException(status_code=403, detail="You are not a member of this Pandal.")

    if membership.role not in ("admin", "cashier"):
        raise HTTPException(
            status_code=403,
            detail="Only the organiser or cashier can add income.",
        )

    # Idempotency check: the same request_id must never create two income rows.
    existing_income = (
        db.query(IncomeTransaction)
        .filter(IncomeTransaction.request_id == data.request_id)
        .first()
    )
    if existing_income is not None:
        if str(existing_income.pandal_id) != str(pandal.id):
            raise HTTPException(
                status_code=409,
                detail="This request ID is already associated with another Pandal.",
            )
        return income_response(existing_income)

    received_by_user = (
        db.query(User)
        .filter(User.id == data.received_by)
        .first()
    )
    if received_by_user is None:
        raise HTTPException(status_code=404, detail="Received-by user not found.")

    received_by_membership = get_pandal_membership(
        pandal_id,
        received_by_user.id,
        db,
    )
    if received_by_membership is None:
        raise HTTPException(
            status_code=400,
            detail="Received-by user is not a member of this Pandal.",
        )

    income = IncomeTransaction(
        request_id=data.request_id,
        pandal_id=pandal.id,
        category=data.category,
        source_name=data.source_name,
        amount=data.amount,
        payment_method=data.payment_method,
        transaction_reference=data.transaction_reference,
        transaction_date=data.transaction_date,
        transaction_time=data.transaction_time,
        proof_url=data.proof_url,
        received_by=received_by_user.id,
        notes=data.notes,
        created_by=current_user.id,
    )

    db.add(income)

    try:
        db.commit()
        db.refresh(income)
    except IntegrityError:
        # Handles two identical requests arriving at almost exactly the same time.
        db.rollback()
        existing_income = (
            db.query(IncomeTransaction)
            .filter(IncomeTransaction.request_id == data.request_id)
            .first()
        )
        if existing_income is None:
            raise HTTPException(
                status_code=409,
                detail="Unable to create income transaction. Please try again.",
            )
        return income_response(existing_income)

    return income_response(income)


@router.get("/{pandal_id}/income")
def get_income_transactions(
    pandal_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    pandal = db.query(Pandal).filter(Pandal.id == pandal_id).first()
    if pandal is None:
        raise HTTPException(status_code=404, detail="Pandal not found.")

    membership = get_pandal_membership(pandal_id, current_user.id, db)
    if membership is None:
        raise HTTPException(status_code=403, detail="You are not a member of this Pandal.")

    transactions = (
        db.query(IncomeTransaction)
        .filter(IncomeTransaction.pandal_id == pandal_id)
        .order_by(
            IncomeTransaction.transaction_date.desc(),
            IncomeTransaction.transaction_time.desc(),
        )
        .all()
    )

    return [
        {
            "id": str(transaction.id),
            "pandal_id": str(transaction.pandal_id),
            "category": transaction.category,
            "source_name": transaction.source_name,
            "amount": transaction.amount,
            "payment_method": transaction.payment_method,
            "transaction_reference": transaction.transaction_reference,
            "transaction_date": transaction.transaction_date,
            "transaction_time": transaction.transaction_time,
            "proof_url": transaction.proof_url,
            "received_by": str(transaction.received_by),
            "notes": transaction.notes,
            "created_by": str(transaction.created_by),
        }
        for transaction in transactions
    ]


@router.put("/{pandal_id}/income/{income_id}")
def update_income(
    pandal_id: str,
    income_id: str,
    data: IncomeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    pandal = db.query(Pandal).filter(Pandal.id == pandal_id).first()
    if pandal is None:
        raise HTTPException(status_code=404, detail="Pandal not found.")

    membership = get_pandal_membership(pandal_id, current_user.id, db)
    if membership is None:
        raise HTTPException(status_code=403, detail="You are not a member of this Pandal.")

    if membership.role not in ("admin", "cashier"):
        raise HTTPException(
            status_code=403,
            detail="Only the organiser or cashier can update income.",
        )

    income = (
        db.query(IncomeTransaction)
        .filter(
            IncomeTransaction.id == income_id,
            IncomeTransaction.pandal_id == pandal_id,
        )
        .first()
    )
    if income is None:
        raise HTTPException(status_code=404, detail="Income transaction not found.")

    update_data = data.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided for update.")

    if "received_by" in update_data:
        received_by_user = (
            db.query(User).filter(User.id == update_data["received_by"]).first()
        )
        if received_by_user is None:
            raise HTTPException(status_code=404, detail="Received-by user not found.")
        if get_pandal_membership(pandal_id, received_by_user.id, db) is None:
            raise HTTPException(
                status_code=400,
                detail="Received-by user is not a member of this Pandal.",
            )

    old_data = {}
    for field in update_data:
        old_value = getattr(income, field)
        if hasattr(old_value, "isoformat"):
            old_value = old_value.isoformat()
        elif old_value is not None:
            old_value = str(old_value)
        old_data[field] = old_value

    for field, value in update_data.items():
        setattr(income, field, value)

    new_data = {}
    for field in update_data:
        new_value = getattr(income, field)
        if hasattr(new_value, "isoformat"):
            new_value = new_value.isoformat()
        elif new_value is not None:
            new_value = str(new_value)
        new_data[field] = new_value

    audit_log = AuditLog(
        pandal_id=pandal.id,
        user_id=current_user.id,
        action="UPDATE",
        entity_type="income",
        entity_id=income.id,
        old_data=str(old_data),
        new_data=str(new_data),
    )
    db.add(audit_log)

    db.commit()
    db.refresh(income)

    return {
        "message": "Income transaction updated successfully.",
        **income_response(income).model_dump(),
    }
