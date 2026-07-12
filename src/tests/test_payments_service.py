from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.auth.models import Role, User
from src.orders.models import OrderStatus
from src.payments.schemas import PaymentCreate
from src.payments.service import PaymentService
from src.tests.conftest import ADMIN_ID, CUSTOMER_ID, ORDER_ID


@pytest.mark.asyncio
async def test_payment_adds_loyalty_points_with_actor_and_ip(session, monkeypatch, now):
    from src.payments import service as payments_service_module

    order = SimpleNamespace(
        id=ORDER_ID,
        customer_id=CUSTOMER_ID,
        status=OrderStatus.WAITING_FOR_PAYMENT,
        total_amount=Decimal("25.00"),
    )
    current_user = User(
        id=ADMIN_ID,
        name="Admin",
        email="admin@example.com",
        password_hash="hash",
        role=Role.ADMIN,
        is_verified=True,
        created_at=now,
        updated_at=now,
    )
    service = PaymentService()
    service.order_service.get_order_by_id = AsyncMock(return_value=order)
    service.order_service.ensure_customer_owns_order = MagicMock()
    service.order_service.mark_order_paid = AsyncMock()
    service.get_payment_by_order_id = AsyncMock(return_value=None)
    audit_register_mock = AsyncMock()
    add_points_mock = AsyncMock(return_value=None)
    monkeypatch.setattr(payments_service_module.audit_service, "register", audit_register_mock)
    monkeypatch.setattr(payments_service_module.loyalty_service, "add_points", add_points_mock)

    await service.request_mock_payment(
        PaymentCreate(order_id=ORDER_ID, method="MOCK"),
        current_user,
        session,
        actor_id=ADMIN_ID,
        ip="203.0.113.10",
    )

    add_points_mock.assert_awaited_once_with(
        CUSTOMER_ID,
        Decimal("25.00"),
        session,
        actor_id=ADMIN_ID,
        ip="203.0.113.10",
    )


@pytest.mark.asyncio
async def test_anonymous_payment_approved_for_anonymous_order_does_not_add_loyalty_points(
    session, monkeypatch
):
    from src.payments import service as payments_service_module

    order = SimpleNamespace(
        id=ORDER_ID,
        customer_id=None,
        status=OrderStatus.WAITING_FOR_PAYMENT,
        total_amount=Decimal("25.00"),
    )
    service = PaymentService()
    service.order_service.get_order_by_id = AsyncMock(return_value=order)
    service.order_service.ensure_customer_owns_order = MagicMock()
    service.order_service.mark_order_paid = AsyncMock()
    service.get_payment_by_order_id = AsyncMock(return_value=None)
    monkeypatch.setattr(payments_service_module.audit_service, "register", AsyncMock())
    add_points_mock = AsyncMock(return_value=None)
    monkeypatch.setattr(payments_service_module.loyalty_service, "add_points", add_points_mock)

    await service.request_mock_payment(
        PaymentCreate(order_id=ORDER_ID, method="MOCK"),
        None,
        session,
        ip="203.0.113.10",
    )

    service.order_service.mark_order_paid.assert_awaited_once_with(order, session)
    service.order_service.ensure_customer_owns_order.assert_not_called()
    add_points_mock.assert_not_awaited()
