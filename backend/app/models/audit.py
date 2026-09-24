from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    pandal_id = Column(
        UUID(as_uuid=True),
        nullable=False
    )

    user_id = Column(
        UUID(as_uuid=True),
        nullable=False
    )

    action = Column(
        String(50),
        nullable=False
    )

    entity_type = Column(
        String(50),
        nullable=False
    )

    entity_id = Column(
        UUID(as_uuid=True),
        nullable=False
    )

    old_data = Column(
        Text,
        nullable=True
    )

    new_data = Column(
        Text,
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )