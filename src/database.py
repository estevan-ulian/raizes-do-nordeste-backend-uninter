from typing import AsyncGenerator
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from src.config import config


async_engine = create_async_engine(url=config.DATABASE_URL, echo=True)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    Session = async_sessionmaker(bind=async_engine, class_=AsyncSession, expire_on_commit=False)

    async with Session() as session:
        yield session
