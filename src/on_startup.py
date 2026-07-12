from sqlmodel import func, select

from src.auth.models import Role, User
from src.config import config
from src.database import AsyncSessionLocal


async def create_first_admin_if_not_exists() -> None:
    """Check if there is at least one user with admin role.

    If none exists, create one using the FIRST_ADMIN_EMAIL and
    FIRST_ADMIN_PASSWORD environment variables.
    """
    from src.auth.service import UserService

    async with AsyncSessionLocal() as session:
        # Check if any admin already exists
        statement = select(func.count(User.id)).where(User.role == Role.ADMIN)
        result = await session.exec(statement)
        admin_count = result.one()
        if admin_count > 0:
            print("Admin user already exists — skipping creation.")
            return
        service = UserService()
        user_data = {
            "name": "Administrador",
            "email": config.FIRST_ADMIN_EMAIL,
            "password": config.FIRST_ADMIN_PASSWORD,
            "is_verified": True,
        }
        admin = await service.create_user(user_data, session, role=Role.ADMIN)
        await session.commit()
        print(f"First admin user created — email: {admin.email}, id: {admin.id}")
