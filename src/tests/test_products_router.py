from decimal import Decimal
from unittest.mock import AsyncMock

from src.tests.conftest import ADMIN_ID, PRODUCT_CATEGORY_ID, PRODUCT_ID


def test_create_product_passes_actor_and_ip(client, monkeypatch, now):
    from src.products import router as products_router

    product = {
        "id": PRODUCT_ID,
        "name": "Cuscuz",
        "description": None,
        "price": Decimal("12.50"),
        "category_id": PRODUCT_CATEGORY_ID,
        "image_url": None,
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }
    create_product_mock = AsyncMock(return_value=product)
    monkeypatch.setattr(products_router.product_service, "create_product", create_product_mock)

    response = client.post(
        "/products/",
        data={
            "name": "Cuscuz",
            "price": "12.50",
            "category_id": str(PRODUCT_CATEGORY_ID),
        },
    )

    assert response.status_code == 201
    create_product_mock.assert_awaited_once()
    _, kwargs = create_product_mock.await_args
    assert kwargs["actor_id"] == ADMIN_ID
    assert kwargs["ip"] == "testclient"


def test_create_product_category_passes_actor_and_ip(client, monkeypatch, now):
    from src.products import router as products_router

    category = {
        "id": PRODUCT_CATEGORY_ID,
        "name": "Pratos típicos",
        "created_at": now,
        "updated_at": now,
    }
    create_category_mock = AsyncMock(return_value=category)
    monkeypatch.setattr(products_router.product_service, "create_category", create_category_mock)

    response = client.post("/products/categories", json={"name": "Pratos típicos"})

    assert response.status_code == 201
    assert response.json()["result"]["name"] == "Pratos típicos"
    create_category_mock.assert_awaited_once()
    _, kwargs = create_category_mock.await_args
    assert kwargs["actor_id"] == ADMIN_ID
    assert kwargs["ip"] == "testclient"


def test_list_product_categories(client, monkeypatch, now):
    from src.products import router as products_router

    categories = [
        {
            "id": PRODUCT_CATEGORY_ID,
            "name": "Pratos típicos",
            "created_at": now,
            "updated_at": now,
        }
    ]
    list_categories_mock = AsyncMock(return_value=categories)
    monkeypatch.setattr(products_router.product_service, "list_categories", list_categories_mock)

    response = client.get("/products/categories")

    assert response.status_code == 200
    assert response.json()["result"][0]["name"] == "Pratos típicos"
    list_categories_mock.assert_awaited_once()


def test_update_product_passes_actor_and_ip(client, monkeypatch, now):
    from src.products import router as products_router

    existing_product = MagicProduct(image_url=None)
    updated_product = {
        "id": PRODUCT_ID,
        "name": "Cuscuz com queijo",
        "description": None,
        "price": Decimal("14.50"),
        "category_id": PRODUCT_CATEGORY_ID,
        "image_url": None,
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }
    monkeypatch.setattr(
        products_router.product_service,
        "get_product_by_id",
        AsyncMock(return_value=existing_product),
    )
    update_product_mock = AsyncMock(return_value=updated_product)
    monkeypatch.setattr(products_router.product_service, "update_product", update_product_mock)

    response = client.patch(
        f"/products/{PRODUCT_ID}",
        data={"name": "Cuscuz com queijo", "price": "14.50"},
    )

    assert response.status_code == 200
    update_product_mock.assert_awaited_once()
    _, kwargs = update_product_mock.await_args
    assert kwargs["actor_id"] == ADMIN_ID
    assert kwargs["ip"] == "testclient"


def test_deactivate_product_passes_actor_and_ip(client, monkeypatch, now):
    from src.products import router as products_router

    existing_product = MagicProduct(image_url=None)
    deactivated_product = {
        "id": PRODUCT_ID,
        "name": "Cuscuz",
        "description": None,
        "price": Decimal("12.50"),
        "category_id": PRODUCT_CATEGORY_ID,
        "image_url": None,
        "is_active": False,
        "created_at": now,
        "updated_at": now,
    }
    monkeypatch.setattr(
        products_router.product_service,
        "get_product_by_id",
        AsyncMock(return_value=existing_product),
    )
    deactivate_product_mock = AsyncMock(return_value=deactivated_product)
    monkeypatch.setattr(products_router.product_service, "deactivate_product", deactivate_product_mock)

    response = client.delete(f"/products/{PRODUCT_ID}")

    assert response.status_code == 200
    deactivate_product_mock.assert_awaited_once()
    _, kwargs = deactivate_product_mock.await_args
    assert kwargs["actor_id"] == ADMIN_ID
    assert kwargs["ip"] == "testclient"


class MagicProduct:
    def __init__(self, image_url):
        self.image_url = image_url
