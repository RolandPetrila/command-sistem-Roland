"""Test automations module endpoints."""

import pytest


@pytest.mark.asyncio
async def test_automations_tasks_list(client):
    """GET /api/automations/tasks returns task list."""
    resp = await client.get("/api/automations/tasks")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_automations_shortcuts_list(client):
    """GET /api/automations/shortcuts returns shortcuts."""
    resp = await client.get("/api/automations/shortcuts")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_automations_monitors_list(client):
    """GET /api/automations/monitors returns uptime monitors."""
    resp = await client.get("/api/automations/monitors")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_automations_health(client):
    """GET /api/automations/health returns system health."""
    resp = await client.get("/api/automations/health")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)


@pytest.mark.asyncio
async def test_automations_notifications(client):
    """GET /api/automations/notifications returns notifications."""
    resp = await client.get("/api/automations/notifications")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data or isinstance(data, list)
