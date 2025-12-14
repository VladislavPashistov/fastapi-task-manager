from datetime import datetime, timedelta, timezone
from uuid import uuid4, UUID

from jose import JWTError, ExpiredSignatureError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# Password hashing --------------------------------

pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"],
    deprecated="auto",
    argon2__rounds=16,
)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


# JWT auth ----------------------------------------
ALGORITHM = "HS256"


class TokenExpired(Exception):
    ...


class InvalidToken(Exception):
    ...


def create_jwt(
        user_id: str | UUID,
        exp_min: int = settings.ACCESS_TOKEN_EXPIRE_MINUTES
) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=exp_min)

    return jwt.encode(
        {
            "sub": str(user_id),
            "iat": now,
            "exp": exp,
            "jti": str(uuid4()),
        },
        settings.SECRET_KEY,
        algorithm=ALGORITHM,
    )


def verify_jwt(token: str) -> UUID:
    try:
        payload = jwt.decode(
            str(token),
            settings.SECRET_KEY,
            algorithms=[ALGORITHM],
        )
        return UUID(payload["sub"])
    except ExpiredSignatureError as e:
        raise TokenExpired() from e
    except JWTError as e:
        raise InvalidToken() from e
