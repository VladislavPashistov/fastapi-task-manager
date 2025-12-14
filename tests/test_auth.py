import uuid
import pytest
from fastapi import HTTPException
from pydantic.v1 import EmailStr

from app.api.deps import get_current_user
from app.core import create_jwt
from app.schemas import CreateUser
from app.services import create_user_service


@pytest.mark.asyncio  # or anyio?
async def test_register_duplicate_email(async_client):
    email = f"{uuid.uuid4()}@example.com"
    username = str(uuid.uuid4())

    r1 = await async_client.post(
        "/auth/register",
        json={
            "username": username,
            "email": email,
            "password": "strongpassword",
        },
    )
    assert r1.status_code == 201

    r2 = await async_client.post(
        "/auth/register",
        json={
            "username": f"x{username}",
            "email": email,
            "password": "strongpassword",
        },
    )
    assert r2.status_code == 409


@pytest.mark.asyncio
async def test_current_user_valid(async_session):
    username = str(uuid.uuid4())
    email = f"{uuid.uuid4()}@example.com"
    password = str(uuid.uuid4())
    data = CreateUser(
        username=username,
        password=password,
        email=EmailStr(email)
    )

    user = await create_user_service(async_session, data=data)
    token = create_jwt(str(user.id))

    current = await get_current_user(token=token, db=async_session)

    assert current.id == user.id
    assert current.email == email


@pytest.mark.asyncio
async def test_current_user_invalid(async_session):
    username = str(uuid.uuid4())
    email = f"{uuid.uuid4()}@example.com"
    password = str(uuid.uuid4())
    data = CreateUser(
        username=username,
        password=password,
        email=EmailStr(email)
    )
    await create_user_service(async_session, data=data)
    token = "invalid.token.value"

    with pytest.raises(HTTPException) as exc:
        await get_current_user(token=token, db=async_session)

    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_current_user_user_not_found(async_session):
    fake_user_id = str(uuid.uuid4())
    token = create_jwt(fake_user_id)

    with pytest.raises(HTTPException) as exc:
        await get_current_user(token=token, db=async_session)

    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_current_user_expired(async_session):
    fake_user_id = str(uuid.uuid4())
    token = create_jwt(user_id=fake_user_id,
                       exp_min=-10)
    with pytest.raises(HTTPException) as exc:
        await get_current_user(token=token, db=async_session)

    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_auth_flow_success(async_client):
    email = f"{uuid.uuid4()}@example.com"
    username = str(uuid.uuid4())
    password = "qwerty1234"

    req_register = await async_client.post(
        "/auth/register",
        json={
            "username": username,
            "email": email,
            "password": password,
        },
    )
    assert req_register.status_code in (201, 200)

    req_login = await async_client.post(
        "/auth/login",
        data={
            "username": email,
            "password": password
        }
    )
    assert req_login.status_code == 200
    token = req_login.json()["access_token"]

    req_me = await async_client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert req_me.status_code == 200
    body = req_me.json()
    assert body["email"] == email
    assert body["username"] == username


@pytest.mark.asyncio
async def test_users_me_unauthenticated(async_client):
    req = await async_client.get("/users/me")
    assert req.status_code == 401


@pytest.mark.asyncio
async def test_login_wrong_password(async_client):
    email = f"{uuid.uuid4()}@example.com"
    username = str(uuid.uuid4())
    password = "qwerty1234"

    await async_client.post(
        "/auth/register",
        json={
            "username": username,
            "email": email,
            "password": password,
        },
    )

    r = await async_client.post(
        "/auth/login",
        data={
            "username": username,
            "password": "wrongpassword",
        },
    )

    assert r.status_code == 401
