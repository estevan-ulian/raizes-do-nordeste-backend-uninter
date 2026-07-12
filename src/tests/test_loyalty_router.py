from unittest.mock import AsyncMock

from src.auth.models import Role
from src.tests.conftest import CUSTOMER_ID, LOYALTY_ACCOUNT_ID, LOYALTY_REDEMPTION_ID


def test_create_redemption_passes_actor_and_ip(client, current_user, monkeypatch, now):
    from src.loyalty import router as loyalty_router

    current_user.id = CUSTOMER_ID
    current_user.role = Role.CUSTOMER
    redemption = {
        "id": LOYALTY_REDEMPTION_ID,
        "loyalty_account_id": LOYALTY_ACCOUNT_ID,
        "points_used": 10,
        "reward": "Sobremesa",
        "created_at": now,
    }
    redeem_points_mock = AsyncMock(return_value=redemption)
    monkeypatch.setattr(loyalty_router.loyalty_service, "redeem_points", redeem_points_mock)

    response = client.post("/loyalty/me/redemptions", json={"points_used": 10, "reward": "Sobremesa"})

    assert response.status_code == 201
    redeem_points_mock.assert_awaited_once()
    _, kwargs = redeem_points_mock.await_args
    assert kwargs["actor_id"] == CUSTOMER_ID
    assert kwargs["ip"] == "testclient"
