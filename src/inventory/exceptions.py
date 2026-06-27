from fastapi import FastAPI, status

from src.exceptions import AppException, create_exception_handler
from src.schemas import ErrorCode


class InventoryNotFoundException(AppException):
    """Inventory item was not found in the database."""

    status_code = status.HTTP_404_NOT_FOUND
    message = "Estoque não encontrado para a unidade e produto informados."
    error_code = ErrorCode.INVENTORY_NOT_FOUND


class InventoryInsufficientException(AppException):
    """Inventory item does not have enough quantity for an exit movement."""

    status_code = status.HTTP_409_CONFLICT
    message = "Estoque insuficiente para realizar a saída solicitada."
    error_code = ErrorCode.INVENTORY_INSUFFICIENT


def register_inventory_exception_handlers(app: FastAPI):
    """Register all inventory-related exception handlers."""
    exceptions = [InventoryInsufficientException, InventoryNotFoundException]
    for exc_class in exceptions:
        app.add_exception_handler(exc_class, create_exception_handler(exc_class))
