import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

import sqlalchemy.dialects.postgresql as pg
from sqlmodel import Column, Field, Relationship, SQLModel
from sqlmodel import Enum as SQLEnum

from src.utils import get_utc_now

if TYPE_CHECKING:
    from src.audit.models import AuditLog
    from src.loyalty.models import LoyaltyAccount
    from src.orders.models import Order
    from src.privacy.models import LGPDConsent


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
    is_active: bool = Field(default=True)
    created_at: datetime = Field(sa_column=Column(pg.TIMESTAMP(timezone=True), default=get_utc_now))
    updated_at: datetime = Field(sa_column=Column(pg.TIMESTAMP(timezone=True), default=get_utc_now))

    orders: list["Order"] = Relationship(back_populates="customer")
    loyalty_account: Optional["LoyaltyAccount"] = Relationship(back_populates="customer")
    lgpd_consents: list["LGPDConsent"] = Relationship(back_populates="user")
    audit_logs: list["AuditLog"] = Relationship(back_populates="user")
