import logging
from typing import Any
from uuid import UUID

from sqlmodel.ext.asyncio.session import AsyncSession

from src.audit.models import AuditLog

logger = logging.getLogger(__name__)


class AuditAction:
    """Canonical audit action names used across the application."""

    ORDER_CREATED = "ORDER_CREATED"
    ORDER_STATUS_UPDATED = "ORDER_STATUS_UPDATED"
    ORDER_CANCELED = "ORDER_CANCELED"
    PAYMENT_PROCESSED = "PAYMENT_PROCESSED"
    INVENTORY_MOVEMENT_APPLIED = "INVENTORY_MOVEMENT_APPLIED"
    PROMOTION_CREATED = "PROMOTION_CREATED"
    PROMOTION_UPDATED = "PROMOTION_UPDATED"
    PROMOTION_DEACTIVATED = "PROMOTION_DEACTIVATED"
    USER_LOGIN = "USER_LOGIN"
    USER_LOGOUT = "USER_LOGOUT"
    USER_CREATED = "USER_CREATED"
    USER_UPDATED = "USER_UPDATED"
    USER_ACTIVATED = "USER_ACTIVATED"
    USER_DEACTIVATED = "USER_DEACTIVATED"
    USER_REGISTERED = "USER_REGISTERED"
    USER_EMAIL_VERIFIED = "USER_EMAIL_VERIFIED"
    USER_TOKEN_REFRESHED = "USER_TOKEN_REFRESHED"
    PASSWORD_RESET_REQUESTED = "PASSWORD_RESET_REQUESTED"
    PASSWORD_RESET_CONFIRMED = "PASSWORD_RESET_CONFIRMED"
    LGPD_CONSENTS_REGISTERED = "LGPD_CONSENTS_REGISTERED"
    PRODUCT_CREATED = "PRODUCT_CREATED"
    PRODUCT_UPDATED = "PRODUCT_UPDATED"
    PRODUCT_DEACTIVATED = "PRODUCT_DEACTIVATED"
    PRODUCT_CATEGORY_CREATED = "PRODUCT_CATEGORY_CREATED"
    UNIT_CREATED = "UNIT_CREATED"
    UNIT_UPDATED = "UNIT_UPDATED"
    UNIT_DEACTIVATED = "UNIT_DEACTIVATED"
    LOYALTY_ACCOUNT_CREATED = "LOYALTY_ACCOUNT_CREATED"
    LOYALTY_REDEMPTION_CREATED = "LOYALTY_REDEMPTION_CREATED"


class AuditService:
    """Registers audit logs for sensitive operations.

    The audit log entry is added to the same session passed by the caller so it
    participates in the same transaction whenever possible. Only operational
    data should be stored in ``details`` — never sensitive personal data.
    """

    async def register(
        self,
        session: AsyncSession,
        action: str,
        resource: str,
        resource_id: UUID | None = None,
        user_id: UUID | None = None,
        details: dict[str, Any] | None = None,
        ip: str | None = None,
    ) -> AuditLog:
        audit_log = AuditLog(
            action=action,
            resource=resource,
            resource_id=resource_id,
            user_id=user_id,
            details=details,
            ip=ip,
        )
        session.add(audit_log)
        await session.flush()
        return audit_log


audit_service = AuditService()
