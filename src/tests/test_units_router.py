from types import SimpleNamespace
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from src.app import app
from src.database import get_async_session
from src.tests.conftest import ADMIN_ID, PRODUCT_CATEGORY_ID, PRODUCT_ID, UNIT_ID


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


def test_get_unit_menu_is_public_and_forwards_filters(session, monkeypatch):
    from src.units import router as units_router

    async def override_session():
        yield session

    unit = SimpleNamespace(id=UNIT_ID, name="Matriz", is_active=True)
    menu_item = {
        "id": PRODUCT_ID,
        "name": "X-Baião",
        "description": "Lanche regional",
        "price": "29.90",
        "image_url": "/api/uploads/products/x-baiao.webp",
        "category": {"id": PRODUCT_CATEGORY_ID, "name": "Lanches"},
        "available": False,
    }
    monkeypatch.setattr(
        units_router.unit_service,
        "get_unit_by_id",
        AsyncMock(return_value=unit),
    )
    list_menu_mock = AsyncMock(return_value=([menu_item], 1))
    monkeypatch.setattr(units_router.unit_service, "list_menu", list_menu_mock)
    app.dependency_overrides[get_async_session] = override_session

    public_client = TestClient(app)
    try:
        response = public_client.get(
            f"/units/{UNIT_ID}/menu",
            params={
                "page": 2,
                "limit": 10,
                "categoryId": str(PRODUCT_CATEGORY_ID),
                "includeUnavailable": "true",
            },
        )
    finally:
        public_client.close()
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["result"] == {
        "unit_id": str(UNIT_ID),
        "unit_name": "Matriz",
        "items": [
            {
                "id": str(PRODUCT_ID),
                "name": "X-Baião",
                "description": "Lanche regional",
                "price": "29.90",
                "image_url": "/api/uploads/products/x-baiao.webp",
                "category": {"id": str(PRODUCT_CATEGORY_ID), "name": "Lanches"},
                "available": False,
            }
        ],
        "total": 1,
        "page": 2,
        "limit": 10,
    }
    list_menu_mock.assert_awaited_once_with(
        UNIT_ID,
        session,
        page=2,
        limit=10,
        category_id=PRODUCT_CATEGORY_ID,
        include_unavailable=True,
    )


def test_get_unit_menu_rejects_inactive_unit(client, monkeypatch):
    from src.units import router as units_router

    unit = SimpleNamespace(id=UNIT_ID, name="Matriz", is_active=False)
    monkeypatch.setattr(
        units_router.unit_service,
        "get_unit_by_id",
        AsyncMock(return_value=unit),
    )
    list_menu_mock = AsyncMock()
    monkeypatch.setattr(units_router.unit_service, "list_menu", list_menu_mock)

    response = client.get(f"/units/{UNIT_ID}/menu")

    assert response.status_code == 404
    assert response.json()["success"] is False
    list_menu_mock.assert_not_awaited()
