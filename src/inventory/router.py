import uuid

from fastapi import APIRouter, Depends, Query, Request, status
from sqlmodel.ext.asyncio.session import AsyncSession

from src.auth.dependencies import RoleChecker
from src.auth.exceptions import InsufficientPermissionException
from src.auth.models import Role, User
from src.database import get_async_session
from src.exceptions import error_responses
from src.inventory.exceptions import InventoryInsufficientException, InventoryNotFoundException
from src.inventory.schemas import InventoryListResponse, InventoryMovementCreate, InventoryResponse
from src.inventory.service import InventoryService
from src.products.exceptions import ProductNotFoundException
from src.products.service import ProductService
from src.schemas import SuccessSchema
from src.units.exceptions import UnitNotFoundException
from src.units.service import UnitService
from src.utils import get_request_ip

router = APIRouter(prefix="/inventory", tags=["inventory"])
inventory_service = InventoryService()
product_service = ProductService()
unit_service = UnitService()
manage_inventory_role_checker = RoleChecker(allowed_roles=[Role.ADMIN, Role.MANAGER])
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
    "/movements",
    response_model=SuccessSchema[InventoryResponse],
    responses=error_responses(
        InsufficientPermissionException,
        InventoryInsufficientException,
        InventoryNotFoundException,
        ProductNotFoundException,
        UnitNotFoundException,
    ),
    status_code=status.HTTP_200_OK,
    openapi_extra=AUTHORIZATION_OPENAPI_EXTRA,
)
async def apply_inventory_movement(
    movement_data: InventoryMovementCreate,
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(manage_inventory_role_checker),
):
    """Apply an inventory entry or exit movement."""
    await ensure_unit_and_product_match(movement_data.unit_id, movement_data.product_id, session)
    ip = get_request_ip(request)
    inventory_item = await inventory_service.apply_movement(
        movement_data, session, actor_id=current_user.id, ip=ip
    )
    return SuccessSchema(message="Movimentação de estoque registrada com sucesso.", result=inventory_item)


@router.get(
    "/",
    response_model=SuccessSchema[InventoryListResponse],
    responses=error_responses(
        InsufficientPermissionException,
        ProductNotFoundException,
        UnitNotFoundException,
    ),
    status_code=status.HTTP_200_OK,
    openapi_extra=AUTHORIZATION_OPENAPI_EXTRA,
)
async def list_inventory(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    unit_id: uuid.UUID | None = Query(default=None),
    product_id: uuid.UUID | None = Query(default=None),
    session: AsyncSession = Depends(get_async_session),
    _current_user: User = Depends(manage_inventory_role_checker),
):
    """List inventory balances by unit and product."""
    if unit_id and product_id:
        await ensure_unit_and_product_match(unit_id, product_id, session)
    elif unit_id:
        await ensure_unit_exists(unit_id, session)
    elif product_id:
        await ensure_product_exists(product_id, session)

    inventory_items, total = await inventory_service.list_inventory(
        session,
        page=page,
        limit=limit,
        unit_id=unit_id,
        product_id=product_id,
    )
    return SuccessSchema(
        message="Estoques obtidos com sucesso.",
        result=InventoryListResponse(items=inventory_items, total=total, page=page, limit=limit),
    )


async def ensure_unit_exists(unit_id: uuid.UUID, session: AsyncSession) -> None:
    unit = await unit_service.get_unit_by_id(unit_id, session)
    if not unit or not unit.is_active:
        raise UnitNotFoundException()


async def ensure_product_exists(product_id: uuid.UUID, session: AsyncSession):
    product = await product_service.get_product_by_id(product_id, session)
    if not product or not product.is_active:
        raise ProductNotFoundException()
    return product


async def ensure_unit_and_product_match(
    unit_id: uuid.UUID,
    product_id: uuid.UUID,
    session: AsyncSession,
) -> None:
    await ensure_unit_exists(unit_id, session)
    await ensure_product_exists(product_id, session)
