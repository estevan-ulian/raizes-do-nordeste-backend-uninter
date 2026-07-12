from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class UnitCreate(BaseModel):
    """Schema for creating a business unit."""

    name: str = Field(min_length=1, max_length=255)
    address: str = Field(min_length=1, max_length=500)


class UnitUpdate(BaseModel):
    """Schema for updating a business unit."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    address: str | None = Field(default=None, min_length=1, max_length=500)
    is_active: bool | None = None


class UnitResponse(BaseModel):
    """Schema for unit data returned in responses."""

    id: UUID
    name: str
    address: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UnitMenuCategoryResponse(BaseModel):
    """Product category summary exposed in a unit menu."""

    id: UUID
    name: str


class UnitMenuItemResponse(BaseModel):
    """Public product information and its availability at a unit."""

    id: UUID
    name: str
    description: str | None = None
    price: Decimal
    image_url: str | None = None
    category: UnitMenuCategoryResponse
    available: bool


class UnitMenuResponse(BaseModel):
    """Paginated public menu for a business unit."""

    unit_id: UUID
    unit_name: str
    items: list[UnitMenuItemResponse]
    total: int
    page: int
    limit: int
