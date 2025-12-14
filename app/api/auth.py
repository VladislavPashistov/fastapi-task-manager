from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.schemas import CreateUser, ReadUser, Token
from app.api.deps import get_current_user
from app.services import create_user_service, login_user_service
from app.db import get_db
from fastapi.security import OAuth2PasswordRequestForm

import logging

logger = logging.getLogger(__name__)

router_auth = APIRouter(prefix="/auth")


@router_auth.post(path="/register", response_model=ReadUser, status_code=201)
async def register(
        data: CreateUser,
        db: AsyncSession = Depends(get_db),
):

    return await create_user_service(db=db, data=data)


# TODO(auth): доработать обработку ошибок логина
# - неверный логин/пароль -> InvalidLoginOrPassword -> 401
# - пользователь заблокирован -> UserInactive -> 403
# - БД недоступна/ошибка БД -> SQLAlchemyError -> 500
# - всё остальное -> Exception
@router_auth.post(path="/login", response_model=Token, status_code=200)
async def login(
        form: OAuth2PasswordRequestForm = Depends(),
        db: AsyncSession = Depends(get_db),
):

    return await login_user_service(
        db=db,
        login=form.username,   # ← тут username или email
        password=form.password,
    )


router_users = APIRouter(prefix="/users")


@router_users.get(path="/me", response_model=ReadUser, status_code=200)
async def me(current_user: User = Depends(get_current_user)):
    return current_user


router_health = APIRouter(prefix="/health")


@router_health.get(path="")
async def health_check():
    return {"status": "ok"}
