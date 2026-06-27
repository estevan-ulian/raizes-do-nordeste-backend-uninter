from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.security import generate_password_hash

from .models import Role, User
from .schemas import UserCreate, UserRegister


class UserService:
    async def get_user_by_email(self, email: str, session: AsyncSession) -> User | None:
        """Get a user by email. Returns None if not found."""
        statement = select(User).where(User.email == email)
        result = await session.exec(statement)
        return result.one_or_none()

    async def user_already_exists(self, email: str, session: AsyncSession) -> bool:
        """Check if a user with the email already exists."""
        return await self.get_user_by_email(email, session) is not None

    async def create_user(
        self, user_data: UserCreate | UserRegister | dict, session: AsyncSession, role: Role = Role.CUSTOMER
    ) -> User:
        """Create a user with the specified role."""
        if isinstance(user_data, dict):
            user_data_dict = user_data.copy()
        else:
            user_data_dict = user_data.model_dump()
        password = user_data_dict.pop("password")
        # LGPD consent fields are not part of the User model; they are handled
        # separately through the privacy module.
        user_data_dict.pop("privacy_consent", None)
        user_data_dict.pop("marketing_consent", None)
        new_user = User(**user_data_dict)
        new_user.password_hash = generate_password_hash(password)
        new_user.role = role
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        return new_user

    async def update_user(self, user_data: dict, user: User, session: AsyncSession):
        for key, value in user_data.items():
            setattr(user, key, value)
        await session.commit()
        await session.refresh(user)
        return user
