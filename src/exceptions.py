import logging

from fastapi import FastAPI, status
from fastapi.requests import Request
from fastapi.responses import JSONResponse

from src.schemas import ErrorCode, ErrorSchema

logger = logging.getLogger(__name__)


class AppException(Exception):
    """Base exception for Raízes do Nordeste API."""

    def __init__(self, message: str | None = None, *args: object) -> None:
        if message is not None:
            self.message = message
        super().__init__(*args)

    status_code: int
    message: str
    error_code: ErrorCode


def create_exception_handler(exception_class):
    async def handler(request, exc):
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorSchema(
                message=exc.message,
                error_code=exc.error_code,
            ).model_dump(),
        )

    return handler


def error_responses(*exceptions: type["AppException"]) -> dict:
    """Generate OpenAPI response documentation for exceptions.

    Usage:
        responses=error_responses(InsufficientPermissionException, UserAlreadyExistsException)
    """
    result = {}
    for exc in exceptions:
        result[exc.status_code] = {
            "model": ErrorSchema,
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "message": exc.message,
                        "error_code": exc.error_code.value,
                    }
                }
            },
        }
    return result


def register_global_exception_handlers(app: FastAPI):
    """Registers global exception handlers for the FastAPI app."""

    @app.exception_handler(401)
    async def _not_authorized_exception_handler(_request: Request, _exception: Exception) -> JSONResponse:
        logger.exception(_exception)
        error_content = ErrorSchema(
            message="Você precisa estar autenticado para acessar este recurso.",
            error_code=ErrorCode.UNAUTHORIZED,
        ).model_dump()
        return JSONResponse(content=error_content, status_code=status.HTTP_401_UNAUTHORIZED)

    @app.exception_handler(404)
    async def _not_found_exception_handler(_request: Request, _exception: Exception) -> JSONResponse:
        logger.exception(_exception)
        error_content = ErrorSchema(
            message="O recurso solicitado não foi encontrado.",
            error_code=ErrorCode.NOT_FOUND,
        ).model_dump()
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=error_content)

    @app.exception_handler(500)
    async def _internal_server_error_handler(_request: Request, _exception: Exception) -> JSONResponse:
        logger.exception(_exception)
        error_content = ErrorSchema(
            message="Ocorreu um erro interno no servidor. Por favor, tente novamente mais tarde.",
            error_code=ErrorCode.INTERNAL_SERVER_ERROR,
        ).model_dump()
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=error_content)
