from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True)

    email = Column(String(255), unique=True, nullable=False, index=True)

    full_name = Column(String(150), nullable=False)

    profile_picture = Column(String(500), nullable=True)

    google_id = Column(String(255), unique=True, nullable=True, index=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )