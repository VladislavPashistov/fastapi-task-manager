import pytest
import uuid


@pytest.mark.asyncio
async def test_create_task_404_category_not_found(async_client, auth_headers):
    payload = {
        "title": "Test task",
        "description": "Test description",
        "category_id": str(uuid.uuid4()),
    }

    response = await async_client.post("/tasks", json=payload, headers=auth_headers)

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_patch_task_404_category_not_found(async_client, auth_headers):
    category_id = str(uuid.uuid4())
    payload = {"name": "category name"}
    r_patch = await async_client.patch(
        f"/categories/{category_id}",
        json=payload, headers=auth_headers
    )
    assert r_patch.status_code == 404


@pytest.mark.asyncio
async def test_create_category_201_happy_path(async_client, auth_headers):
    payload = {"name": "Work"}
    r = await async_client.post("/categories", json=payload, headers=auth_headers)
    assert r.status_code == 201

    data = r.json()
    assert "id" in data
    assert data["name"] == "Work"


@pytest.mark.asyncio
async def test_create_category_401_unauthorized(async_client):
    r = await async_client.post("/categories", json={"name": "Work"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_create_category_409_conflict(async_client, auth_headers):
    payload = {"name": "Work"}
    r1 = await async_client.post("/categories", json=payload, headers=auth_headers)
    assert r1.status_code == 201

    r2 = await async_client.post("/categories", json=payload, headers=auth_headers)
    assert r2.status_code == 409


@pytest.mark.asyncio
async def test_get_category_200_happy_path(async_client, auth_headers):
    r_create = await async_client.post("/categories", json={"name": "Work"}, headers=auth_headers)
    assert r_create.status_code == 201
    category_id = r_create.json()["id"]

    r_get = await async_client.get(f"/categories/{category_id}", headers=auth_headers)
    assert r_get.status_code == 200
    assert r_get.json()["id"] == category_id


@pytest.mark.asyncio
async def test_get_categories_200_happy_path(async_client, auth_headers):
    r = await async_client.get("/categories", headers=auth_headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@pytest.mark.asyncio
async def test_delete_category_204_happy_path(async_client, auth_headers):
    r_create = await async_client.post("/categories", json={"name": "Work"}, headers=auth_headers)
    assert r_create.status_code == 201
    category_id = r_create.json()["id"]

    r_del = await async_client.delete(f"/categories/{category_id}", headers=auth_headers)
    assert r_del.status_code == 204

    r_get = await async_client.get(f"/categories/{category_id}", headers=auth_headers)
    assert r_get.status_code == 404
