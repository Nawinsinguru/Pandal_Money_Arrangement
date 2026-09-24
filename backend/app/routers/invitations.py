from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.member import PandalMember
from app.models.pandal import Pandal
from app.models.invitation import PandalInvitation
from app.schemas.invitation import (
    InvitationCreate,
    InvitationResponse,
)


router = APIRouter(
    prefix="/pandals",
    tags=["Pandal Invitations"],
)


@router.post(
    "/{pandal_id}/invitations",
    response_model=InvitationResponse,
)
def invite_member(
    pandal_id: str,
    data: InvitationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 1. Check that the Pandal exists
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

    # 2. Check that the logged-in user is a member
    membership = (
        db.query(PandalMember)
        .filter(
            PandalMember.pandal_id == pandal.id,
            PandalMember.user_id == current_user.id,
        )
        .first()
    )

    # 3. Only Organiser can invite
    if membership is None or membership.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only the organiser can invite committee members.",
        )

    # 4. Check if this email is already a registered application user
    existing_user = (
        db.query(User)
        .filter(User.email == data.email)
        .first()
    )

    if existing_user:
        existing_membership = (
            db.query(PandalMember)
            .filter(
                PandalMember.pandal_id == pandal.id,
                PandalMember.user_id == existing_user.id,
            )
            .first()
        )

        if existing_membership:
            raise HTTPException(
                status_code=409,
                detail="This user is already a member of this Pandal.",
            )

    # 5. Check for an existing pending invitation
    existing_invitation = (
        db.query(PandalInvitation)
        .filter(
            PandalInvitation.pandal_id == pandal.id,
            PandalInvitation.email == data.email,
            PandalInvitation.status == "pending",
        )
        .first()
    )

    if existing_invitation:
        raise HTTPException(
            status_code=409,
            detail="A pending invitation already exists for this email.",
        )

    # 6. Create invitation
    invitation = PandalInvitation(
        pandal_id=pandal.id,
        email=data.email,
        role=data.role,
        invited_by=current_user.id,
        status="pending",
    )

    db.add(invitation)
    db.commit()
    db.refresh(invitation)

    return InvitationResponse(
        id=str(invitation.id),
        pandal_id=str(invitation.pandal_id),
        email=invitation.email,
        role=invitation.role,
        status=invitation.status,
        message="Invitation created successfully.",
    )

@router.get("/{pandal_id}/members")
def get_pandal_members(
    pandal_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Check that the pandal exists
    pandal = db.query(Pandal).filter(Pandal.id == pandal_id).first()

    if pandal is None:
        raise HTTPException(
            status_code=404,
            detail="Pandal not found."
        )

    # Check that current user belongs to this pandal
    current_membership = (
        db.query(PandalMember)
        .filter(
            PandalMember.pandal_id == pandal_id,
            PandalMember.user_id == current_user.id,
        )
        .first()
    )

    if current_membership is None:
        raise HTTPException(
            status_code=403,
            detail="You are not a member of this Pandal."
        )

    # Get all members
    members = (
        db.query(PandalMember, User)
        .join(User, PandalMember.user_id == User.id)
        .filter(PandalMember.pandal_id == pandal_id)
        .all()
    )

    return [
        {
            "user_id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "role": membership.role,
        }
        for membership, user in members
    ]