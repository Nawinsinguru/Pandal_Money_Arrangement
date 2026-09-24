"""add idempotency request ids to income and expense transactions

Revision ID: 7d2f1c9b4e10
Revises: 5c0a6701a523
Create Date: 2026-09-24

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "7d2f1c9b4e10"
down_revision = "5c0a6701a523"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "income_transactions",
        sa.Column("request_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index(
        "ix_income_transactions_request_id",
        "income_transactions",
        ["request_id"],
        unique=True,
    )

    op.add_column(
        "expense_transactions",
        sa.Column("request_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index(
        "ix_expense_transactions_request_id",
        "expense_transactions",
        ["request_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_expense_transactions_request_id",
        table_name="expense_transactions",
    )
    op.drop_column("expense_transactions", "request_id")

    op.drop_index(
        "ix_income_transactions_request_id",
        table_name="income_transactions",
    )
    op.drop_column("income_transactions", "request_id")
