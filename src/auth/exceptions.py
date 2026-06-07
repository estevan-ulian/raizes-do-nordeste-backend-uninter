from fastapi import FastAPI, status

from src.exceptions import AppException, create_exception_handler
from src.schemas import ErrorCode


class UserNotFoundException(AppException):
    """User was not found in the database"""

    status_code = status.HTTP_404_NOT_FOUND
    message = "Usuário não encontrado. Certifique-se de que o email fornecido está correto."
    error_code = ErrorCode.NOT_FOUND


class UserAlreadyExistsException(AppException):
    """User has provided an email for a user who exists during sign up"""

    status_code = status.HTTP_409_CONFLICT
    message = "Já existe um usuário com este email."
    error_code = ErrorCode.USER_ALREADY_EXISTS


class InvalidCredentials(AppException):
    """The provided credentials are invalid"""

    status_code = status.HTTP_401_UNAUTHORIZED
    message = "As credenciais inseridas são inválidas. Verifique os dados inseridos e tente novamente."
    error_code = ErrorCode.INVALID_CREDENTIALS


class AccountNotVerifiedException(AppException):
    """User's account is not verified"""

    status_code = status.HTTP_403_FORBIDDEN
    message = "Sua conta não foi verificada. Verifique seu email e clique no link de verificação para ativar sua conta."
    error_code = ErrorCode.USER_NOT_VERIFIED


class PasswordsDoNotMatchException(AppException):
    """As senhas não coincidem."""

    status_code = status.HTTP_400_BAD_REQUEST
    message = "As senhas não coincidem."
    error_code = ErrorCode.PASSWORDS_DO_NOT_MATCH


class InsufficientPermissionException(AppException):
    """User does not have sufficient permissions to access the resource"""

    status_code = status.HTTP_403_FORBIDDEN
    message = "Você não tem permissão suficiente para acessar este recurso."
    error_code = ErrorCode.UNAUTHORIZED


class InvalidTokenException(AppException):
    """User provided an invalid or expired token"""

    status_code = status.HTTP_401_UNAUTHORIZED
    message = "Sessão inválida ou expirada. Faça login novamente para continuar."
    error_code = ErrorCode.INVALID_TOKEN


class ResetTokenInvalidException(AppException):
    """ResetToken is invalid"""

    status_code = status.HTTP_400_BAD_REQUEST
    message = """Token de redefinição de senha inválido ou expirado. Por favor, solicite uma nova redefinição de senha."""  # noqa: E501
    error_code = ErrorCode.RESET_TOKEN_INVALID


class AccessTokenRequiredException(AppException):
    """AccessToken is required"""

    status_code = status.HTTP_401_UNAUTHORIZED
    message = "Sessão inválida ou expirada. Faça login novamente para continuar."
    error_code = ErrorCode.ACCESS_TOKEN_REQUIRED


class UserSessionExpiredException(AppException):
    """User Session has expired"""

    status_code = status.HTTP_401_UNAUTHORIZED
    message = "A sessão expirou. Faça login novamente para continuar."
    error_code = ErrorCode.USER_SESSION_EXPIRED


class RefreshTokenRequiredException(AppException):
    """RefreshToken is required"""

    status_code = status.HTTP_401_UNAUTHORIZED
    message = "Token de atualização é obrigatório."
    error_code = ErrorCode.REFRESH_TOKEN_REQUIRED


def register_auth_exception_handlers(app: FastAPI):
    """Register all auth-related exception handlers."""
    exceptions = [
        AccessTokenRequiredException,
        AccountNotVerifiedException,
        InvalidCredentials,
        InvalidTokenException,
        InsufficientPermissionException,
        PasswordsDoNotMatchException,
        RefreshTokenRequiredException,
        UserAlreadyExistsException,
        UserNotFoundException,
        UserSessionExpiredException,
        ResetTokenInvalidException,
    ]
    for exc_class in exceptions:
        app.add_exception_handler(exc_class, create_exception_handler(exc_class))
