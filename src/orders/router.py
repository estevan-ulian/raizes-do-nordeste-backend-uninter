import uuid

from fastapi import APIRouter, Depends, Query, Request, status
from sqlmodel.ext.asyncio.session import AsyncSession

from src.auth.dependencies import RoleChecker, get_optional_current_user
from src.auth.exceptions import (
    AccessTokenRequiredException,
    AccountNotVerifiedException,
    InsufficientPermissionException,
)
from src.auth.models import Role, User
from src.database import get_async_session
from src.exceptions import error_responses
from src.orders.exceptions import (
    OrderCannotBeCanceledException,
    OrderItemInvalidException,
    OrderNotFoundException,
    OrderStockInsufficientException,
    OrderStatusInvalidException,
)
from src.orders.models import OrderChannel, OrderStatus
from src.orders.schemas import OrderCancel, OrderCreate, OrderListResponse, OrderResponse, OrderStatusUpdate
from src.orders.service import ANONYMOUS_ORDER_CHANNELS, OrderService
from src.schemas import SuccessSchema
from src.promotions.exceptions import PromotionNotApplicableException, PromotionNotFoundException
from src.utils import get_request_ip

router = APIRouter(prefix="/orders", tags=["orders"])
order_service = OrderService()
create_order_role_checker = RoleChecker(allowed_roles=[Role.ADMIN, Role.MANAGER, Role.SERVER, Role.CUSTOMER])
manage_order_role_checker = RoleChecker(allowed_roles=[Role.ADMIN, Role.MANAGER, Role.KITCHEN, Role.SERVER])
OPTIONAL_AUTHORIZATION_OPENAPI_EXTRA = {
    "parameters": [
        {
            "name": "Authorization",
            "in": "header",
            "required": False,
            "description": "Optional for TOTEM and COUNTER orders. Required for APP, WEB, and PICKUP orders.",
            "schema": {"type": "string", "example": "Bearer eyJhbGciOiJIUzI1NiIs..."},
        }
    ]
}


def ensure_create_order_permission(order_data: OrderCreate, current_user: User | None) -> None:
    if current_user is None:
        if order_data.order_channel in ANONYMOUS_ORDER_CHANNELS and order_data.customer_id is None:
            return
        raise AccessTokenRequiredException()
    if not current_user.is_verified:
        raise AccountNotVerifiedException()
    if current_user.role not in create_order_role_checker.allowed_roles:
        raise InsufficientPermissionException()


@router.post(
    "/",
    response_model=SuccessSchema[OrderResponse],
    responses=error_responses(
        AccessTokenRequiredException,
        AccountNotVerifiedException,
        InsufficientPermissionException,
        OrderItemInvalidException,
        OrderStockInsufficientException,
        PromotionNotApplicableException,
        PromotionNotFoundException,
    ),
    status_code=status.HTTP_201_CREATED,
    openapi_extra=OPTIONAL_AUTHORIZATION_OPENAPI_EXTRA,
)
async def create_order(
    order_data: OrderCreate,
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    current_user: User | None = Depends(get_optional_current_user),
):
    """Create an order with items and an origin channel."""
    ensure_create_order_permission(order_data, current_user)
    ip = get_request_ip(request)
    order = await order_service.create_order(
        order_data,
        current_user,
        session,
        actor_id=current_user.id if current_user else None,
        ip=ip,
    )
    return SuccessSchema(message="Pedido criado com sucesso.", result=order)


@router.get(
    "/",
    response_model=SuccessSchema[OrderListResponse],
    responses=error_responses(InsufficientPermissionException),
    status_code=status.HTTP_200_OK,
    openapi_extra=OPTIONAL_AUTHORIZATION_OPENAPI_EXTRA,
)
async def list_orders(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    order_channel: OrderChannel | None = Query(default=None),
    order_status: OrderStatus | None = Query(default=None),
    customer_id: uuid.UUID | None = Query(default=None),
    session: AsyncSession = Depends(get_async_session),
    _current_user: User = Depends(manage_order_role_checker),
):
    """List orders with pagination and filters."""
    orders, total = await order_service.list_orders(
        session,
        page=page,
        limit=limit,
        order_channel=order_channel,
        status=order_status,
        customer_id=customer_id,
    )
    return SuccessSchema(
        message="Pedidos obtidos com sucesso.",
        result=OrderListResponse(items=orders, total=total, page=page, limit=limit),
    )


@router.get(
    "/{order_id}",
    response_model=SuccessSchema[OrderResponse],
    responses=error_responses(InsufficientPermissionException, OrderNotFoundException),
    status_code=status.HTTP_200_OK,
    openapi_extra=OPTIONAL_AUTHORIZATION_OPENAPI_EXTRA,
)
async def get_order(
    order_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
    _current_user: User = Depends(manage_order_role_checker),
):
    """Get an order by id."""
    order = await order_service.get_order_response(order_id, session)
    return SuccessSchema(message="Pedido obtido com sucesso.", result=order)


@router.patch(
    "/{order_id}/status",
    response_model=SuccessSchema[OrderResponse],
    responses=error_responses(
        InsufficientPermissionException, OrderNotFoundException, OrderStatusInvalidException
    ),
    status_code=status.HTTP_200_OK,
    openapi_extra=OPTIONAL_AUTHORIZATION_OPENAPI_EXTRA,
)
async def update_order_status(
    order_id: uuid.UUID,
    status_data: OrderStatusUpdate,
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(manage_order_role_checker),
):
    """Update an order status following the allowed transitions."""
    ip = get_request_ip(request)
    order = await order_service.update_order_status(
        order_id, status_data.status, session, actor_id=current_user.id, ip=ip
    )
    return SuccessSchema(message="Status do pedido atualizado com sucesso.", result=order)


@router.post(
    "/{order_id}/cancel",
    response_model=SuccessSchema[OrderResponse],
    responses=error_responses(
        InsufficientPermissionException, OrderCannotBeCanceledException, OrderNotFoundException
    ),
    status_code=status.HTTP_200_OK,
    openapi_extra=OPTIONAL_AUTHORIZATION_OPENAPI_EXTRA,
)
async def cancel_order(
    order_id: uuid.UUID,
    _cancel_data: OrderCancel,
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(create_order_role_checker),
):
    """Cancel an order if its current status allows it."""
    order_to_cancel = await order_service.get_order_by_id(order_id, session)
    if not order_to_cancel:
        raise OrderNotFoundException()
    order_service.ensure_customer_owns_order(current_user, order_to_cancel)
    ip = get_request_ip(request)
    order = await order_service.cancel_order(order_id, session, actor_id=current_user.id, ip=ip)
    return SuccessSchema(message="Pedido cancelado com sucesso.", result=order)
