import logging
from fastapi import FastAPI, status
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from typing import Callable, Awaitable
from src.schemas import ErrorCode, ErrorSchema

logger = logging.getLogger(__name__)


class BaseException(Exception):
    """Base exception for Raízes do Nordeste API."""

    pass


def create_exception_handler(
    status_code: int, response: ErrorSchema
) -> Callable[[Request, Exception], Awaitable[JSONResponse]]:
    async def exception_handler(_request: Request, _exception: Exception) -> JSONResponse:
        logger.exception(_exception)
        return JSONResponse(status_code=status_code, content=response.model_dump())

    return exception_handler


def register_global_exception_handlers(app: FastAPI):
    """Registers global exception handlers for the FastAPI app."""

    @app.exception_handler(404)
    async def _not_found_exception_handler(_request: Request, _exception: Exception) -> JSONResponse:
        logger.exception(_exception)
        error_content = ErrorSchema(
            message="O recurso solicitado não foi encontrado.",
            error_code=ErrorCode.NOT_FOUND,
            details=None,
        ).model_dump()
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=error_content)

    @app.exception_handler(500)
    async def _internal_server_error_handler(_request: Request, _exception: Exception) -> JSONResponse:
        logger.exception(_exception)
        error_content = ErrorSchema(
            message="Ocorreu um erro interno no servidor. Por favor, tente novamente mais tarde.",
            error_code=ErrorCode.INTERNAL_SERVER_ERROR,
            details=None,
        ).model_dump()
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=error_content)
