from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PromotionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    discount_percent: Decimal = Field(gt=0, le=100, max_digits=5, decimal_places=2)
    starts_at: date
    ends_at: date

    @model_validator(mode="after")
    def validate_period(self):
        if self.ends_at < self.starts_at:
            raise ValueError("ends_at must be greater than or equal to starts_at")
        return self


class PromotionUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    discount_percent: Decimal | None = Field(
        default=None, gt=0, le=100, max_digits=5, decimal_places=2
    )
    starts_at: date | None = None
    ends_at: date | None = None
    is_active: bool | None = None


class PromotionResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    discount_percent: Decimal
    starts_at: date
    ends_at: date
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PromotionListResponse(BaseModel):
    items: list[PromotionResponse]
    total: int
    page: int
    limit: int

