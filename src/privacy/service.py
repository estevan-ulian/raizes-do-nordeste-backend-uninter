from uuid import UUID

from sqlmodel.ext.asyncio.session import AsyncSession

from src.privacy.models import LGPDConsent


class PrivacyService:
    """Manages LGPD consent records."""

    async def register_account_consents(
        self,
        user_id: UUID,
        marketing_consent: bool,
        session: AsyncSession,
    ) -> list[LGPDConsent]:
        """Register the minimum LGPD consents for a newly created account.

        Always registers the ACCOUNT_CREATION consent (required for the
        contract execution). When ``marketing_consent`` is True, also
        registers the MARKETING_AND_LOYALTY consent.
        """
        consents: list[LGPDConsent] = [
            LGPDConsent(
                user_id=user_id,
                purpose="ACCOUNT_CREATION",
                legal_basis="CONTRACT_EXECUTION",
                is_granted=True,
            )
        ]
        if marketing_consent:
            consents.append(
                LGPDConsent(
                    user_id=user_id,
                    purpose="MARKETING_AND_LOYALTY",
                    legal_basis="CONSENT",
                    is_granted=True,
                )
            )
        for consent in consents:
            session.add(consent)
        await session.flush()
        return consents


privacy_service = PrivacyService()