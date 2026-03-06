import logging

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.services import (
    UserAlreadyExists, InvalidLoginOrPassword, UserNotFound,
    CategoryAlreadyExists, CategoryNotFound, CategoryDeleteFailed, CategoryValidationError,
    TaskAlreadyExists, TaskNotFound, TaskDeleteFailed, TaskValidationError,
    NotificationNotFound,
)

log = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def http_handler(_request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def request_validation_handler(_request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={"detail": exc.errors()},
        )

    # User
    @app.exception_handler(UserAlreadyExists)
    async def user_exists_handler(_request: Request, _exc: UserAlreadyExists):
        return JSONResponse(status_code=409, content={"detail": "User already exists"})

    @app.exception_handler(InvalidLoginOrPassword)
    async def invalid_login_handler(_request: Request, _exc: InvalidLoginOrPassword):
        return JSONResponse(status_code=401, content={"detail": "Invalid login or password"})

    @app.exception_handler(UserNotFound)
    async def user_not_found_handler(_request: Request, _exc: UserNotFound):
        return JSONResponse(status_code=401, content={"detail": "User not found"})

    # Category
    @app.exception_handler(CategoryAlreadyExists)
    async def category_exists_handler(_request: Request, _exc: CategoryAlreadyExists):
        return JSONResponse(status_code=409, content={"detail": "Category already exists"})

    @app.exception_handler(CategoryNotFound)
    async def category_not_found_handler(_request: Request, _exc: CategoryNotFound):
        return JSONResponse(status_code=404, content={"detail": "Category not found"})

    @app.exception_handler(CategoryValidationError)
    async def category_validation_handler(_request: Request, exc: CategoryValidationError):
        msg = str(exc) or "Category validation error"
        return JSONResponse(status_code=400, content={"detail": msg})

    @app.exception_handler(CategoryDeleteFailed)
    async def category_delete_failed_handler(_request: Request, _exc: CategoryDeleteFailed):
        return JSONResponse(status_code=500, content={"detail": "Failed to delete category"})

    # Task
    @app.exception_handler(TaskAlreadyExists)
    async def task_exists_handler(_request: Request, _exc: TaskAlreadyExists):
        return JSONResponse(status_code=409, content={"detail": "Task already exists"})

    @app.exception_handler(TaskNotFound)
    async def task_not_found_handler(_request: Request, _exc: TaskNotFound):
        return JSONResponse(status_code=404, content={"detail": "Task not found"})

    @app.exception_handler(TaskValidationError)
    async def task_validation_handler(_request: Request, exc: TaskValidationError):
        msg = str(exc) or "Task validation error"
        return JSONResponse(status_code=400, content={"detail": msg})

    @app.exception_handler(TaskDeleteFailed)
    async def task_delete_failed_handler(_request: Request, _exc: TaskDeleteFailed):
        return JSONResponse(status_code=500, content={"detail": "Failed to delete task"})

    @app.exception_handler(NotificationNotFound)
    async def notification_not_found_handler(_request: Request, _exc: NotificationNotFound):
        return JSONResponse(status_code=404, content={"detail": "Notification not found"})

    @app.exception_handler(ResponseValidationError)
    async def resp_validation_handler(_request: Request, exc: ResponseValidationError):
        log.exception("Response validation error")
        msg = str(exc) or "Response validation error"
        return JSONResponse(status_code=500, content={"detail": msg})

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError):
        log.exception("Database error: %s", exc)  # Логируем ошибку
        return JSONResponse(
            status_code=500,
            content={"detail": "Database error occurred."},
        )

    # Fallback
    @app.exception_handler(Exception)
    async def unhandled_handler(_request: Request, exc: Exception):
        # log.exception("Unhandled exception", exc_info=exc)
        log.exception("Unhandled exception: %s", exc)
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})
