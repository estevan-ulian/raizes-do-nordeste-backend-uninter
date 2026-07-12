from unittest.mock import AsyncMock, MagicMock

from src.audit.service import AuditAction
from src.auth.models import Role, User
from src.security import create_access_token, create_url_safe_token
from src.tests.conftest import ADMIN_ID, CUSTOMER_ID


def test_register_creates_customer_and_audits(client, monkeypatch, now):
    from src.auth import router as auth_router

    customer = User(
        id=CUSTOMER_ID,
        name="Cliente",
        email="cliente@example.com",
        password_hash="hash",
        role=Role.CUSTOMER,
        is_verified=False,
        created_at=now,
        updated_at=now,
    )
    user_already_exists_mock = AsyncMock(return_value=False)
    create_user_mock = AsyncMock(return_value=customer)
    register_account_consents_mock = AsyncMock(return_value=[])
    audit_register_mock = AsyncMock()
    monkeypatch.setattr(auth_router.user_service, "user_already_exists", user_already_exists_mock)
    monkeypatch.setattr(auth_router.user_service, "create_user", create_user_mock)
    monkeypatch.setattr(
        auth_router.privacy_service, "register_account_consents", register_account_consents_mock
    )
    monkeypatch.setattr(auth_router.audit_service, "register", audit_register_mock)
    monkeypatch.setattr(auth_router.send_mail, "delay", MagicMock())

    response = client.post(
        "/auth/register",
        json={
            "name": "Cliente",
            "email": "cliente@example.com",
            "password": "12345678",
            "privacy_consent": True,
            "marketing_consent": True,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["result"]["id"] == str(CUSTOMER_ID)
    register_account_consents_mock.assert_awaited_once()
    _, consent_kwargs = register_account_consents_mock.await_args
    assert consent_kwargs["actor_id"] == CUSTOMER_ID
    assert consent_kwargs["ip"] == "testclient"
    audit_register_mock.assert_awaited_once()
    _, audit_kwargs = audit_register_mock.await_args
    assert audit_kwargs["action"] == AuditAction.USER_REGISTERED
    assert audit_kwargs["user_id"] == CUSTOMER_ID
    assert audit_kwargs["ip"] == "testclient"


def test_list_users_requires_admin_and_returns_paginated_users(client, monkeypatch, now):
    from src.auth import router as auth_router

    users = [
        User(
            id=ADMIN_ID,
            name="Admin",
            email="admin@example.com",
            password_hash="hash",
            role=Role.ADMIN,
            is_verified=True,
            created_at=now,
            updated_at=now,
        ),
        User(
            id=CUSTOMER_ID,
            name="Cliente",
            email="cliente@example.com",
            password_hash="hash",
            role=Role.CUSTOMER,
            is_verified=True,
            created_at=now,
            updated_at=now,
        ),
    ]
    list_users_mock = AsyncMock(return_value=(users, 2))
    monkeypatch.setattr(auth_router.user_service, "list_users", list_users_mock)

    response = client.get("/auth/users?page=1&limit=20")

    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "Usuários obtidos com sucesso."
    assert body["result"]["total"] == 2
    assert body["result"]["items"][0]["id"] == str(ADMIN_ID)
    list_users_mock.assert_awaited_once()


def test_list_users_rejects_non_admin(client, current_user, monkeypatch):
    from src.auth import router as auth_router

    current_user.role = Role.MANAGER
    list_users_mock = AsyncMock()
    monkeypatch.setattr(auth_router.user_service, "list_users", list_users_mock)

    response = client.get("/auth/users")

    assert response.status_code == 403
    list_users_mock.assert_not_awaited()


def test_login_returns_tokens_and_audits(client, monkeypatch, now):
    from src.auth import router as auth_router

    customer = User(
        id=CUSTOMER_ID,
        name="Cliente",
        email="cliente@example.com",
        password_hash="hash",
        role=Role.CUSTOMER,
        is_verified=True,
        created_at=now,
        updated_at=now,
    )
    get_user_by_email_mock = AsyncMock(return_value=customer)
    audit_register_mock = AsyncMock()
    monkeypatch.setattr(auth_router.user_service, "get_user_by_email", get_user_by_email_mock)
    monkeypatch.setattr(auth_router, "verify_password", MagicMock(return_value=True))
    monkeypatch.setattr(auth_router, "create_access_token", MagicMock(side_effect=["access", "refresh"]))
    monkeypatch.setattr(auth_router.audit_service, "register", audit_register_mock)

    response = client.post(
        "/auth/login",
        json={"email": "cliente@example.com", "password": "12345678"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["result"]["access_token"] == "access"
    assert body["result"]["refresh_token"] == "refresh"
    audit_register_mock.assert_awaited_once()
    _, audit_kwargs = audit_register_mock.await_args
    assert audit_kwargs["action"] == AuditAction.USER_LOGIN
    assert audit_kwargs["user_id"] == CUSTOMER_ID
    assert audit_kwargs["ip"] == "testclient"


def test_login_rejects_inactive_user(client, monkeypatch, now):
    from src.auth import router as auth_router

    customer = User(
        id=CUSTOMER_ID,
        name="Cliente",
        email="cliente@example.com",
        password_hash="hash",
        role=Role.CUSTOMER,
        is_verified=True,
        is_active=False,
        created_at=now,
        updated_at=now,
    )
    monkeypatch.setattr(auth_router.user_service, "get_user_by_email", AsyncMock(return_value=customer))

    response = client.post(
        "/auth/login",
        json={"email": "cliente@example.com", "password": "12345678"},
    )

    assert response.status_code == 403
    assert response.json()["error_code"] == "USER_INACTIVE"


def test_refresh_rejects_inactive_user(client, monkeypatch, now):
    from src.auth import dependencies as auth_dependencies
    from src.auth import router as auth_router

    user = User(
        id=CUSTOMER_ID,
        name="Cliente",
        email="cliente@example.com",
        password_hash="hash",
        role=Role.CUSTOMER,
        is_verified=True,
        is_active=False,
        created_at=now,
        updated_at=now,
    )
    refresh_token = create_access_token(
        user_data={"email": user.email, "user_id": str(user.id), "role": user.role},
        refresh=True,
    )
    monkeypatch.setattr(auth_dependencies, "token_in_blocklist", AsyncMock(return_value=False))
    monkeypatch.setattr(auth_router.user_service, "get_user_by_email", AsyncMock(return_value=user))
    revoke_mock = AsyncMock()
    monkeypatch.setattr(auth_router, "add_jti_to_blocklist", revoke_mock)

    response = client.get("/auth/refresh", headers={"Authorization": f"Bearer {refresh_token}"})

    assert response.status_code == 403
    assert response.json()["error_code"] == "USER_INACTIVE"
    revoke_mock.assert_not_awaited()


def test_update_me_updates_own_profile_and_audits(client, current_user, monkeypatch):
    from src.auth import router as auth_router

    current_user.name = "Admin atualizado"
    current_user.phone = "11999999999"
    update_user_mock = AsyncMock(return_value=current_user)
    audit_register_mock = AsyncMock()
    monkeypatch.setattr(auth_router.user_service, "update_user", update_user_mock)
    monkeypatch.setattr(auth_router.audit_service, "register", audit_register_mock)

    response = client.patch("/auth/me", json={"name": "Admin atualizado", "phone": "11999999999"})

    assert response.status_code == 200
    assert response.json()["result"]["name"] == "Admin atualizado"
    update_user_mock.assert_awaited_once()
    update_args, _ = update_user_mock.await_args
    assert update_args[0] == {"name": "Admin atualizado", "phone": "11999999999"}
    audit_register_mock.assert_awaited_once()
    _, audit_kwargs = audit_register_mock.await_args
    assert audit_kwargs["action"] == AuditAction.USER_UPDATED
    assert audit_kwargs["user_id"] == ADMIN_ID
    assert audit_kwargs["ip"] == "testclient"


def test_update_user_status_admin_only_updates_and_audits(client, monkeypatch, now):
    from src.auth import router as auth_router

    target_user = User(
        id=CUSTOMER_ID,
        name="Cliente",
        email="cliente@example.com",
        password_hash="hash",
        role=Role.CUSTOMER,
        is_verified=True,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    deactivated_user = target_user.model_copy(update={"is_active": False})
    monkeypatch.setattr(auth_router.user_service, "get_user_by_id", AsyncMock(return_value=target_user))
    update_user_mock = AsyncMock(return_value=deactivated_user)
    audit_register_mock = AsyncMock()
    monkeypatch.setattr(auth_router.user_service, "update_user", update_user_mock)
    monkeypatch.setattr(auth_router.audit_service, "register", audit_register_mock)

    response = client.patch(f"/auth/users/{CUSTOMER_ID}/status", json={"is_active": False})

    assert response.status_code == 200
    assert response.json()["result"]["is_active"] is False
    update_user_mock.assert_awaited_once()
    update_args, _ = update_user_mock.await_args
    assert update_args[0] == {"is_active": False}
    audit_register_mock.assert_awaited_once()
    _, audit_kwargs = audit_register_mock.await_args
    assert audit_kwargs["action"] == AuditAction.USER_DEACTIVATED
    assert audit_kwargs["resource_id"] == CUSTOMER_ID
    assert audit_kwargs["user_id"] == ADMIN_ID


def test_update_user_status_rejects_admin_self_deactivation(
    client, current_user, monkeypatch
):
    from src.auth import router as auth_router

    monkeypatch.setattr(
        auth_router.user_service, "get_user_by_id", AsyncMock(return_value=current_user)
    )
    other_admin_mock = AsyncMock()
    monkeypatch.setattr(auth_router.user_service, "has_other_active_admin", other_admin_mock)
    update_mock = AsyncMock()
    monkeypatch.setattr(auth_router.user_service, "update_user", update_mock)

    response = client.patch(f"/auth/users/{ADMIN_ID}/status", json={"is_active": False})

    assert response.status_code == 409
    assert response.json()["error_code"] == "ADMIN_STATUS_CONFLICT"
    other_admin_mock.assert_not_awaited()
    update_mock.assert_not_awaited()


def test_update_user_status_rejects_last_active_admin(client, monkeypatch, now):
    from src.auth import router as auth_router

    target_admin = User(
        id=CUSTOMER_ID,
        name="Outro admin",
        email="outro-admin@example.com",
        password_hash="hash",
        role=Role.ADMIN,
        is_verified=True,
        created_at=now,
        updated_at=now,
    )
    monkeypatch.setattr(
        auth_router.user_service, "get_user_by_id", AsyncMock(return_value=target_admin)
    )
    monkeypatch.setattr(
        auth_router.user_service, "has_other_active_admin", AsyncMock(return_value=False)
    )
    update_mock = AsyncMock()
    monkeypatch.setattr(auth_router.user_service, "update_user", update_mock)

    response = client.patch(f"/auth/users/{CUSTOMER_ID}/status", json={"is_active": False})

    assert response.status_code == 409
    assert response.json()["error_code"] == "ADMIN_STATUS_CONFLICT"
    update_mock.assert_not_awaited()


def test_update_user_status_rejects_non_admin(client, current_user, monkeypatch):
    from src.auth import router as auth_router

    current_user.role = Role.MANAGER
    get_user_by_id_mock = AsyncMock()
    monkeypatch.setattr(auth_router.user_service, "get_user_by_id", get_user_by_id_mock)

    response = client.patch(f"/auth/users/{CUSTOMER_ID}/status", json={"is_active": False})

    assert response.status_code == 403
    get_user_by_id_mock.assert_not_awaited()


def test_create_user_audits_admin_creation(client, monkeypatch, now):
    from src.auth import router as auth_router

    created_user = User(
        id=CUSTOMER_ID,
        name="Atendente",
        email="server@example.com",
        password_hash="hash",
        role=Role.SERVER,
        is_verified=False,
        created_at=now,
        updated_at=now,
    )
    monkeypatch.setattr(auth_router.user_service, "user_already_exists", AsyncMock(return_value=False))
    monkeypatch.setattr(auth_router.user_service, "create_user", AsyncMock(return_value=created_user))
    audit_register_mock = AsyncMock()
    monkeypatch.setattr(auth_router.audit_service, "register", audit_register_mock)
    monkeypatch.setattr(auth_router.send_mail, "delay", MagicMock())

    response = client.post(
        "/auth/users",
        json={
            "name": "Atendente",
            "email": "server@example.com",
            "password": "12345678",
            "role": "server",
        },
    )

    assert response.status_code == 201
    audit_register_mock.assert_awaited_once()
    _, audit_kwargs = audit_register_mock.await_args
    assert audit_kwargs["action"] == AuditAction.USER_CREATED
    assert audit_kwargs["user_id"] == ADMIN_ID
    assert audit_kwargs["resource_id"] == CUSTOMER_ID
    assert audit_kwargs["ip"] == "testclient"


def test_verify_email_audits(client, monkeypatch, now):
    from src.auth import router as auth_router

    user = User(
        id=CUSTOMER_ID,
        name="Cliente",
        email="cliente@example.com",
        password_hash="hash",
        role=Role.CUSTOMER,
        is_verified=False,
        created_at=now,
        updated_at=now,
    )
    monkeypatch.setattr(auth_router, "decode_url_safe_token", MagicMock(return_value={"email": user.email}))
    monkeypatch.setattr(auth_router.user_service, "get_user_by_email", AsyncMock(return_value=user))
    monkeypatch.setattr(auth_router.user_service, "update_user", AsyncMock(return_value=user))
    audit_register_mock = AsyncMock()
    monkeypatch.setattr(auth_router.audit_service, "register", audit_register_mock)

    response = client.get("/auth/verify/token")

    assert response.status_code == 200
    audit_register_mock.assert_awaited_once()
    _, audit_kwargs = audit_register_mock.await_args
    assert audit_kwargs["action"] == AuditAction.USER_EMAIL_VERIFIED
    assert audit_kwargs["user_id"] == CUSTOMER_ID
    assert audit_kwargs["ip"] == "testclient"


def test_verify_email_is_idempotent_success(client, monkeypatch, now):
    from src.auth import router as auth_router

    user = User(
        id=CUSTOMER_ID,
        name="Cliente",
        email="cliente@example.com",
        password_hash="hash",
        role=Role.CUSTOMER,
        is_verified=True,
        created_at=now,
        updated_at=now,
    )
    monkeypatch.setattr(auth_router, "decode_url_safe_token", MagicMock(return_value={"email": user.email}))
    monkeypatch.setattr(auth_router.user_service, "get_user_by_email", AsyncMock(return_value=user))
    update_mock = AsyncMock()
    monkeypatch.setattr(auth_router.user_service, "update_user", update_mock)

    response = client.get("/auth/verify/token")

    assert response.status_code == 200
    assert response.json()["success"] is True
    update_mock.assert_not_awaited()


def test_refresh_audits_token_refresh(client, monkeypatch, now):
    from src.auth import dependencies as auth_dependencies
    from src.auth import router as auth_router

    user = User(
        id=CUSTOMER_ID,
        name="Cliente",
        email="cliente@example.com",
        password_hash="hash",
        role=Role.CUSTOMER,
        is_verified=True,
        created_at=now,
        updated_at=now,
    )
    refresh_token = create_access_token(
        user_data={"email": user.email, "user_id": str(user.id), "role": user.role},
        refresh=True,
    )
    monkeypatch.setattr(auth_dependencies, "token_in_blocklist", AsyncMock(return_value=False))
    monkeypatch.setattr(auth_router.user_service, "get_user_by_email", AsyncMock(return_value=user))
    monkeypatch.setattr(auth_router, "add_jti_to_blocklist", AsyncMock())
    monkeypatch.setattr(auth_router, "create_access_token", MagicMock(side_effect=["access", "refresh"]))
    audit_register_mock = AsyncMock()
    monkeypatch.setattr(auth_router.audit_service, "register", audit_register_mock)

    response = client.get("/auth/refresh", headers={"Authorization": f"Bearer {refresh_token}"})

    assert response.status_code == 200
    assert response.json()["result"]["access_token"] == "access"
    audit_register_mock.assert_awaited_once()
    _, audit_kwargs = audit_register_mock.await_args
    assert audit_kwargs["action"] == AuditAction.USER_TOKEN_REFRESHED
    assert audit_kwargs["user_id"] == CUSTOMER_ID
    assert audit_kwargs["ip"] == "testclient"


def test_logout_audits_and_handles_malformed_user_id(client, monkeypatch):
    from src.auth import dependencies as auth_dependencies
    from src.auth import router as auth_router

    access_token = create_access_token(
        user_data={"email": "cliente@example.com", "user_id": "not-a-uuid", "role": Role.CUSTOMER}
    )
    refresh_token = create_access_token(
        user_data={"email": "cliente@example.com", "user_id": str(CUSTOMER_ID), "role": Role.CUSTOMER},
        refresh=True,
    )
    monkeypatch.setattr(auth_dependencies, "token_in_blocklist", AsyncMock(return_value=False))
    monkeypatch.setattr(auth_router, "add_jti_to_blocklist", AsyncMock())
    audit_register_mock = AsyncMock()
    monkeypatch.setattr(auth_router.audit_service, "register", audit_register_mock)

    response = client.post(
        "/auth/logout",
        json={"refresh_token": refresh_token},
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    audit_register_mock.assert_awaited_once()
    _, audit_kwargs = audit_register_mock.await_args
    assert audit_kwargs["action"] == AuditAction.USER_LOGOUT
    assert audit_kwargs["user_id"] is None
    assert audit_kwargs["details"] == {"refresh_token_revoked": True}


def test_reset_password_request_audits(client, monkeypatch, now):
    from src.auth import router as auth_router

    user = User(
        id=CUSTOMER_ID,
        name="Cliente",
        email="cliente@example.com",
        password_hash="hash",
        role=Role.CUSTOMER,
        is_verified=True,
        created_at=now,
        updated_at=now,
    )
    monkeypatch.setattr(auth_router.user_service, "get_user_by_email", AsyncMock(return_value=user))
    monkeypatch.setattr(auth_router.send_mail, "delay", MagicMock())
    audit_register_mock = AsyncMock()
    monkeypatch.setattr(auth_router.audit_service, "register", audit_register_mock)

    response = client.post("/auth/reset_password", json={"email": user.email})

    assert response.status_code == 200
    audit_register_mock.assert_awaited_once()
    _, audit_kwargs = audit_register_mock.await_args
    assert audit_kwargs["action"] == AuditAction.PASSWORD_RESET_REQUESTED
    assert audit_kwargs["user_id"] == CUSTOMER_ID
    assert audit_kwargs["ip"] == "testclient"


def test_reset_password_confirm_audits(client, monkeypatch, now):
    from src.auth import router as auth_router

    user = User(
        id=CUSTOMER_ID,
        name="Cliente",
        email="cliente@example.com",
        password_hash="hash",
        role=Role.CUSTOMER,
        is_verified=True,
        created_at=now,
        updated_at=now,
    )
    token = create_url_safe_token({"email": user.email, "id": "reset-id"})
    monkeypatch.setattr(auth_router.user_service, "get_user_by_email", AsyncMock(return_value=user))
    monkeypatch.setattr(auth_router.user_service, "update_user", AsyncMock(return_value=user))
    monkeypatch.setattr(auth_router, "reset_token_in_blocklist", AsyncMock(return_value=False))
    monkeypatch.setattr(auth_router, "add_reset_token_to_blocklist", AsyncMock())
    monkeypatch.setattr(auth_router, "generate_password_hash", MagicMock(return_value="new-hash"))
    audit_register_mock = AsyncMock()
    monkeypatch.setattr(auth_router.audit_service, "register", audit_register_mock)

    response = client.post(
        "/auth/reset_password_confirm",
        json={"token": token, "password": "12345678", "password_confirm": "12345678"},
    )

    assert response.status_code == 200
    audit_register_mock.assert_awaited_once()
    _, audit_kwargs = audit_register_mock.await_args
    assert audit_kwargs["action"] == AuditAction.PASSWORD_RESET_CONFIRMED
    assert audit_kwargs["user_id"] == CUSTOMER_ID
    assert audit_kwargs["ip"] == "testclient"
