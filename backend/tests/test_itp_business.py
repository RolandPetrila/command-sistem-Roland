"""Business flow tests for ITP module — multi-step scenarios."""

import json

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _inspection_payload(**overrides):
    """Default inspection creation payload with optional overrides."""
    base = {
        "plate_number": "AR 01 TST",
        "brand": "Dacia",
        "model": "Logan",
        "year": 2020,
        "fuel_type": "benzina",
        "owner_name": "Test Owner",
        "inspection_date": "2026-03-23",
        "expiry_date": "2026-03-28",
        "result": "admis",
        "price": 150.0,
    }
    base.update(overrides)
    return base


def _appointment_payload(**overrides):
    """Default appointment creation payload with optional overrides."""
    base = {
        "plate_number": "AR 02 TST",
        "owner_name": "Test Owner",
        "owner_phone": "0747000000",
        "scheduled_date": "2026-03-25",
        "scheduled_time": "10:00",
        "duration_min": 30,
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# 1. Inspection -> Invoice flow
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_itp_inspection_to_invoice(client):
    """Create inspection -> generate invoice data -> verify invoice fields."""
    # Create inspection
    resp = await client.post("/api/itp/inspections", json=_inspection_payload())
    assert resp.status_code == 200
    inspection_id = resp.json()["id"]

    try:
        # Generate invoice data from inspection
        resp = await client.post(
            f"/api/itp/inspections/{inspection_id}/create-invoice"
        )
        assert resp.status_code == 200
        invoice = resp.json()

        # Verify invoice data matches inspection
        assert invoice["total"] == 150.0
        assert "items" in invoice
        assert len(invoice["items"]) >= 1
        assert invoice["items"][0]["price"] == 150.0
        assert "AR 01 TST" in invoice["items"][0]["description"]
        assert invoice["client_name"]  # non-empty
        assert invoice["source"] == "itp"
        assert invoice["linked_inspection_id"] == inspection_id
    finally:
        await client.delete(f"/api/itp/inspections/{inspection_id}")


# ---------------------------------------------------------------------------
# 2. Vehicle history
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_itp_vehicle_history(client):
    """Create 2 inspections for same plate -> verify history returns both."""
    plate = "AR 01 TST"
    ids = []

    # Create two inspections for the same plate on different dates
    for i, dt in enumerate(["2026-03-20", "2026-03-23"]):
        resp = await client.post(
            "/api/itp/inspections",
            json=_inspection_payload(
                inspection_date=dt,
                expiry_date="2028-03-23",
                price=150.0 + i * 10,
            ),
        )
        assert resp.status_code == 200, resp.text
        ids.append(resp.json()["id"])

    try:
        resp = await client.get(f"/api/itp/vehicle/{plate}/history")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 2
        assert data["plate_number"] == plate
        assert len(data["inspections"]) >= 2
    finally:
        for iid in ids:
            await client.delete(f"/api/itp/inspections/{iid}")


# ---------------------------------------------------------------------------
# 3. Rejection requires reasons
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_itp_rejection_requires_reasons(client):
    """'Respins' without rejection_reasons -> 422 validation error.
    'Respins' with rejection_reasons -> success."""
    # Missing rejection_reasons -> expect 422 (Pydantic validation)
    resp = await client.post(
        "/api/itp/inspections",
        json=_inspection_payload(result="Respins"),
    )
    assert resp.status_code == 422, (
        f"Expected 422 for rejected without reasons, got {resp.status_code}"
    )

    # With rejection_reasons -> success
    reasons = json.dumps(["Franare"])
    resp = await client.post(
        "/api/itp/inspections",
        json=_inspection_payload(
            result="Respins",
            rejection_reasons=reasons,
        ),
    )
    assert resp.status_code == 200, resp.text
    inspection_id = resp.json()["id"]

    # Cleanup
    await client.delete(f"/api/itp/inspections/{inspection_id}")


# ---------------------------------------------------------------------------
# 4. Appointment state machine
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_itp_appointment_state_machine(client):
    """Verify allowed transitions: scheduled -> confirmed -> checked_in -> completed.
    Then verify invalid transition (completed -> scheduled) fails."""
    # Create appointment (starts as 'scheduled')
    resp = await client.post(
        "/api/itp/appointments",
        json=_appointment_payload(),
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data.get("created") is True
    appt_id = data["id"]

    try:
        # scheduled -> confirmed
        resp = await client.put(
            f"/api/itp/appointments/{appt_id}",
            json={"status": "confirmed"},
        )
        assert resp.status_code == 200, resp.text

        # confirmed -> checked_in
        resp = await client.put(
            f"/api/itp/appointments/{appt_id}",
            json={"status": "checked_in"},
        )
        assert resp.status_code == 200, resp.text

        # checked_in -> completed
        resp = await client.put(
            f"/api/itp/appointments/{appt_id}",
            json={"status": "completed"},
        )
        assert resp.status_code == 200, resp.text

        # Invalid: completed -> scheduled (terminal state)
        resp = await client.put(
            f"/api/itp/appointments/{appt_id}",
            json={"status": "scheduled"},
        )
        assert resp.status_code == 400, (
            f"Expected 400 for invalid transition, got {resp.status_code}"
        )
    finally:
        await client.delete(f"/api/itp/appointments/{appt_id}")


# ---------------------------------------------------------------------------
# 5. Expiring alerts
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_itp_expiring_alerts(client):
    """Inspection expiring in 5 days should appear in /expiring?days=7."""
    from datetime import date, timedelta

    today = date.today()
    expiry = (today + timedelta(days=5)).isoformat()
    insp_date = today.isoformat()

    resp = await client.post(
        "/api/itp/inspections",
        json=_inspection_payload(
            inspection_date=insp_date,
            expiry_date=expiry,
        ),
    )
    assert resp.status_code == 200
    inspection_id = resp.json()["id"]

    try:
        resp = await client.get("/api/itp/expiring", params={"days": 7})
        assert resp.status_code == 200
        items = resp.json()
        assert isinstance(items, list)

        # Find our inspection in the expiring list
        found = any(
            item.get("id") == inspection_id for item in items
        )
        assert found, (
            f"Inspection {inspection_id} (expires {expiry}) not found in "
            f"expiring list (days=7). Got {len(items)} items."
        )
    finally:
        await client.delete(f"/api/itp/inspections/{inspection_id}")


# ---------------------------------------------------------------------------
# 6. Export CSV
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_itp_export_csv(client):
    """Export CSV should return 200 with CSV content-type (needs data)."""
    # Ensure at least one inspection exists for export
    resp = await client.post(
        "/api/itp/inspections",
        json=_inspection_payload(),
    )
    assert resp.status_code == 200
    inspection_id = resp.json()["id"]

    try:
        resp = await client.get("/api/itp/export/csv")
        assert resp.status_code == 200
        content_type = resp.headers.get("content-type", "")
        assert "csv" in content_type.lower(), (
            f"Expected CSV content-type, got: {content_type}"
        )
        # Body should contain header row with plate_number
        body = resp.text
        assert "plate_number" in body
    finally:
        await client.delete(f"/api/itp/inspections/{inspection_id}")


# ---------------------------------------------------------------------------
# 7. Stats endpoints
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_itp_stats(client):
    """Stats overview and monthly endpoints return valid JSON with expected keys."""
    # Overview
    resp = await client.get("/api/itp/stats/overview")
    assert resp.status_code == 200
    overview = resp.json()
    for key in ("total", "admis", "respins", "admis_rate", "avg_price", "this_month"):
        assert key in overview, f"Missing key '{key}' in stats/overview"

    # Monthly
    resp = await client.get("/api/itp/stats/monthly")
    assert resp.status_code == 200
    monthly = resp.json()
    assert "year" in monthly
    assert "data" in monthly
    assert isinstance(monthly["data"], list)
    assert len(monthly["data"]) == 12  # all 12 months
    # Each month entry should have expected keys
    first = monthly["data"][0]
    for key in ("month", "count", "admis", "respins", "name"):
        assert key in first, f"Missing key '{key}' in monthly data entry"
