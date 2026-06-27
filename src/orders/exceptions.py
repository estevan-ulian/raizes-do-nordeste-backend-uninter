from fastapi import FastAPI, status

from src.exceptions import AppException, create_exception_handler
from src.schemas import ErrorCode


class OrderNotFoundException(AppException):
    """Order was not found in the database."""

    status_code = status.HTTP_404_NOT_FOUND
    message = "Pedido não encontrado."
    error_code = ErrorCode.ORDER_NOT_FOUND


class OrderItemInvalidException(AppException):
    """Order has invalid items."""

    status_code = status.HTTP_409_CONFLICT
    message = "Pedido contém itens inválidos ou indisponíveis para a unidade informada."
    error_code = ErrorCode.ORDER_ITEM_INVALID


class OrderStockInsufficientException(AppException):
    """Order cannot be created because inventory is insufficient."""

    status_code = status.HTTP_409_CONFLICT
    message = "Estoque insuficiente para um ou mais itens do pedido."
    error_code = ErrorCode.ORDER_STOCK_INSUFFICIENT


class OrderStatusInvalidException(AppException):
    """Order status transition is invalid."""

    status_code = status.HTTP_409_CONFLICT
    message = "Transição de status do pedido inválida."
    error_code = ErrorCode.ORDER_STATUS_INVALID


class OrderCannotBeCanceledException(AppException):
    """Order cannot be canceled in its current status."""

    status_code = status.HTTP_409_CONFLICT
    message = "Pedido não pode ser cancelado no status atual."
    error_code = ErrorCode.ORDER_STATUS_INVALID


def register_orders_exception_handlers(app: FastAPI):
    """Register all orders-related exception handlers."""
    exceptions = [
        OrderCannotBeCanceledException,
        OrderItemInvalidException,
        OrderNotFoundException,
        OrderStockInsufficientException,
        OrderStatusInvalidException,
    ]
    for exc_class in exceptions:
        app.add_exception_handler(exc_class, create_exception_handler(exc_class))
