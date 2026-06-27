import uuid

from fastapi import APIRouter, Depends, Query, Request, status
from sqlmodel.ext.asyncio.session import AsyncSession

from src.auth.dependencies import RoleChecker
from src.auth.exceptions import InsufficientPermissionException
from src.auth.models import Role, User
from src.database import get_async_session
from src.exceptions import error_responses
from src.promotions.exceptions import (
    PromotionInvalidPeriodException,
    PromotionNotFoundException,
)
from src.promotions.schemas import (
    PromotionCreate,
    PromotionListResponse,
    PromotionResponse,
    PromotionUpdate,
)
from src.promotions.service import promotion_service
from src.schemas import SuccessSchema

router = APIRouter(prefix="/promotions", tags=["promotions"])
manage_promotions = RoleChecker(allowed_roles=[Role.ADMIN, Role.MANAGER])
view_promotions = RoleChecker(allowed_roles=list(Role))
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
    response_model=SuccessSchema[PromotionResponse],
    responses=error_responses(InsufficientPermissionException),
    status_code=status.HTTP_201_CREATED,
    openapi_extra=AUTHORIZATION_OPENAPI_EXTRA,
)
async def create_promotion(
    data: PromotionCreate,
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(manage_promotions),
):
    """Create a promotion. Requires ADMIN or MANAGER role."""
    promotion = await promotion_service.create_promotion(
        data,
        session,
        current_user.id,
        request.client.host if request.client else None,
    )
    return SuccessSchema(message="Promoção criada com sucesso.", result=promotion)


@router.get(
    "/",
    response_model=SuccessSchema[PromotionListResponse],
    responses=error_responses(InsufficientPermissionException),
    status_code=status.HTTP_200_OK,
    openapi_extra=AUTHORIZATION_OPENAPI_EXTRA,
)
async def list_promotions(
    page: int = Query(default=1, ge=1, description="Page number."),
    limit: int = Query(default=20, ge=1, le=100, description="Items per page."),
    available_only: bool = Query(
        default=True,
        alias="availableOnly",
        description="Return only active promotions within their validity period.",
    ),
    session: AsyncSession = Depends(get_async_session),
    _current_user: User = Depends(view_promotions),
):
    """List promotions with pagination and an availability filter."""
    items, total = await promotion_service.list_promotions(
        session, page=page, limit=limit, available_only=available_only
    )
    result = PromotionListResponse(items=items, total=total, page=page, limit=limit)
    return SuccessSchema(message="Promoções obtidas com sucesso.", result=result)


@router.get(
    "/{promotion_id}",
    response_model=SuccessSchema[PromotionResponse],
    responses=error_responses(InsufficientPermissionException, PromotionNotFoundException),
    status_code=status.HTTP_200_OK,
    openapi_extra=AUTHORIZATION_OPENAPI_EXTRA,
)
async def get_promotion(
    promotion_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
    _current_user: User = Depends(view_promotions),
):
    """Get a promotion by id. Requires an authenticated user."""
    promotion = await promotion_service.get_promotion_by_id(promotion_id, session)
    if promotion is None:
        raise PromotionNotFoundException()
    return SuccessSchema(message="Promoção obtida com sucesso.", result=promotion)


@router.patch(
    "/{promotion_id}",
    response_model=SuccessSchema[PromotionResponse],
    responses=error_responses(
        InsufficientPermissionException,
        PromotionNotFoundException,
        PromotionInvalidPeriodException,
    ),
    status_code=status.HTTP_200_OK,
    openapi_extra=AUTHORIZATION_OPENAPI_EXTRA,
)
async def update_promotion(
    promotion_id: uuid.UUID,
    data: PromotionUpdate,
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(manage_promotions),
):
    """Update a promotion, its validity period, or active state. Requires ADMIN or MANAGER role."""
    promotion = await promotion_service.get_promotion_by_id(promotion_id, session)
    if promotion is None:
        raise PromotionNotFoundException()
    updated = await promotion_service.update_promotion(
        promotion,
        data,
        session,
        current_user.id,
        request.client.host if request.client else None,
    )
    return SuccessSchema(message="Promoção atualizada com sucesso.", result=updated)


@router.delete(
    "/{promotion_id}",
    response_model=SuccessSchema[PromotionResponse],
    responses=error_responses(InsufficientPermissionException, PromotionNotFoundException),
    status_code=status.HTTP_200_OK,
    openapi_extra=AUTHORIZATION_OPENAPI_EXTRA,
)
async def deactivate_promotion(
    promotion_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(manage_promotions),
):
    """Deactivate a promotion without deleting its history. Requires ADMIN or MANAGER role."""
    promotion = await promotion_service.get_promotion_by_id(promotion_id, session)
    if promotion is None:
        raise PromotionNotFoundException()
    deactivated = await promotion_service.deactivate_promotion(
        promotion,
        session,
        current_user.id,
        request.client.host if request.client else None,
    )
    return SuccessSchema(message="Promoção desativada com sucesso.", result=deactivated)
