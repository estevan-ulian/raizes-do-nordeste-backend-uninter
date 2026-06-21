import uuid
from datetime import datetime
from typing import TYPE_CHECKING

import sqlalchemy.dialects.postgresql as pg
from sqlmodel import Column, Field, Relationship, SQLModel

from src.utils import get_utc_now

if TYPE_CHECKING:
    from src.auth.models import User


class LoyaltyAccount(SQLModel, table=True):
    __tablename__ = "loyalty_accounts"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    customer_id: uuid.UUID = Field(foreign_key="users.id", nullable=False, index=True, unique=True)
    points_balance: int = Field(default=0, nullable=False)
    consent_granted: bool = Field(default=False)
    created_at: datetime = Field(sa_column=Column(pg.TIMESTAMP(timezone=True), default=get_utc_now))
    updated_at: datetime = Field(sa_column=Column(pg.TIMESTAMP(timezone=True), default=get_utc_now))

    customer: "User" = Relationship(back_populates="loyalty_account")
    redemptions: list["LoyaltyRedemption"] = Relationship(back_populates="loyalty_account")


class LoyaltyRedemption(SQLModel, table=True):
    __tablename__ = "loyalty_redemptions"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    loyalty_account_id: uuid.UUID = Field(foreign_key="loyalty_accounts.id", nullable=False, index=True)
    points_used: int = Field(nullable=False)
    reward: str = Field(max_length=255, nullable=False)
    created_at: datetime = Field(sa_column=Column(pg.TIMESTAMP(timezone=True), default=get_utc_now))

    loyalty_account: "LoyaltyAccount" = Relationship(back_populates="redemptions")
