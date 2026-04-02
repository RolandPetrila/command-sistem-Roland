"""
Invoice Recurring sub-module:
  - Set invoice as recurring (monthly/quarterly/yearly)
  - List recurring invoices
  - Process (auto-clone) overdue recurring invoices

Endpoints are mounted on crud_router via include_router() in crud.py.
"""

from __future__ import annotations

import logging
from datetime import date

from fastapi import APIRouter, HTTPException

from app.core.activity_log import log_activity
from app.db.database import get_db

from .router import (
    RecurringSet,
    _next_invoice_number,
)

logger = logging.getLogger(__name__)

recurring_router = APIRouter()


# ═══════════════════════════════════════════
# Helper: ensure table + date calculation
# ═══════════════════════════════════════════

async def _ensure_recurring_table():
    """Create recurring_invoices table if it doesn't exist, with original_day column."""
    async with get_db() as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS recurring_invoices (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id  INTEGER NOT NULL REFERENCES invoices(id),
                frequency   TEXT DEFAULT 'monthly',
                next_due    TEXT,
                original_day INTEGER,
                enabled     INTEGER DEFAULT 1,
                created_at  TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Add original_day column if table already existed without it
        try:
            await db.execute(
                "ALTER TABLE recurring_invoices ADD COLUMN original_day INTEGER"
            )
        except Exception:
            pass  # Column already exists
        await db.commit()


def _calc_next_due(frequency: str, from_date: str | None = None, original_day: int | None = None) -> str:
    """Calculate next due date based on frequency from a given date.

    Uses original_day to preserve the day-of-month from when recurring was set up.
    E.g., Jan 31 -> Feb 28 -> Mar 31 (not Mar 28) because original_day=31.
    Falls back to min(original_day, days_in_target_month) for short months.
    """
    import calendar

    base = date.fromisoformat(from_date) if from_date else date.today()
    # Preserve the original day from the first invoice date
    if original_day is None:
        original_day = base.day

    if frequency == "monthly":
        month = base.month + 1
        year = base.year
        if month > 12:
            month = 1
            year += 1
        max_day = calendar.monthrange(year, month)[1]
        day = min(original_day, max_day)
        return date(year, month, day).isoformat()
    elif frequency == "quarterly":
        month = base.month + 3
        year = base.year
        while month > 12:
            month -= 12
            year += 1
        max_day = calendar.monthrange(year, month)[1]
        day = min(original_day, max_day)
        return date(year, month, day).isoformat()
    elif frequency == "yearly":
        year = base.year + 1
        max_day = calendar.monthrange(year, base.month)[1]
        day = min(original_day, max_day)
        return date(year, base.month, day).isoformat()
    else:
        # Default to monthly
        month = base.month + 1
        year = base.year
        if month > 12:
            month = 1
            year += 1
        max_day = calendar.monthrange(year, month)[1]
        day = min(original_day, max_day)
        return date(year, month, day).isoformat()


# ═══════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════

@recurring_router.post("/{invoice_id}/set-recurring")
async def set_recurring(invoice_id: int, data: RecurringSet):
    """Marcheaza o factura ca recurenta (lunar/trimestrial/anual)."""
    await _ensure_recurring_table()

    valid_frequencies = ("monthly", "quarterly", "yearly")
    if data.frequency not in valid_frequencies:
        raise HTTPException(400, f"Frecventa invalida. Optiuni: {', '.join(valid_frequencies)}")

    async with get_db() as db:
        cursor = await db.execute(
            "SELECT invoice_number, date FROM invoices WHERE id = ?", (invoice_id,)
        )
        inv_row = await cursor.fetchone()
        if not inv_row:
            raise HTTPException(404, "Factura negasita.")

        # Preserve the original day-of-month from the invoice date for correct clamping
        inv_date = date.fromisoformat(inv_row["date"]) if inv_row["date"] else date.today()
        original_day = inv_date.day

        next_due = data.next_due or _calc_next_due(data.frequency, inv_row["date"], original_day=original_day)

        # Check if already set as recurring
        cursor = await db.execute(
            "SELECT id, original_day FROM recurring_invoices WHERE invoice_id = ?", (invoice_id,)
        )
        existing = await cursor.fetchone()

        if existing:
            # Keep original_day from when it was first set, unless it was NULL
            stored_day = existing["original_day"] if existing["original_day"] else original_day
            await db.execute(
                "UPDATE recurring_invoices SET frequency = ?, next_due = ?, original_day = ?, enabled = 1 WHERE invoice_id = ?",
                (data.frequency, next_due, stored_day, invoice_id),
            )
        else:
            await db.execute(
                """INSERT INTO recurring_invoices (invoice_id, frequency, next_due, original_day, enabled)
                   VALUES (?, ?, ?, ?, 1)""",
                (invoice_id, data.frequency, next_due, original_day),
            )
        await db.commit()

    await log_activity(
        action="invoice.set_recurring",
        summary=f"Factura {inv_row['invoice_number']} setata ca recurenta ({data.frequency})",
        details={
            "invoice_id": invoice_id,
            "frequency": data.frequency,
            "next_due": next_due,
        },
    )
    return {
        "message": f"Factura {inv_row['invoice_number']} setata ca recurenta ({data.frequency}).",
        "next_due": next_due,
        "frequency": data.frequency,
    }


@recurring_router.get("/recurring/list")
async def list_recurring():
    """Lista toate facturile recurente cu datele urmatoarei scadente."""
    await _ensure_recurring_table()
    async with get_db() as db:
        cursor = await db.execute(
            """SELECT r.id as recurring_id, r.frequency, r.next_due, r.enabled,
                      r.original_day,
                      i.id as invoice_id, i.invoice_number, i.total, i.status,
                      i.date as invoice_date, i.client_id,
                      c.name as client_name
               FROM recurring_invoices r
               JOIN invoices i ON r.invoice_id = i.id
               LEFT JOIN clients c ON i.client_id = c.id
               ORDER BY r.next_due ASC"""
        )
        rows = await cursor.fetchall()

    result = []
    today_str = date.today().isoformat()
    for row in rows:
        d = dict(row)
        d["is_overdue"] = bool(d.get("next_due") and d["next_due"] < today_str and d["enabled"])
        result.append(d)
    return result


@recurring_router.post("/recurring/process")
async def process_recurring():
    """Auto-clone all overdue recurring invoices and advance their next_due date.

    For each enabled recurring entry whose next_due <= today:
    - Read the original invoice
    - Create a new invoice (cloned fields, today's date, new invoice number)
    - Advance next_due to the next period
    - Log the action
    Returns a list of newly created invoice numbers.
    """
    await _ensure_recurring_table()
    today = date.today()
    today_str = today.isoformat()
    created = []

    async with get_db() as db:
        cursor = await db.execute(
            """SELECT r.id as rec_id, r.frequency, r.next_due, r.original_day,
                      i.id as invoice_id, i.invoice_number, i.client_id,
                      i.items_json, i.subtotal, i.vat_percent, i.vat_amount,
                      i.total, i.notes, i.series, i.due_date
               FROM recurring_invoices r
               JOIN invoices i ON r.invoice_id = i.id
               WHERE r.enabled = 1 AND r.next_due <= ?
               ORDER BY r.next_due ASC""",
            (today_str,),
        )
        due_rows = [dict(r) for r in await cursor.fetchall()]

    for row in due_rows:
        # Generate new invoice number
        new_number = await _next_invoice_number(row["series"])

        async with get_db() as db:
            # Insert the cloned invoice
            cursor = await db.execute(
                """INSERT INTO invoices
                   (client_id, invoice_number, series, date, due_date,
                    items_json, subtotal, vat_percent, vat_amount, total,
                    currency, status, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'RON', 'draft', ?)""",
                (
                    row["client_id"],
                    new_number,
                    row["series"],
                    today_str,
                    row["due_date"],
                    row["items_json"],
                    row["subtotal"],
                    row["vat_percent"],
                    row["vat_amount"],
                    row["total"],
                    row["notes"],
                ),
            )
            new_invoice_id = cursor.lastrowid

            # Advance next_due to the next period (using existing next_due as base)
            next_due_new = _calc_next_due(
                row["frequency"],
                from_date=row["next_due"],
                original_day=row["original_day"],
            )

            await db.execute(
                "UPDATE recurring_invoices SET next_due = ? WHERE id = ?",
                (next_due_new, row["rec_id"]),
            )
            await db.commit()

        await log_activity(
            action="invoice.recurring_clone",
            summary=f"Factura recurenta generata: {new_number} (sursa: {row['invoice_number']})",
            details={
                "source_invoice_id": row["invoice_id"],
                "new_invoice_id": new_invoice_id,
                "new_invoice_number": new_number,
                "frequency": row["frequency"],
                "next_due_new": next_due_new,
            },
        )
        created.append({"invoice_number": new_number, "invoice_id": new_invoice_id, "next_due": next_due_new})

    return {
        "processed": len(created),
        "created": created,
        "message": f"{len(created)} factura/facturi recurente generate." if created else "Nicio factura scadenta.",
    }
