import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

import sqlalchemy.dialects.postgresql as pg
from sqlalchemy import Column, Numeric
from sqlmodel import Field, Relationship, SQLModel

from src.utils import get_utc_now

if TYPE_CHECKING:
    from src.orders.models import Order


class Promotion(SQLModel, table=True):
    __tablename__ = "promotions"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=255, nullable=False)
    description: str | None = Field(default=None)
    discount_percent: Decimal = Field(sa_column=Column(Numeric(5, 2), nullable=False))
    starts_at: date = Field(nullable=False)
    ends_at: date = Field(nullable=False)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(sa_column=Column(pg.TIMESTAMP(timezone=True), default=get_utc_now))
    updated_at: datetime = Field(sa_column=Column(pg.TIMESTAMP(timezone=True), default=get_utc_now))

    order_promotions: list["OrderPromotion"] = Relationship(back_populates="promotion")


class OrderPromotion(SQLModel, table=True):
    __tablename__ = "order_promotions"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    order_id: uuid.UUID = Field(foreign_key="orders.id", nullable=False, index=True)
    promotion_id: uuid.UUID = Field(foreign_key="promotions.id", nullable=False, index=True)
    discount_amount: Decimal = Field(sa_column=Column(Numeric(10, 2), nullable=False))
    created_at: datetime = Field(sa_column=Column(pg.TIMESTAMP(timezone=True), default=get_utc_now))

    order: "Order" = Relationship(back_populates="order_promotions")
    promotion: "Promotion" = Relationship(back_populates="order_promotions")
