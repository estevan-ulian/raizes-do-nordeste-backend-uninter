import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

import sqlalchemy.dialects.postgresql as pg
from sqlalchemy import Column, Numeric
from sqlmodel import Field, Relationship, SQLModel

from src.utils import get_utc_now

if TYPE_CHECKING:
    from src.inventory.models import Inventory
    from src.orders.models import OrderItem
    from src.units.models import Unit


class Product(SQLModel, table=True):
    __tablename__ = "products"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    unit_id: uuid.UUID = Field(foreign_key="units.id", nullable=False, index=True)
    name: str = Field(max_length=255, nullable=False)
    description: str | None = Field(default=None)
    price: Decimal = Field(sa_column=Column(Numeric(10, 2), nullable=False))
    category: str = Field(max_length=100, nullable=False, index=True)
    image_url: str | None = Field(default=None, max_length=500)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(sa_column=Column(pg.TIMESTAMP(timezone=True), default=get_utc_now))
    updated_at: datetime = Field(sa_column=Column(pg.TIMESTAMP(timezone=True), default=get_utc_now))

    unit: "Unit" = Relationship(back_populates="products")
    order_items: list["OrderItem"] = Relationship(back_populates="product")
    inventory_items: list["Inventory"] = Relationship(back_populates="product")
