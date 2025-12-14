from typing import Any, AsyncGenerator

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession
from app.core.config import settings


# создаём движок
async_engine = create_async_engine(
    settings.DATABASE_URL_ASYNC,
    pool_pre_ping=True,
    echo=False
)


# создаём фабрику сессий
async_session = async_sessionmaker(
    bind=async_engine,
    expire_on_commit=False
)


async def get_db() -> AsyncGenerator[AsyncSession, Any]:
    async with async_session() as db:
        yield db
