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
