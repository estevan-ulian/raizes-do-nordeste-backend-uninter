from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.orders.models import OrderChannel, OrderStatus


class OrderItemCreate(BaseModel):
    """Schema for order item creation."""

    product_id: UUID = Field()
    quantity: int = Field(gt=0)

    model_config = ConfigDict(populate_by_name=True)


class OrderCreate(BaseModel):
    """Schema for order creation."""

    customer_id: UUID | None = Field(
        default=None,
    )
    promotion_id: UUID | None = None
    unit_id: UUID = Field()
    order_channel: OrderChannel = Field()
    items: list[OrderItemCreate] = Field(min_length=1)
    payment_method: str = Field(default="MOCK", min_length=1, max_length=50)
    notes: str | None = Field(
        default=None,
    )

    model_config = ConfigDict(populate_by_name=True)


class OrderItemResponse(BaseModel):
    """Schema for order item data returned in responses."""

    id: UUID
    product_id: UUID = Field()
    quantity: int = Field()
    unit_price: Decimal = Field()
    subtotal: Decimal

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class OrderResponse(BaseModel):
    """Schema for order data returned in responses."""

    id: UUID
    customer_id: UUID | None = Field(default=None)
    unit_id: UUID = Field()
    order_channel: OrderChannel = Field()
    status: OrderStatus
    total_amount: Decimal = Field()
    payment_method: str = Field()
    discount_amount: Decimal = Field(default=Decimal("0.00"))
    promotion_ids: list[UUID] = Field(default_factory=list)
    notes: str | None = Field(
        default=None,
    )
    items: list[OrderItemResponse] = Field()
    created_at: datetime = Field()
    updated_at: datetime = Field()

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class OrderListResponse(BaseModel):
    """Schema for paginated order lists."""

    items: list[OrderResponse]
    total: int
    page: int
    limit: int

    model_config = ConfigDict(from_attributes=True)


class OrderStatusUpdate(BaseModel):
    """Schema for updating an order status."""

    status: OrderStatus


class OrderCancel(BaseModel):
    """Schema for canceling an order."""

    reason: str | None = Field(default=None, max_length=500)

    model_config = ConfigDict(populate_by_name=True)
