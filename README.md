
# TaskManager (API)

Упрощённый менеджер задач с категориями и напоминаниями: FastAPI + PostgreSQL + Celery (+ Beat) + Redis/RabbitMQ, запуск в Docker Compose, JWT-аутентификация.

## Возможности

- Регистрация/логин, JWT Bearer-токены
- CRUD задач + отметка «выполнено»
- Категории задач
- Напоминания (отложенные задачи Celery)
- Периодические фоновые задачи (Celery Beat)
- Swagger/OpenAPI: `/docs`, `/openapi.json`
- Healthcheck: `/health`

## Требования

- Docker + Docker Compose (рекомендуется)
- Локально: Python 3.11+, Poetry

## Быстрый старт (Docker)

1) Создай `.env` в корне проекта:

```env
# DB
DATABASE_URL_ASYNC=postgresql+asyncpg://app:pass@db_dev:5432/app_db
DATABASE_URL_SYNC=postgresql+psycopg://app:pass@db_dev:5432/app_db
# В settings используется также DATABASE_URL_SYNC_ (если не нужно — убери из config.py)
DATABASE_URL_SYNC_=postgresql+psycopg://app:pass@db_dev:5432/app_db

# Celery
CELERY_BROKER_URL=amqp://app:pass@rabbitmq:5672//
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Auth
SECRET_KEY=change_me
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

2. Подними окружение:

```bash
docker compose -f docker-compose.yaml up --build
```

3. Открой API:

* Swagger: `http://localhost/docs` (или просто `localhost`) 
* Healthcheck: `http://localhost/health`

> В compose поднимаются два инстанса backend (для балансировки) и `nginx` на порту `80`. Конфиг Nginx ожидается в `./nginx/nginx.conf`.

## Запуск локально (без Docker)

```bash
poetry install
poetry run uvicorn app.main:app --reload
```

Celery:

```bash
poetry run celery -A app.core.celery_app worker -l info
poetry run celery -A app.core.celery_app beat -l info
```

Перед запуском должны быть доступны PostgreSQL, RabbitMQ и Redis, а переменные окружения — заданы (см. `.env` выше).

## Тесты (с хоста)

```bash
 pip install pytest  # если нет
 pytest
```

## API (основные маршруты)

Точный список и схемы смотри в Swagger (`/docs`). Базово:

**Auth (public)**

* `POST /auth/register` — регистрация (JSON: `username`, `email`, `password`)
* `POST /auth/login` — логин (в проекте используется form-data: `username`, `password`)
  Ответ: `{ "access_token": "...", "token_type": "bearer" }`

**Users**

* `GET /users/me` — текущий пользователь

**Tasks**

* `GET /tasks` — список (фильтры: `completed`, `category`, `due_before`, `due_after`)
* `POST /tasks` — создать
* `GET /tasks/{id}` — получить
* `PUT/PATCH /tasks/{id}` — обновить
* `POST /tasks/{id}/complete` — отметить выполненной
* `DELETE /tasks/{id}` — удалить

**Categories**

* `GET /categories` — список
* `POST /categories` — создать
* `GET /categories/{id}` — получить
* `PUT/PATCH /categories/{id}` — обновить
* `DELETE /categories/{id}` — удалить

## Архитектура (кратко)

* `app.main` — FastAPI приложение, подключение роутеров
* `app.core.config` — настройки через env (`pydantic-settings`)
* `app.core.security` — хэширование паролей + JWT (HS256)
* `app.core.celery_app` — Celery + расписание Beat (например, `catch_up` и `cleanup` ежедневно)
* `app.core.exception_handlers` — единые обработчики доменных ошибок
