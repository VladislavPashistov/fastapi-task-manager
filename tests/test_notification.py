import datetime
import uuid

import pytest
from jose import jwt
from sqlalchemy import UUID

from app.core.config import settings
from app.models import Notification, Channel, Status


async def _get_user1_id(auth_header) -> UUID:
    bearer_token = auth_header["Authorization"].split()[1]
    decoded_token = jwt.decode(bearer_token, settings.SECRET_KEY, algorithms=["HS256"])
    return decoded_token["sub"]


async def _create_ntf(async_session, *, user_id, read: bool, created_at: datetime.datetime):
    ntf = Notification(
        user_id=user_id,
        task_id=uuid.uuid4(),
        channel=Channel.in_app,
        status=Status.pending,
        message=f"msg-{uuid.uuid4()}",
        created_at=created_at,
        read_at=(created_at + datetime.timedelta(minutes=1)) if read else None,
    )
    async_session.add(ntf)
    await async_session.commit()
    await async_session.refresh(ntf)
    return ntf


@pytest.mark.asyncio
async def test_get_unread_notifications_200_happy_path(async_client, async_session, auth_headers):
    user_id = await _get_user1_id(auth_headers)
    now = datetime.datetime.now(datetime.timezone.utc)

    await _create_ntf(async_session, user_id=user_id, read=False, created_at=now)
    await _create_ntf(
        async_session, user_id=user_id, read=False, created_at=now + datetime.timedelta(seconds=1))
    await _create_ntf(
        async_session, user_id=user_id, read=True, created_at=now + datetime.timedelta(seconds=2))

    r = await async_client.get("/notifications/unread", headers=auth_headers)
    assert r.status_code == 200

    data = r.json()
    assert isinstance(data, list)
    assert len(data) == 2
    assert all(item["read_at"] is None for item in data)


@pytest.mark.asyncio
async def test_get_read_notifications_200_happy_path(async_client, async_session, auth_headers):
    user_id = await _get_user1_id(auth_headers)
    now = datetime.datetime.now(datetime.timezone.utc)

    await _create_ntf(async_session, user_id=user_id, read=True, created_at=now)
    await _create_ntf(
        async_session, user_id=user_id, read=True, created_at=now + datetime.timedelta(seconds=1))
    await _create_ntf(
        async_session, user_id=user_id, read=False, created_at=now + datetime.timedelta(seconds=2))

    r = await async_client.get("/notifications/read", headers=auth_headers)
    assert r.status_code == 200

    data = r.json()
    assert isinstance(data, list)
    assert len(data) == 2
    assert all(item["read_at"] is not None for item in data)


@pytest.mark.asyncio
async def test_get_unread_notifications_limit_offset(async_client, async_session, auth_headers):
    user_id = await _get_user1_id(auth_headers)
    base = datetime.datetime.now(datetime.timezone.utc)

    for i in range(5):
        await _create_ntf(
            async_session, user_id=user_id, read=False,
            created_at=base + datetime.timedelta(seconds=i)
        )

    r = await async_client.get("/notifications/unread?limit=2&offset=1", headers=auth_headers)
    assert r.status_code == 200

    data = r.json()
    assert isinstance(data, list)
    assert len(data) == 2


@pytest.mark.asyncio
async def test_get_notification_200_happy_path(async_client, async_session, auth_headers):
    user_id = await _get_user1_id(auth_headers)
    ntf = await _create_ntf(
        async_session,
        user_id=user_id,
        read=False,
        created_at=datetime.datetime.now(datetime.timezone.utc),
    )

    r = await async_client.get(f"/notifications/{ntf.id}", headers=auth_headers)
    assert r.status_code == 200

    data = r.json()
    assert data["id"] == str(ntf.id)
    assert data["message"] == ntf.message
    assert data["read_at"] is None


@pytest.mark.asyncio
async def test_get_notification_401_unauthorized(async_client, async_session, auth_headers):
    user_id = await _get_user1_id(auth_headers)
    ntf = await _create_ntf(
        async_session,
        user_id=user_id,
        read=False,
        created_at=datetime.datetime.now(datetime.timezone.utc),
    )

    r = await async_client.get(f"/notifications/{ntf.id}")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_get_notification_404_not_found(async_client, auth_headers):
    ntf_id = str(uuid.uuid4())
    r = await async_client.get(f"/notifications/{ntf_id}", headers=auth_headers)
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_mark_one_notification_204_happy_path(async_client, async_session, auth_headers):
    user_id = await _get_user1_id(auth_headers)
    ntf = await _create_ntf(
        async_session,
        user_id=user_id,
        read=False,
        created_at=datetime.datetime.now(datetime.timezone.utc),
    )
    await async_session.commit()

    r = await async_client.post(f"/notifications/{ntf.id}/read", headers=auth_headers)
    assert r.status_code == 204

    r_get = await async_client.get(f"/notifications/{ntf.id}", headers=auth_headers)
    assert r_get.status_code == 200
    assert r_get.json()["read_at"] is not None


@pytest.mark.asyncio
async def test_mark_one_notification_401_unauthorized(async_client, async_session, auth_headers):
    user_id = await _get_user1_id(auth_headers)
    ntf = await _create_ntf(
        async_session,
        user_id=user_id,
        read=False,
        created_at=datetime.datetime.now(datetime.timezone.utc),
    )

    r = await async_client.post(f"/notifications/{ntf.id}/read")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_mark_all_notifications_204_happy_path(async_client, async_session, auth_headers):
    user_id = await _get_user1_id(auth_headers)
    now = datetime.datetime.now(datetime.timezone.utc)

    await _create_ntf(async_session, user_id=user_id, read=False, created_at=now)
    await _create_ntf(
        async_session, user_id=user_id, read=False, created_at=now + datetime.timedelta(seconds=1))
    await _create_ntf(
        async_session, user_id=user_id, read=True, created_at=now + datetime.timedelta(seconds=2))

    r = await async_client.post("/notifications/read-all", headers=auth_headers)
    assert r.status_code == 204

    r_unread = await async_client.get("/notifications/unread", headers=auth_headers)
    assert r_unread.status_code == 200
    assert r_unread.json() == []


@pytest.mark.asyncio
async def test_mark_all_notifications_401_unauthorized(async_client):
    r = await async_client.post("/notifications/read-all")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_get_notification_404_foreign_user(async_client, async_session, auth_headers):
    # user1 notification
    user1_id = await _get_user1_id(auth_headers)
    ntf = await _create_ntf(
        async_session,
        user_id=user1_id,
        read=False,
        created_at=datetime.datetime.now(datetime.timezone.utc),
    )

    # user2 register
    email2 = f"{uuid.uuid4()}@example.com"
    username2 = f"user_{uuid.uuid4()}"
    password2 = "StrongPass123!"

    r_reg = await async_client.post(
        "/auth/register",
        json={"username": username2, "email": email2, "password": password2},
    )
    assert r_reg.status_code == 201

    # user2 login -> token
    r_login = await async_client.post(
        "/auth/login",
        data={"username": email2, "password": password2},
    )
    assert r_login.status_code == 200
    token2 = r_login.json()["access_token"]
    headers2 = {"Authorization": f"Bearer {token2}"}

    # user2 tries to read чужое уведомление
    r_get = await async_client.get(f"/notifications/{ntf.id}", headers=headers2)
    assert r_get.status_code == 404
