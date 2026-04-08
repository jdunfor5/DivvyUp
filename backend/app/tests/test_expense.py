import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio(loop_scope="session")


# ---------------------------------------------------------------------------
# Shared expense fixture
# ---------------------------------------------------------------------------

def _expense_payload(**overrides) -> dict:
    return {
        "description": "Test lunch",
        "amount": "30.00",
        "currency": "USD",
        "base_amount": "30.00",
        "exchange_rate": "1",
        "category_id": 1,
        "split_type": "equal",
        "expense_date": "2024-06-01",
        **overrides,
    }


@pytest_asyncio.fixture(loop_scope="session")
async def expense(client: AsyncClient, user_a: dict, group: dict) -> dict:
    """An expense created by user_a inside the fixture group."""
    r = await client.post(
        f"/groups/{group['id']}/expenses/",
        json=_expense_payload(),
        headers=user_a["headers"],
    )
    assert r.status_code == 200, r.text
    return r.json()


# ---------------------------------------------------------------------------
# POST /groups/{group_uuid}/expenses/
# ---------------------------------------------------------------------------

async def test_create_expense(client: AsyncClient, user_a: dict, group: dict):
    r = await client.post(
        f"/groups/{group['id']}/expenses/",
        json=_expense_payload(description="Dinner", amount="50.00", base_amount="50.00"),
        headers=user_a["headers"],
    )
    assert r.status_code == 200
    data = r.json()
    assert data["description"] == "Dinner"
    assert data["paid_by"] == user_a["user"]["id"]
    assert data["group_id"] == group["id"]
    assert data["is_deleted"] is False


async def test_create_expense_not_member(client: AsyncClient, user_b: dict, group: dict):
    r = await client.post(
        f"/groups/{group['id']}/expenses/",
        json=_expense_payload(),
        headers=user_b["headers"],
    )
    assert r.status_code == 403


async def test_create_expense_unauthenticated(client: AsyncClient, group: dict):
    r = await client.post(f"/groups/{group['id']}/expenses/", json=_expense_payload())
    assert r.status_code == 401


# ---------------------------------------------------------------------------
# GET /groups/{group_uuid}/expenses/
# ---------------------------------------------------------------------------

async def test_list_expenses(client: AsyncClient, user_a: dict, group: dict, expense: dict):
    r = await client.get(f"/groups/{group['id']}/expenses/", headers=user_a["headers"])
    assert r.status_code == 200
    ids = [e["id"] for e in r.json()]
    assert expense["id"] in ids


async def test_list_expenses_not_member(client: AsyncClient, user_b: dict, group: dict):
    r = await client.get(f"/groups/{group['id']}/expenses/", headers=user_b["headers"])
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# GET /groups/{group_uuid}/expenses/{expense_uuid}
# ---------------------------------------------------------------------------

async def test_get_expense(client: AsyncClient, user_a: dict, group: dict, expense: dict):
    r = await client.get(
        f"/groups/{group['id']}/expenses/{expense['id']}",
        headers=user_a["headers"],
    )
    assert r.status_code == 200
    assert r.json()["id"] == expense["id"]


async def test_get_expense_not_found(client: AsyncClient, user_a: dict, group: dict):
    r = await client.get(
        f"/groups/{group['id']}/expenses/{uuid.uuid4()}",
        headers=user_a["headers"],
    )
    assert r.status_code == 404


async def test_get_expense_not_member(client: AsyncClient, user_b: dict, group: dict, expense: dict):
    r = await client.get(
        f"/groups/{group['id']}/expenses/{expense['id']}",
        headers=user_b["headers"],
    )
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# GET /groups/{group_uuid}/expenses/{expense_uuid}/splits
# ---------------------------------------------------------------------------

async def test_get_expense_splits(client: AsyncClient, user_a: dict, group: dict, expense: dict):
    r = await client.get(
        f"/groups/{group['id']}/expenses/{expense['id']}/splits",
        headers=user_a["headers"],
    )
    assert r.status_code == 200
    splits = r.json()
    assert len(splits) >= 1
    user_ids = [s["user_id"] for s in splits]
    assert user_a["user"]["id"] in user_ids


async def test_splits_sum_equals_base_amount(client: AsyncClient, user_a: dict, group: dict, expense: dict):
    r = await client.get(
        f"/groups/{group['id']}/expenses/{expense['id']}/splits",
        headers=user_a["headers"],
    )
    assert r.status_code == 200
    total = sum(float(s["share_amount"]) for s in r.json())
    assert abs(total - float(expense["base_amount"])) < 0.01


# ---------------------------------------------------------------------------
# PATCH /groups/{group_uuid}/expenses/{expense_uuid}
# ---------------------------------------------------------------------------

async def test_update_expense_as_creator(client: AsyncClient, user_a: dict, group: dict, expense: dict):
    r = await client.patch(
        f"/groups/{group['id']}/expenses/{expense['id']}",
        json={"description": "Updated description"},
        headers=user_a["headers"],
    )
    assert r.status_code == 200
    assert r.json()["description"] == "Updated description"


async def test_update_expense_as_non_member(client: AsyncClient, user_b: dict, group: dict, expense: dict):
    r = await client.patch(
        f"/groups/{group['id']}/expenses/{expense['id']}",
        json={"description": "Should fail"},
        headers=user_b["headers"],
    )
    assert r.status_code == 403


async def test_update_expense_not_found(client: AsyncClient, user_a: dict, group: dict):
    r = await client.patch(
        f"/groups/{group['id']}/expenses/{uuid.uuid4()}",
        json={"description": "Ghost"},
        headers=user_a["headers"],
    )
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /groups/{group_uuid}/expenses/{expense_uuid}
# ---------------------------------------------------------------------------

async def test_delete_expense_as_creator(client: AsyncClient, user_a: dict, group: dict):
    # Create a dedicated expense so we don't affect other tests.
    create_r = await client.post(
        f"/groups/{group['id']}/expenses/",
        json=_expense_payload(description="To delete"),
        headers=user_a["headers"],
    )
    assert create_r.status_code == 200
    eid = create_r.json()["id"]

    delete_r = await client.delete(
        f"/groups/{group['id']}/expenses/{eid}",
        headers=user_a["headers"],
    )
    assert delete_r.status_code == 204


async def test_deleted_expense_not_in_list(client: AsyncClient, user_a: dict, group: dict):
    create_r = await client.post(
        f"/groups/{group['id']}/expenses/",
        json=_expense_payload(description="Will be soft-deleted"),
        headers=user_a["headers"],
    )
    eid = create_r.json()["id"]

    await client.delete(
        f"/groups/{group['id']}/expenses/{eid}",
        headers=user_a["headers"],
    )

    list_r = await client.get(f"/groups/{group['id']}/expenses/", headers=user_a["headers"])
    ids = [e["id"] for e in list_r.json()]
    assert eid not in ids


async def test_delete_expense_as_non_member(client: AsyncClient, user_b: dict, group: dict, expense: dict):
    r = await client.delete(
        f"/groups/{group['id']}/expenses/{expense['id']}",
        headers=user_b["headers"],
    )
    assert r.status_code == 403
