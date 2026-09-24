from sqlalchemy import (
    Column,
    String,
    Date,
    Time,
    DateTime,
    ForeignKey,
    Numeric,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class ExpenseTransaction(Base):
    __tablename__ = "expense_transactions"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Idempotency key: prevents the same submit request from creating
    # the same expense transaction more than once.
    request_id = Column(
        UUID(as_uuid=True),
        unique=True,
        nullable=True,
        index=True,
    )

    pandal_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pandals.id", ondelete="CASCADE"),
        nullable=False,
    )

    expense_type = Column(String(30), nullable=False)
    item_name = Column(String(200), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)

    spent_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )

    payment_method = Column(String(30), nullable=False)
    expense_date = Column(Date, nullable=False)
    expense_time = Column(Time, nullable=False)
    proof_url = Column(String(500), nullable=False)
    notes = Column(Text, nullable=True)

    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
