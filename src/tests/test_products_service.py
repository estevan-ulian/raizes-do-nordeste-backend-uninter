from unittest.mock import AsyncMock

import pytest
from sqlalchemy.exc import IntegrityError

from src.products.exceptions import ProductCategoryAlreadyExistsException
from src.products.schemas import ProductCategoryCreate
from src.products.service import ProductService


@pytest.mark.asyncio
async def test_create_category_translates_concurrent_unique_conflict(session):
    service = ProductService()
    service.get_category_by_name = AsyncMock(return_value=None)
    session.flush.side_effect = IntegrityError("insert", {}, Exception("unique violation"))

    with pytest.raises(ProductCategoryAlreadyExistsException):
        await service.create_category(ProductCategoryCreate(name="Bebidas"), session)

    session.rollback.assert_awaited_once()
    session.commit.assert_not_awaited()
