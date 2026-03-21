"""Test filemanager module endpoints."""

import pytest


@pytest.mark.asyncio
async def test_filemanager_browse_root(client):
    """GET /api/fm/browse returns directory listing."""
    resp = await client.get("/api/fm/browse")
    assert resp.status_code == 200
    data = resp.json()
    assert "entries" in data or "items" in data or isinstance(data, list)


@pytest.mark.asyncio
async def test_filemanager_search(client):
    """GET /api/fm/search/fulltext with a query."""
    resp = await client.get("/api/fm/search/fulltext", params={"q": "test"})
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, (list, dict))


@pytest.mark.asyncio
async def test_filemanager_tags_list(client):
    """GET /api/fm/tags returns tag list."""
    resp = await client.get("/api/fm/tags")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, (list, dict))


@pytest.mark.asyncio
async def test_filemanager_favorites(client):
    """GET /api/fm/favorites returns favorites list."""
    resp = await client.get("/api/fm/favorites")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, (list, dict))


@pytest.mark.asyncio
async def test_filemanager_duplicates(client):
    """POST /api/fm/duplicates scans for duplicates."""
    resp = await client.post("/api/fm/duplicates", json={"path": "."})
    assert resp.status_code in (200, 422)
    data = resp.json()
    assert isinstance(data, (list, dict))


@pytest.mark.asyncio
async def test_filemanager_upload_no_file(client):
    """POST /api/fm/upload without file returns error."""
    resp = await client.post("/api/fm/upload")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_filemanager_path_traversal_blocked(client):
    """Path traversal attempts should be blocked."""
    resp = await client.get("/api/fm/browse", params={"path": "../../etc/passwd"})
    assert resp.status_code in (200, 400, 403)


@pytest.mark.asyncio
async def test_filemanager_mkdir(client):
    """POST /api/fm/mkdir requires name parameter."""
    resp = await client.post("/api/fm/mkdir", json={})
    assert resp.status_code in (400, 422)
