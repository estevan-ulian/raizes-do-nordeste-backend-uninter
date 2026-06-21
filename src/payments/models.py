import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Any

import sqlalchemy.dialects.postgresql as pg
from sqlalchemy import Column, Numeric
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, Relationship, SQLModel
from sqlmodel import Enum as SQLEnum

from src.utils import get_utc_now

if TYPE_CHECKING:
    from src.orders.models import Order


class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class Payment(SQLModel, table=True):
    __tablename__ = "payments"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    order_id: uuid.UUID = Field(foreign_key="orders.id", nullable=False, index=True, unique=True)
    status: PaymentStatus = Field(default=PaymentStatus.PENDING, sa_type=SQLEnum(PaymentStatus))
    amount: Decimal = Field(sa_column=Column(Numeric(10, 2), nullable=False))
    method: str = Field(max_length=50, nullable=False)
    gateway_response: dict[str, Any] | None = Field(default=None, sa_column=Column(JSONB, nullable=True))
    gateway_transaction_id: str | None = Field(default=None, max_length=255)
    created_at: datetime = Field(sa_column=Column(pg.TIMESTAMP(timezone=True), default=get_utc_now))
    updated_at: datetime = Field(sa_column=Column(pg.TIMESTAMP(timezone=True), default=get_utc_now))

    order: "Order" = Relationship(back_populates="payment")
