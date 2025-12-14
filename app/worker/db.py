import os
from contextlib import contextmanager
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def _get_db_uri() -> str:
    url_db = os.environ.get("DATABASE_URL_SYNC")
    if not url_db:
        raise RuntimeError("DATABASE_URL_SYNC is not set")
    return url_db


@lru_cache(maxsize=1)
def get_engine():
    return create_engine(
        _get_db_uri(),
        pool_pre_ping=True
    )


@lru_cache(maxsize=1)
def get_session_factory():
    return sessionmaker(
        bind=get_engine(),
        autoflush=False,
        expire_on_commit=False
    )


@contextmanager
def session_scope():
    session = get_session_factory()()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
