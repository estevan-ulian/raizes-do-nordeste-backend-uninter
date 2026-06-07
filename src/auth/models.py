import uuid
from datetime import datetime
from enum import Enum

import sqlalchemy.dialects.postgresql as pg
from sqlmodel import Column, Field, SQLModel
from sqlmodel import Enum as SQLEnum

from src.utils import get_utc_now


class Role(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    KITCHEN = "kitchen"
    SERVER = "server"
    CUSTOMER = "customer"


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=255, nullable=False)
    email: str = Field(max_length=255, unique=True, index=True, nullable=False)
    password_hash: str = Field(max_length=255, nullable=False)
    phone: str | None = Field(max_length=20, default=None)
    role: Role = Field(default=Role.CUSTOMER, sa_type=SQLEnum(Role))
    is_verified: bool = Field(default=False)
    created_at: datetime = Field(sa_column=Column(pg.TIMESTAMP(timezone=True), default=get_utc_now))
    updated_at: datetime = Field(sa_column=Column(pg.TIMESTAMP(timezone=True), default=get_utc_now))
