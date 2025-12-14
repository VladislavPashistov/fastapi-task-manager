import datetime
import logging

from sqlalchemy.sql.functions import now

from app.core import celery_app
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.services.service_task import sync_delete_task_service
from app.worker.db import session_scope
from app.models import Task, Notification

log = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=5)
def send_task_reminder(
        self, task_id: str,
        user_id: str,
        message: str,
):
    with session_scope() as db:
        stmt = select(Task).where(
            Task.id == task_id,
            Task.user_id == user_id,
            Task.last_reminder_id == str(self.request.id),
            Task.reminder_time.isnot(None),
            Task.is_completed.is_(False),
        )
        task = db.execute(stmt).scalar_one_or_none()

        if task is None:
            log.warning(f"task_id={task_id} user_id={user_id} request_id={self.request.id}")
            return

        try:
            noti = Notification(
                user_id=task.user_id,
                task_id=task.id,
                read_at=None,
                message=message,
            )
            db.add(noti)

            task.reminder_time = None
            task.last_reminder_id = None
            db.commit()
            log.warning(f"successfully noti: "
                        f"task_id={task_id} user_id={user_id} request_id={self.request.id}"
                        )
        except IntegrityError as e:
            num_err = getattr(e.orig, 'sqlstate', None)
            log.warning(f"request_id={self.request.id}, error_sqlstate={num_err}")
            db.rollback()
            db.refresh(task)

            # unique violation -> считаем, что уже создано
            if num_err == "23505" and task is not None:
                task.reminder_time = None
                task.last_reminder_id = None
                db.commit()
                return

            raise
        except Exception as e:
            db.rollback()
            log.exception("Failed to send reminder")
            raise self.retry(exc=e, countdown=10)


# напоминалка о просроченных (запланированных и не сделанных) тасках
@celery_app.task(bind=True, max_retries=5)
def catch_up(self):
    with session_scope() as db:
        tasks = db.execute(
            select(Task).where(
                Task.is_completed.is_(False),
                Task.reminder_time.isnot(None),
                Task.reminder_time <= now(),
            )).scalars().all()

        for task in tasks:
            try:
                db.add(
                    Notification(
                        user_id=task.user_id,
                        task_id=task.id,
                        message="Task not completed",
                    )
                )
                task.reminder_time = None
                task.last_reminder_id = None

                db.commit()

            except IntegrityError as e:
                num_err = getattr(e.orig, "sqlstate", None)
                log.warning(f"error_sqlstate={num_err}")
                db.rollback()
                db.merge(task)

                if num_err == "23505":
                    task.reminder_time = None
                    task.last_reminder_id = None
                    db.commit()
                    continue

                raise

            except Exception as e:
                db.rollback()
                log.exception("Failed to send reminder")
                raise self.retry(exc=e, countdown=10)


# очистка
@celery_app.task
def cleanup(batch_size: int = 500):
    with session_scope() as db:
        expire_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(weeks=4)

        while True:
            tasks = db.execute(
                select(Task).where(
                    Task.is_completed.is_(True),
                    Task.updated_at <= expire_date,
                ).order_by(Task.updated_at, Task.id).limit(batch_size)
            ).scalars().all()

            if not tasks:
                break

            for task in tasks:
                try:
                    sync_delete_task_service(
                        db=db,
                        user_id=task.user_id,
                        task_id=task.id,
                    )
                except Exception:
                    log.exception("Failed to delete task from cleanup")
                    db.rollback()
                    break

            db.commit()
