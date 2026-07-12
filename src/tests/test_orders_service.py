from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from src.auth.models import Role, User
from src.inventory.models import Inventory
from src.orders.models import Order, OrderChannel, OrderStatus
from src.orders.exceptions import OrderItemInvalidException
from src.orders.schemas import OrderCreate, OrderItemCreate
from src.orders.service import OrderService
from src.products.models import Product
from src.tests.conftest import ADMIN_ID, ORDER_ID, PRODUCT_CATEGORY_ID, PRODUCT_ID, UNIT_ID
from src.units.models import Unit


class _ExecResult:
    def __init__(self, value=None, values=None):
        self.value = value
        self.values = values or []

    def one_or_none(self):
        return self.value

    def all(self):
        return self.values


@pytest.mark.asyncio
async def test_create_order_allows_anonymous_operational_channel(session, monkeypatch, now):
    from src.orders import service as orders_service_module

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
    unit = Unit(id=UNIT_ID, name="Unidade Centro", address="Rua A", is_active=True)
    product = Product(
        id=PRODUCT_ID,
        name="Baião Burger",
        price=Decimal("12.50"),
        category_id=PRODUCT_CATEGORY_ID,
        is_active=True,
    )
    inventory = Inventory(unit_id=UNIT_ID, product_id=PRODUCT_ID, quantity=3)
    created_response = {
        "id": ORDER_ID,
        "customer_id": None,
        "unit_id": UNIT_ID,
        "order_channel": OrderChannel.TOTEM,
        "status": OrderStatus.WAITING_FOR_PAYMENT,
        "total_amount": Decimal("25.00"),
        "payment_method": "MOCK",
        "discount_amount": Decimal("0.00"),
        "promotion_ids": [],
        "notes": None,
        "items": [],
        "created_at": now,
        "updated_at": now,
    }
    session.exec.side_effect = [
        _ExecResult(unit),
        _ExecResult(values=[product]),
        _ExecResult(values=[inventory]),
    ]
    audit_register_mock = AsyncMock()
    monkeypatch.setattr(orders_service_module.audit_service, "register", audit_register_mock)
    service = OrderService()
    service.get_order_response = AsyncMock(return_value=created_response)

    response = await service.create_order(
        OrderCreate(
            unit_id=UNIT_ID,
            order_channel=OrderChannel.TOTEM,
            items=[OrderItemCreate(product_id=PRODUCT_ID, quantity=2)],
            payment_method="MOCK",
        ),
        current_user,
        session,
        actor_id=ADMIN_ID,
        ip="203.0.113.10",
    )

    added_order = next(call.args[0] for call in session.add.call_args_list if isinstance(call.args[0], Order))
    assert response["customer_id"] is None
    assert added_order.customer_id is None
    assert added_order.payment_method == "MOCK"
    assert inventory.quantity == 1
    audit_register_mock.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize("order_channel", [OrderChannel.APP, OrderChannel.WEB, OrderChannel.PICKUP])
async def test_create_order_rejects_anonymous_identified_channels(session, now, order_channel):
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

    with pytest.raises(OrderItemInvalidException):
        await OrderService().create_order(
            OrderCreate(
                unit_id=UNIT_ID,
                order_channel=order_channel,
                items=[OrderItemCreate(product_id=PRODUCT_ID, quantity=2)],
            ),
            current_user,
            session,
        )

    session.exec.assert_not_awaited()
    session.add.assert_not_called()


@pytest.mark.asyncio
async def test_create_order_allows_anonymous_counter_channel(session, monkeypatch, now):
    from src.orders import service as orders_service_module

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
    unit = Unit(id=UNIT_ID, name="Unidade Centro", address="Rua A", is_active=True)
    product = Product(
        id=PRODUCT_ID,
        name="Baião Burger",
        price=Decimal("12.50"),
        category_id=PRODUCT_CATEGORY_ID,
        is_active=True,
    )
    inventory = Inventory(unit_id=UNIT_ID, product_id=PRODUCT_ID, quantity=3)
    created_response = {
        "id": ORDER_ID,
        "customer_id": None,
        "unit_id": UNIT_ID,
        "order_channel": OrderChannel.COUNTER,
        "status": OrderStatus.WAITING_FOR_PAYMENT,
        "total_amount": Decimal("25.00"),
        "payment_method": "MOCK",
        "discount_amount": Decimal("0.00"),
        "promotion_ids": [],
        "notes": None,
        "items": [],
        "created_at": now,
        "updated_at": now,
    }
    session.exec.side_effect = [
        _ExecResult(unit),
        _ExecResult(values=[product]),
        _ExecResult(values=[inventory]),
    ]
    monkeypatch.setattr(orders_service_module.audit_service, "register", AsyncMock())
    service = OrderService()
    service.get_order_response = AsyncMock(return_value=created_response)

    response = await service.create_order(
        OrderCreate(
            unit_id=UNIT_ID,
            order_channel=OrderChannel.COUNTER,
            items=[OrderItemCreate(product_id=PRODUCT_ID, quantity=2)],
        ),
        current_user,
        session,
    )

    added_order = next(call.args[0] for call in session.add.call_args_list if isinstance(call.args[0], Order))
    assert response["customer_id"] is None
    assert added_order.customer_id is None
    assert added_order.order_channel == OrderChannel.COUNTER
