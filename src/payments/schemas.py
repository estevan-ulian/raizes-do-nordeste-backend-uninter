from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.payments.models import PaymentStatus


class PaymentCreate(BaseModel):
    """Schema for requesting a mock payment."""

    order_id: UUID = Field()
    method: str = Field(default="MOCK", min_length=1, max_length=50)

    model_config = ConfigDict(populate_by_name=True)


class PaymentResponse(BaseModel):
    """Schema for payment data returned in responses."""

    id: UUID
    order_id: UUID = Field()
    status: PaymentStatus
    amount: Decimal = Field()
    method: str = Field()
    gateway_response: dict | None = Field(
        default=None,
    )
    gateway_transaction_id: str | None = Field(
        default=None,
    )
    created_at: datetime = Field()
    updated_at: datetime = Field()

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
