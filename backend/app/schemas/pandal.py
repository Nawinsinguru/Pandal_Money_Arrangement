from datetime import date
from pydantic import BaseModel, Field


class PandalCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    location: str | None = Field(default=None, max_length=300)
    year: str = Field(min_length=4, max_length=4)
    start_date: date | None = None
    end_date: date | None = None


class PandalResponse(BaseModel):
    id: str
    name: str
    location: str | None
    year: str
    start_date: date | None
    end_date: date | None
    role: str