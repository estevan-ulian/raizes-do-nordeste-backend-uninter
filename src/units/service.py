import uuid

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.units.models import Unit
from src.units.schemas import UnitCreate, UnitUpdate


class UnitService:
    async def create_unit(self, unit_data: UnitCreate, session: AsyncSession) -> Unit:
        new_unit = Unit(**unit_data.model_dump())
        session.add(new_unit)
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

    async def update_unit(self, unit: Unit, unit_data: UnitUpdate, session: AsyncSession) -> Unit:
        update_data = unit_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(unit, key, value)
        await session.commit()
        await session.refresh(unit)
        return unit

    async def deactivate_unit(self, unit: Unit, session: AsyncSession) -> Unit:
        unit.is_active = False
        await session.commit()
        await session.refresh(unit)
        return unit
