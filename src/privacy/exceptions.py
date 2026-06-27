from fastapi import FastAPI, status

from src.exceptions import AppException, create_exception_handler
from src.schemas import ErrorCode


class PrivacyConsentRequiredException(AppException):
    """Privacy consent is required to create an account (LGPD)."""

    status_code = status.HTTP_400_BAD_REQUEST
    message = "O consentimento de privacidade é obrigatório para criar a conta."
    error_code = ErrorCode.PRIVACY_CONSENT_REQUIRED


def register_privacy_exception_handlers(app: FastAPI):
    """Register all privacy-related exception handlers."""
    exceptions = [PrivacyConsentRequiredException]
    for exc_class in exceptions:
        app.add_exception_handler(exc_class, create_exception_handler(exc_class))
