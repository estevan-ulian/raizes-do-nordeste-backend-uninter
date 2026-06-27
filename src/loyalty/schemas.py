from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class LoyaltyAccountResponse(BaseModel):
    """Schema for loyalty account data returned in responses."""

    id: UUID
    customer_id: UUID = Field()
    points_balance: int = Field()
    consent_granted: bool = Field()
    created_at: datetime = Field()
    updated_at: datetime = Field()

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class LoyaltyRedemptionCreate(BaseModel):
    """Schema for requesting a loyalty redemption."""

    points_used: int = Field(gt=0)
    reward: str = Field(min_length=1, max_length=255)


class LoyaltyRedemptionResponse(BaseModel):
    """Schema for loyalty redemption data returned in responses."""

    id: UUID
    loyalty_account_id: UUID = Field()
    points_used: int = Field()
    reward: str = Field()
    created_at: datetime = Field()

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
