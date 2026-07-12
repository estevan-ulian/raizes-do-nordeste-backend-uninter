import uuid

from fastapi import APIRouter, Depends, Query, Request, status
from sqlmodel.ext.asyncio.session import AsyncSession

from src.auth.dependencies import RoleChecker
from src.auth.exceptions import InsufficientPermissionException
from src.auth.models import Role, User
from src.database import get_async_session
from src.exceptions import error_responses
from src.schemas import SuccessSchema
from src.units.exceptions import UnitNotFoundException
from src.units.schemas import UnitCreate, UnitResponse, UnitUpdate
from src.units.service import UnitService
from src.utils import get_request_ip

router = APIRouter(prefix="/units", tags=["units"])
unit_service = UnitService()
manage_units_role_checker = RoleChecker(allowed_roles=[Role.ADMIN, Role.MANAGER])
AUTHORIZATION_OPENAPI_EXTRA = {
    "parameters": [
        {
            "name": "Authorization",
            "in": "header",
            "required": True,
            "description": "The access token to use for authentication.",
            "schema": {"type": "string", "example": "Bearer eyJhbGciOiJIUzI1NiIs..."},
        }
    ]
}


@router.post(
    "/",
    response_model=SuccessSchema[UnitResponse],
    responses=error_responses(InsufficientPermissionException),
    status_code=status.HTTP_201_CREATED,
    openapi_extra=AUTHORIZATION_OPENAPI_EXTRA,
)
async def create_unit(
    unit_data: UnitCreate,
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(manage_units_role_checker),
):
    """Create a new business unit. Requires ADMIN or MANAGER role."""
    new_unit = await unit_service.create_unit(
        unit_data, session, actor_id=current_user.id, ip=get_request_ip(request)
    )
    return SuccessSchema(message="Unidade criada com sucesso.", result=new_unit)


@router.get(
    "/",
    response_model=SuccessSchema[list[UnitResponse]],
    responses=error_responses(InsufficientPermissionException),
    status_code=status.HTTP_200_OK,
    openapi_extra=AUTHORIZATION_OPENAPI_EXTRA,
)
async def list_units(
    include_inactive: bool = Query(default=False, alias="includeInactive"),
    session: AsyncSession = Depends(get_async_session),
    _current_user: User = Depends(manage_units_role_checker),
):
    """List business units."""
    units = await unit_service.list_units(session, include_inactive=include_inactive)
    return SuccessSchema(message="Unidades obtidas com sucesso.", result=units)


@router.get(
    "/{unit_id}",
    response_model=SuccessSchema[UnitResponse],
    responses=error_responses(InsufficientPermissionException, UnitNotFoundException),
    status_code=status.HTTP_200_OK,
    openapi_extra=AUTHORIZATION_OPENAPI_EXTRA,
)
async def get_unit(
    unit_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
    _current_user: User = Depends(manage_units_role_checker),
):
    """Get a business unit by id."""
    unit = await unit_service.get_unit_by_id(unit_id, session)
    if not unit:
        raise UnitNotFoundException()
    return SuccessSchema(message="Unidade obtida com sucesso.", result=unit)


@router.patch(
    "/{unit_id}",
    response_model=SuccessSchema[UnitResponse],
    responses=error_responses(InsufficientPermissionException, UnitNotFoundException),
    status_code=status.HTTP_200_OK,
    openapi_extra=AUTHORIZATION_OPENAPI_EXTRA,
)
async def update_unit(
    unit_id: uuid.UUID,
    unit_data: UnitUpdate,
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(manage_units_role_checker),
):
    """Update a business unit. Requires ADMIN or MANAGER role."""
    unit = await unit_service.get_unit_by_id(unit_id, session)
    if not unit:
        raise UnitNotFoundException()
    updated_unit = await unit_service.update_unit(
        unit, unit_data, session, actor_id=current_user.id, ip=get_request_ip(request)
    )
    return SuccessSchema(message="Unidade atualizada com sucesso.", result=updated_unit)


@router.delete(
    "/{unit_id}",
    response_model=SuccessSchema[UnitResponse],
    responses=error_responses(InsufficientPermissionException, UnitNotFoundException),
    status_code=status.HTTP_200_OK,
    openapi_extra=AUTHORIZATION_OPENAPI_EXTRA,
)
async def deactivate_unit(
    unit_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(manage_units_role_checker),
):
    """Deactivate a business unit. Requires ADMIN or MANAGER role."""
    unit = await unit_service.get_unit_by_id(unit_id, session)
    if not unit:
        raise UnitNotFoundException()
    deactivated_unit = await unit_service.deactivate_unit(
        unit, session, actor_id=current_user.id, ip=get_request_ip(request)
    )
    return SuccessSchema(message="Unidade desativada com sucesso.", result=deactivated_unit)
