import uuid
from datetime import datetime
from typing import TYPE_CHECKING

import sqlalchemy.dialects.postgresql as pg
from sqlalchemy import UniqueConstraint
from sqlmodel import Column, Field, Relationship, SQLModel

from src.utils import get_utc_now

if TYPE_CHECKING:
    from src.products.models import Product
    from src.units.models import Unit


class Inventory(SQLModel, table=True):
    __tablename__ = "inventory"
    __table_args__ = (UniqueConstraint("unit_id", "product_id", name="uq_inventory_unit_product"),)

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    unit_id: uuid.UUID = Field(foreign_key="units.id", nullable=False, index=True)
    product_id: uuid.UUID = Field(foreign_key="products.id", nullable=False, index=True)
    quantity: int = Field(default=0, nullable=False)
    minimum_quantity: int = Field(default=0, nullable=False)
    created_at: datetime = Field(sa_column=Column(pg.TIMESTAMP(timezone=True), default=get_utc_now))
    updated_at: datetime = Field(sa_column=Column(pg.TIMESTAMP(timezone=True), default=get_utc_now))

    unit: "Unit" = Relationship(back_populates="inventory_items")
    product: "Product" = Relationship(back_populates="inventory_items")
