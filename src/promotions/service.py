import uuid
from datetime import date

from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.audit.service import AuditAction, audit_service
from src.promotions.exceptions import PromotionInvalidPeriodException
from src.promotions.models import Promotion
from src.promotions.schemas import PromotionCreate, PromotionUpdate
from src.utils import get_utc_now


class PromotionService:
    async def create_promotion(
        self,
        data: PromotionCreate,
        session: AsyncSession,
        actor_id: uuid.UUID,
        ip: str | None = None,
    ) -> Promotion:
        promotion = Promotion(**data.model_dump())
        session.add(promotion)
        await session.flush()
        await self._audit(promotion, AuditAction.PROMOTION_CREATED, session, actor_id, ip)
        await session.commit()
        await session.refresh(promotion)
        return promotion

    async def list_promotions(
        self,
        session: AsyncSession,
        page: int = 1,
        limit: int = 20,
        available_only: bool = True,
    ) -> tuple[list[Promotion], int]:
        filters = []
        if available_only:
            today = date.today()
            filters = [
                Promotion.is_active,
                Promotion.starts_at <= today,
                Promotion.ends_at >= today,
            ]

        total_statement = select(func.count(Promotion.id)).where(*filters)
        total_result = await session.exec(total_statement)
        total = total_result.one()
        statement = (
            select(Promotion)
            .where(*filters)
            .order_by(Promotion.starts_at.desc(), Promotion.name)
            .offset((page - 1) * limit)
            .limit(limit)
        )
        result = await session.exec(statement)
        return list(result.all()), total

    async def get_promotion_by_id(
        self, promotion_id: uuid.UUID, session: AsyncSession
    ) -> Promotion | None:
        result = await session.exec(select(Promotion).where(Promotion.id == promotion_id))
        return result.one_or_none()

    async def update_promotion(
        self,
        promotion: Promotion,
        data: PromotionUpdate,
        session: AsyncSession,
        actor_id: uuid.UUID,
        ip: str | None = None,
    ) -> Promotion:
        values = data.model_dump(exclude_unset=True)
        starts_at = values.get("starts_at", promotion.starts_at)
        ends_at = values.get("ends_at", promotion.ends_at)
        if ends_at < starts_at:
            raise PromotionInvalidPeriodException()
        for field, value in values.items():
            setattr(promotion, field, value)
        promotion.updated_at = get_utc_now()
        await session.flush()
        await self._audit(promotion, AuditAction.PROMOTION_UPDATED, session, actor_id, ip)
        await session.commit()
        await session.refresh(promotion)
        return promotion

    async def deactivate_promotion(
        self,
        promotion: Promotion,
        session: AsyncSession,
        actor_id: uuid.UUID,
        ip: str | None = None,
    ) -> Promotion:
        promotion.is_active = False
        promotion.updated_at = get_utc_now()
        await session.flush()
        await self._audit(promotion, AuditAction.PROMOTION_DEACTIVATED, session, actor_id, ip)
        await session.commit()
        await session.refresh(promotion)
        return promotion

    @staticmethod
    def is_applicable(promotion: Promotion, reference_date: date | None = None) -> bool:
        current_date = reference_date or date.today()
        return (
            promotion.is_active
            and promotion.starts_at <= current_date
            and promotion.ends_at >= current_date
        )

    @staticmethod
    async def _audit(
        promotion: Promotion,
        action: str,
        session: AsyncSession,
        actor_id: uuid.UUID,
        ip: str | None,
    ) -> None:
        await audit_service.register(
            session,
            action=action,
            resource="promotion",
            resource_id=promotion.id,
            user_id=actor_id,
            details={
                "name": promotion.name,
                "discount_percent": str(promotion.discount_percent),
                "starts_at": promotion.starts_at.isoformat(),
                "ends_at": promotion.ends_at.isoformat(),
                "is_active": promotion.is_active,
            },
            ip=ip,
        )


promotion_service = PromotionService()

