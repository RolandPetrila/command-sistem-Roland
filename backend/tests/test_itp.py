"""Test ITP module — inspections CRUD + stats."""

import pytest


@pytest.mark.asyncio
async def test_inspection_create_and_read(client):
    """Create an inspection and verify it can be read."""
    resp = await client.post("/api/itp/inspections", json={
        "plate_number": "B 999 TST",
        "brand": "Dacia",
        "model": "Logan",
        "year": 2020,
        "fuel_type": "benzina",
        "owner_name": "Test Owner",
        "inspection_date": "2026-03-21",
        "expiry_date": "2028-03-21",
        "result": "admis",
        "price": 150.0,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "id" in data
    inspection_id = data["id"]

    # Read back
    resp = await client.get(f"/api/itp/inspections/{inspection_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["plate_number"] == "B 999 TST"
    assert data["brand"] == "Dacia"
    assert data["result"] == "admis"

    # Cleanup
    await client.delete(f"/api/itp/inspections/{inspection_id}")


@pytest.mark.asyncio
async def test_inspections_list(client):
    """GET /api/itp/inspections returns a list."""
    resp = await client.get("/api/itp/inspections")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data or isinstance(data, list)


@pytest.mark.asyncio
async def test_stats_overview(client):
    """GET /api/itp/stats/overview returns statistics."""
    resp = await client.get("/api/itp/stats/overview")
    assert resp.status_code == 200
    data = resp.json()
    assert "total" in data
