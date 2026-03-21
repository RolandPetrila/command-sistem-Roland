"""Test AI module endpoints."""

import pytest


@pytest.mark.asyncio
async def test_ai_providers_list(client):
    """GET /api/ai/providers returns available AI providers."""
    resp = await client.get("/api/ai/providers")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    # Each provider should have name and available fields
    for p in data:
        assert "name" in p
        assert "configured" in p


@pytest.mark.asyncio
async def test_ai_config_list(client):
    """GET /api/ai/config returns config keys (no values exposed)."""
    resp = await client.get("/api/ai/config")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_ai_chat_sessions_list(client):
    """GET /api/ai/chat/sessions returns list (may be empty)."""
    resp = await client.get("/api/ai/chat/sessions")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_ai_chat_create_session(client):
    """POST /api/ai/chat/sessions creates a new session."""
    resp = await client.post("/api/ai/chat/sessions", json={
        "title": "Test Session",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "id" in data
    session_id = data["id"]

    # Verify session exists
    resp2 = await client.get(f"/api/ai/chat/sessions/{session_id}")
    assert resp2.status_code == 200

    # Cleanup: delete session
    await client.delete(f"/api/ai/chat/sessions/{session_id}")
