import uuid
from datetime import datetime
from typing import TYPE_CHECKING

import sqlalchemy.dialects.postgresql as pg
from sqlmodel import Column, Field, Relationship, SQLModel

from src.utils import get_utc_now

if TYPE_CHECKING:
    from src.inventory.models import Inventory
    from src.orders.models import Order


class Unit(SQLModel, table=True):
    __tablename__ = "units"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=255, nullable=False)
    address: str = Field(max_length=500, nullable=False)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(sa_column=Column(pg.TIMESTAMP(timezone=True), default=get_utc_now))
    updated_at: datetime = Field(sa_column=Column(pg.TIMESTAMP(timezone=True), default=get_utc_now))

    inventory_items: list["Inventory"] = Relationship(back_populates="unit")
    orders: list["Order"] = Relationship(back_populates="unit")
