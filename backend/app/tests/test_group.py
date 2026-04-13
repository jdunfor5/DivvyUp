import uuid
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio(loop_scope="session")


# ---------------------------------------------------------------------------
# POST /groups/
# ---------------------------------------------------------------------------

async def test_create_group(client: AsyncClient, user_a: dict):
    r = await client.post(
        "/groups/",
        json={"name": "My Group", "description": "A test group"},
        headers=user_a["headers"],
    )
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "My Group"
    assert data["created_by"] == user_a["user"]["id"]
    assert "invite_code" in data


async def test_create_group_unauthenticated(client: AsyncClient):
    r = await client.post("/groups/", json={"name": "No Auth Group"})
    assert r.status_code == 401


# ---------------------------------------------------------------------------
# POST /groups/join
# ---------------------------------------------------------------------------

async def test_join_group(client: AsyncClient, user_b: dict, group: dict):
    r = await client.post(
        "/groups/join",
        json={"invite_code": group["invite_code"]},
        headers=user_b["headers"],
    )
    assert r.status_code == 200
    assert r.json()["id"] == group["id"]


async def test_join_group_invalid_code(client: AsyncClient, user_a: dict):
    r = await client.post(
        "/groups/join",
        json={"invite_code": "BADCODE1"},
        headers=user_a["headers"],
    )
    assert r.status_code == 404


async def test_join_group_already_member(client: AsyncClient, user_a: dict, group: dict):
    # user_a created the group and is already a member.
    r = await client.post(
        "/groups/join",
        json={"invite_code": group["invite_code"]},
        headers=user_a["headers"],
    )
    assert r.status_code == 400


# ---------------------------------------------------------------------------
# GET /groups/
# ---------------------------------------------------------------------------

async def test_list_groups(client: AsyncClient, user_a: dict, group: dict):
    r = await client.get("/groups/", headers=user_a["headers"])
    assert r.status_code == 200
    ids = [g["id"] for g in r.json()]
    assert group["id"] in ids


async def test_list_groups_empty(client: AsyncClient, user_b: dict):
    # user_b has not joined any group yet.
    r = await client.get("/groups/", headers=user_b["headers"])
    assert r.status_code == 200
    assert r.json() == []


# ---------------------------------------------------------------------------
# GET /groups/{group_uuid}
# ---------------------------------------------------------------------------

async def test_get_group(client: AsyncClient, user_a: dict, group: dict):
    r = await client.get(f"/groups/{group['id']}", headers=user_a["headers"])
    assert r.status_code == 200
    assert r.json()["id"] == group["id"]


async def test_get_group_not_member(client: AsyncClient, user_b: dict, group: dict):
    r = await client.get(f"/groups/{group['id']}", headers=user_b["headers"])
    assert r.status_code == 403


async def test_get_group_not_found(client: AsyncClient, user_a: dict):
    r = await client.get(f"/groups/{uuid.uuid4()}", headers=user_a["headers"])
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# PATCH /groups/{group_uuid}
# ---------------------------------------------------------------------------

async def test_update_group_as_admin(client: AsyncClient, user_a: dict, group: dict):
    r = await client.patch(
        f"/groups/{group['id']}",
        json={"name": "Renamed Group"},
        headers=user_a["headers"],
    )
    assert r.status_code == 200
    assert r.json()["name"] == "Renamed Group"


async def test_update_group_as_non_member(client: AsyncClient, user_b: dict, group: dict):
    r = await client.patch(
        f"/groups/{group['id']}",
        json={"name": "Should Fail"},
        headers=user_b["headers"],
    )
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# GET /groups/{group_uuid}/members
# ---------------------------------------------------------------------------

async def test_get_group_members(client: AsyncClient, user_a: dict, group: dict):
    r = await client.get(f"/groups/{group['id']}/members", headers=user_a["headers"])
    assert r.status_code == 200
    members = r.json()
    assert len(members) >= 1
    user_ids = [m["user_id"] for m in members]
    assert user_a["user"]["id"] in user_ids


async def test_get_group_members_not_member(client: AsyncClient, user_b: dict, group: dict):
    r = await client.get(f"/groups/{group['id']}/members", headers=user_b["headers"])
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# GET /groups/{group_uuid}/members/{user_uuid}
# ---------------------------------------------------------------------------

async def test_get_group_member(client: AsyncClient, user_a: dict, group: dict):
    r = await client.get(
        f"/groups/{group['id']}/members/{user_a['user']['id']}",
        headers=user_a["headers"],
    )
    assert r.status_code == 200
    assert r.json()["user_id"] == user_a["user"]["id"]
    assert r.json()["role"] == "admin"


# ---------------------------------------------------------------------------
# DELETE /groups/{group_uuid}/members  (leave group)
# ---------------------------------------------------------------------------

async def test_leave_group_as_member(client: AsyncClient, user_b: dict, group: dict):
    # Have user_b join first.
    join_r = await client.post(
        "/groups/join",
        json={"invite_code": group["invite_code"]},
        headers=user_b["headers"],
    )
    assert join_r.status_code == 200

    leave_r = await client.delete(
        f"/groups/{group['id']}/members",
        headers=user_b["headers"],
    )
    assert leave_r.status_code == 204


async def test_leave_group_as_admin_forbidden(client: AsyncClient, user_a: dict, group: dict):
    r = await client.delete(f"/groups/{group['id']}/members", headers=user_a["headers"])
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# PATCH /groups/{group_uuid}/members/{user_uuid}/transfer
# ---------------------------------------------------------------------------

async def test_transfer_ownership(client: AsyncClient, user_a: dict, user_b: dict, group: dict):
    # user_b must be a member first.
    await client.post(
        "/groups/join",
        json={"invite_code": group["invite_code"]},
        headers=user_b["headers"],
    )

    r = await client.patch(
        f"/groups/{group['id']}/members/{user_b['user']['id']}/transfer",
        headers=user_a["headers"],
    )
    assert r.status_code == 200

    # Confirm user_b is now admin.
    member_r = await client.get(
        f"/groups/{group['id']}/members/{user_b['user']['id']}",
        headers=user_b["headers"],
    )
    assert member_r.json()["role"] == "admin"


async def test_transfer_ownership_to_self(client: AsyncClient, user_a: dict, group: dict):
    r = await client.patch(
        f"/groups/{group['id']}/members/{user_a['user']['id']}/transfer",
        headers=user_a["headers"],
    )
    assert r.status_code == 400


# ---------------------------------------------------------------------------
# DELETE /groups/{group_uuid}
# ---------------------------------------------------------------------------

async def test_delete_group_as_non_member(client: AsyncClient, user_b: dict, group: dict):
    r = await client.delete(f"/groups/{group['id']}", headers=user_b["headers"])
    assert r.status_code == 403


async def test_delete_group_as_admin(client: AsyncClient, user_a: dict):
    # Create a dedicated group so deleting it doesn't break other tests.
    create_r = await client.post(
        "/groups/",
        json={"name": "Disposable Group"},
        headers=user_a["headers"],
    )
    assert create_r.status_code == 200
    gid = create_r.json()["id"]

    delete_r = await client.delete(f"/groups/{gid}", headers=user_a["headers"])
    assert delete_r.status_code == 204

    get_r = await client.get(f"/groups/{gid}", headers=user_a["headers"])
    assert get_r.status_code == 404
