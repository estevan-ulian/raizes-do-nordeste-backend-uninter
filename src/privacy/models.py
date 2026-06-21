import uuid
from datetime import datetime
from typing import TYPE_CHECKING

import sqlalchemy.dialects.postgresql as pg
from sqlmodel import Column, Field, Relationship, SQLModel

from src.utils import get_utc_now

if TYPE_CHECKING:
    from src.auth.models import User


class LGPDConsent(SQLModel, table=True):
    __tablename__ = "lgpd_consents"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False, index=True)
    purpose: str = Field(max_length=255, nullable=False)
    legal_basis: str = Field(max_length=255, nullable=False)
    is_granted: bool = Field(default=True)
    created_at: datetime = Field(sa_column=Column(pg.TIMESTAMP(timezone=True), default=get_utc_now))
    revoked_at: datetime | None = Field(
        default=None,
        sa_column=Column(pg.TIMESTAMP(timezone=True), nullable=True),
    )

    user: "User" = Relationship(back_populates="lgpd_consents")
