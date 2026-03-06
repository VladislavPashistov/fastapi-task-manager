# TaskManager (API)

Упрощённый менеджер задач с категориями и напоминаниями: FastAPI + PostgreSQL + Celery (+ Beat) + Redis/RabbitMQ, запуск в Docker Compose, JWT-аутентификация.

## Возможности

- Регистрация и логин, JWT Bearer-токены
- CRUD задач
- Отметка задачи как выполненной
- CRUD категорий
- Напоминания через Celery
- Периодические фоновые задачи через Celery Beat
- Swagger/OpenAPI: `/docs`, `/openapi.json`
- Healthcheck: `/health`
- Nginx как reverse proxy и балансировщик между backend-инстансами
- Мониторинг и логи: Grafana / Prometheus / Loki / Promtail
- Тесты на `pytest`
- Нагрузочные тесты через `locust`

## Что использовалось

- **FastAPI** — API
- **PostgreSQL** — база данных
- **SQLAlchemy** — ORM
- **Alembic** — миграции
- **JWT** — аутентификация
- **Celery + Beat** — фоновые и периодические задачи
- **RabbitMQ** — брокер
- **Redis** — result backend
- **Docker Compose** — запуск окружения
- **Nginx** — проксирование и балансировка
- **Pytest** — тесты
- **Locust** — нагрузочное тестирование
- **Grafana / Prometheus / Loki** — мониторинг и логирование

## Структура проекта

```text
app/
├── api/         # роутеры
├── core/        # конфиг, security, celery, обработка ошибок
├── db/          # подключение к БД
├── models/      # модели
├── schemas/     # pydantic-схемы
├── services/    # бизнес-логика
├── worker/      # celery tasks
└── main.py      # точка входа
```

Дополнительно:
- `migrations/` — Alembic миграции
- `tests/` — тесты
- `load_tests/` — locust-сценарии
- `grafana/` — конфиги мониторинга
- `nginx/` — конфиг nginx

## Требования

- Docker + Docker Compose (рекомендуется)
- Локально: Python 3.11+, Poetry
- PostgreSQL, RabbitMQ и Redis — если запускать без Docker

## Быстрый старт (Docker)

1) Создай `.env` в корне проекта:

```env
DATABASE_URL_ASYNC_INNER=postgresql+asyncpg://app:pass@database:5432/app_db
DATABASE_URL_SYNC_OUT=postgresql+psycopg://app:pass@localhost:5432/app_db
DATABASE_URL_SYNC_INNER=postgresql+psycopg://app:pass@database:5432/app_db
DATABASE_URL_ASYNC_OUT=postgresql+asyncpg://app:pass@localhost:5432/app_db

CELERY_BROKER_URL=amqp://app:pass@rabbitmq:5672//
CELERY_RESULT_BACKEND=redis://redis:6379/0

SECRET_KEY=change_me
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

2) Подними окружение:

```bash
docker compose -f docker-compose.yaml up --build
```

3) Открой API:

- Swagger: `http://localhost/docs`
- OpenAPI: `http://localhost/openapi.json`
- Healthcheck: `http://localhost/health`

> В compose поднимаются два backend-инстанса, `nginx`, Postgres, RabbitMQ, Redis и сервисы для мониторинга.

## Запуск локально (без Docker)

Установка зависимостей:

```bash
poetry install
```

Применение миграций:

```bash
poetry run alembic -x env=out upgrade head
```

Запуск API:

```bash
poetry run uvicorn app.main:app --reload
```

Запуск Celery worker:

```bash
poetry run celery -A app.core.celery_app worker -l info
```

Запуск Celery Beat:

```bash
poetry run celery -A app.core.celery_app beat -l info
```

Перед запуском должны быть доступны PostgreSQL, RabbitMQ и Redis, а переменные окружения должны быть заданы.

## Тесты

```bash
poetry run pytest
```

## Нагрузочное тестирование

```bash
locust -f load_tests/locustfile.py
```

Дополнительно:
- `LoadTestingReport.md` — отчёт по нагрузочному тестированию
- `scripts/seed_loadtest_users.py` — подготовка тестовых пользователей

## API (основные маршруты)

Точный список и схемы — в Swagger (`/docs`).

**Auth**
- `POST /auth/register` — регистрация
- `POST /auth/login` — логин

**Users**
- `GET /users/me` — текущий пользователь

**Tasks**
- `GET /tasks` — список задач
- `POST /tasks` — создать задачу
- `GET /tasks/{id}` — получить задачу
- `PUT/PATCH /tasks/{id}` — обновить
- `POST /tasks/{id}/complete` — отметить выполненной
- `DELETE /tasks/{id}` — удалить

**Categories**
- `GET /categories` — список категорий
- `POST /categories` — создать категорию
- `GET /categories/{id}` — получить категорию
- `PUT/PATCH /categories/{id}` — обновить
- `DELETE /categories/{id}` — удалить

**Notifications**
- напоминания и связанные фоновые операции

## Архитектура (кратко)

- `app.main` — FastAPI приложение и подключение роутеров
- `app.core.config` — настройки через env
- `app.core.security` — хэширование паролей и JWT
- `app.core.celery_app` — Celery и Beat
- `app.core.exception_handlers` — единая обработка ошибок
- `app.services.*` — основная бизнес-логика
- `app.worker.tasks` — фоновые задачи
- `migrations/` — миграции базы

## Что есть в проекте

- Docker-окружение для запуска всех сервисов
- Nginx перед двумя backend-инстансами
- Миграции Alembic
- Автотесты
- Нагрузочные тесты
- Конфиги мониторинга и логирования
- GitHub Actions CI
