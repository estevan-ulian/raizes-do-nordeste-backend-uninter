from fastapi import FastAPI, status

from src.exceptions import AppException, create_exception_handler
from src.schemas import ErrorCode


class UnitNotFoundException(AppException):
    """Unit was not found in the database."""

    status_code = status.HTTP_404_NOT_FOUND
    message = "Unidade não encontrada."
    error_code = ErrorCode.NOT_FOUND


def register_units_exception_handlers(app: FastAPI):
    """Register all units-related exception handlers."""
    exceptions = [UnitNotFoundException]
    for exc_class in exceptions:
        app.add_exception_handler(exc_class, create_exception_handler(exc_class))
