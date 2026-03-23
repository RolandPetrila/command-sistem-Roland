"""Business flow tests for Calculator and Reports modules."""

import pytest


# ---------------------------------------------------------------------------
# 1. Quick Quote
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_quick_quote(client):
    """POST /api/calculator/quick-quote returns price > 0 with method details."""
    resp = await client.post("/api/calculator/quick-quote", json={
        "word_count": 1500,
        "source_lang": "en",
        "target_lang": "ro",
        "document_type": "technical",
    })
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["market_price"] > 0
    assert data["market_price_with_lang"] > 0
    assert data["word_count"] == 1500
    assert data["document_type"] == "technical"
    assert "method_prices" in data
    assert "weights_used" in data
    assert "language_info" in data
    assert data["currency"] == "RON"


# ---------------------------------------------------------------------------
# 2. Language Coefficients
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_quick_quote_language_coefficients(client):
    """GET /api/calculator/language-coefficients returns expected languages."""
    resp = await client.get("/api/calculator/language-coefficients")
    assert resp.status_code == 200
    data = resp.json()

    assert "coefficients" in data
    assert "total_languages" in data
    assert data["total_languages"] > 0

    # Build lookup by language code
    coefs = {c["code"]: c["coefficient"] for c in data["coefficients"]}

    # Verify key languages are present
    for lang in ("de", "fr", "en"):
        assert lang in coefs, f"Missing language '{lang}' in coefficients"

    # German should have a higher coefficient than English (base = 1.0)
    assert coefs["de"] > coefs["en"], (
        f"Expected de ({coefs['de']}) > en ({coefs['en']})"
    )


# ---------------------------------------------------------------------------
# 3. Templates CRUD
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_calculator_templates_crud(client):
    """Create template -> verify in list -> delete -> verify gone."""
    # Create
    resp = await client.post("/api/calculator/templates", json={
        "name": "Test Template Biz",
        "word_count": 2000,
        "document_type": "legal",
        "complexity": "high",
        "source_lang": "en",
        "target_lang": "ro",
        "price": 250.0,
        "notes": "test template for business flow",
    })
    assert resp.status_code == 201, resp.text
    template = resp.json()
    template_id = template["id"]
    assert template["name"] == "Test Template Biz"
    assert template["word_count"] == 2000
    assert template["price"] == 250.0

    try:
        # List and verify template is present
        resp = await client.get("/api/calculator/templates")
        assert resp.status_code == 200
        data = resp.json()
        assert "templates" in data
        found = any(t["id"] == template_id for t in data["templates"])
        assert found, f"Template {template_id} not found in list"
    finally:
        # Delete
        resp = await client.delete(f"/api/calculator/templates/{template_id}")
        assert resp.status_code == 200
        assert resp.json().get("deleted_id") == template_id


# ---------------------------------------------------------------------------
# 4. Backup endpoint
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_backup_endpoint(client):
    """POST /api/reports/backup creates a backup with integrity check."""
    resp = await client.post("/api/reports/backup")
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert "filename" in data
    assert data["filename"].startswith("backup_")
    assert data["size_bytes"] > 0
    assert data["integrity_ok"] is True
    assert "timestamp" in data


# ---------------------------------------------------------------------------
# 5. DB Integrity
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_db_integrity(client):
    """GET /api/reports/db-integrity returns ok with table count."""
    resp = await client.get("/api/reports/db-integrity")
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["ok"] is True
    assert data["tables_count"] > 0
    assert "db_size_bytes" in data
    assert data["db_size_bytes"] > 0
    assert "db_size_human" in data


# ---------------------------------------------------------------------------
# 6. My Day endpoint
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_my_day_endpoint(client):
    """GET /api/reports/dashboard/my-day returns daily summary with all sections."""
    resp = await client.get("/api/reports/dashboard/my-day")
    assert resp.status_code == 200, resp.text
    data = resp.json()

    # Greeting
    assert "greeting" in data
    assert isinstance(data["greeting"], str)
    assert len(data["greeting"]) > 0

    # Date
    assert "date" in data

    # ITP section
    assert "itp" in data
    itp = data["itp"]
    assert "appointments_today" in itp
    assert "expiring_7_days" in itp
    assert "overdue_count" in itp

    # Invoices section
    assert "invoices" in data
    invoices = data["invoices"]
    assert "overdue" in invoices
    assert "due_this_week" in invoices
    assert "total_receivable" in invoices

    # Quick stats section
    assert "quick_stats" in data
    qs = data["quick_stats"]
    for key in ("invoices_this_month", "revenue_this_month",
                "translations_this_month", "itp_this_month"):
        assert key in qs, f"Missing key '{key}' in quick_stats"
