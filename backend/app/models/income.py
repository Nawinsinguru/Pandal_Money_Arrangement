from sqlalchemy import (
    Column,
    String,
    Date,
    Time,
    DateTime,
    ForeignKey,
    Numeric,
    Text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class IncomeTransaction(Base):
    __tablename__ = "income_transactions"

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

    category = Column(
        String(50),
        nullable=False
    )

    source_name = Column(
        String(200),
        nullable=False
    )

    amount = Column(
        Numeric(12, 2),
        nullable=False
    )

    payment_method = Column(
        String(30),
        nullable=False
    )

    transaction_reference = Column(
        String(200),
        nullable=True
    )

    transaction_date = Column(
        Date,
        nullable=False
    )

    transaction_time = Column(
        Time,
        nullable=False
    )

    proof_url = Column(
        String(500),
        nullable=False
    )

    received_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )

    notes = Column(
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