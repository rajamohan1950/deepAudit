import pytest


@pytest.mark.asyncio
async def test_register_tenant(client):
    resp = await client.post("/api/v1/tenants", json={
        "name": "Test Tenant",
        "email": "test@example.com",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert "api_key" in data
    assert data["tenant"]["name"] == "Test Tenant"
    assert data["api_key"].startswith("da_")


@pytest.mark.asyncio
async def test_register_duplicate_tenant(client):
    await client.post("/api/v1/tenants", json={
        "name": "Dup Tenant",
        "email": "dup@example.com",
    })
    resp = await client.post("/api/v1/tenants", json={
        "name": "Dup Tenant 2",
        "email": "dup@example.com",
    })
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_get_profile_no_auth(client):
    resp = await client.get("/api/v1/tenants/me")
    assert resp.status_code == 401
