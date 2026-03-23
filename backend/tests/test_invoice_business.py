"""
Comprehensive pytest tests for invoice business flows.

Covers: full lifecycle, series management, duplicate detection,
pagination, CSV export, item presets, payment recording, overdue detection.
"""

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _create_client(client, name="Test Business Client SRL"):
    """Create a client and return its id."""
    resp = await client.post("/api/invoice/clients", json={
        "name": name,
        "cui": "RO99887766",
        "address": "Str. Testului 10, Cluj-Napoca",
        "email": "business@example.com",
        "phone": "0740000000",
    })
    assert resp.status_code == 201, f"Failed to create client: {resp.text}"
    return resp.json()["id"]


async def _create_invoice(client, client_id, *, series="TST",
                          inv_date="2026-03-23", due_date="2026-04-23",
                          description="Traducere EN-RO", unit_price=250.0,
                          notes="Test invoice"):
    """Create an invoice and return the full response dict."""
    resp = await client.post("/api/invoice/create", json={
        "client_id": client_id,
        "series_prefix": series,
        "date": inv_date,
        "due_date": due_date,
        "items": [{"description": description, "quantity": 1, "unit_price": unit_price}],
        "notes": notes,
    })
    assert resp.status_code == 201, f"Failed to create invoice: {resp.text}"
    return resp.json()


async def _delete_invoice(client, invoice_id):
    """Delete an invoice (must be in draft status)."""
    resp = await client.delete(f"/api/invoice/{invoice_id}")
    # 200 = deleted, 404 = already gone, 409 = not draft (acceptable in cleanup)
    assert resp.status_code in (200, 404, 409), f"Unexpected delete status: {resp.status_code}"


async def _delete_client(client, client_id):
    """Delete a client. Tolerates 404 (already deleted) and 409 (has invoices)."""
    resp = await client.delete(f"/api/invoice/clients/{client_id}")
    assert resp.status_code in (200, 404, 409), f"Unexpected client delete status: {resp.status_code}"


# ---------------------------------------------------------------------------
# 1. Full invoice lifecycle
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_invoice_full_lifecycle(client):
    """Create client -> Create invoice -> Read -> Generate PDF -> Delete invoice -> Delete client."""
    # --- Create client ---
    client_id = await _create_client(client)

    # --- Create invoice ---
    inv = await _create_invoice(client, client_id)
    invoice_id = inv["id"]
    assert "invoice_number" in inv, "Response must contain invoice_number"
    assert inv["total"] == 250.0, f"Expected total 250.0, got {inv['total']}"

    # --- Read invoice ---
    resp = await client.get(f"/api/invoice/{invoice_id}")
    assert resp.status_code == 200, f"Failed to read invoice: {resp.text}"
    data = resp.json()
    assert data["client_name"] == "Test Business Client SRL"
    assert data["notes"] == "Test invoice"
    assert len(data["items"]) == 1
    assert data["items"][0]["description"] == "Traducere EN-RO"

    # --- Generate PDF ---
    resp = await client.post(f"/api/invoice/{invoice_id}/pdf")
    assert resp.status_code == 200, f"PDF generation failed: {resp.text}"
    content_type = resp.headers.get("content-type", "")
    assert "pdf" in content_type, f"Expected PDF content-type, got: {content_type}"
    assert len(resp.content) > 100, "PDF content too small — likely empty or error"

    # --- Cleanup ---
    await _delete_invoice(client, invoice_id)
    await _delete_client(client, client_id)

    # Verify invoice is gone
    resp = await client.get(f"/api/invoice/{invoice_id}")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# 2. Invoice series management
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_invoice_series_management(client):
    """Create series -> List series -> Verify in list -> Delete series."""
    # --- Create series ---
    resp = await client.post("/api/invoice/series", json={
        "prefix": "XTEST",
        "name": "Test Series",
        "description": "Test series for pytest",
    })
    assert resp.status_code == 201, f"Failed to create series: {resp.text}"
    series_id = resp.json()["id"]

    # --- List series and verify ---
    resp = await client.get("/api/invoice/series")
    assert resp.status_code == 200
    series_list = resp.json()
    assert isinstance(series_list, list), "Expected list of series"
    prefixes = [s["prefix"] for s in series_list]
    assert "XTEST" in prefixes, f"XTEST not found in series list: {prefixes}"

    # --- Delete series ---
    resp = await client.delete(f"/api/invoice/series/{series_id}")
    assert resp.status_code == 200, f"Failed to delete series: {resp.text}"

    # Verify deleted
    resp = await client.get("/api/invoice/series")
    prefixes_after = [s["prefix"] for s in resp.json()]
    assert "XTEST" not in prefixes_after, "Series XTEST should have been deleted"


# ---------------------------------------------------------------------------
# 3. Duplicate detection
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_invoice_duplicate_detection(client):
    """Create client -> Create invoice -> Create SAME invoice -> Expect warning."""
    client_id = await _create_client(client, name="Dup Detect Client SRL")
    invoice_ids = []

    try:
        # First invoice
        inv1 = await _create_invoice(client, client_id, inv_date="2026-03-23")
        invoice_ids.append(inv1["id"])
        # First invoice should NOT have a warning
        assert "warning" not in inv1 or inv1.get("warning") is None, \
            "First invoice should not have a duplicate warning"

        # Second invoice — same client, same date
        inv2 = await _create_invoice(client, client_id, inv_date="2026-03-23")
        invoice_ids.append(inv2["id"])
        # Second invoice SHOULD have a duplicate warning
        assert "warning" in inv2, "Second invoice should contain duplicate warning"
        assert inv2["warning"] is not None, "Duplicate warning should not be None"
        assert "duplicate_id" in inv2, "Response should contain duplicate_id"
        assert inv2["duplicate_id"] == inv1["id"], \
            f"duplicate_id should reference first invoice ({inv1['id']}), got {inv2['duplicate_id']}"

    finally:
        # Cleanup
        for iid in reversed(invoice_ids):
            await _delete_invoice(client, iid)
        await _delete_client(client, client_id)


# ---------------------------------------------------------------------------
# 4. Pagination
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_invoice_pagination(client):
    """Create client + 3 invoices -> Verify pagination with per_page=2."""
    client_id = await _create_client(client, name="Pagination Client SRL")
    invoice_ids = []

    try:
        # Create 3 invoices with different dates to ensure stable ordering
        for i in range(3):
            inv = await _create_invoice(
                client, client_id,
                inv_date=f"2026-03-{20 + i:02d}",
                description=f"Traducere pagina {i + 1}",
                unit_price=100.0 * (i + 1),
            )
            invoice_ids.append(inv["id"])

        # Page 1 with per_page=2
        resp = await client.get("/api/invoice/list", params={"page": 1, "per_page": 2})
        assert resp.status_code == 200, f"Pagination request failed: {resp.text}"
        data = resp.json()
        assert "items" in data, "Response must contain 'items' key"
        assert "total" in data, "Response must contain 'total' key"
        assert "page" in data, "Response must contain 'page' key"
        assert "pages" in data, "Response must contain 'pages' key"
        assert len(data["items"]) <= 2, f"Expected max 2 items, got {len(data['items'])}"
        assert data["total"] >= 3, f"Expected total >= 3, got {data['total']}"
        assert data["pages"] >= 2, f"Expected pages >= 2 (has_more), got {data['pages']}"

    finally:
        for iid in reversed(invoice_ids):
            await _delete_invoice(client, iid)
        await _delete_client(client, client_id)


# ---------------------------------------------------------------------------
# 5. CSV export
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_invoice_csv_export(client):
    """GET /api/invoice/export/csv -> 200 + text/csv content-type."""
    resp = await client.get("/api/invoice/export/csv")
    assert resp.status_code == 200, f"CSV export failed: {resp.text}"
    content_type = resp.headers.get("content-type", "")
    assert "csv" in content_type, f"Expected CSV content-type, got: {content_type}"
    # The CSV should contain at least a header row (BOM + headers)
    assert len(resp.content) > 10, "CSV content too small — may be empty"


# ---------------------------------------------------------------------------
# 6. Item presets
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_invoice_item_presets(client):
    """Create preset -> List presets -> Verify in list -> Delete preset."""
    # --- Create preset ---
    resp = await client.post("/api/invoice/items/presets", json={
        "description": "Traducere tehnica EN-RO",
        "unit_price": 0.08,
        "unit": "cuvant",
        "category": "traduceri",
    })
    assert resp.status_code == 201, f"Failed to create preset: {resp.text}"
    preset_id = resp.json()["id"]

    # --- List presets and verify ---
    resp = await client.get("/api/invoice/items/presets")
    assert resp.status_code == 200
    presets = resp.json()
    assert isinstance(presets, list), "Expected list of presets"
    found = [p for p in presets if p["id"] == preset_id]
    assert len(found) == 1, f"Preset {preset_id} not found in list"
    assert found[0]["description"] == "Traducere tehnica EN-RO"
    assert found[0]["unit_price"] == 0.08
    assert found[0]["category"] == "traduceri"

    # --- Delete preset ---
    resp = await client.delete(f"/api/invoice/items/presets/{preset_id}")
    assert resp.status_code == 200, f"Failed to delete preset: {resp.text}"

    # Verify deleted
    resp = await client.get("/api/invoice/items/presets")
    remaining_ids = [p["id"] for p in resp.json()]
    assert preset_id not in remaining_ids, "Preset should have been deleted"


# ---------------------------------------------------------------------------
# 7. Payment recording
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_invoice_payment_recording(client):
    """Create invoice -> Record partial payment -> List payments -> Verify."""
    client_id = await _create_client(client, name="Payment Client SRL")
    inv = await _create_invoice(client, client_id, unit_price=500.0)
    invoice_id = inv["id"]

    try:
        # --- Record partial payment ---
        resp = await client.post(f"/api/invoice/{invoice_id}/payments", json={
            "amount": 200.0,
            "payment_date": "2026-03-23",
            "method": "transfer",
            "notes": "Prima rata",
        })
        assert resp.status_code == 200, f"Payment recording failed: {resp.text}"
        pay_data = resp.json()
        assert "payment_id" in pay_data, "Response must contain payment_id"
        assert pay_data["total_paid"] == 200.0, f"Expected total_paid 200.0, got {pay_data['total_paid']}"
        assert pay_data["remaining"] == 300.0, f"Expected remaining 300.0, got {pay_data['remaining']}"
        assert pay_data["fully_paid"] is False, "Should not be fully paid yet"

        # --- List payments ---
        resp = await client.get(f"/api/invoice/{invoice_id}/payments")
        assert resp.status_code == 200, f"List payments failed: {resp.text}"
        payments_data = resp.json()
        assert "payments" in payments_data, "Response must contain 'payments' key"
        assert len(payments_data["payments"]) == 1, \
            f"Expected 1 payment, got {len(payments_data['payments'])}"
        assert payments_data["total_paid"] == 200.0
        assert payments_data["remaining"] == 300.0
        assert payments_data["invoice_total"] == 500.0
        assert payments_data["fully_paid"] is False

        # --- Record remaining payment ---
        resp = await client.post(f"/api/invoice/{invoice_id}/payments", json={
            "amount": 300.0,
            "payment_date": "2026-03-24",
            "method": "cash",
        })
        assert resp.status_code == 200
        pay_data2 = resp.json()
        assert pay_data2["fully_paid"] is True, "Should be fully paid now"
        assert pay_data2["remaining"] <= 0.01, f"Remaining should be ~0, got {pay_data2['remaining']}"

    finally:
        # Invoice may now be 'paid' (auto-status on full payment),
        # so delete may return 409 — that is acceptable in cleanup.
        await _delete_invoice(client, invoice_id)
        await _delete_client(client, client_id)


# ---------------------------------------------------------------------------
# 8. Overdue detection
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_invoice_overdue_detection(client):
    """Create invoice with past due_date -> GET /overdue -> Verify overdue."""
    client_id = await _create_client(client, name="Overdue Client SRL")
    inv = await _create_invoice(
        client, client_id,
        inv_date="2025-01-01",
        due_date="2025-01-15",
        description="Traducere restanta",
        unit_price=150.0,
    )
    invoice_id = inv["id"]

    try:
        # --- Check overdue list ---
        resp = await client.get("/api/invoice/overdue")
        assert resp.status_code == 200, f"Overdue list failed: {resp.text}"
        overdue_list = resp.json()
        assert isinstance(overdue_list, list), "Expected list of overdue invoices"

        # Find our invoice in the overdue list
        our_overdue = [o for o in overdue_list if o["id"] == invoice_id]
        assert len(our_overdue) == 1, \
            f"Invoice {invoice_id} with past due_date should appear in overdue list"
        assert our_overdue[0]["days_overdue"] > 0, \
            f"days_overdue should be positive, got {our_overdue[0]['days_overdue']}"

    finally:
        await _delete_invoice(client, invoice_id)
        await _delete_client(client, client_id)
