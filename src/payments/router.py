from fastapi import APIRouter, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession

from src.auth.dependencies import RoleChecker
from src.auth.exceptions import InsufficientPermissionException
from src.auth.models import Role, User
from src.database import get_async_session
from src.exceptions import error_responses
from src.orders.exceptions import OrderStatusInvalidException
from src.payments.exceptions import PaymentAlreadyExistsException, PaymentInvalidException
from src.payments.schemas import PaymentCreate, PaymentResponse
from src.payments.service import PaymentService
from src.schemas import SuccessSchema

router = APIRouter(prefix="/payments", tags=["payments"])
payment_service = PaymentService()
payment_role_checker = RoleChecker(allowed_roles=[Role.ADMIN, Role.MANAGER, Role.SERVER, Role.CUSTOMER])
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
    response_model=SuccessSchema[PaymentResponse],
    responses=error_responses(
        InsufficientPermissionException,
        OrderStatusInvalidException,
        PaymentAlreadyExistsException,
        PaymentInvalidException,
    ),
    status_code=status.HTTP_200_OK,
    openapi_extra=AUTHORIZATION_OPENAPI_EXTRA,
)
async def request_mock_payment(
    payment_data: PaymentCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(payment_role_checker),
):
    """Request a mock payment and update the order when approved."""
    payment = await payment_service.request_mock_payment(payment_data, current_user, session)
    return SuccessSchema(message="Pagamento processado com sucesso.", result=payment)
