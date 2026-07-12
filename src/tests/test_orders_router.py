from decimal import Decimal
from unittest.mock import AsyncMock

from src.app import app
from src.auth.dependencies import get_optional_current_user
from src.orders.models import OrderChannel, OrderStatus
from src.tests.conftest import ADMIN_ID, CUSTOMER_ID, ORDER_ID, PRODUCT_ID, UNIT_ID


def test_create_order_passes_actor_and_ip(client, monkeypatch, now):
    from src.orders import router as orders_router

    order = {
        "id": ORDER_ID,
        "customer_id": CUSTOMER_ID,
        "unit_id": UNIT_ID,
        "order_channel": OrderChannel.APP,
        "status": OrderStatus.WAITING_FOR_PAYMENT,
        "total_amount": Decimal("25.00"),
        "payment_method": "MOCK",
        "discount_amount": Decimal("0.00"),
        "promotion_ids": [],
        "notes": None,
        "items": [
            {
                "id": PRODUCT_ID,
                "product_id": PRODUCT_ID,
                "quantity": 2,
                "unit_price": Decimal("12.50"),
                "subtotal": Decimal("25.00"),
            }
        ],
        "created_at": now,
        "updated_at": now,
    }
    create_order_mock = AsyncMock(return_value=order)
    monkeypatch.setattr(orders_router.order_service, "create_order", create_order_mock)

    response = client.post(
        "/orders/",
        json={
            "customer_id": str(CUSTOMER_ID),
            "unit_id": str(UNIT_ID),
            "order_channel": "APP",
            "items": [{"product_id": str(PRODUCT_ID), "quantity": 2}],
            "payment_method": "MOCK",
        },
    )

    assert response.status_code == 201
    create_order_mock.assert_awaited_once()
    _, kwargs = create_order_mock.await_args
    assert kwargs["actor_id"] == ADMIN_ID
    assert kwargs["ip"] == "testclient"


def test_create_totem_order_without_authorization(client, monkeypatch, now):
    from src.orders import router as orders_router

    async def override_optional_current_user():
        return None

    app.dependency_overrides[get_optional_current_user] = override_optional_current_user
    order = {
        "id": ORDER_ID,
        "customer_id": None,
        "unit_id": UNIT_ID,
        "order_channel": OrderChannel.TOTEM,
        "status": OrderStatus.WAITING_FOR_PAYMENT,
        "total_amount": Decimal("12.50"),
        "payment_method": "MOCK",
        "discount_amount": Decimal("0.00"),
        "promotion_ids": [],
        "notes": None,
        "items": [
            {
                "id": PRODUCT_ID,
                "product_id": PRODUCT_ID,
                "quantity": 1,
                "unit_price": Decimal("12.50"),
                "subtotal": Decimal("12.50"),
            }
        ],
        "created_at": now,
        "updated_at": now,
    }
    create_order_mock = AsyncMock(return_value=order)
    monkeypatch.setattr(orders_router.order_service, "create_order", create_order_mock)

    response = client.post(
        "/orders/",
        json={
            "unit_id": str(UNIT_ID),
            "order_channel": "TOTEM",
            "items": [{"product_id": str(PRODUCT_ID), "quantity": 1}],
            "payment_method": "MOCK",
        },
    )

    assert response.status_code == 201
    create_order_mock.assert_awaited_once()
    args, kwargs = create_order_mock.await_args
    assert args[1] is None
    assert kwargs["actor_id"] is None


def test_create_app_order_without_authorization_requires_token(client, monkeypatch):
    from src.orders import router as orders_router

    async def override_optional_current_user():
        return None

    app.dependency_overrides[get_optional_current_user] = override_optional_current_user
    create_order_mock = AsyncMock()
    monkeypatch.setattr(orders_router.order_service, "create_order", create_order_mock)

    response = client.post(
        "/orders/",
        json={
            "customer_id": str(CUSTOMER_ID),
            "unit_id": str(UNIT_ID),
            "order_channel": "APP",
            "items": [{"product_id": str(PRODUCT_ID), "quantity": 1}],
            "payment_method": "MOCK",
        },
    )

    assert response.status_code == 401
    create_order_mock.assert_not_awaited()
