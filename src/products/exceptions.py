from fastapi import FastAPI, status

from src.exceptions import AppException, create_exception_handler
from src.schemas import ErrorCode


class ProductNotFoundException(AppException):
    """Product was not found in the database."""

    status_code = status.HTTP_404_NOT_FOUND
    message = "Produto não encontrado."
    error_code = ErrorCode.NOT_FOUND


class ProductCategoryAlreadyExistsException(AppException):
    """Product category already exists."""

    status_code = status.HTTP_409_CONFLICT
    message = "Já existe uma categoria de produto com este nome."
    error_code = ErrorCode.PRODUCT_CATEGORY_ALREADY_EXISTS


class ProductCategoryNotFoundException(AppException):
    """Product category was not found."""

    status_code = status.HTTP_404_NOT_FOUND
    message = "Categoria de produto não encontrada."
    error_code = ErrorCode.PRODUCT_CATEGORY_NOT_FOUND


class ProductImageInvalidException(AppException):
    """Product image has an invalid format."""

    status_code = status.HTTP_400_BAD_REQUEST
    message = "Imagem inválida. Envie um arquivo JPG, PNG ou WEBP."
    error_code = ErrorCode.INVALID_PRODUCT_IMAGE


class ProductImageTooLargeException(AppException):
    """Product image is larger than the accepted limit."""

    status_code = status.HTTP_400_BAD_REQUEST
    message = "Imagem muito grande. Envie um arquivo com até 5MB."
    error_code = ErrorCode.PRODUCT_IMAGE_TOO_LARGE


def register_products_exception_handlers(app: FastAPI):
    """Register all products-related exception handlers."""
    exceptions = [
        ProductCategoryAlreadyExistsException,
        ProductCategoryNotFoundException,
        ProductImageInvalidException,
        ProductImageTooLargeException,
        ProductNotFoundException,
    ]
    for exc_class in exceptions:
        app.add_exception_handler(exc_class, create_exception_handler(exc_class))
