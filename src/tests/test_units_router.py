from unittest.mock import AsyncMock

from src.tests.conftest import ADMIN_ID, UNIT_ID


def test_create_unit_passes_actor_and_ip(client, monkeypatch, now):
    from src.units import router as units_router

    unit = {
        "id": UNIT_ID,
        "name": "Matriz",
        "address": "Rua A",
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }
    create_unit_mock = AsyncMock(return_value=unit)
    monkeypatch.setattr(units_router.unit_service, "create_unit", create_unit_mock)

    response = client.post("/units/", json={"name": "Matriz", "address": "Rua A"})

    assert response.status_code == 201
    create_unit_mock.assert_awaited_once()
    _, kwargs = create_unit_mock.await_args
    assert kwargs["actor_id"] == ADMIN_ID
    assert kwargs["ip"] == "testclient"


def test_update_unit_passes_actor_and_ip(client, monkeypatch, now):
    from src.units import router as units_router

    unit = {
        "id": UNIT_ID,
        "name": "Matriz atualizada",
        "address": "Rua B",
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }
    monkeypatch.setattr(units_router.unit_service, "get_unit_by_id", AsyncMock(return_value=object()))
    update_unit_mock = AsyncMock(return_value=unit)
    monkeypatch.setattr(units_router.unit_service, "update_unit", update_unit_mock)

    response = client.patch(f"/units/{UNIT_ID}", json={"name": "Matriz atualizada"})

    assert response.status_code == 200
    update_unit_mock.assert_awaited_once()
    _, kwargs = update_unit_mock.await_args
    assert kwargs["actor_id"] == ADMIN_ID
    assert kwargs["ip"] == "testclient"


def test_deactivate_unit_passes_actor_and_ip(client, monkeypatch, now):
    from src.units import router as units_router

    unit = {
        "id": UNIT_ID,
        "name": "Matriz",
        "address": "Rua A",
        "is_active": False,
        "created_at": now,
        "updated_at": now,
    }
    monkeypatch.setattr(units_router.unit_service, "get_unit_by_id", AsyncMock(return_value=object()))
    deactivate_unit_mock = AsyncMock(return_value=unit)
    monkeypatch.setattr(units_router.unit_service, "deactivate_unit", deactivate_unit_mock)

    response = client.delete(f"/units/{UNIT_ID}")

    assert response.status_code == 200
    deactivate_unit_mock.assert_awaited_once()
    _, kwargs = deactivate_unit_mock.await_args
    assert kwargs["actor_id"] == ADMIN_ID
    assert kwargs["ip"] == "testclient"
