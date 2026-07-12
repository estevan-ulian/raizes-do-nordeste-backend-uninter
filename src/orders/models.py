import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Optional

import sqlalchemy.dialects.postgresql as pg
from sqlalchemy import Column, Numeric
from sqlmodel import Field, Relationship, SQLModel
from sqlmodel import Enum as SQLEnum

from src.utils import get_utc_now

if TYPE_CHECKING:
    from src.auth.models import User
    from src.payments.models import Payment
    from src.products.models import Product
    from src.promotions.models import OrderPromotion
    from src.units.models import Unit


class OrderChannel(str, Enum):
    APP = "APP"
    TOTEM = "TOTEM"
    COUNTER = "COUNTER"
    PICKUP = "PICKUP"
    WEB = "WEB"


class OrderStatus(str, Enum):
    WAITING_FOR_PAYMENT = "WAITING_FOR_PAYMENT"
    PAID = "PAID"
    IN_THE_KITCHEN = "IN_THE_KITCHEN"
    READY = "READY"
    DELIVERED = "DELIVERED"
    CANCELED = "CANCELED"


class Order(SQLModel, table=True):
    __tablename__ = "orders"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    customer_id: uuid.UUID | None = Field(default=None, foreign_key="users.id", nullable=True, index=True)
    unit_id: uuid.UUID = Field(foreign_key="units.id", nullable=False, index=True)
    order_channel: OrderChannel = Field(sa_type=SQLEnum(OrderChannel), nullable=False, index=True)
    status: OrderStatus = Field(default=OrderStatus.WAITING_FOR_PAYMENT, sa_type=SQLEnum(OrderStatus))
    total_amount: Decimal = Field(sa_column=Column(Numeric(10, 2), nullable=False))
    payment_method: str = Field(default="MOCK", max_length=50, nullable=False)
    notes: str | None = Field(default=None)
    created_at: datetime = Field(sa_column=Column(pg.TIMESTAMP(timezone=True), default=get_utc_now))
    updated_at: datetime = Field(sa_column=Column(pg.TIMESTAMP(timezone=True), default=get_utc_now))

    customer: Optional["User"] = Relationship(back_populates="orders")
    unit: "Unit" = Relationship(back_populates="orders")
    items: list["OrderItem"] = Relationship(back_populates="order")
    payment: Optional["Payment"] = Relationship(back_populates="order")
    order_promotions: list["OrderPromotion"] = Relationship(back_populates="order")


class OrderItem(SQLModel, table=True):
    __tablename__ = "order_items"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    order_id: uuid.UUID = Field(foreign_key="orders.id", nullable=False, index=True)
    product_id: uuid.UUID = Field(foreign_key="products.id", nullable=False, index=True)
    quantity: int = Field(nullable=False)
    unit_price: Decimal = Field(sa_column=Column(Numeric(10, 2), nullable=False))
    subtotal: Decimal = Field(sa_column=Column(Numeric(10, 2), nullable=False))
    created_at: datetime = Field(sa_column=Column(pg.TIMESTAMP(timezone=True), default=get_utc_now))

    order: "Order" = Relationship(back_populates="items")
    product: "Product" = Relationship(back_populates="order_items")
