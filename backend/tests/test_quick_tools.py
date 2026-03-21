"""Test quick_tools module endpoints."""

import pytest


@pytest.mark.asyncio
async def test_exchange_rate(client):
    """GET /api/quick-tools/exchange-rate returns BNR rates."""
    resp = await client.get("/api/quick-tools/exchange-rate")
    # May fail if no internet, but endpoint should exist
    assert resp.status_code in (200, 502)
    if resp.status_code == 200:
        data = resp.json()
        assert "rates" in data or "date" in data


@pytest.mark.asyncio
async def test_exchange_rate_convert(client):
    """GET /api/quick-tools/exchange-rate/convert converts currency."""
    resp = await client.get(
        "/api/quick-tools/exchange-rate/convert",
        params={"amount": 100, "from": "EUR", "to": "RON"},
    )
    assert resp.status_code in (200, 502)


@pytest.mark.asyncio
async def test_company_check_valid_cui(client):
    """GET /api/quick-tools/company-check/{cui} with valid CUI."""
    resp = await client.get("/api/quick-tools/company-check/43978110")
    assert resp.status_code in (200, 502)
    if resp.status_code == 200:
        data = resp.json()
        assert "found" in data
        assert "cui" in data


@pytest.mark.asyncio
async def test_company_check_invalid_cui(client):
    """GET /api/quick-tools/company-check with invalid CUI returns 400."""
    resp = await client.get("/api/quick-tools/company-check/abc")
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_number_to_words_integer(client):
    """Number to words with simple integer."""
    resp = await client.get("/api/quick-tools/number-to-words", params={"number": 42})
    assert resp.status_code == 200
    data = resp.json()
    assert "words" in data
