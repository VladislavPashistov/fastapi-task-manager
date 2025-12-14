from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    DATABASE_URL_ASYNC: str
    DATABASE_URL_SYNC: str

    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    DATABASE_URL_SYNC_: str
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    # если переменные тут не найдены, ищи их в .env
    # model_config = SettingsConfigDict(env_file="../../.env")


# noinspection PyArgumentList
settings = Settings()
