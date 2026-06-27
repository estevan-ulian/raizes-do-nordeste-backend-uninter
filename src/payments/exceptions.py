from fastapi import FastAPI, status

from src.exceptions import AppException, create_exception_handler
from src.schemas import ErrorCode


class PaymentNotFoundException(AppException):
    """Payment was not found in the database."""

    status_code = status.HTTP_404_NOT_FOUND
    message = "Pagamento não encontrado."
    error_code = ErrorCode.PAYMENT_NOT_FOUND


class PaymentAlreadyExistsException(AppException):
    """Payment already exists for the order."""

    status_code = status.HTTP_409_CONFLICT
    message = "Já existe pagamento registrado para este pedido."
    error_code = ErrorCode.PAYMENT_ALREADY_EXISTS


class PaymentInvalidException(AppException):
    """Payment cannot be requested for the order."""

    status_code = status.HTTP_409_CONFLICT
    message = "Pagamento inválido para o estado atual do pedido."
    error_code = ErrorCode.PAYMENT_INVALID


def register_payments_exception_handlers(app: FastAPI):
    """Register all payments-related exception handlers."""
    exceptions = [PaymentAlreadyExistsException, PaymentInvalidException, PaymentNotFoundException]
    for exc_class in exceptions:
        app.add_exception_handler(exc_class, create_exception_handler(exc_class))
