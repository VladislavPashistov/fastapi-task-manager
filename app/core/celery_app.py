from celery import Celery
from celery.schedules import crontab
from kombu import Queue, Exchange

from app.core.config import settings

broker = settings.CELERY_BROKER_URL
backend = settings.CELERY_RESULT_BACKEND

celery_app = Celery(
    "app",
    broker=broker,
    backend=backend,
    include=["app.worker.tasks"],
    task_default_queue="tasks"

)

celery_app.conf.update(
    enable_utc=True,

    task_default_queue="tasks",
    task_default_exchange="tasks",
    task_default_routing_key="tasks",
    task_default_exchange_type="direct",

    task_queues=(
        Queue("tasks", Exchange("tasks", type="direct"), routing_key="tasks"),
    ),
)

schedule = {
    "catch_up": {
        "task": "app.worker.tasks.catch_up",
        "schedule": crontab(minute=0, hour=0)
    },
    "cleanup": {
        "task": "app.worker.tasks.cleanup",
        "schedule": crontab(minute=0, hour=0)
    }
}

celery_app.conf.beat_schedule = schedule
