import uuid

from sqlalchemy import and_
from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.audit.service import AuditAction, audit_service
from src.inventory.models import Inventory
from src.products.models import Product, ProductCategory
from src.units.models import Unit
from src.units.schemas import (
    UnitCreate,
    UnitMenuCategoryResponse,
    UnitMenuItemResponse,
    UnitUpdate,
)
from src.utils import get_utc_now


class UnitService:
    async def create_unit(
        self,
        unit_data: UnitCreate,
        session: AsyncSession,
        actor_id: uuid.UUID | None = None,
        ip: str | None = None,
    ) -> Unit:
        new_unit = Unit(**unit_data.model_dump())
        session.add(new_unit)
        await session.flush()
        await self._audit(
            new_unit,
            AuditAction.UNIT_CREATED,
            session,
            actor_id,
            ip,
            changed_fields=list(unit_data.model_dump(exclude_unset=True).keys()),
        )
        await session.commit()
        await session.refresh(new_unit)
        return new_unit

    async def list_units(self, session: AsyncSession, include_inactive: bool = False) -> list[Unit]:
        statement = select(Unit).order_by(Unit.name)
        if not include_inactive:
            statement = statement.where(Unit.is_active)
        result = await session.exec(statement)
        return list(result.all())

    async def get_unit_by_id(self, unit_id: uuid.UUID, session: AsyncSession) -> Unit | None:
        statement = select(Unit).where(Unit.id == unit_id)
        result = await session.exec(statement)
        return result.one_or_none()

    async def list_menu(
        self,
        unit_id: uuid.UUID,
        session: AsyncSession,
        page: int = 1,
        limit: int = 20,
        category_id: uuid.UUID | None = None,
        include_unavailable: bool = False,
    ) -> tuple[list[UnitMenuItemResponse], int]:
        """List active global products with their availability at a unit.

        Exact inventory quantities are intentionally not exposed. Availability
        is informative; order creation remains responsible for locking and
        validating the current inventory balance.
        """
        inventory_join = and_(
            Inventory.unit_id == unit_id,
            Inventory.product_id == Product.id,
        )
        filters = [Product.is_active]
        if category_id:
            filters.append(Product.category_id == category_id)
        if not include_unavailable:
            filters.append(Inventory.quantity > 0)

        total_statement = (
            select(func.count(Product.id))
            .join(ProductCategory, ProductCategory.id == Product.category_id)
            .outerjoin(Inventory, inventory_join)
            .where(*filters)
        )
        total_result = await session.exec(total_statement)
        total = total_result.one()

        statement = (
            select(Product, ProductCategory, Inventory.quantity)
            .join(ProductCategory, ProductCategory.id == Product.category_id)
            .outerjoin(Inventory, inventory_join)
            .where(*filters)
            .order_by(ProductCategory.name, Product.name)
            .offset((page - 1) * limit)
            .limit(limit)
        )
        result = await session.exec(statement)
        items = [
            UnitMenuItemResponse(
                id=product.id,
                name=product.name,
                description=product.description,
                price=product.price,
                image_url=product.image_url,
                category=UnitMenuCategoryResponse(id=category.id, name=category.name),
                available=quantity is not None and quantity > 0,
            )
            for product, category, quantity in result.all()
        ]
        return items, total

    async def update_unit(
        self,
        unit: Unit,
        unit_data: UnitUpdate,
        session: AsyncSession,
        actor_id: uuid.UUID | None = None,
        ip: str | None = None,
    ) -> Unit:
        update_data = unit_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(unit, key, value)
        unit.updated_at = get_utc_now()
        await session.flush()
        await self._audit(
            unit,
            AuditAction.UNIT_UPDATED,
            session,
            actor_id,
            ip,
            changed_fields=list(update_data.keys()),
        )
        await session.commit()
        await session.refresh(unit)
        return unit

    async def deactivate_unit(
        self,
        unit: Unit,
        session: AsyncSession,
        actor_id: uuid.UUID | None = None,
        ip: str | None = None,
    ) -> Unit:
        unit.is_active = False
        unit.updated_at = get_utc_now()
        await session.flush()
        await self._audit(
            unit,
            AuditAction.UNIT_DEACTIVATED,
            session,
            actor_id,
            ip,
            changed_fields=["is_active"],
        )
        await session.commit()
        await session.refresh(unit)
        return unit

    @staticmethod
    async def _audit(
        unit: Unit,
        action: str,
        session: AsyncSession,
        actor_id: uuid.UUID | None,
        ip: str | None,
        changed_fields: list[str],
    ) -> None:
        await audit_service.register(
            session,
            action=action,
            resource="unit",
            resource_id=unit.id,
            user_id=actor_id,
            details={
                "name": unit.name,
                "is_active": unit.is_active,
                "changed_fields": changed_fields,
            },
            ip=ip,
        )
