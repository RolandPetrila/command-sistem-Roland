"""
Invoice Payments sub-module:
  - Add partial payment to an invoice
  - List payments for an invoice with summary

Endpoints are mounted on crud_router via include_router() in crud.py.
"""

from __future__ import annotations

import logging
from datetime import date

from fastapi import APIRouter, HTTPException

from app.core.activity_log import log_activity
from app.db.database import get_db

from .router import PartialPayment

logger = logging.getLogger(__name__)

payments_router = APIRouter()


# ═══════════════════════════════════════════
# Helper: ensure table
# ═══════════════════════════════════════════

async def _ensure_payments_table():
    """Create invoice_payments table if it doesn't exist."""
    async with get_db() as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS invoice_payments (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id    INTEGER NOT NULL REFERENCES invoices(id),
                amount        REAL NOT NULL,
                payment_date  TEXT NOT NULL,
                method        TEXT DEFAULT 'transfer',
                notes         TEXT,
                created_at    TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()


# ═══════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════

@payments_router.post("/{invoice_id}/payments")
async def add_partial_payment(invoice_id: int, data: PartialPayment):
    """Inregistrare plata partiala pentru o factura."""
    await _ensure_payments_table()

    if data.amount <= 0:
        raise HTTPException(400, "Suma platii trebuie sa fie pozitiva.")

    valid_methods = ("transfer", "cash", "card")
    if data.method not in valid_methods:
        raise HTTPException(400, f"Metoda de plata invalida. Optiuni: {', '.join(valid_methods)}")

    async with get_db() as db:
        cursor = await db.execute(
            "SELECT invoice_number, total, status FROM invoices WHERE id = ?", (invoice_id,)
        )
        inv_row = await cursor.fetchone()
        if not inv_row:
            raise HTTPException(404, "Factura negasita.")

        if inv_row["status"] == "cancelled":
            raise HTTPException(409, "Nu se pot inregistra plati pentru o factura anulata.")

        # Calculate already paid amount
        cursor = await db.execute(
            "SELECT COALESCE(SUM(amount), 0) as paid FROM invoice_payments WHERE invoice_id = ?",
            (invoice_id,),
        )
        paid_row = await cursor.fetchone()
        already_paid = paid_row["paid"]
        remaining = round(inv_row["total"] - already_paid, 2)

        if data.amount > remaining + 0.01:  # small tolerance for rounding
            raise HTTPException(
                400,
                f"Suma depaseste restul de plata. Total factura: {inv_row['total']:.2f} RON, "
                f"deja platit: {already_paid:.2f} RON, rest: {remaining:.2f} RON.",
            )

        cursor = await db.execute(
            """INSERT INTO invoice_payments (invoice_id, amount, payment_date, method, notes)
               VALUES (?, ?, ?, ?, ?)""",
            (invoice_id, data.amount, data.payment_date, data.method, data.notes),
        )
        payment_id = cursor.lastrowid

        new_paid = round(already_paid + data.amount, 2)
        new_remaining = round(inv_row["total"] - new_paid, 2)

        # Auto-mark as paid if fully paid
        if new_remaining <= 0.01:
            await db.execute(
                "UPDATE invoices SET status = 'paid', payment_date = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (data.payment_date, invoice_id),
            )

        await db.commit()

    await log_activity(
        action="invoice.partial_payment",
        summary=f"Plata {data.amount:.2f} RON inregistrata pentru {inv_row['invoice_number']}",
        details={
            "invoice_id": invoice_id,
            "payment_id": payment_id,
            "amount": data.amount,
            "method": data.method,
            "total_paid": new_paid,
            "remaining": new_remaining,
        },
    )
    return {
        "payment_id": payment_id,
        "message": f"Plata de {data.amount:.2f} RON inregistrata cu succes.",
        "total_paid": new_paid,
        "remaining": new_remaining,
        "fully_paid": new_remaining <= 0.01,
    }


@payments_router.get("/{invoice_id}/payments")
async def list_payments(invoice_id: int):
    """Lista toate platile pentru o factura cu sumar."""
    await _ensure_payments_table()

    async with get_db() as db:
        cursor = await db.execute(
            "SELECT invoice_number, total, status FROM invoices WHERE id = ?", (invoice_id,)
        )
        inv_row = await cursor.fetchone()
        if not inv_row:
            raise HTTPException(404, "Factura negasita.")

        cursor = await db.execute(
            "SELECT * FROM invoice_payments WHERE invoice_id = ? ORDER BY payment_date ASC, id ASC",
            (invoice_id,),
        )
        payments = await cursor.fetchall()

    total_paid = sum(p["amount"] for p in payments)
    remaining = round(inv_row["total"] - total_paid, 2)

    return {
        "invoice_number": inv_row["invoice_number"],
        "invoice_total": inv_row["total"],
        "total_paid": round(total_paid, 2),
        "remaining": max(remaining, 0),
        "fully_paid": remaining <= 0.01,
        "payments": [dict(p) for p in payments],
    }
