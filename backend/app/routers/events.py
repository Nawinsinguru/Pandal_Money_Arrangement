from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user

from app.models.user import User
from app.models.member import PandalMember
from app.models.pandal import Pandal
from app.models.event import Event

from app.schemas.event import (
    EventCreate,
    EventResponse,
)

router = APIRouter(
    prefix="/pandals",
    tags=["Events"],
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


# ============================================================
# CREATE EVENT
# ============================================================

@router.post(
    "/{pandal_id}/events",
    response_model=EventResponse,
)
def create_event(
    pandal_id: str,
    data: EventCreate,
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

    # 2. Check membership
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

    # 3. Only organiser can manage events
    if membership.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only the organiser can create events.",
        )

    # 4. Create event
    event = Event(
        pandal_id=pandal.id,
        event_name=data.event_name,
        planned_budget=data.planned_budget,
        budget_arranged=data.budget_arranged,
        description=data.description,
        created_by=current_user.id,
    )

    db.add(event)
    db.commit()
    db.refresh(event)

    return EventResponse(
        id=str(event.id),
        pandal_id=str(event.pandal_id),
        event_name=event.event_name,
        planned_budget=event.planned_budget,
        budget_arranged=event.budget_arranged,
        description=event.description,
        created_by=str(event.created_by),
    )


# ============================================================
# GET EVENTS
# ============================================================

@router.get(
    "/{pandal_id}/events",
    response_model=list[EventResponse],
)
def get_events(
    pandal_id: str,
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

    # 2. Check membership
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

    # 3. Get all events for this Pandal
    events = (
        db.query(Event)
        .filter(Event.pandal_id == pandal_id)
        .order_by(Event.created_at.desc())
        .all()
    )

    # 4. Return events
    return [
        EventResponse(
            id=str(event.id),
            pandal_id=str(event.pandal_id),
            event_name=event.event_name,
            planned_budget=event.planned_budget,
            budget_arranged=event.budget_arranged,
            description=event.description,
            created_by=str(event.created_by),
        )
        for event in events
    ]