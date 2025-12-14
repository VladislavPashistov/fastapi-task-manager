from pydantic import EmailStr
from sqlalchemy import select, or_
from uuid import UUID
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.core import hash_password, verify_password, create_jwt
from app.schemas import CreateUser


class UserNotFound(Exception):
    ...


class UserAlreadyExists(Exception):
    ...


class InvalidLoginOrPassword(Exception):
    ...


async def create_user_service(db: AsyncSession,
                              data: CreateUser,
                              ) -> User:
    # проверка на уникальность
    q = (select(User)
         .where(or_(User.username == data.username,
                    User.email == data.email)))

    res = await db.execute(q)
    if res.scalars().first() is not None:
        raise UserAlreadyExists()

    # хеш пароля
    hashed_password = hash_password(data.password)

    # создание модели
    user = User(username=data.username,
                email=data.email,
                hashed_password=hashed_password,
                fullname=data.fullname,
                )

    # сохранение в бд
    db.add(user)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise UserAlreadyExists()

    await db.refresh(user)
    return user


async def login_user_service(
        db: AsyncSession,
        login: str,
        password: str
) -> dict[str, str]:
    q = select(User).where(User.email == login)
    result = (await db.execute(q)).scalars().first()

    if not result:
        q = select(User).where(User.username == login)
        result = (await db.execute(q)).scalars().first()

    if not result or not verify_password(password, str(result.hashed_password)):
        raise InvalidLoginOrPassword()

    token = create_jwt(str(result.id))
    return {
        "access_token": token,
        "token_type": "bearer",
    }


async def get_user_by_id(
        db: AsyncSession,
        user_id: UUID
) -> User:
    q = select(User).where(User.id == user_id)
    result = await db.execute(q)

    result = result.scalar_one_or_none()
    if result is None:
        raise UserNotFound()

    return result


async def get_user_by_email(
        db: AsyncSession,
        email: EmailStr
) -> User | None:
    q = select(User).where(User.email == email)
    result = await db.execute(q)

    return result.scalar_one_or_none()


async def get_user_by_username(
        db: AsyncSession,
        username: str
) -> User | None:
    q = select(User).where(User.username == username)
    result = await db.execute(q)

    return result.scalar_one_or_none()
