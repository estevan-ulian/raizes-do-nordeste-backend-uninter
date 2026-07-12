import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query, Request, status
from sqlmodel.ext.asyncio.session import AsyncSession

from src.audit.service import AuditAction, audit_service
from src.auth.dependencies import AccessTokenBearer, RefreshTokenBearer, RoleChecker, get_current_user
from src.auth.exceptions import (
    AccountInactiveException,
    AdminStatusConflictException,
    InsufficientPermissionException,
    InvalidCredentials,
    InvalidTokenException,
    PasswordsDoNotMatchException,
    ResetTokenInvalidException,
    UserAlreadyExistsException,
    UserNotFoundException,
    UserSessionExpiredException,
)
from src.auth.models import Role, User
from src.auth.schemas import (
    LoginRequest,
    LogoutRequest,
    PasswordResetConfirmSchema,
    PasswordResetRequestSchema,
    TokenResponse,
    UserCreate,
    UserListResponse,
    UserRegister,
    UserResponse,
    UserSelfUpdate,
    UserStatusUpdate,
)
from src.auth.service import UserService
from src.database import get_async_session
from src.exceptions import error_responses
from src.privacy.exceptions import PrivacyConsentRequiredException
from src.privacy.service import privacy_service
from src.schemas import SuccessSchema
from src.security import (
    add_jti_to_blocklist,
    add_reset_token_to_blocklist,
    create_access_token,
    create_url_safe_token,
    decode_token,
    decode_url_safe_token,
    generate_password_hash,
    reset_token_in_blocklist,
    verify_password,
)
from src.templates.user_request_reset_password import generate_user_request_reset_password_template
from src.templates.user_verify_email import generate_user_verify_email_template
from src.utils import get_request_ip, get_utc_now
from src.worker import send_mail

router = APIRouter(prefix="/auth", tags=["auth"])
user_service = UserService()

ROLE_CREATION_PERMISSIONS: dict[Role, list[Role]] = {
    Role.ADMIN: [role for role in Role],  # ADMIN can create users of any role
    Role.MANAGER: [Role.KITCHEN, Role.SERVER],  # MANAGER can only create KITCHEN and SERVER users
}
create_user_role_checker = RoleChecker(allowed_roles=[Role.ADMIN, Role.MANAGER])
list_users_role_checker = RoleChecker(allowed_roles=[Role.ADMIN])
manage_user_status_role_checker = RoleChecker(allowed_roles=[Role.ADMIN])

REFRESH_ACCESS_TOKEN_EXPIRY_DAYS = 7


@router.post(
    "/users",
    response_model=SuccessSchema[UserResponse],
    responses=error_responses(InsufficientPermissionException, UserAlreadyExistsException),
    status_code=status.HTTP_201_CREATED,
    openapi_extra={
        "parameters": [
            {
                "name": "Authorization",
                "in": "header",
                "required": True,
                "description": "The access token to use for authentication.",
                "schema": {"type": "string", "example": "Bearer eyJhbGciOiJIUzI1NiIs..."},
            }
        ]
    },
)
async def create_user(
    user_data: UserCreate,
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(create_user_role_checker),
):
    """Create a new user with the specified role.
    Only ADMIN users can create users of any role, while MANAGER users can only create KITCHEN and SERVER users.
    """  # noqa: E501
    allowed = ROLE_CREATION_PERMISSIONS.get(current_user.role, [])
    if user_data.role not in allowed:
        raise InsufficientPermissionException()
    user_exists = await user_service.user_already_exists(user_data.email, session)
    if user_exists:
        raise UserAlreadyExistsException()
    new_user = await user_service.create_user(user_data, session, role=user_data.role)
    await audit_service.register(
        session,
        action=AuditAction.USER_CREATED,
        resource="user",
        resource_id=new_user.id,
        user_id=current_user.id,
        details={
            "created_user_id": str(new_user.id),
            "created_role": new_user.role.value,
            "actor_role": current_user.role.value,
        },
        ip=get_request_ip(request),
    )
    await session.commit()
    token = create_url_safe_token(
        {
            "email": new_user.email,
            "id": str(uuid.uuid4()),
            "exp": (datetime.now(timezone.utc) + timedelta(hours=1)).timestamp(),
        }
    )
    html_message = generate_user_verify_email_template(new_user.name, token)
    send_mail.delay(
        recipients=[new_user.email],
        subject="Bem-vindo ao Raízes do Nordeste!",
        body=html_message,
    )
    return SuccessSchema(message="Usuário criado com sucesso.", result=new_user)


@router.get(
    "/users",
    response_model=SuccessSchema[UserListResponse],
    responses=error_responses(InsufficientPermissionException),
    status_code=status.HTTP_200_OK,
    openapi_extra={
        "parameters": [
            {
                "name": "Authorization",
                "in": "header",
                "required": True,
                "description": "The access token to use for authentication.",
                "schema": {"type": "string", "example": "Bearer eyJhbGciOiJIUzI1NiIs..."},
            }
        ]
    },
)
async def list_users(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_async_session),
    _current_user: User = Depends(list_users_role_checker),
):
    """List users. Requires ADMIN role."""
    users, total = await user_service.list_users(session, page=page, limit=limit)
    result = UserListResponse(items=users, total=total, page=page, limit=limit)
    return SuccessSchema(message="Usuários obtidos com sucesso.", result=result)


@router.patch(
    "/users/{user_id}/status",
    response_model=SuccessSchema[UserResponse],
    responses=error_responses(
        AdminStatusConflictException, InsufficientPermissionException, UserNotFoundException
    ),
    status_code=status.HTTP_200_OK,
    openapi_extra={
        "parameters": [
            {
                "name": "Authorization",
                "in": "header",
                "required": True,
                "description": "The access token to use for authentication.",
                "schema": {"type": "string", "example": "Bearer eyJhbGciOiJIUzI1NiIs..."},
            }
        ]
    },
)
async def update_user_status(
    user_id: uuid.UUID,
    status_data: UserStatusUpdate,
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(manage_user_status_role_checker),
):
    """Activate or deactivate a user. Requires ADMIN role."""
    user = await user_service.get_user_by_id(user_id, session)
    if not user:
        raise UserNotFoundException()
    if not status_data.is_active and user.role == Role.ADMIN:
        if user.id == current_user.id or not await user_service.has_other_active_admin(user.id, session):
            raise AdminStatusConflictException()
    updated_user = await user_service.update_user({"is_active": status_data.is_active}, user, session)
    await audit_service.register(
        session,
        action=(AuditAction.USER_ACTIVATED if status_data.is_active else AuditAction.USER_DEACTIVATED),
        resource="user",
        resource_id=updated_user.id,
        user_id=current_user.id,
        details={
            "target_user_id": str(updated_user.id),
            "is_active": updated_user.is_active,
            "actor_role": current_user.role.value,
        },
        ip=get_request_ip(request),
    )
    await session.commit()
    return SuccessSchema(message="Status do usuário atualizado com sucesso.", result=updated_user)


@router.post(
    "/register",
    response_model=SuccessSchema[UserResponse],
    status_code=status.HTTP_201_CREATED,
    responses=error_responses(UserAlreadyExistsException, PrivacyConsentRequiredException),
)
async def register(
    user_data: UserRegister,
    request: Request,
    session: AsyncSession = Depends(get_async_session),
):
    """Public route for CUSTOMER registration."""
    if not user_data.privacy_consent:
        raise PrivacyConsentRequiredException()
    user_exists = await user_service.user_already_exists(user_data.email, session)
    if user_exists:
        raise UserAlreadyExistsException()
    new_user = await user_service.create_user(user_data, session, role=Role.CUSTOMER)
    await privacy_service.register_account_consents(
        new_user.id,
        user_data.marketing_consent,
        session,
        actor_id=new_user.id,
        ip=get_request_ip(request),
    )
    await audit_service.register(
        session,
        action=AuditAction.USER_REGISTERED,
        resource="user",
        resource_id=new_user.id,
        user_id=new_user.id,
        details={
            "role": new_user.role.value,
            "privacy_consent": user_data.privacy_consent,
            "marketing_consent": user_data.marketing_consent,
        },
        ip=get_request_ip(request),
    )
    await session.commit()
    token = create_url_safe_token(
        {
            "email": new_user.email,
            "id": str(uuid.uuid4()),
            "exp": (datetime.now(timezone.utc) + timedelta(hours=1)).timestamp(),
        }
    )
    html_message = generate_user_verify_email_template(new_user.name, token)
    send_mail.delay(
        recipients=[new_user.email],
        subject="Bem-vindo ao Raízes do Nordeste!",
        body=html_message,
    )
    return SuccessSchema(message="Usuário cadastrado com sucesso.", result=new_user)


@router.get(
    "/verify/{token}",
    status_code=status.HTTP_200_OK,
    response_model=SuccessSchema[None],
    responses=error_responses(InvalidTokenException, UserNotFoundException),
)
async def verify_email(
    token: str,
    request: Request,
    session: AsyncSession = Depends(get_async_session),
):
    """Verify a user's email address after registration."""
    token_data = decode_url_safe_token(token)
    if not token_data:
        raise InvalidTokenException()
    user_email = token_data.get("email")
    if not user_email:
        raise InvalidTokenException()
    user = await user_service.get_user_by_email(user_email, session)
    if not user:
        raise UserNotFoundException()
    if user.is_verified:
        return SuccessSchema(message="E-mail já verificado.", result=None)
    await user_service.update_user({"is_verified": True}, user, session)
    await audit_service.register(
        session,
        action=AuditAction.USER_EMAIL_VERIFIED,
        resource="user",
        resource_id=user.id,
        user_id=user.id,
        details={"is_verified": True},
        ip=get_request_ip(request),
    )
    await session.commit()
    return SuccessSchema(message="Email verificado com sucesso.", result=None)


@router.post(
    "/login",
    response_model=SuccessSchema[TokenResponse],
    responses=error_responses(InvalidCredentials),
)
async def login(
    login_data: LoginRequest,
    request: Request,
    session: AsyncSession = Depends(get_async_session),
):
    """Authenticate a user with email and password."""
    email = login_data.email
    password = login_data.password
    user = await user_service.get_user_by_email(email, session)
    if not user:
        raise InvalidCredentials()
    if not user.is_active:
        raise AccountInactiveException()
    password_valid = verify_password(password, user.password_hash)
    if not password_valid:
        raise InvalidCredentials()
    access_token = create_access_token(
        user_data={"email": user.email, "user_id": str(user.id), "role": user.role}
    )
    refresh_token = create_access_token(
        user_data={"email": user.email, "user_id": str(user.id), "role": user.role},
        refresh=True,
        expiry=timedelta(days=REFRESH_ACCESS_TOKEN_EXPIRY_DAYS),
    )
    await audit_service.register(
        session,
        action=AuditAction.USER_LOGIN,
        resource="auth",
        resource_id=user.id,
        user_id=user.id,
        details={"role": user.role.value},
        ip=get_request_ip(request),
    )
    await session.commit()
    return SuccessSchema(
        message="Autenticado com sucesso!",
        result={
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": user,
        },
    )


@router.get(
    "/refresh",
    status_code=status.HTTP_200_OK,
    response_model=SuccessSchema[TokenResponse],
    responses=error_responses(
        AccountInactiveException, UserSessionExpiredException, UserNotFoundException
    ),
    openapi_extra={
        "parameters": [
            {
                "name": "Authorization",
                "in": "header",
                "required": True,
                "description": "The refresh token to use for authentication.",
                "schema": {"type": "string", "example": "Bearer eyJhbGciOiJIUzI1NiIs..."},
            }
        ]
    },
)
async def refresh(
    request: Request,
    token_details: dict = Depends(RefreshTokenBearer()),
    session: AsyncSession = Depends(get_async_session),
):
    """Refresh the authentication token."""
    expiry_timestamp = token_details["exp"]
    if datetime.fromtimestamp(expiry_timestamp, tz=timezone.utc) < get_utc_now():
        raise UserSessionExpiredException()

    user_email = token_details["user"]["email"]
    user = await user_service.get_user_by_email(user_email, session)
    if not user:
        raise UserNotFoundException()
    if not user.is_active:
        raise AccountInactiveException()

    old_refresh_jti = token_details["jti"]
    await add_jti_to_blocklist(old_refresh_jti)

    new_access_token = create_access_token(user_data=token_details["user"])
    new_refresh_token = create_access_token(
        user_data={"email": user.email, "user_id": str(user.id), "role": user.role},
        refresh=True,
        expiry=timedelta(days=REFRESH_ACCESS_TOKEN_EXPIRY_DAYS),
    )
    await audit_service.register(
        session,
        action=AuditAction.USER_TOKEN_REFRESHED,
        resource="auth",
        resource_id=user.id,
        user_id=user.id,
        details={"old_refresh_token_revoked": True},
        ip=get_request_ip(request),
    )
    await session.commit()
    return SuccessSchema(
        message="Token atualizado com sucesso!",
        result={
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "user": user,
        },
    )


@router.get(
    "/me",
    response_model=SuccessSchema[UserResponse],
    openapi_extra={
        "parameters": [
            {
                "name": "Authorization",
                "in": "header",
                "required": True,
                "description": "The access token to use for authentication.",
                "schema": {"type": "string", "example": "Bearer eyJhbGciOiJIUzI1NiIs..."},
            }
        ]
    },
)
async def me(user: User = Depends(get_current_user)):
    """Return the data of the authenticated user."""
    return SuccessSchema(message="Dados do usuário obtidos com sucesso!", result=user)


@router.patch(
    "/me",
    response_model=SuccessSchema[UserResponse],
    status_code=status.HTTP_200_OK,
    openapi_extra={
        "parameters": [
            {
                "name": "Authorization",
                "in": "header",
                "required": True,
                "description": "The access token to use for authentication.",
                "schema": {"type": "string", "example": "Bearer eyJhbGciOiJIUzI1NiIs..."},
            }
        ]
    },
)
async def update_me(
    data: UserSelfUpdate,
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """Update the authenticated user's own profile data."""
    update_data = data.model_dump(exclude_unset=True)
    updated_user = await user_service.update_user(update_data, current_user, session)
    await audit_service.register(
        session,
        action=AuditAction.USER_UPDATED,
        resource="user",
        resource_id=updated_user.id,
        user_id=updated_user.id,
        details={"changed_fields": list(update_data.keys())},
        ip=get_request_ip(request),
    )
    await session.commit()
    return SuccessSchema(message="Dados do usuário atualizados com sucesso.", result=updated_user)


@router.post("/logout", status_code=status.HTTP_200_OK, response_model=SuccessSchema[None])
async def logout(
    logout_data: LogoutRequest,
    request: Request,
    token_details: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_async_session),
):
    """Logout the authenticated user."""
    jti = token_details["jti"]
    await add_jti_to_blocklist(jti)
    refresh_token_data = decode_token(logout_data.refresh_token)
    refresh_token_revoked = bool(refresh_token_data and refresh_token_data.get("refresh"))
    if refresh_token_revoked:
        refresh_jti = refresh_token_data["jti"]
        await add_jti_to_blocklist(refresh_jti)
    user_data = token_details.get("user", {})
    user_id = user_data.get("user_id")
    try:
        parsed_user_id = uuid.UUID(user_id) if user_id else None
    except ValueError:
        parsed_user_id = None
    await audit_service.register(
        session,
        action=AuditAction.USER_LOGOUT,
        resource="auth",
        resource_id=parsed_user_id,
        user_id=parsed_user_id,
        details={"refresh_token_revoked": refresh_token_revoked},
        ip=get_request_ip(request),
    )
    await session.commit()
    return SuccessSchema(message="Logout realizado com sucesso!", result=None)


@router.post(
    "/reset_password", response_model=SuccessSchema[None], responses=error_responses(UserNotFoundException)
)
async def reset_password(
    reset_data: PasswordResetRequestSchema,
    request: Request,
    session: AsyncSession = Depends(get_async_session),
):
    """Request a password reset with the given email."""
    email = reset_data.email
    user = await user_service.get_user_by_email(email, session)
    if user:
        token = create_url_safe_token(
            {
                "email": email,
                "id": str(uuid.uuid4()),
                "exp": (datetime.now(timezone.utc) + timedelta(hours=1)).timestamp(),
            }
        )
        html_message = generate_user_request_reset_password_template(token)
        send_mail.delay(
            recipients=[email],
            subject="Redefinição de senha",
            body=html_message,
        )
        await audit_service.register(
            session,
            action=AuditAction.PASSWORD_RESET_REQUESTED,
            resource="auth",
            resource_id=user.id,
            user_id=user.id,
            details={"reset_email_sent": True},
            ip=get_request_ip(request),
        )
        await session.commit()
    # Always return success, even if the email was not sent (e.g., user not found).
    # Prevents leaking information about the existence of the user.
    return SuccessSchema(message="E-mail de redefinição de senha enviado com sucesso!", result=None)


@router.post(
    "/reset_password_confirm",
    response_model=SuccessSchema[None],
    responses=error_responses(PasswordsDoNotMatchException, InvalidTokenException, UserNotFoundException),
)
async def reset_password_confirm(
    reset_password_data: PasswordResetConfirmSchema,
    request: Request,
    session: AsyncSession = Depends(get_async_session),
):
    """Reset the password using the given token and new password."""
    new_password = reset_password_data.password
    new_password_confirm = reset_password_data.password_confirm
    if new_password != new_password_confirm:
        raise PasswordsDoNotMatchException()
    token = reset_password_data.token
    token_data = decode_url_safe_token(token)
    if not token_data:
        raise InvalidTokenException()

    token_id = token_data.get("id")
    if token_id and await reset_token_in_blocklist(str(token_id)):
        raise ResetTokenInvalidException()

    email = token_data["email"]
    user = await user_service.get_user_by_email(email, session)
    if not user:
        raise UserNotFoundException()
    password_hash = generate_password_hash(new_password)
    await user_service.update_user({"password_hash": password_hash}, user, session)

    if token_id:
        await add_reset_token_to_blocklist(str(token_id))
    await audit_service.register(
        session,
        action=AuditAction.PASSWORD_RESET_CONFIRMED,
        resource="auth",
        resource_id=user.id,
        user_id=user.id,
        details={"reset_token_revoked": bool(token_id)},
        ip=get_request_ip(request),
    )
    await session.commit()
    return SuccessSchema(message="Senha redefinida com sucesso!", result=None)
