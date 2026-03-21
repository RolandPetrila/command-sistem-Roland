"""Test invoice module — client CRUD."""

import pytest


@pytest.mark.asyncio
async def test_client_crud(client):
    """Create, Read, Update, Delete a client."""
    # CREATE
    resp = await client.post("/api/invoice/clients", json={
        "name": "Test Client SRL",
        "cui": "RO12345678",
        "address": "Str. Test 1, Bucuresti",
        "email": "test@example.com",
        "phone": "0721000000",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert "id" in data
    client_id = data["id"]

    # READ
    resp = await client.get(f"/api/invoice/clients/{client_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Test Client SRL"
    assert data["cui"] == "RO12345678"

    # UPDATE
    resp = await client.put(f"/api/invoice/clients/{client_id}", json={
        "name": "Test Client Updated SRL",
        "phone": "0722111111",
    })
    assert resp.status_code == 200

    # Verify update
    resp = await client.get(f"/api/invoice/clients/{client_id}")
    assert resp.json()["name"] == "Test Client Updated SRL"

    # DELETE
    resp = await client.delete(f"/api/invoice/clients/{client_id}")
    assert resp.status_code == 200

    # Verify deleted
    resp = await client.get(f"/api/invoice/clients/{client_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_clients_list(client):
    """GET /api/invoice/clients returns a list."""
    resp = await client.get("/api/invoice/clients")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
