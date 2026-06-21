import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

import sqlalchemy.dialects.postgresql as pg
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, Relationship, SQLModel

from src.utils import get_utc_now

if TYPE_CHECKING:
    from src.auth.models import User


class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_logs"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID | None = Field(default=None, foreign_key="users.id", index=True)
    action: str = Field(max_length=100, nullable=False)
    resource: str = Field(max_length=100, nullable=False)
    resource_id: uuid.UUID | None = Field(default=None, index=True)
    details: dict[str, Any] | None = Field(default=None, sa_column=Column(JSONB, nullable=True))
    ip: str | None = Field(default=None, max_length=45)
    created_at: datetime = Field(sa_column=Column(pg.TIMESTAMP(timezone=True), default=get_utc_now))

    user: Optional["User"] = Relationship(back_populates="audit_logs")
