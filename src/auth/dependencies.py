from fastapi import Depends
from fastapi.requests import Request
from fastapi.security import HTTPBearer
from sqlmodel.ext.asyncio.session import AsyncSession

from src.auth.models import Role, User
from src.auth.service import UserService
from src.database import get_async_session
from src.security import decode_token, token_in_blocklist

from .exceptions import (
    AccessTokenRequiredException,
    AccountInactiveException,
    AccountNotVerifiedException,
    InsufficientPermissionException,
    InvalidTokenException,
    RefreshTokenRequiredException,
    UserNotFoundException,
)

user_service = UserService()


class TokenBearer(HTTPBearer):
    def __init__(self, auto_error=True):
        super().__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> dict | None:
        creds = await super().__call__(request)
        if creds is None:
            return None
        token = creds.credentials
        token_data = decode_token(token)
        if token_data is None:
            raise InvalidTokenException()
        if await token_in_blocklist(token_data["jti"]):
            raise InvalidTokenException()
        self.verify_token_data(token_data)
        return token_data

    def verify_token_data(self, token_data: dict):
        raise NotImplementedError("Method verify_token_data must be implemented in subclasses")


class AccessTokenBearer(TokenBearer):
    def verify_token_data(self, token_data: dict) -> None:
        if token_data and token_data["refresh"]:
            raise AccessTokenRequiredException()


class RefreshTokenBearer(TokenBearer):
    def verify_token_data(self, token_data: dict) -> None:
        if token_data and not token_data["refresh"]:
            raise RefreshTokenRequiredException()


async def get_current_user(
    token_details: dict = Depends(AccessTokenBearer()), session: AsyncSession = Depends(get_async_session)
):
    user_email = token_details["user"]["email"]
    user = await user_service.get_user_by_email(user_email, session)
    if not user:
        raise UserNotFoundException()
    if not user.is_active:
        raise AccountInactiveException()
    return user


async def get_optional_current_user(
    token_details: dict | None = Depends(AccessTokenBearer(auto_error=False)),
    session: AsyncSession = Depends(get_async_session),
) -> User | None:
    if token_details is None:
        return None
    user_email = token_details["user"]["email"]
    user = await user_service.get_user_by_email(user_email, session)
    if not user:
        raise UserNotFoundException()
    if not user.is_active:
        raise AccountInactiveException()
    return user


class RoleChecker:
    def __init__(self, allowed_roles: list[Role]) -> None:
        self.allowed_roles = allowed_roles

    async def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if not current_user.is_verified:
            raise AccountNotVerifiedException()
        if current_user.role not in self.allowed_roles:
            raise InsufficientPermissionException()
        return current_user
