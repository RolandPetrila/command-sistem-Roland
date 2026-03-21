"""Test health and base endpoints."""

import time

import pytest


@pytest.mark.asyncio
async def test_health_ok(client):
    """GET /api/health returns status ok."""
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "version" in data


@pytest.mark.asyncio
async def test_health_response_time(client):
    """Health endpoint responds in under 2 seconds."""
    start = time.perf_counter()
    resp = await client.get("/api/health")
    elapsed = time.perf_counter() - start
    assert resp.status_code == 200
    assert elapsed < 2.0, f"Health took {elapsed:.2f}s (max 2s)"


@pytest.mark.asyncio
async def test_modules_list(client):
    """GET /api/modules returns a non-empty list."""
    resp = await client.get("/api/modules")
    assert resp.status_code == 200
    modules = resp.json()
    assert isinstance(modules, list)
    assert len(modules) >= 10, f"Expected 10+ modules, got {len(modules)}"


@pytest.mark.asyncio
async def test_diagnostics(client):
    """GET /api/diagnostics returns system info."""
    resp = await client.get("/api/diagnostics")
    assert resp.status_code == 200
    data = resp.json()
    assert "request_stats" in data
    assert "system" in data
    assert data["system"]["modules_loaded"] >= 10


@pytest.mark.asyncio
async def test_speed_payload(client):
    """GET /api/network/speed-payload returns 500KB."""
    resp = await client.get("/api/network/speed-payload")
    assert resp.status_code == 200
    assert len(resp.content) == 500 * 1024
