import uuid

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.audit.service import AuditAction, audit_service
from src.units.models import Unit
from src.units.schemas import UnitCreate, UnitUpdate
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
