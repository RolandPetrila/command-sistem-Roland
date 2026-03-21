"""Test translator file operations."""

import pytest


@pytest.mark.asyncio
async def test_translator_providers_list(client):
    """GET /api/translator/providers returns provider list."""
    resp = await client.get("/api/translator/providers")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_translator_usage_stats(client):
    """GET /api/translator/usage returns usage statistics."""
    resp = await client.get("/api/translator/usage")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_translator_tm_list(client):
    """GET /api/translator/tm returns translation memory entries."""
    resp = await client.get("/api/translator/tm")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, (list, dict))


@pytest.mark.asyncio
async def test_translator_glossary_list(client):
    """GET /api/translator/glossary returns glossary terms."""
    resp = await client.get("/api/translator/glossary")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, (list, dict))


@pytest.mark.asyncio
async def test_translator_file_upload_no_file(client):
    """POST /api/translator/file without file returns 4xx."""
    resp = await client.post("/api/translator/file")
    assert resp.status_code in (400, 422)
