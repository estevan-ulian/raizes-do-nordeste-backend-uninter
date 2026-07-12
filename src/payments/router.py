from fastapi import APIRouter, Depends, Request, status
from sqlmodel.ext.asyncio.session import AsyncSession

from src.database import get_async_session
from src.exceptions import error_responses
from src.orders.exceptions import OrderStatusInvalidException
from src.payments.exceptions import PaymentAlreadyExistsException, PaymentInvalidException
from src.payments.schemas import PaymentCreate, PaymentResponse
from src.payments.service import PaymentService
from src.schemas import SuccessSchema
from src.utils import get_request_ip

router = APIRouter(prefix="/payments", tags=["payments"])
payment_service = PaymentService()


@router.post(
    "/",
    response_model=SuccessSchema[PaymentResponse],
    responses=error_responses(
        OrderStatusInvalidException,
        PaymentAlreadyExistsException,
        PaymentInvalidException,
    ),
    status_code=status.HTTP_200_OK,
)
async def request_mock_payment(
    payment_data: PaymentCreate,
    request: Request,
    session: AsyncSession = Depends(get_async_session),
):
    """Request a mock payment and update the order when approved."""
    ip = get_request_ip(request)
    payment = await payment_service.request_mock_payment(
        payment_data, None, session, actor_id=None, ip=ip
    )
    return SuccessSchema(message="Pagamento processado com sucesso.", result=payment)
