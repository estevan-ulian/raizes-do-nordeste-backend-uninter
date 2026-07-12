from decimal import Decimal
from unittest.mock import AsyncMock

from src.payments.models import PaymentStatus
from src.tests.conftest import ORDER_ID, PAYMENT_ID


def test_request_mock_payment_passes_anonymous_actor_and_ip(client, monkeypatch, now):
    from src.payments import router as payments_router

    payment = {
        "id": PAYMENT_ID,
        "order_id": ORDER_ID,
        "status": PaymentStatus.APPROVED,
        "amount": Decimal("25.00"),
        "method": "MOCK",
        "gateway_response": {"provider": "mock"},
        "gateway_transaction_id": "txn_1",
        "created_at": now,
        "updated_at": now,
    }
    request_mock_payment_mock = AsyncMock(return_value=payment)
    monkeypatch.setattr(payments_router.payment_service, "request_mock_payment", request_mock_payment_mock)

    response = client.post(
        "/payments/",
        json={"order_id": str(ORDER_ID), "method": "MOCK"},
    )

    assert response.status_code == 200
    request_mock_payment_mock.assert_awaited_once()
    _, kwargs = request_mock_payment_mock.await_args
    assert kwargs["actor_id"] is None
    assert kwargs["ip"] == "testclient"
