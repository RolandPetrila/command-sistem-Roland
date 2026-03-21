"""Test AI document operations."""

import pytest


@pytest.mark.asyncio
async def test_ai_providers_list(client):
    """GET /api/ai/providers returns provider list."""
    resp = await client.get("/api/ai/providers")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_ai_config_keys(client):
    """GET /api/ai/config returns config keys (no values exposed)."""
    resp = await client.get("/api/ai/config")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, (list, dict))


@pytest.mark.asyncio
async def test_ai_summarize_no_file(client):
    """POST /api/ai/summarize without file returns 4xx."""
    resp = await client.post("/api/ai/summarize")
    assert resp.status_code in (400, 422)


@pytest.mark.asyncio
async def test_ai_classify_no_file(client):
    """POST /api/ai/classify without file returns 4xx."""
    resp = await client.post("/api/ai/classify")
    assert resp.status_code in (400, 422)


@pytest.mark.asyncio
async def test_ai_token_usage(client):
    """GET /api/ai/token-usage returns usage data."""
    resp = await client.get("/api/ai/token-usage")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, (list, dict))


@pytest.mark.asyncio
async def test_ai_context_data(client):
    """GET /api/ai/context-data returns DB stats for context-aware chat."""
    resp = await client.get("/api/ai/context-data")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
