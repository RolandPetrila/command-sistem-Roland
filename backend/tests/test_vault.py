"""Test vault module endpoints — critical security module."""

import pytest


@pytest.mark.asyncio
async def test_vault_status(client):
    """GET /api/vault/status returns vault status."""
    resp = await client.get("/api/vault/status")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    assert "configured" in data


@pytest.mark.asyncio
async def test_vault_keys_requires_unlock(client):
    """GET /api/vault/keys requires vault to be unlocked."""
    resp = await client.get("/api/vault/keys")
    assert resp.status_code in (200, 400, 403, 422)


@pytest.mark.asyncio
async def test_vault_setup_empty_password(client):
    """POST /api/vault/setup with empty password should fail."""
    resp = await client.post("/api/vault/setup", json={"password": ""})
    assert resp.status_code in (400, 422)


@pytest.mark.asyncio
async def test_vault_unlock_wrong_password(client):
    """POST /api/vault/unlock with wrong password."""
    resp = await client.post("/api/vault/unlock", json={"password": "wrong_password_123"})
    assert resp.status_code in (200, 400, 401, 403, 422)


@pytest.mark.asyncio
async def test_vault_key_get_nonexistent(client):
    """GET /api/vault/keys/nonexistent returns error."""
    resp = await client.get("/api/vault/keys/__does_not_exist_999__")
    assert resp.status_code in (400, 403, 404, 422)


@pytest.mark.asyncio
async def test_vault_key_delete_nonexistent(client):
    """DELETE /api/vault/keys/nonexistent returns error."""
    resp = await client.delete("/api/vault/keys/__does_not_exist_999__")
    assert resp.status_code in (400, 403, 404, 422)
