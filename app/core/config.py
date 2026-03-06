from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    # session backend + seed_loadtest_users.py
    DATABASE_URL_ASYNC_INNER: str

    # alembic out container (from localhost)
    DATABASE_URL_SYNC_OUT: str

    # pytest
    DATABASE_URL_ASYNC_OUT: str

    # alembic into container + session worker
    DATABASE_URL_SYNC_INNER: str

    # Celery
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    # Auth
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    # если переменные тут не найдены, ищи их в .env
    # model_config = SettingsConfigDict(env_file="../../.env")


# noinspection PyArgumentList
settings = Settings()
