from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import verify_jwt, TokenExpired, InvalidToken
from app.db import get_db
from app.models import User
from app.services import get_user_by_id, UserNotFound

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# verify_jwt
async def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: AsyncSession = Depends(get_db),
        ) -> User:
    try:
        user_id = verify_jwt(token)
        user = await get_user_by_id(db, user_id)
    except (TokenExpired, InvalidToken, UserNotFound):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def check_recent_activity():
    raise NotImplementedError
