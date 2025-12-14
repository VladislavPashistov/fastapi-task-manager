import uuid
import pytest


# conftest: async_session, async_client

@pytest.mark.asyncio
async def test_create_task_201_happy_path(async_client, auth_headers):
    payload = {
        "title": "Test task",
        "description": "Test description",
    }

    response = await async_client.post("/tasks", json=payload, headers=auth_headers)

    assert response.status_code == 201

    data = response.json()
    assert data["title"] == payload["title"]
    assert data["description"] == payload["description"]
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_task_401_unauthorized(async_client):
    payload = {"title": "Test task", "description": "Test description"}

    response = await async_client.post("/tasks", json=payload)

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_task_409_conflict(async_client, auth_headers):
    payload = {"title": "Test task", "description": "Test description"}

    response = await async_client.post("/tasks", json=payload, headers=auth_headers)

    assert response.status_code == 201

    second_response = await async_client.post("/tasks", json=payload, headers=auth_headers)

    assert second_response.status_code == 409


@pytest.mark.asyncio
async def test_get_tasks_200_happy_path(async_client, auth_headers):
    response = await async_client.get("/tasks", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_tasks_401_unauthorized(async_client):
    response = await async_client.get("/tasks")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_task_200_happy_path(async_client, auth_headers):
    payload = {"title": "Test task", "description": "Test description"}

    r_create = await async_client.post("/tasks", json=payload, headers=auth_headers)
    assert r_create.status_code == 201
    task_id = r_create.json()["id"]

    r_get = await async_client.get(f"/tasks/{task_id}", headers=auth_headers)
    assert r_get.status_code == 200
    assert r_get.json()["id"] == task_id


@pytest.mark.asyncio
async def test_get_task_401_unauthorized(async_client, auth_headers):
    payload = {"title": "Test task", "description": "Test description"}

    r_create = await async_client.post("/tasks", json=payload, headers=auth_headers)
    assert r_create.status_code == 201

    task_id = r_create.json()["id"]

    r_get = await async_client.get(f"/tasks/{task_id}")
    assert r_get.status_code == 401


@pytest.mark.asyncio
async def test_get_task_404_not_found(async_client, auth_headers):
    task_id = str(uuid.uuid4())
    r_get = await async_client.get(f"/tasks/{task_id}", headers=auth_headers)
    assert r_get.status_code == 404


@pytest.mark.asyncio
async def test_patch_task_200_happy_path(async_client, auth_headers):
    payload = {
        "title": "Test task",
        "description": "Test description",
    }
    response = await async_client.post("/tasks", json=payload, headers=auth_headers)
    assert response.status_code == 201

    task_id = response.json()["id"]
    payload = {"title": "New title"}
    response = await async_client.patch(f"/tasks/{task_id}", json=payload, headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == task_id
    assert data["title"] == "New title"


@pytest.mark.asyncio
async def test_patch_task_401_unauthorized(async_client, auth_headers):
    payload = {
        "title": "Test task",
        "description": "Test description",
    }
    response = await async_client.post("/tasks", json=payload, headers=auth_headers)
    assert response.status_code == 201

    task_id = response.json()["id"]
    payload = {"title": "New title"}
    response = await async_client.patch(f"/tasks/{task_id}", json=payload)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_patch_task_404_not_found(async_client, auth_headers):
    task_id = str(uuid.uuid4())
    payload = {"title": "New title"}
    r_patch = await async_client.patch(f"/tasks/{task_id}", json=payload, headers=auth_headers)
    assert r_patch.status_code == 404


# переименовать в title уже существующей таски
@pytest.mark.skip(reason="temporarily disabled")
@pytest.mark.asyncio
async def test_patch_task_409_conflict(async_client, auth_headers):
    r = await async_client.post(
        "/tasks", json={"title": "A", "description": "1"}, headers=auth_headers)
    assert r.status_code == 201

    r = await async_client.post(
        "/tasks", json={"title": "B", "description": "2"}, headers=auth_headers)
    assert r.status_code == 201
    b_id = r.json()["id"]

    # r = await async_client.patch(f"/tasks/{b_id}", json={"title": "A"}, headers=auth_headers)
    # assert r.status_code == 409

    r = await async_client.get(f"/tasks/{b_id}", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["title"] == "B"


@pytest.mark.asyncio
async def test_delete_task_204_happy_path(async_client, auth_headers):
    payload = {"title": "Test task", "description": "Test description"}
    r_crt = await async_client.post("/tasks", json=payload, headers=auth_headers)
    assert r_crt.status_code == 201

    task_id = r_crt.json()["id"]
    r_del = await async_client.delete(f"/tasks/{task_id}", headers=auth_headers)
    assert r_del.status_code == 204

    r_get_deleted = await async_client.get(f"/tasks/{task_id}", headers=auth_headers)
    assert r_get_deleted.status_code == 404


@pytest.mark.asyncio
async def test_delete_task_401_unauthorized(async_client, auth_headers):
    payload = {"title": "Test task", "description": "Test description"}
    r_crt = await async_client.post("/tasks", json=payload, headers=auth_headers)
    assert r_crt.status_code == 201

    task_id = r_crt.json()["id"]
    r_del = await async_client.delete(f"/tasks/{task_id}")
    assert r_del.status_code == 401


@pytest.mark.asyncio
async def test_delete_task_404_not_found(async_client, auth_headers):
    task_id = str(uuid.uuid4())
    r_del = await async_client.delete(f"/tasks/{task_id}", headers=auth_headers)
    assert r_del.status_code == 404


@pytest.mark.asyncio
async def test_get_task_404_foreign_user(async_client, auth_headers):
    # user1 creates task
    r_create = await async_client.post(
        "/tasks",
        json={"title": "User1 task", "description": "secret"},
        headers=auth_headers,
    )
    assert r_create.status_code == 201
    task_id = r_create.json()["id"]

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

    # user2 пробует читать чужую задачу
    r_get = await async_client.get(f"/tasks/{task_id}", headers=headers2)
    assert r_get.status_code == 404
