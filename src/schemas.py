from enum import Enum
from typing import Optional, TypeVar, Generic, Any
from pydantic import BaseModel, ConfigDict
from datetime import datetime
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
    details: Optional[Any] = None
    error_code: Optional[ErrorCode] = None
