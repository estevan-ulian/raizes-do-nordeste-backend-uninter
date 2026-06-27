import uuid
from decimal import Decimal

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.audit.service import AuditAction, audit_service
from src.auth.models import User
from src.loyalty.service import loyalty_service
from src.orders.models import OrderStatus
from src.orders.service import OrderService
from src.payments.exceptions import PaymentAlreadyExistsException, PaymentInvalidException
from src.payments.models import Payment, PaymentStatus
from src.payments.schemas import PaymentCreate
from src.utils import get_utc_now


class PaymentService:
    def __init__(self) -> None:
        self.order_service = OrderService()

    async def request_mock_payment(
        self,
        payment_data: PaymentCreate,
        current_user: User,
        session: AsyncSession,
        actor_id: uuid.UUID | None = None,
        ip: str | None = None,
    ) -> Payment:
        order = await self.order_service.get_order_by_id(payment_data.order_id, session)
        if not order:
            raise PaymentInvalidException()
        self.order_service.ensure_customer_owns_order(current_user, order)
        if order.status != OrderStatus.WAITING_FOR_PAYMENT:
            raise PaymentInvalidException()
        if await self.get_payment_by_order_id(order.id, session):
            raise PaymentAlreadyExistsException()

        payment_status = payment_data.force_status or PaymentStatus.APPROVED
        transaction_id = f"mock_{uuid.uuid4()}"
        gateway_response = {
            "provider": "mock",
            "status": payment_status.value,
            "transactionId": transaction_id,
            "amount": str(order.total_amount),
            "processedAt": get_utc_now().isoformat(),
        }
        payment = Payment(
            order_id=order.id,
            status=payment_status,
            amount=Decimal(order.total_amount),
            method=payment_data.method,
            gateway_response=gateway_response,
            gateway_transaction_id=transaction_id,
        )  # type: ignore
        session.add(payment)
        if payment_status == PaymentStatus.APPROVED:
            await self.order_service.mark_order_paid(order, session)
        await session.flush()
        await audit_service.register(
            session,
            action=AuditAction.PAYMENT_PROCESSED,
            resource="payment",
            resource_id=payment.id,
            user_id=actor_id or current_user.id,
            details={
                "order_id": str(order.id),
                "status": payment_status.value,
                "method": payment_data.method,
                "amount": str(order.total_amount),
            },
            ip=ip,
        )
        if payment_status == PaymentStatus.APPROVED:
            await loyalty_service.add_points(order.customer_id, order.total_amount, session)
        await session.commit()
        await session.refresh(payment)
        return payment

    async def get_payment_by_order_id(self, order_id: uuid.UUID, session: AsyncSession) -> Payment | None:
        statement = select(Payment).where(Payment.order_id == order_id)
        result = await session.exec(statement)
        return result.one_or_none()
