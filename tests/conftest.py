import uuid
from typing import Dict

import pytest
from alembic import command
from alembic.config import Config
from httpx import AsyncClient, ASGITransport
from sqlalchemy import event

from app.db import get_db as real_get_db
from app.main import app

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from app.core.config import settings


# setup migrations
@pytest.fixture(scope="session", autouse=True)
def apply_migrations():
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.cmd_opts = type("obj", (), {"x": ["env=out"]})()
    command.upgrade(alembic_cfg, "head")


# scope не session: жертвуем ради стабильности
@pytest.fixture(scope="function")
async def async_engine():
    async_engine = create_async_engine(
        settings.DATABASE_URL_ASYNC_OUT,
        echo=False,
    )
    try:
        yield async_engine
    finally:
        await async_engine.dispose()


@pytest.fixture(scope="function")
async def async_session(async_engine):
    async with async_engine.connect() as conn:
        outer_tx = await conn.begin()

        session = AsyncSession(bind=conn, expire_on_commit=False)
        await session.begin_nested()  # SAVEPOINT чтобы session.commit() не фиксировал outer_tx

        # триггер на закрытие транзакции
        @event.listens_for(session.sync_session, "after_transaction_end")
        def _restart_savepoint(sess, trans):
            # if a top-level SAVEPOINT ended, open a new one
            # noinspection PyProtectedMember
            if trans.nested and not trans._parent.nested:
                sess.begin_nested()

        try:
            yield session  # тут основная работа триггера
        finally:
            await session.close()
            await outer_tx.rollback()


@pytest.fixture(scope="function")
async def override_get_db(async_session):
    async def _override():
        yield async_session

    app.dependency_overrides[real_get_db] = _override
    try:
        yield
    finally:
        app.dependency_overrides.pop(real_get_db, None)


@pytest.fixture(scope="function")
async def async_client(override_get_db):
    base_url = "http://test"

    async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url=base_url,
    ) as client:
        yield client


@pytest.fixture(scope="function")
async def auth_headers(async_client) -> Dict[str, str]:
    mail = str(uuid.uuid4()) + "@example.com"
    username = str(uuid.uuid4())[:9]
    password = str(uuid.uuid4())[:9]

    await async_client.post(
        url="/auth/register",
        json={
            "email": mail,
            "username": username,
            "password": password,
        })

    log = await async_client.post(
        url="/auth/login",
        data={
            "username": username,
            "password": password,
        }
    )
    if log.status_code != 200:
        raise AssertionError("Login failed")

    token = log.json().get("access_token")

    return {"Authorization": f"Bearer {token}"}
