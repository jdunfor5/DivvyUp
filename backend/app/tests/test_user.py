import uuid
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio(loop_scope="session")


# ---------------------------------------------------------------------------
# POST /users/
# ---------------------------------------------------------------------------

async def test_create_user(client: AsyncClient):
    payload = {
        "email": f"{uuid.uuid4().hex[:8]}@test.com",
        "password": "TestPass123!",
        "display_name": "New User",
    }
    r = await client.post("/users/", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["email"] == payload["email"]
    assert data["display_name"] == payload["display_name"]
    assert "id" in data
    assert "password_hash" not in data


async def test_create_user_duplicate_email(client: AsyncClient):
    payload = {
        "email": f"{uuid.uuid4().hex[:8]}@test.com",
        "password": "TestPass123!",
        "display_name": "Duplicate User",
    }
    r1 = await client.post("/users/", json=payload)
    assert r1.status_code == 200

    r2 = await client.post("/users/", json=payload)
    assert r2.status_code == 400


async def test_create_user_invalid_email(client: AsyncClient):
    r = await client.post("/users/", json={
        "email": "not-an-email",
        "password": "TestPass123!",
        "display_name": "Bad Email",
    })
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# GET /users/me
# ---------------------------------------------------------------------------

async def test_get_me(client: AsyncClient, user_a: dict):
    r = await client.get("/users/me", headers=user_a["headers"])
    assert r.status_code == 200
    assert r.json()["id"] == user_a["user"]["id"]


async def test_get_me_unauthenticated(client: AsyncClient):
    r = await client.get("/users/me")
    assert r.status_code == 401


# ---------------------------------------------------------------------------
# GET /users/{user_uuid}
# ---------------------------------------------------------------------------

async def test_get_user_by_id(client: AsyncClient, user_a: dict, user_b: dict):
    target_id = user_b["user"]["id"]
    r = await client.get(f"/users/{target_id}", headers=user_a["headers"])
    assert r.status_code == 200
    assert r.json()["id"] == target_id


async def test_get_user_not_found(client: AsyncClient, user_a: dict):
    r = await client.get(f"/users/{uuid.uuid4()}", headers=user_a["headers"])
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# PATCH /users/me
# ---------------------------------------------------------------------------

async def test_update_me(client: AsyncClient, user_a: dict):
    r = await client.patch(
        "/users/me",
        json={"display_name": "Updated Name"},
        headers=user_a["headers"],
    )
    assert r.status_code == 200
    assert r.json()["display_name"] == "Updated Name"


async def test_update_me_partial(client: AsyncClient, user_a: dict):
    r = await client.patch(
        "/users/me",
        json={"venmo_handle": "myvenmo"},
        headers=user_a["headers"],
    )
    assert r.status_code == 200
    assert r.json()["venmo_handle"] == "myvenmo"


# ---------------------------------------------------------------------------
# DELETE /users/me
# ---------------------------------------------------------------------------

async def test_delete_me(client: AsyncClient):
    # Create a fresh user so deleting them doesn't affect other fixtures.
    payload = {
        "email": f"{uuid.uuid4().hex[:8]}@test.com",
        "password": "TestPass123!",
        "display_name": "To Be Deleted",
    }
    r = await client.post("/users/", json=payload)
    assert r.status_code == 200

    token_r = await client.post(
        "/auth/token",
        data={"username": payload["email"], "password": payload["password"]},
    )
    headers = {"Authorization": f"Bearer {token_r.json()['access_token']}"}

    delete_r = await client.delete("/users/me", headers=headers)
    assert delete_r.status_code == 204

    # Confirm the token no longer resolves to a valid user.
    me_r = await client.get("/users/me", headers=headers)
    assert me_r.status_code == 401


async def test_delete_me_as_group_admin_forbidden(client: AsyncClient, user_a: dict, group: dict):
    # user_a is admin of `group`, so deleting their account should be blocked.
    r = await client.delete("/users/me", headers=user_a["headers"])
    assert r.status_code == 403
