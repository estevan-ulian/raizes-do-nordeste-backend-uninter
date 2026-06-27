from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class InventoryMovementType(str, Enum):
    ENTRY = "ENTRY"
    EXIT = "EXIT"


class InventoryMovementCreate(BaseModel):
    """Schema for inventory entry and exit movements."""

    unit_id: UUID
    product_id: UUID
    movement_type: InventoryMovementType
    quantity: int = Field(gt=0)
    minimum_quantity: int | None = Field(default=None, ge=0)


class InventoryResponse(BaseModel):
    """Schema for inventory data returned in responses."""

    id: UUID
    unit_id: UUID
    product_id: UUID
    quantity: int
    minimum_quantity: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InventoryListResponse(BaseModel):
    """Schema for paginated inventory lists."""

    items: list[InventoryResponse]
    total: int
    page: int
    limit: int

    model_config = ConfigDict(from_attributes=True)
