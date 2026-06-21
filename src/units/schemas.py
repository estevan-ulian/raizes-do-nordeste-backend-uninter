from datetime import datetime
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
