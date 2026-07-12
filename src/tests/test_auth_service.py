from unittest.mock import MagicMock

import pytest

from src.auth.models import Role
from src.auth.schemas import UserCreate
from src.auth.service import UserService
from src.tests.conftest import ADMIN_ID


@pytest.mark.asyncio
async def test_create_user_flushes_without_committing(session, monkeypatch):
    from src.auth import service as auth_service_module

    monkeypatch.setattr(auth_service_module, "generate_password_hash", MagicMock(return_value="hash"))

    user = await UserService().create_user(
        UserCreate(
            name="Atendente",
            email="atendente@example.com",
            password="12345678",
            role=Role.SERVER,
        ),
        session,
        role=Role.SERVER,
    )

    assert user.password_hash == "hash"
    session.flush.assert_awaited_once()
    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_user_flushes_without_committing(session, current_user):
    updated = await UserService().update_user({"name": "Novo nome"}, current_user, session)

    assert updated.id == ADMIN_ID
    assert updated.name == "Novo nome"
    session.flush.assert_awaited_once()
    session.commit.assert_not_awaited()
