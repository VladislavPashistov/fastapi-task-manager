import logging
from typing import List
from uuid import UUID

from sqlalchemy import select, delete
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, Category
from app.schemas import CreateCategory, UpdateCategory

log = logging.getLogger(__name__)


class CategoryAlreadyExists(Exception):
    ...


class CategoryNotFound(Exception):
    ...


class CategoryDeleteFailed(Exception):
    ...


class CategoryValidationError(Exception):
    ...


async def create_category_service(db: AsyncSession, user: User, data: CreateCategory
                                  ) -> Category:
    name = data.name.strip()

    if name == "":
        raise CategoryValidationError("name cannot be empty")

    req = select(Category).where(
        Category.user_id == user.id,
        Category.name == name
    )
    res = await db.execute(req)

    if res.scalar_one_or_none():
        raise CategoryAlreadyExists()

    category = Category(
        name=name,
        color=data.color,
        user_id=user.id,
    )

    db.add(category)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        log.warning("IntegrityError while creating category")
        raise CategoryAlreadyExists()

    await db.refresh(category)
    return category


async def read_category_service(db: AsyncSession, user: User, category_id: UUID
                                ) -> Category:
    req = select(Category).where(
        Category.user_id == user.id,
        Category.id == category_id,

    )
    res = await db.execute(req)
    result = res.scalar_one_or_none()
    if result is None:
        raise CategoryNotFound()

    return result


async def read_categories_service(db: AsyncSession, user: User
                                  ) -> List[Category]:
    req = select(Category).where(
        Category.user_id == user.id,
    ).order_by(Category.name)
    res = await db.execute(req)

    categories: list[Category] = list(res.scalars().all())
    return categories


async def update_category_service(db: AsyncSession,
                                  user: User,
                                  category_id: UUID,
                                  data: UpdateCategory,
                                  ) -> Category:
    # принадлежит ли категория юзеру
    category = (await db.execute(
        select(Category).where(
            Category.user_id == user.id,
            Category.id == category_id,
        )
    )).scalar_one_or_none()

    if category is None:
        raise CategoryNotFound()

    payload = data.model_dump(exclude_unset=True)

    # проверка / strip
    if "name" in payload:
        if payload["name"] is None:
            raise CategoryValidationError("name cannot be null")
        name = payload["name"].strip()
        if name == "":
            raise CategoryValidationError("name cannot be empty")
        payload["name"] = name

    # WARNING

    allowed = {"name", "color"}
    for key, value in payload.items():
        if key in allowed:
            setattr(category, key, value)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        log.warning("IntegrityError while updating category")
        raise CategoryAlreadyExists()

    await db.refresh(category)
    return category


async def delete_category_service(db: AsyncSession, user: User, category_id: UUID
                                  ) -> None:
    req = delete(Category).where(Category.user_id == user.id,
                                 Category.id == category_id
                                 ).returning(Category.id)

    res = await db.execute(req)
    result = res.scalar_one_or_none()

    if result is None:
        raise CategoryNotFound()

    try:
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        logging.exception("SQLAlchemyError while deleting category")
        raise CategoryDeleteFailed()
