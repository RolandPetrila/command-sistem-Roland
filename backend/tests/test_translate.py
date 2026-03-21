"""Test translation endpoints."""

import pytest


@pytest.mark.asyncio
async def test_translate_en_ro(client):
    """POST /api/translator/text translates English to Romanian."""
    resp = await client.post("/api/translator/text", json={
        "text": "Hello world",
        "source_lang": "en",
        "target_lang": "ro",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "translated_text" in data
    assert len(data["translated_text"]) > 0
    assert data["source_lang"] == "en"
    assert data["target_lang"] == "ro"
    assert data["provider"] in ("deepl", "azure", "google", "gemini", "openai", "tm")


@pytest.mark.asyncio
async def test_translate_empty_text_rejected(client):
    """Empty text should return 400."""
    resp = await client.post("/api/translator/text", json={
        "text": "   ",
        "source_lang": "en",
        "target_lang": "ro",
    })
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_detect_language(client):
    """POST /api/translator/detect detects English text."""
    resp = await client.post("/api/translator/detect", json={
        "text": "This is a simple English sentence for language detection.",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["language"] == "en"
    assert data["confidence"] > 0.5


@pytest.mark.asyncio
async def test_providers_list(client):
    """GET /api/translator/providers returns available providers."""
    resp = await client.get("/api/translator/providers")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    names = [p["name"] for p in data]
    assert "google" in names  # always available (no key needed)
