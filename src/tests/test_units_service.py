from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from src.products.models import Product, ProductCategory
from src.tests.conftest import PRODUCT_CATEGORY_ID, PRODUCT_ID, UNIT_ID
from src.units.service import UnitService


@pytest.mark.asyncio
async def test_list_menu_returns_products_without_exposing_inventory_quantity(session, now):
    service = UnitService()
    category = ProductCategory(
        id=PRODUCT_CATEGORY_ID,
        name="Lanches",
        created_at=now,
        updated_at=now,
    )
    product = Product(
        id=PRODUCT_ID,
        name="X-Baião",
        description="Lanche regional",
        price=Decimal("29.90"),
        category_id=PRODUCT_CATEGORY_ID,
        image_url=None,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    total_result = MagicMock()
    total_result.one.return_value = 1
    items_result = MagicMock()
    items_result.all.return_value = [(product, category, 5)]
    session.exec.side_effect = [total_result, items_result]

    items, total = await service.list_menu(UNIT_ID, session)

    assert total == 1
    assert len(items) == 1
    assert items[0].id == PRODUCT_ID
    assert items[0].category.id == PRODUCT_CATEGORY_ID
    assert items[0].available is True
    assert "quantity" not in items[0].model_dump()
    statements = [str(call.args[0]) for call in session.exec.await_args_list]
    assert all("inventory.quantity >" in statement for statement in statements)


@pytest.mark.asyncio
async def test_list_menu_can_include_products_without_available_stock(session, now):
    service = UnitService()
    category = ProductCategory(
        id=PRODUCT_CATEGORY_ID,
        name="Lanches",
        created_at=now,
        updated_at=now,
    )
    product = Product(
        id=PRODUCT_ID,
        name="X-Baião",
        description=None,
        price=Decimal("29.90"),
        category_id=PRODUCT_CATEGORY_ID,
        image_url=None,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    total_result = MagicMock()
    total_result.one.return_value = 1
    items_result = MagicMock()
    items_result.all.return_value = [(product, category, None)]
    session.exec.side_effect = [total_result, items_result]

    items, total = await service.list_menu(
        UNIT_ID,
        session,
        include_unavailable=True,
    )

    assert total == 1
    assert items[0].available is False
    statements = [str(call.args[0]) for call in session.exec.await_args_list]
    assert all("inventory.quantity >" not in statement for statement in statements)
