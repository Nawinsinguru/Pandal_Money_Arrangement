from decimal import Decimal

from pydantic import BaseModel, Field


class EventCreate(BaseModel):
    event_name: str = Field(
        min_length=2,
        max_length=200,
    )

    planned_budget: Decimal = Field(
        gt=0,
        max_digits=12,
        decimal_places=2,
    )

    budget_arranged: bool = False

    description: str | None = Field(
        default=None,
        max_length=1000,
    )


class EventResponse(BaseModel):
    id: str
    pandal_id: str
    event_name: str
    planned_budget: Decimal
    budget_arranged: bool
    description: str | None
    created_by: str