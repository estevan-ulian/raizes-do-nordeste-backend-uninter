from fastapi import FastAPI, status

from src.exceptions import AppException, create_exception_handler
from src.schemas import ErrorCode


class PromotionNotFoundException(AppException):
    status_code = status.HTTP_404_NOT_FOUND
    message = "Promoção não encontrada."
    error_code = ErrorCode.PROMOTION_NOT_FOUND


class PromotionInvalidPeriodException(AppException):
    status_code = status.HTTP_400_BAD_REQUEST
    message = "O período final da promoção deve ser igual ou posterior ao período inicial."
    error_code = ErrorCode.PROMOTION_INVALID_PERIOD


class PromotionNotApplicableException(AppException):
    status_code = status.HTTP_409_CONFLICT
    message = "A promoção está inativa ou fora do período de vigência."
    error_code = ErrorCode.PROMOTION_NOT_APPLICABLE


def register_promotions_exception_handlers(app: FastAPI):
    for exception in (
        PromotionNotFoundException,
        PromotionInvalidPeriodException,
        PromotionNotApplicableException,
    ):
        app.add_exception_handler(exception, create_exception_handler(exception))

