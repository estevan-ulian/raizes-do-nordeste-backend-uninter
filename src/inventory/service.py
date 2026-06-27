import uuid

from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.audit.service import AuditAction, audit_service
from src.inventory.exceptions import InventoryInsufficientException, InventoryNotFoundException
from src.inventory.models import Inventory
from src.inventory.schemas import InventoryMovementCreate, InventoryMovementType
from src.utils import get_utc_now


class InventoryService:
    async def apply_movement(
        self,
        movement_data: InventoryMovementCreate,
        session: AsyncSession,
        actor_id: uuid.UUID | None = None,
        ip: str | None = None,
    ) -> Inventory:
        inventory_item = await self.get_inventory_item(
            movement_data.unit_id,
            movement_data.product_id,
            session,
            lock=True,
        )

        previous_quantity: int | None = None
        if movement_data.movement_type == InventoryMovementType.ENTRY:
            if inventory_item is None:
                inventory_item = Inventory(
                    unit_id=movement_data.unit_id,
                    product_id=movement_data.product_id,
                    quantity=0,
                    minimum_quantity=movement_data.minimum_quantity or 0,
                )
                session.add(inventory_item)
            else:
                previous_quantity = inventory_item.quantity
            inventory_item.quantity += movement_data.quantity
        else:
            if inventory_item is None:
                raise InventoryNotFoundException()
            previous_quantity = inventory_item.quantity
            if inventory_item.quantity < movement_data.quantity:
                raise InventoryInsufficientException()
            inventory_item.quantity -= movement_data.quantity

        if movement_data.minimum_quantity is not None:
            inventory_item.minimum_quantity = movement_data.minimum_quantity
        inventory_item.updated_at = get_utc_now()
        await session.flush()
        await audit_service.register(
            session,
            action=AuditAction.INVENTORY_MOVEMENT_APPLIED,
            resource="inventory",
            resource_id=inventory_item.id,
            user_id=actor_id,
            details={
                "unit_id": str(movement_data.unit_id),
                "product_id": str(movement_data.product_id),
                "movement_type": movement_data.movement_type.value,
                "quantity": movement_data.quantity,
                "previous_quantity": previous_quantity,
                "new_quantity": inventory_item.quantity,
            },
            ip=ip,
        )
        await session.commit()
        await session.refresh(inventory_item)
        return inventory_item

    async def list_inventory(
        self,
        session: AsyncSession,
        page: int = 1,
        limit: int = 20,
        unit_id: uuid.UUID | None = None,
        product_id: uuid.UUID | None = None,
    ) -> tuple[list[Inventory], int]:
        filters = []
        if unit_id:
            filters.append(Inventory.unit_id == unit_id)
        if product_id:
            filters.append(Inventory.product_id == product_id)

        total_statement = select(func.count(Inventory.id))
        for query_filter in filters:
            total_statement = total_statement.where(query_filter)
        total_result = await session.exec(total_statement)
        total = total_result.one()

        offset = (page - 1) * limit
        statement = select(Inventory).order_by(Inventory.created_at.desc()).offset(offset).limit(limit)
        for query_filter in filters:
            statement = statement.where(query_filter)
        result = await session.exec(statement)
        return list(result.all()), total

    async def get_inventory_item(
        self,
        unit_id: uuid.UUID,
        product_id: uuid.UUID,
        session: AsyncSession,
        lock: bool = False,
    ) -> Inventory | None:
        statement = select(Inventory).where(
            Inventory.unit_id == unit_id,
            Inventory.product_id == product_id,
        )
        if lock:
            statement = statement.with_for_update()
        result = await session.exec(statement)
        return result.one_or_none()
