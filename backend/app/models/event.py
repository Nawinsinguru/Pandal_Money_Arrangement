from sqlalchemy import (
    Column,
    String,
    DateTime,
    ForeignKey,
    Numeric,
    Boolean,
    Text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class Event(Base):
    __tablename__ = "events"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    pandal_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pandals.id", ondelete="CASCADE"),
        nullable=False
    )

    event_name = Column(
        String(200),
        nullable=False
    )

    planned_budget = Column(
        Numeric(12, 2),
        nullable=False
    )

    budget_arranged = Column(
        Boolean,
        nullable=False,
        default=False
    )

    description = Column(
        Text,
        nullable=True
    )

    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )