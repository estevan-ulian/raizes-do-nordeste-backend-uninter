import uuid
from decimal import Decimal

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.loyalty.exceptions import (
    LoyaltyAccountNotFoundException,
    LoyaltyInsufficientPointsException,
)
from src.loyalty.models import LoyaltyAccount, LoyaltyRedemption
from src.privacy.models import LGPDConsent
from src.utils import get_utc_now

MARKETING_LOYALTY_PURPOSE = "MARKETING_AND_LOYALTY"


class LoyaltyService:
    """Minimal loyalty service: accumulate points on approved payments."""

    async def get_or_create_account(self, customer_id: uuid.UUID, session: AsyncSession) -> LoyaltyAccount:
        account = await self.get_account(customer_id, session)
        if account is not None:
            return account
        consent_granted = await self._has_marketing_consent(customer_id, session)
        account = LoyaltyAccount(
            customer_id=customer_id,
            points_balance=0,
            consent_granted=consent_granted,
        )
        session.add(account)
        await session.flush()
        return account

    async def get_account(self, customer_id: uuid.UUID, session: AsyncSession) -> LoyaltyAccount | None:
        statement = select(LoyaltyAccount).where(LoyaltyAccount.customer_id == customer_id)
        result = await session.exec(statement)
        return result.one_or_none()

    async def add_points(
        self, customer_id: uuid.UUID, amount: Decimal, session: AsyncSession
    ) -> LoyaltyAccount | None:
        """Accumulate loyalty points for a paid order.

        Points are only accumulated when the account has a valid
        marketing/loyalty consent. Returns the updated account, or None when
        no consent was granted (points are not accumulated in that case).
        """
        account = await self.get_or_create_account(customer_id, session)
        if not account.consent_granted:
            return None
        points = self._points_for_amount(amount)
        account.points_balance += points
        account.updated_at = get_utc_now()
        session.add(account)
        await session.flush()
        return account

    async def redeem_points(
        self,
        customer_id: uuid.UUID,
        points_used: int,
        reward: str,
        session: AsyncSession,
    ) -> LoyaltyRedemption:
        account = await self.get_account(customer_id, session)
        if account is None:
            raise LoyaltyAccountNotFoundException()
        if account.points_balance < points_used:
            raise LoyaltyInsufficientPointsException()
        account.points_balance -= points_used
        account.updated_at = get_utc_now()
        session.add(account)
        redemption = LoyaltyRedemption(
            loyalty_account_id=account.id,
            points_used=points_used,
            reward=reward,
        )
        session.add(redemption)
        await session.flush()
        await session.commit()
        await session.refresh(redemption)
        return redemption

    async def _has_marketing_consent(self, customer_id: uuid.UUID, session: AsyncSession) -> bool:
        statement = select(LGPDConsent).where(
            LGPDConsent.user_id == customer_id,
            LGPDConsent.purpose == MARKETING_LOYALTY_PURPOSE,
            LGPDConsent.is_granted.is_(True),
            LGPDConsent.revoked_at.is_(None),
        )
        result = await session.exec(statement)
        return result.first() is not None

    @staticmethod
    def _points_for_amount(amount: Decimal) -> int:
        """1 point per R$ 1,00 paid (truncated to whole points)."""
        return int(Decimal(amount).to_integral_value(rounding="ROUND_DOWN"))


loyalty_service = LoyaltyService()
