import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from src.app import app
from src.auth.dependencies import get_current_user, get_optional_current_user
from src.auth.models import Role, User
from src.database import get_async_session


ADMIN_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
CUSTOMER_ID = uuid.UUID("00000000-0000-0000-0000-000000000002")
UNIT_ID = uuid.UUID("00000000-0000-0000-0000-000000000003")
PRODUCT_ID = uuid.UUID("00000000-0000-0000-0000-000000000004")
ORDER_ID = uuid.UUID("00000000-0000-0000-0000-000000000005")
PAYMENT_ID = uuid.UUID("00000000-0000-0000-0000-000000000006")
LOYALTY_ACCOUNT_ID = uuid.UUID("00000000-0000-0000-0000-000000000007")
LOYALTY_REDEMPTION_ID = uuid.UUID("00000000-0000-0000-0000-000000000008")
PRODUCT_CATEGORY_ID = uuid.UUID("00000000-0000-0000-0000-000000000009")


@pytest.fixture
def now():
    return datetime(2026, 1, 1, tzinfo=timezone.utc)


@pytest.fixture
def session():
    session = MagicMock()
    session.add = MagicMock()
    session.exec = AsyncMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    return session


@pytest.fixture
def current_user(now):
    return User(
        id=ADMIN_ID,
        name="Admin",
        email="admin@example.com",
        password_hash="hash",
        role=Role.ADMIN,
        is_verified=True,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def client(session, current_user):
    async def override_session():
        yield session

    async def override_current_user():
        return current_user

    app.dependency_overrides[get_async_session] = override_session
    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_optional_current_user] = override_current_user

    test_client = TestClient(app)
    yield test_client
    test_client.close()
    app.dependency_overrides.clear()
