from prometheus_fastapi_instrumentator import Instrumentator
from fastapi import FastAPI
from app.core.exception_handlers import register_exception_handlers
from app.api import (
    router_auth, router_users, router_health, router_categories, router_task, router_notifications
)

app = FastAPI()

Instrumentator().instrument(app).expose(app)
register_exception_handlers(app)

app.include_router(router_auth)
app.include_router(router_users)
app.include_router(router_categories)
app.include_router(router_task)
app.include_router(router_notifications)
app.include_router(router_health)
