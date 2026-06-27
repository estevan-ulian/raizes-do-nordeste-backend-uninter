from fastapi import FastAPI, status

from src.exceptions import AppException, create_exception_handler
from src.schemas import ErrorCode


class LoyaltyAccountNotFoundException(AppException):
    """Loyalty account was not found for the customer."""

    status_code = status.HTTP_404_NOT_FOUND
    message = "Conta de fidelidade não encontrada."
    error_code = ErrorCode.LOYALTY_ACCOUNT_NOT_FOUND


class LoyaltyInsufficientPointsException(AppException):
    """Loyalty account does not have enough points for the redemption."""

    status_code = status.HTTP_409_CONFLICT
    message = "Pontos de fidelidade insuficientes para o resgate solicitado."
    error_code = ErrorCode.LOYALTY_INSUFFICIENT_POINTS


def register_loyalty_exception_handlers(app: FastAPI):
    """Register all loyalty-related exception handlers."""
    exceptions = [LoyaltyAccountNotFoundException, LoyaltyInsufficientPointsException]
    for exc_class in exceptions:
        app.add_exception_handler(exc_class, create_exception_handler(exc_class))
