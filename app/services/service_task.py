import datetime
import logging
import uuid
from enum import Enum
from typing import List
from uuid import UUID

from sqlalchemy import select, delete
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.models import User, Task, Category
from app.schemas import CreateTask, UpdateTask
from app.services.service_category import CategoryNotFound


class TaskAlreadyExists(Exception):
    ...


class TaskNotFound(Exception):
    ...


class TaskDeleteFailed(Exception):
    ...


class TaskValidationError(Exception):
    ...


log = logging.getLogger(__name__)


async def create_task_service(
        db: AsyncSession,
        data: CreateTask,
        user: User,
):
    if data.category_id is not None:
        category = (await db.execute(
            select(Category).where(
                Category.user_id == user.id,
                Category.id == data.category_id,
            )
        )).scalar_one_or_none()

        if category is None:
            raise CategoryNotFound()

    payload = data.model_dump(exclude_unset=True)

    # проверка / strip
    if "title" in payload:
        if payload["title"] is None:
            raise TaskValidationError("title cannot be null")
        name = payload["title"].strip()
        if name == "":
            raise TaskValidationError("title cannot be empty")
        payload["title"] = name

    task = Task(
        title=payload["title"],
        description=data.description,
        is_completed=data.is_completed,
        reminder_time=data.reminder_time,
        user_id=user.id,
        category_id=data.category_id,
    )

    db.add(task)

    try:
        await db.commit()
    except IntegrityError as e:
        await db.rollback()
        log.warning("IntegrityError")

        # Код SQLSTATE для ошибок ограничений Postgres
        code = getattr(e.orig, "sqlstate", None)

        if code == "23505":  # нарушение уникальности
            raise TaskAlreadyExists()
        elif code == "23503":  # нарушение внешнего ключа (FK)
            raise CategoryNotFound()
        if code in ("23502", "23514"):  # нарушение NOT NULL | CHECK-ограничения
            raise TaskValidationError() from e

        raise

    await db.refresh(task)

    if task.is_completed:
        task.reminder_time = None
        task.last_reminder_id = None
        await db.commit()
        return task

    now = datetime.datetime.now(datetime.timezone.utc)
    rt = task.reminder_time

    if rt is not None and now <= rt:
        from app.worker.tasks import send_task_reminder
        task.last_reminder_id = uuid.uuid4()
        mess = data.message_reminder if data.message_reminder is not None else "reminder"
        send_task_reminder.apply_async(
            kwargs={"task_id": str(task.id),
                    "user_id": str(user.id),
                    "message": mess},
            task_id=str(task.last_reminder_id),
            eta=rt,
        )
        await db.commit()

    await db.refresh(task)
    return task


async def read_tasks_service(
        db: AsyncSession,
        user: User,
        page: int,
        per_page: int,
) -> List[Task]:
    offset = (page - 1) * per_page
    logging.debug(
        "read_tasks user_id=%s page=%s per_page=%s offset=%s",
        user.id, page, per_page, offset
    )

    req = (
        select(Task)
        .where(Task.user_id == user.id)
        .order_by(Task.created_at.desc(), Task.id.desc())
        .offset(offset)
        .limit(per_page)
    )

    try:
        res = await db.execute(req)
    except SQLAlchemyError:
        await db.rollback()
        logging.exception("SQLAlchemyError while reading tasks")
        raise
    result: list[Task] = list(res.scalars().all())
    return result


async def read_task_service(
        db: AsyncSession,
        task_id: UUID,
        user: User,
) -> Task:
    logging.debug(
        "read_task user_id=%s task_id=%s",
        user.id, task_id,
    )

    req = select(Task).where(
        Task.user_id == user.id,
        Task.id == task_id,
    )

    result = await db.execute(req)
    task = result.scalars().first()
    if task is None:
        raise TaskNotFound()

    return task


class ModReqIsNotCompleted(Enum):
    only_expired = "only_expired"
    only_fresh = "only_fresh"
    everything = "everything"


async def read_tasks_is_not_completed(
        db: AsyncSession,
        user: User,
        mod: ModReqIsNotCompleted = ModReqIsNotCompleted.everything,
) -> List[Task]:
    now = datetime.datetime.now(datetime.timezone.utc)
    logging.debug("read_tasks_is_not_completed user_id=%s mod=%s", user.id, mod)

    if mod == ModReqIsNotCompleted.only_fresh:
        req = select(Task).where(
            Task.user_id == user.id,
            Task.is_completed.is_(False),
            Task.reminder_time.is_not(None),
            Task.reminder_time > now,
        ).order_by(Task.reminder_time.desc())
    elif mod == ModReqIsNotCompleted.only_expired:
        req = select(Task).where(
            Task.user_id == user.id,
            Task.is_completed.is_(False),
            Task.reminder_time.is_not(None),
            Task.reminder_time < now,
        ).order_by(Task.reminder_time.desc())
    else:
        req = select(Task).where(
            Task.user_id == user.id,
            Task.is_completed.is_(False),
            Task.reminder_time.is_not(None),
        ).order_by(Task.reminder_time.desc())

    result = await db.execute(req)
    result = result.scalars().all()

    return list(result)


async def update_task_service(
        db: AsyncSession,
        data: UpdateTask,
        task_id: UUID,
        user: User,
) -> Task:
    # тут и переключение complete
    if data.category_id is not None:

        # принадлежит ли категория юзеру
        category = (await db.execute(
            select(Category).where(
                Category.user_id == user.id,
                Category.id == data.category_id,
            )
        )).scalar_one_or_none()

        if category is None:
            raise CategoryNotFound()

    # принадлежит ли таска юзеру
    task = (await db.execute(
        select(Task).where(
            Task.id == task_id,
            Task.user_id == user.id,
        )
    )).scalar_one_or_none()

    if task is None:
        raise TaskNotFound()

    payload = data.model_dump(exclude_unset=True)

    # проверка / strip
    if "title" in payload:
        if payload["title"] is None:
            raise TaskValidationError("title cannot be null")
        name = payload["title"].strip()
        if name == "":
            raise TaskValidationError("title cannot be empty")
        payload["title"] = name

    allowed = {
        "message_reminder", "reminder_time", "is_completed", "description", "title", "category_id"
    }
    for key, value in payload.items():
        if key in allowed:
            setattr(task, key, value)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        logging.exception("IntegrityError while updating task")
        raise TaskAlreadyExists()

    await db.refresh(task)

    if task.is_completed:
        task.reminder_time = None
        task.last_reminder_id = None
        await db.commit()
        await db.refresh(task)
        return task

    now = datetime.datetime.now(datetime.timezone.utc)
    rt = task.reminder_time

    if rt is not None and now <= rt:
        from app.worker.tasks import send_task_reminder
        task.last_reminder_id = uuid.uuid4()
        mess = data.message_reminder if data.message_reminder is not None else "reminder"
        send_task_reminder.apply_async(
            kwargs={"task_id": str(task.id),
                    "user_id": str(user.id),
                    "message": mess},
            task_id=str(task.last_reminder_id),
            eta=rt,
        )
        await db.commit()

    await db.refresh(task)
    return task


async def delete_task_service(
        db: AsyncSession,
        task_id: UUID,
        user_id: UUID,
):
    req = delete(Task).where(
        Task.id == task_id,
        Task.user_id == user_id,
    ).returning(Task)

    res = await db.execute(req)

    if res.scalar_one_or_none() is None:
        raise TaskNotFound()

    try:
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        logging.exception("SQLAlchemyError while deleting task")
        raise TaskDeleteFailed()


def sync_delete_task_service(
        db: Session,
        task_id: UUID,
        user_id: UUID,
):
    req = delete(Task).where(
        Task.id == task_id,
        Task.user_id == user_id,
    ).returning(Task.id)

    res = db.execute(req)
    result = res.scalar_one_or_none()

    if result is None:
        raise TaskNotFound()
