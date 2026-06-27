from datetime import datetime
from enum import Enum
from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, ConfigDict

from src.utils import datetime_to_gmt_str

T = TypeVar("T")


class BaseSchema(BaseModel):
    model_config = ConfigDict(
        json_encoders={datetime: datetime_to_gmt_str},
        validate_by_name=True,
        validate_by_alias=True,
        from_attributes=True,
    )


class ErrorCode(str, Enum):
    """Error codes for API responses."""

    USER_NOT_FOUND = "USER_NOT_FOUND"
    USER_ALREADY_EXISTS = "USER_ALREADY_EXISTS"
    USER_ALREADY_VERIFIED = "USER_ALREADY_VERIFIED"
    USER_NOT_VERIFIED = "USER_NOT_VERIFIED"
    USER_SESSION_EXPIRED = "USER_SESSION_EXPIRED"
    PASSWORDS_DO_NOT_MATCH = "PASSWORDS_DO_NOT_MATCH"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    INVALID_TOKEN = "INVALID_TOKEN"
    ACCESS_TOKEN_REQUIRED = "ACCESS_TOKEN_REQUIRED"
    REFRESH_TOKEN_REQUIRED = "REFRESH_TOKEN_REQUIRED"
    RESET_TOKEN_INVALID = "RESET_TOKEN_INVALID"
    UNAUTHORIZED = "UNAUTHORIZED"
    INVALID_PRODUCT_IMAGE = "INVALID_PRODUCT_IMAGE"
    PRODUCT_IMAGE_TOO_LARGE = "PRODUCT_IMAGE_TOO_LARGE"
    INVENTORY_NOT_FOUND = "INVENTORY_NOT_FOUND"
    INVENTORY_INSUFFICIENT = "INVENTORY_INSUFFICIENT"
    ORDER_NOT_FOUND = "ORDER_NOT_FOUND"
    ORDER_ITEM_INVALID = "ORDER_ITEM_INVALID"
    ORDER_STOCK_INSUFFICIENT = "ORDER_STOCK_INSUFFICIENT"
    ORDER_STATUS_INVALID = "ORDER_STATUS_INVALID"
    PAYMENT_NOT_FOUND = "PAYMENT_NOT_FOUND"
    PAYMENT_ALREADY_EXISTS = "PAYMENT_ALREADY_EXISTS"
    PAYMENT_INVALID = "PAYMENT_INVALID"
    NOT_FOUND = "NOT_FOUND"
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"


class ResponseBaseSchema(BaseSchema):
    """Base schema for all API responses."""

    success: bool
    message: str


class SuccessSchema(ResponseBaseSchema, Generic[T]):
    """Default success response schema."""

    success: bool = True
    result: Optional[T] = None


class ErrorSchema(ResponseBaseSchema):
    """Default error response schema."""

    success: bool = False
    error_code: Optional[ErrorCode] = None


class HealthCheckSchema(BaseSchema):
    """Schema for the health check endpoint."""

    status: str = "ok"
