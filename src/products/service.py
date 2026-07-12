import uuid

from sqlalchemy.exc import IntegrityError
from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.audit.service import AuditAction, audit_service
from src.products.exceptions import (
    ProductCategoryAlreadyExistsException,
    ProductCategoryNotFoundException,
)
from src.products.models import Product, ProductCategory
from src.products.schemas import ProductCategoryCreate, ProductCreate, ProductUpdate
from src.utils import get_utc_now


class ProductService:
    async def create_category(
        self,
        category_data: ProductCategoryCreate,
        session: AsyncSession,
        actor_id: uuid.UUID | None = None,
        ip: str | None = None,
    ) -> ProductCategory:
        name = self._normalize_category_name(category_data.name)
        if await self.get_category_by_name(name, session):
            raise ProductCategoryAlreadyExistsException()
        category = ProductCategory(name=name)
        session.add(category)
        try:
            await session.flush()
        except IntegrityError as exc:
            await session.rollback()
            raise ProductCategoryAlreadyExistsException() from exc
        await audit_service.register(
            session,
            action=AuditAction.PRODUCT_CATEGORY_CREATED,
            resource="product_category",
            resource_id=category.id,
            user_id=actor_id,
            details={"name": category.name},
            ip=ip,
        )
        await session.commit()
        await session.refresh(category)
        return category

    async def list_categories(self, session: AsyncSession) -> list[ProductCategory]:
        statement = select(ProductCategory).order_by(ProductCategory.name)
        result = await session.exec(statement)
        return list(result.all())

    async def get_category_by_name(self, name: str, session: AsyncSession) -> ProductCategory | None:
        statement = select(ProductCategory).where(func.lower(ProductCategory.name) == name.strip().lower())
        result = await session.exec(statement)
        return result.one_or_none()

    async def get_category_by_id(
        self, category_id: uuid.UUID, session: AsyncSession
    ) -> ProductCategory | None:
        statement = select(ProductCategory).where(ProductCategory.id == category_id)
        result = await session.exec(statement)
        return result.one_or_none()

    async def create_product(
        self,
        product_data: ProductCreate,
        session: AsyncSession,
        actor_id: uuid.UUID | None = None,
        ip: str | None = None,
    ) -> Product:
        if not await self.get_category_by_id(product_data.category_id, session):
            raise ProductCategoryNotFoundException()
        new_product = Product(**product_data.model_dump())
        session.add(new_product)
        await session.flush()
        await self._audit(
            new_product,
            AuditAction.PRODUCT_CREATED,
            session,
            actor_id,
            ip,
            changed_fields=list(product_data.model_dump(exclude_unset=True).keys()),
        )
        await session.commit()
        await session.refresh(new_product)
        return new_product

    async def list_products(
        self,
        session: AsyncSession,
        page: int = 1,
        limit: int = 20,
        category_id: uuid.UUID | None = None,
        include_inactive: bool = False,
    ) -> tuple[list[Product], int]:
        filters = []
        if category_id:
            filters.append(Product.category_id == category_id)
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
        actor_id: uuid.UUID | None = None,
        ip: str | None = None,
    ) -> Product:
        update_data = product_data.model_dump(exclude_unset=True)
        category_id = update_data.get("category_id")
        if category_id and not await self.get_category_by_id(category_id, session):
            raise ProductCategoryNotFoundException()
        for key, value in update_data.items():
            setattr(product, key, value)
        product.updated_at = get_utc_now()
        await session.flush()
        await self._audit(
            product,
            AuditAction.PRODUCT_UPDATED,
            session,
            actor_id,
            ip,
            changed_fields=list(update_data.keys()),
        )
        await session.commit()
        await session.refresh(product)
        return product

    async def deactivate_product(
        self,
        product: Product,
        session: AsyncSession,
        actor_id: uuid.UUID | None = None,
        ip: str | None = None,
    ) -> Product:
        product.is_active = False
        product.updated_at = get_utc_now()
        await session.flush()
        await self._audit(
            product,
            AuditAction.PRODUCT_DEACTIVATED,
            session,
            actor_id,
            ip,
            changed_fields=["is_active"],
        )
        await session.commit()
        await session.refresh(product)
        return product

    @staticmethod
    async def _audit(
        product: Product,
        action: str,
        session: AsyncSession,
        actor_id: uuid.UUID | None,
        ip: str | None,
        changed_fields: list[str],
    ) -> None:
        await audit_service.register(
            session,
            action=action,
            resource="product",
            resource_id=product.id,
            user_id=actor_id,
            details={
                "name": product.name,
                "category_id": str(product.category_id),
                "price": str(product.price),
                "is_active": product.is_active,
                "changed_fields": changed_fields,
            },
            ip=ip,
        )

    @staticmethod
    def _normalize_category_name(name: str) -> str:
        return " ".join(name.strip().split())
