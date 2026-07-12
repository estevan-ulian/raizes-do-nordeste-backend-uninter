import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

import sqlalchemy.dialects.postgresql as pg
from sqlalchemy import Column, Index, Numeric, text
from sqlmodel import Field, Relationship, SQLModel

from src.utils import get_utc_now

if TYPE_CHECKING:
    from src.inventory.models import Inventory
    from src.orders.models import OrderItem


class Product(SQLModel, table=True):
    __tablename__ = "products"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=255, nullable=False)
    description: str | None = Field(default=None)
    price: Decimal = Field(sa_column=Column(Numeric(10, 2), nullable=False))
    category_id: uuid.UUID = Field(foreign_key="product_categories.id", nullable=False, index=True)
    image_url: str | None = Field(default=None, max_length=500)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(sa_column=Column(pg.TIMESTAMP(timezone=True), default=get_utc_now))
    updated_at: datetime = Field(sa_column=Column(pg.TIMESTAMP(timezone=True), default=get_utc_now))

    order_items: list["OrderItem"] = Relationship(back_populates="product")
    inventory_items: list["Inventory"] = Relationship(back_populates="product")
    category: "ProductCategory" = Relationship(back_populates="products")


class ProductCategory(SQLModel, table=True):
    __tablename__ = "product_categories"
    __table_args__ = (
        Index("uq_product_categories_name_lower", text("lower(name)"), unique=True),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=100, nullable=False)
    created_at: datetime = Field(sa_column=Column(pg.TIMESTAMP(timezone=True), default=get_utc_now))
    updated_at: datetime = Field(sa_column=Column(pg.TIMESTAMP(timezone=True), default=get_utc_now))

    products: list["Product"] = Relationship(back_populates="category")
