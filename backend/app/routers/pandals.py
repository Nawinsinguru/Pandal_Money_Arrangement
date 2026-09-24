from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.pandal import Pandal
from app.models.member import PandalMember
from app.models.user import User
from app.schemas.pandal import PandalCreate, PandalResponse


router = APIRouter(
    prefix="/pandals",
    tags=["Pandals"],
)


@router.post(
    "",
    response_model=PandalResponse,
)
def create_pandal(
    data: PandalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Create the Pandal
    pandal = Pandal(
        name=data.name,
        location=data.location,
        year=data.year,
        start_date=data.start_date,
        end_date=data.end_date,
        created_by=current_user.id,
    )

    db.add(pandal)
    db.flush()

    # Creator automatically becomes Organiser/Admin
    membership = PandalMember(
        pandal_id=pandal.id,
        user_id=current_user.id,
        role="admin",
    )

    db.add(membership)
    db.commit()
    db.refresh(pandal)

    return PandalResponse(
        id=str(pandal.id),
        name=pandal.name,
        location=pandal.location,
        year=pandal.year,
        start_date=pandal.start_date,
        end_date=pandal.end_date,
        role="admin",
    )

@router.get("")
def get_my_pandals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    memberships = (
        db.query(PandalMember, Pandal)
        .join(Pandal, PandalMember.pandal_id == Pandal.id)
        .filter(PandalMember.user_id == current_user.id)
        .all()
    )

    return [
        {
            "id": str(pandal.id),
            "name": pandal.name,
            "location": pandal.location,
            "year": pandal.year,
            "start_date": pandal.start_date,
            "end_date": pandal.end_date,
            "role": membership.role,
        }
        for membership, pandal in memberships
    ]