import uuid

from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.products.models import Product
from src.products.schemas import ProductCreate, ProductUpdate
from src.utils import get_utc_now


class ProductService:
    async def create_product(self, product_data: ProductCreate, session: AsyncSession) -> Product:
        new_product = Product(**product_data.model_dump())
        session.add(new_product)
        await session.commit()
        await session.refresh(new_product)
        return new_product

    async def list_products(
        self,
        session: AsyncSession,
        page: int = 1,
        limit: int = 20,
        unit_id: uuid.UUID | None = None,
        category: str | None = None,
        include_inactive: bool = False,
    ) -> tuple[list[Product], int]:
        filters = []
        if unit_id:
            filters.append(Product.unit_id == unit_id)
        if category:
            filters.append(func.lower(Product.category).contains(category.strip().lower()))
        if not include_inactive:
            filters.append(Product.is_active)

        total_statement = select(func.count(Product.id))
        for query_filter in filters:
            total_statement = total_statement.where(query_filter)
        total_result = await session.exec(total_statement)
        total = total_result.one()

        offset = (page - 1) * limit
        statement = select(Product).order_by(Product.name).offset(offset).limit(limit)
        for query_filter in filters:
            statement = statement.where(query_filter)
        result = await session.exec(statement)
        return list(result.all()), total

    async def get_product_by_id(self, product_id: uuid.UUID, session: AsyncSession) -> Product | None:
        statement = select(Product).where(Product.id == product_id)
        result = await session.exec(statement)
        return result.one_or_none()

    async def update_product(
        self,
        product: Product,
        product_data: ProductUpdate,
        session: AsyncSession,
    ) -> Product:
        update_data = product_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(product, key, value)
        product.updated_at = get_utc_now()
        await session.commit()
        await session.refresh(product)
        return product

    async def deactivate_product(self, product: Product, session: AsyncSession) -> Product:
        product.is_active = False
        product.updated_at = get_utc_now()
        await session.commit()
        await session.refresh(product)
        return product
