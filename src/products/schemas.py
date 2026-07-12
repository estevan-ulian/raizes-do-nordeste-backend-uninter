from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProductCreate(BaseModel):
    """Schema for creating a product."""

    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    price: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    category_id: UUID = Field()
    image_url: str | None = Field(default=None, max_length=500)


class ProductUpdate(BaseModel):
    """Schema for updating a product."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    price: Decimal | None = Field(default=None, gt=0, max_digits=10, decimal_places=2)
    category_id: UUID | None = None
    image_url: str | None = Field(default=None, max_length=500)
    is_active: bool | None = None


class ProductResponse(BaseModel):
    """Schema for product data returned in responses."""

    id: UUID
    name: str
    description: str | None = None
    price: Decimal
    category_id: UUID = Field()
    image_url: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductListResponse(BaseModel):
    """Schema for paginated product lists."""

    items: list[ProductResponse]
    total: int
    page: int
    limit: int

    model_config = ConfigDict(from_attributes=True)


class ProductCategoryCreate(BaseModel):
    """Schema for creating a product category."""

    name: str = Field(min_length=1, max_length=100)


class ProductCategoryResponse(BaseModel):
    """Schema for product category data returned in responses."""

    id: UUID
    name: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
