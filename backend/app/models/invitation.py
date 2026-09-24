from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class PandalInvitation(Base):
    __tablename__ = "pandal_invitations"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    pandal_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pandals.id", ondelete="CASCADE"),
        nullable=False,
    )

    email = Column(
        String(255),
        nullable=False,
        index=True,
    )

    role = Column(
        String(20),
        nullable=False,
    )

    invited_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )

    status = Column(
        String(20),
        nullable=False,
        default="pending",
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )