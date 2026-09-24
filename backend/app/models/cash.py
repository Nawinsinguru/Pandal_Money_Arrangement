from sqlalchemy import (
    Column,
    String,
    Date,
    Time,
    Boolean,
    ForeignKey
)
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.core.database import Base


class CashExpenseDetail(Base):
    __tablename__ = "cash_expense_details"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    expense_id = Column(
        UUID(as_uuid=True),
        ForeignKey(
            "expense_transactions.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        unique=True
    )

    given_to = Column(
        String(200),
        nullable=False
    )

    given_date = Column(
        Date,
        nullable=False
    )

    given_time = Column(
        Time,
        nullable=False
    )

    location = Column(
        String(300),
        nullable=False
    )

    organiser_known = Column(
        Boolean,
        nullable=False
    )

    purpose = Column(
        String(500),
        nullable=False
    )