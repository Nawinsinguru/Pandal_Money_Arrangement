from pydantic import BaseModel, EmailStr, Field


class InvitationCreate(BaseModel):
    email: EmailStr
    role: str = Field(pattern="^(cashier|viewer)$")


class InvitationResponse(BaseModel):
    id: str
    pandal_id: str
    email: str
    role: str
    status: str
    message: str