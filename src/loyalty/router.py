from fastapi import APIRouter, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession

from src.auth.dependencies import RoleChecker
from src.auth.exceptions import InsufficientPermissionException
from src.auth.models import Role, User
from src.database import get_async_session
from src.exceptions import error_responses
from src.loyalty.exceptions import (
    LoyaltyAccountNotFoundException,
    LoyaltyInsufficientPointsException,
)
from src.loyalty.schemas import (
    LoyaltyAccountResponse,
    LoyaltyRedemptionCreate,
    LoyaltyRedemptionResponse,
)
from src.loyalty.service import loyalty_service
from src.schemas import SuccessSchema

router = APIRouter(prefix="/loyalty", tags=["loyalty"])
customer_role_checker = RoleChecker(allowed_roles=[Role.CUSTOMER])
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


@router.get(
    "/me",
    response_model=SuccessSchema[LoyaltyAccountResponse],
    responses=error_responses(InsufficientPermissionException),
    status_code=status.HTTP_200_OK,
    openapi_extra=AUTHORIZATION_OPENAPI_EXTRA,
)
async def get_my_loyalty_account(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(customer_role_checker),
):
    """Return the loyalty account for the authenticated customer."""
    account = await loyalty_service.get_or_create_account(current_user.id, session)
    await session.commit()
    return SuccessSchema(message="Conta de fidelidade obtida com sucesso.", result=account)


@router.post(
    "/me/redemptions",
    response_model=SuccessSchema[LoyaltyRedemptionResponse],
    responses=error_responses(
        InsufficientPermissionException,
        LoyaltyAccountNotFoundException,
        LoyaltyInsufficientPointsException,
    ),
    status_code=status.HTTP_201_CREATED,
    openapi_extra=AUTHORIZATION_OPENAPI_EXTRA,
)
async def create_redemption(
    redemption_data: LoyaltyRedemptionCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(customer_role_checker),
):
    """Redeem loyalty points for a reward."""
    redemption = await loyalty_service.redeem_points(
        current_user.id, redemption_data.points_used, redemption_data.reward, session
    )
    return SuccessSchema(message="Resgate de fidelidade realizado com sucesso.", result=redemption)