"""Test reports module endpoints."""

import pytest


@pytest.mark.asyncio
async def test_reports_disk_stats(client):
    """GET /api/reports/disk-stats returns disk usage stats."""
    resp = await client.get("/api/reports/disk-stats")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)


@pytest.mark.asyncio
async def test_reports_system_info(client):
    """GET /api/reports/system-info returns system information."""
    resp = await client.get("/api/reports/system-info")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)


@pytest.mark.asyncio
async def test_reports_timeline(client):
    """GET /api/reports/timeline returns activity timeline."""
    resp = await client.get("/api/reports/timeline")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)


@pytest.mark.asyncio
async def test_reports_timeline_stats(client):
    """GET /api/reports/timeline/stats returns aggregated stats."""
    resp = await client.get("/api/reports/timeline/stats", params={"group_by": "day", "days": 7})
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, (list, dict))


@pytest.mark.asyncio
async def test_reports_journal(client):
    """GET /api/reports/journal returns journal entries."""
    resp = await client.get("/api/reports/journal")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, (list, dict))


@pytest.mark.asyncio
async def test_reports_bookmarks(client):
    """GET /api/reports/bookmarks returns bookmarks."""
    resp = await client.get("/api/reports/bookmarks")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, (list, dict))


@pytest.mark.asyncio
async def test_reports_dashboard_summary(client):
    """GET /api/reports/dashboard-summary returns summary."""
    resp = await client.get("/api/reports/dashboard-summary")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
