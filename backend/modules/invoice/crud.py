"""
Invoice CRUD sub-router:
  - Client CRUD + history
  - Invoice list/create/get/update/delete
  - Invoice status/payment
  - Invoice series CRUD
  - Overdue invoices
  - ANAF CUI verification
  - Send invoice by email
"""

from __future__ import annotations

import json
import logging
import smtplib
from datetime import date, timedelta
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import httpx
from fastapi import APIRouter, HTTPException

from app.core.activity_log import log_activity
from app.db.database import get_db

from .router import (
    ClientCreate,
    ClientUpdate,
    FromCalculationRequest,
    InvoiceCreate,
    InvoiceItem,
    InvoiceSeriesCreate,
    InvoiceSeriesUpdate,
    InvoiceUpdate,
    ItemPresetCreate,
    PartialPayment,
    RecurringSet,
    SendEmailRequest,
    StatusUpdate,
    INVOICES_DIR,
    _build_invoice_pdf,
    _calculate_totals,
    _items_from_json,
    _items_to_json,
    _next_invoice_number,
    _row_to_dict,
)

logger = logging.getLogger(__name__)

crud_router = APIRouter(prefix="/api/invoice", tags=["Invoice CRUD"])


# ═══════════════════════════════════════════
# Client endpoints
# ═══════════════════════════════════════════

@crud_router.get("/clients")
async def list_clients():
    """Lista toti clientii."""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM clients ORDER BY name ASC"
        )
        rows = await cursor.fetchall()
    return [dict(row) for row in rows]


@crud_router.post("/clients", status_code=201)
async def create_client(data: ClientCreate):
    """Creare client nou."""
    async with get_db() as db:
        cursor = await db.execute(
            """INSERT INTO clients (name, cui, reg_com, address, email, phone, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (data.name, data.cui, data.reg_com, data.address, data.email, data.phone, data.notes),
        )
        await db.commit()
        client_id = cursor.lastrowid

    await log_activity(
        action="invoice.client_create",
        summary=f"Client creat: {data.name}",
        details={"client_id": client_id, "name": data.name},
    )
    return {"id": client_id, "message": f"Client '{data.name}' creat cu succes."}


@crud_router.get("/clients/{client_id}")
async def get_client(client_id: int):
    """Detalii client dupa ID."""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM clients WHERE id = ?", (client_id,)
        )
        row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Client negasit.")
    return dict(row)


@crud_router.put("/clients/{client_id}")
async def update_client(client_id: int, data: ClientUpdate):
    """Actualizare client existent."""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM clients WHERE id = ?", (client_id,)
        )
        existing = await cursor.fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Client negasit.")

        updates = data.model_dump(exclude_unset=True)
        if not updates:
            raise HTTPException(status_code=400, detail="Niciun camp de actualizat.")

        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values())
        values.append(client_id)

        await db.execute(
            f"UPDATE clients SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            values,
        )
        await db.commit()

    await log_activity(
        action="invoice.client_update",
        summary=f"Client actualizat: ID {client_id}",
        details={"client_id": client_id, "fields": list(updates.keys())},
    )
    return {"message": "Client actualizat cu succes."}


@crud_router.delete("/clients/{client_id}")
async def delete_client(client_id: int):
    """Stergere client (doar daca nu are facturi)."""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT COUNT(*) as cnt FROM invoices WHERE client_id = ?", (client_id,)
        )
        row = await cursor.fetchone()
        if row and row["cnt"] > 0:
            raise HTTPException(
                status_code=409,
                detail=f"Clientul are {row['cnt']} facturi asociate. Sterge facturile intai.",
            )

        cursor = await db.execute(
            "SELECT name FROM clients WHERE id = ?", (client_id,)
        )
        client_row = await cursor.fetchone()
        if not client_row:
            raise HTTPException(status_code=404, detail="Client negasit.")
        client_name = client_row["name"]

        await db.execute("DELETE FROM clients WHERE id = ?", (client_id,))
        await db.commit()

    await log_activity(
        action="invoice.client_delete",
        summary=f"Client sters: {client_name}",
        details={"client_id": client_id},
    )
    return {"message": f"Client '{client_name}' sters cu succes."}


@crud_router.get("/clients/{client_id}/history")
async def client_history(client_id: int):
    """Returneaza toate facturile unui client cu sumar totaluri."""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM clients WHERE id = ?", (client_id,)
        )
        client = await cursor.fetchone()
        if not client:
            raise HTTPException(status_code=404, detail="Client negasit.")

        cursor = await db.execute(
            """SELECT i.*, c.name as client_name
               FROM invoices i
               LEFT JOIN clients c ON i.client_id = c.id
               WHERE i.client_id = ?
               ORDER BY i.date DESC, i.id DESC""",
            (client_id,),
        )
        rows = await cursor.fetchall()
        invoices = [_row_to_dict(row) for row in rows]

        cursor = await db.execute(
            """SELECT
                 COUNT(*) as total_facturi,
                 COALESCE(SUM(total), 0) as total_valoare,
                 COALESCE(AVG(total), 0) as medie_factura,
                 COUNT(CASE WHEN status = 'paid' THEN 1 END) as facturi_platite,
                 COUNT(CASE WHEN status = 'draft' THEN 1 END) as facturi_draft,
                 COUNT(CASE WHEN status = 'sent' THEN 1 END) as facturi_trimise,
                 COUNT(CASE WHEN status = 'cancelled' THEN 1 END) as facturi_anulate,
                 COALESCE(SUM(CASE WHEN status = 'paid' THEN total ELSE 0 END), 0) as total_incasat
               FROM invoices
               WHERE client_id = ?""",
            (client_id,),
        )
        summary_row = await cursor.fetchone()

    summary = {
        "total_facturi": summary_row["total_facturi"],
        "total_valoare": round(summary_row["total_valoare"], 2),
        "medie_factura": round(summary_row["medie_factura"], 2),
        "facturi_platite": summary_row["facturi_platite"],
        "facturi_draft": summary_row["facturi_draft"],
        "facturi_trimise": summary_row["facturi_trimise"],
        "facturi_anulate": summary_row["facturi_anulate"],
        "total_incasat": round(summary_row["total_incasat"], 2),
    }

    return {
        "client": dict(client),
        "invoices": invoices,
        "summary": summary,
    }


# ═══════════════════════════════════════════
# Invoice series CRUD
# ═══════════════════════════════════════════

@crud_router.get("/series")
async def list_series():
    """Lista toate seriile de facturi."""
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM invoice_series ORDER BY is_default DESC, name ASC")
        rows = await cursor.fetchall()
    return [dict(r) for r in rows]


@crud_router.post("/series", status_code=201)
async def create_series(data: InvoiceSeriesCreate):
    """Creare serie noua de facturi."""
    async with get_db() as db:
        cursor = await db.execute(
            "INSERT INTO invoice_series (prefix, name, description) VALUES (?, ?, ?)",
            (data.prefix.upper().strip(), data.name, data.description),
        )
        await db.commit()
        series_id = cursor.lastrowid
    await log_activity(
        action="invoice.series_create",
        summary=f"Serie facturi creata: {data.prefix} — {data.name}",
    )
    return {"id": series_id, "message": f"Serie '{data.prefix}' creata cu succes."}


@crud_router.put("/series/{series_id}")
async def update_series(series_id: int, data: InvoiceSeriesUpdate):
    """Actualizare serie facturi."""
    updates = data.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(400, "Niciun camp de actualizat")
    if "active" in updates:
        updates["active"] = 1 if updates["active"] else 0
    fields = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [series_id]
    async with get_db() as db:
        cursor = await db.execute(
            f"UPDATE invoice_series SET {fields} WHERE id = ?", values
        )
        await db.commit()
        if cursor.rowcount == 0:
            raise HTTPException(404, "Serie negasita")
    return {"message": "Serie actualizata cu succes."}


@crud_router.put("/series/{series_id}/default")
async def set_default_series(series_id: int):
    """Seteaza o serie ca implicita."""
    async with get_db() as db:
        await db.execute("UPDATE invoice_series SET is_default = 0")
        cursor = await db.execute(
            "UPDATE invoice_series SET is_default = 1 WHERE id = ?", (series_id,)
        )
        await db.commit()
        if cursor.rowcount == 0:
            raise HTTPException(404, "Serie negasita")
    return {"message": "Serie setata ca implicita."}


@crud_router.delete("/series/{series_id}")
async def delete_series(series_id: int):
    """Sterge o serie (doar daca nu e implicita si nu are facturi)."""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT is_default, prefix FROM invoice_series WHERE id = ?", (series_id,)
        )
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(404, "Serie negasita")
        if row["is_default"]:
            raise HTTPException(409, "Nu se poate sterge seria implicita")
        cursor = await db.execute(
            "SELECT COUNT(*) as cnt FROM invoices WHERE series = ?", (row["prefix"],)
        )
        cnt_row = await cursor.fetchone()
        if cnt_row and cnt_row["cnt"] > 0:
            raise HTTPException(409, f"Seria are {cnt_row['cnt']} facturi asociate")
        await db.execute("DELETE FROM invoice_series WHERE id = ?", (series_id,))
        await db.commit()
    return {"message": "Serie stearsa cu succes."}


# ═══════════════════════════════════════════
# Overdue invoices
# ═══════════════════════════════════════════

@crud_router.get("/overdue")
async def list_overdue():
    """Lista facturi cu scadenta depasita (neplatite)."""
    today = date.today().isoformat()
    async with get_db() as db:
        cursor = await db.execute(
            """SELECT i.*, c.name as client_name, c.email as client_email, c.phone as client_phone
               FROM invoices i
               LEFT JOIN clients c ON i.client_id = c.id
               WHERE i.due_date IS NOT NULL AND i.due_date < ? AND i.status NOT IN ('paid', 'cancelled')
               ORDER BY i.due_date ASC""",
            (today,),
        )
        rows = await cursor.fetchall()
    result = []
    today_d = date.today()
    for row in rows:
        d = _row_to_dict(row)
        try:
            due = date.fromisoformat(d["due_date"])
            d["days_overdue"] = (today_d - due).days
        except (ValueError, TypeError):
            d["days_overdue"] = 0
        result.append(d)
    return result


# ═══════════════════════════════════════════
# Invoice list / create
# ═══════════════════════════════════════════

@crud_router.get("/list")
async def list_invoices(
    page: int = 1,
    per_page: int = 50,
):
    """Lista facturile cu numele clientului (paginat).

    Args:
        page: Numarul paginii (default 1, minim 1).
        per_page: Facturi per pagina (default 50, max 200).
    """
    from fastapi import Query as _Q  # noqa: local import to avoid top-level conflict

    if page < 1:
        page = 1
    if per_page < 1:
        per_page = 50
    if per_page > 200:
        per_page = 200
    offset = (page - 1) * per_page

    async with get_db() as db:
        # Total count
        cursor = await db.execute("SELECT COUNT(*) as cnt FROM invoices")
        total = (await cursor.fetchone())["cnt"]

        # Paginated results
        cursor = await db.execute(
            """SELECT i.*, c.name as client_name
               FROM invoices i
               LEFT JOIN clients c ON i.client_id = c.id
               ORDER BY i.date DESC, i.id DESC
               LIMIT ? OFFSET ?""",
            (per_page, offset),
        )
        rows = await cursor.fetchall()

    items = [_row_to_dict(row) for row in rows]
    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page if per_page > 0 else 1,
    }


@crud_router.post("/create", status_code=201)
async def create_invoice(data: InvoiceCreate):
    """Creare factura noua cu calcul automat subtotal/TVA/total."""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT id, name FROM clients WHERE id = ?", (data.client_id,)
        )
        client = await cursor.fetchone()
        if not client:
            raise HTTPException(status_code=404, detail="Client negasit.")

    for item in data.items:
        item.total = round(item.quantity * item.unit_price, 2)

    subtotal, vat_amount, total = _calculate_totals(data.items, data.vat_percent)
    invoice_number = await _next_invoice_number(data.series_prefix)
    items_json = _items_to_json(data.items)

    async with get_db() as db:
        cursor = await db.execute(
            """INSERT INTO invoices
               (client_id, invoice_number, date, due_date, items_json,
                subtotal, vat_percent, vat_amount, total, notes, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'draft')""",
            (
                data.client_id, invoice_number, data.date, data.due_date,
                items_json, subtotal, data.vat_percent, vat_amount, total, data.notes,
            ),
        )
        await db.commit()
        invoice_id = cursor.lastrowid

    await log_activity(
        action="invoice.create",
        summary=f"Factura {invoice_number} creata — {total} RON",
        details={
            "invoice_id": invoice_id,
            "invoice_number": invoice_number,
            "client": client["name"],
            "total": total,
        },
    )
    return {
        "id": invoice_id,
        "invoice_number": invoice_number,
        "total": total,
        "message": f"Factura {invoice_number} creata cu succes.",
    }


# ═══════════════════════════════════════════
# Invoice detail (parametric /{invoice_id})
# ═══════════════════════════════════════════

@crud_router.get("/{invoice_id}")
async def get_invoice(invoice_id: int):
    """Detalii factura cu informatii client."""
    async with get_db() as db:
        cursor = await db.execute(
            """SELECT i.*, c.name as client_name, c.cui as client_cui,
                      c.reg_com as client_reg_com, c.address as client_address,
                      c.email as client_email, c.phone as client_phone
               FROM invoices i
               LEFT JOIN clients c ON i.client_id = c.id
               WHERE i.id = ?""",
            (invoice_id,),
        )
        row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Factura negasita.")
    return _row_to_dict(row)


@crud_router.put("/{invoice_id}")
async def update_invoice(invoice_id: int, data: InvoiceUpdate):
    """Actualizare factura (doar daca este in status draft)."""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM invoices WHERE id = ?", (invoice_id,)
        )
        existing = await cursor.fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Factura negasita.")
        if existing["status"] != "draft":
            raise HTTPException(
                status_code=409,
                detail=f"Factura nu poate fi modificata — status curent: {existing['status']}.",
            )

        updates = data.model_dump(exclude_unset=True)
        if not updates:
            raise HTTPException(status_code=400, detail="Niciun camp de actualizat.")

        if "client_id" in updates:
            cursor = await db.execute(
                "SELECT id FROM clients WHERE id = ?", (updates["client_id"],)
            )
            if not await cursor.fetchone():
                raise HTTPException(status_code=404, detail="Client negasit.")

        if "items" in updates:
            items = [InvoiceItem(**it) for it in updates["items"]] if isinstance(updates["items"][0], dict) else updates["items"]
            for item in items:
                item.total = round(item.quantity * item.unit_price, 2)
            vat_pct = updates.get("vat_percent", existing["vat_percent"])
            subtotal, vat_amount, total = _calculate_totals(items, vat_pct)
            updates["items_json"] = _items_to_json(items)
            updates["subtotal"] = subtotal
            updates["vat_amount"] = vat_amount
            updates["total"] = total
            del updates["items"]
        elif "vat_percent" in updates:
            old_items = _items_from_json(existing["items_json"])
            items = [InvoiceItem(**it) for it in old_items]
            subtotal, vat_amount, total = _calculate_totals(items, updates["vat_percent"])
            updates["subtotal"] = subtotal
            updates["vat_amount"] = vat_amount
            updates["total"] = total

        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values())
        values.append(invoice_id)

        await db.execute(
            f"UPDATE invoices SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            values,
        )
        await db.commit()

    await log_activity(
        action="invoice.update",
        summary=f"Factura ID {invoice_id} actualizata",
        details={"invoice_id": invoice_id, "fields": list(data.model_dump(exclude_unset=True).keys())},
    )
    return {"message": "Factura actualizata cu succes."}


@crud_router.delete("/{invoice_id}")
async def delete_invoice(invoice_id: int):
    """Stergere factura (doar daca este in status draft)."""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT invoice_number, status, pdf_path FROM invoices WHERE id = ?",
            (invoice_id,),
        )
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Factura negasita.")
        if row["status"] != "draft":
            raise HTTPException(
                status_code=409,
                detail=f"Factura nu poate fi stearsa — status curent: {row['status']}.",
            )
        invoice_number = row["invoice_number"]

        if row["pdf_path"]:
            pdf_path = Path(row["pdf_path"])
            if pdf_path.exists():
                pdf_path.unlink()

        await db.execute("DELETE FROM invoices WHERE id = ?", (invoice_id,))
        await db.commit()

    await log_activity(
        action="invoice.delete",
        summary=f"Factura {invoice_number} stearsa",
        details={"invoice_id": invoice_id, "invoice_number": invoice_number},
    )
    return {"message": f"Factura {invoice_number} stearsa cu succes."}


@crud_router.put("/{invoice_id}/status")
async def change_status(invoice_id: int, data: StatusUpdate):
    """Schimbare status factura cu validari de tranzitie."""
    valid_transitions = {
        "draft": ["sent", "cancelled"],
        "sent": ["paid", "cancelled"],
        "paid": [],
        "cancelled": ["draft"],
    }

    async with get_db() as db:
        cursor = await db.execute(
            "SELECT invoice_number, status FROM invoices WHERE id = ?",
            (invoice_id,),
        )
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Factura negasita.")

        current = row["status"]
        new_status = data.status.lower()

        if new_status not in valid_transitions.get(current, []):
            allowed = valid_transitions.get(current, [])
            raise HTTPException(
                status_code=409,
                detail=f"Tranzitie invalida: {current} -> {new_status}. Tranzitii permise: {allowed or 'niciuna'}.",
            )

        await db.execute(
            "UPDATE invoices SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (new_status, invoice_id),
        )
        await db.commit()

    await log_activity(
        action="invoice.status_change",
        summary=f"Factura {row['invoice_number']}: {current} -> {new_status}",
        details={
            "invoice_id": invoice_id,
            "invoice_number": row["invoice_number"],
            "old_status": current,
            "new_status": new_status,
        },
    )
    return {"message": f"Status actualizat: {current} -> {new_status}."}


@crud_router.put("/{invoice_id}/payment")
async def mark_payment(invoice_id: int):
    """Marcheaza o factura ca platita cu data curenta."""
    today = date.today().isoformat()
    async with get_db() as db:
        cursor = await db.execute(
            "UPDATE invoices SET status = 'paid', payment_date = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (today, invoice_id),
        )
        await db.commit()
        if cursor.rowcount == 0:
            raise HTTPException(404, "Factura negasita")
    await log_activity(
        action="invoice.payment",
        summary=f"Factura #{invoice_id} marcata ca platita",
        details={"invoice_id": invoice_id, "payment_date": today},
    )
    return {"message": "Factura marcata ca platita.", "payment_date": today}


# ═══════════════════════════════════════════
# Send invoice email
# ═══════════════════════════════════════════

async def _get_smtp_config() -> dict[str, str]:
    """Citeste configurarea SMTP din ai_config table."""
    keys = ["smtp_host", "smtp_port", "smtp_user", "smtp_pass", "smtp_from"]
    config = {}
    async with get_db() as db:
        for key in keys:
            cursor = await db.execute(
                "SELECT value FROM ai_config WHERE key = ?", (key,)
            )
            row = await cursor.fetchone()
            config[key] = row["value"] if row else ""
    return config


@crud_router.post("/{invoice_id}/send-email")
async def send_invoice_email(invoice_id: int, data: SendEmailRequest):
    """Trimite factura PDF pe email."""
    async with get_db() as db:
        cursor = await db.execute(
            """SELECT i.*, c.name as client_name, c.cui as client_cui,
                      c.reg_com as client_reg_com, c.address as client_address,
                      c.email as client_email, c.phone as client_phone
               FROM invoices i
               LEFT JOIN clients c ON i.client_id = c.id
               WHERE i.id = ?""",
            (invoice_id,),
        )
        row = await cursor.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Factura negasita.")

    invoice = dict(row)
    inv_number = invoice["invoice_number"]

    pdf_path = invoice.get("pdf_path")
    if not pdf_path or not Path(pdf_path).exists():
        items = _items_from_json(invoice.get("items_json", "[]"))
        pdf_filename = f"{inv_number}.pdf"
        pdf_path = str(INVOICES_DIR / pdf_filename)
        try:
            _build_invoice_pdf(invoice, items, pdf_path)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Eroare la generare PDF: {exc}")

        async with get_db() as db:
            await db.execute(
                "UPDATE invoices SET pdf_path = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (pdf_path, invoice_id),
            )
            await db.commit()

    smtp_config = await _get_smtp_config()
    if not smtp_config.get("smtp_host") or not smtp_config.get("smtp_user"):
        raise HTTPException(
            status_code=400,
            detail="Configurare SMTP lipsa. Seteaza smtp_host, smtp_port, smtp_user, smtp_pass, smtp_from in setarile AI.",
        )

    subject = data.subject or f"Factura {inv_number} — CIP Inspection SRL"
    body = data.body or (
        f"Buna ziua,\n\n"
        f"Va transmitem atasat factura {inv_number} in valoare de {invoice['total']:.2f} RON.\n\n"
        f"Cu stima,\nCIP Inspection SRL"
    )

    msg = MIMEMultipart()
    msg["From"] = smtp_config.get("smtp_from") or smtp_config["smtp_user"]
    msg["To"] = data.to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    pdf_file = Path(pdf_path)
    if pdf_file.exists():
        with open(pdf_file, "rb") as f:
            part = MIMEApplication(f.read(), Name=pdf_file.name)
            part["Content-Disposition"] = f'attachment; filename="{pdf_file.name}"'
            msg.attach(part)

    try:
        port = int(smtp_config.get("smtp_port") or "587")
        if port == 465:
            server = smtplib.SMTP_SSL(smtp_config["smtp_host"], port, timeout=30)
        else:
            server = smtplib.SMTP(smtp_config["smtp_host"], port, timeout=30)
            server.starttls()
        server.login(smtp_config["smtp_user"], smtp_config["smtp_pass"])
        server.sendmail(msg["From"], [data.to_email], msg.as_string())
        server.quit()
    except smtplib.SMTPException as exc:
        logger.error("Eroare SMTP: %s", exc)
        raise HTTPException(status_code=500, detail=f"Eroare la trimitere email: {exc}")
    except Exception as exc:
        logger.error("Eroare email: %s", exc)
        raise HTTPException(status_code=500, detail=f"Eroare la trimitere email: {exc}")

    await log_activity(
        action="invoice.send_email",
        summary=f"Factura {inv_number} trimisa pe email la {data.to_email}",
        details={
            "invoice_id": invoice_id,
            "invoice_number": inv_number,
            "to": data.to_email,
        },
    )

    return {
        "message": f"Factura {inv_number} trimisa cu succes la {data.to_email}.",
        "invoice_number": inv_number,
        "to": data.to_email,
    }


# ═══════════════════════════════════════════
# ANAF CUI Verification
# ═══════════════════════════════════════════

@crud_router.get("/verify-cui/{cui}")
async def verify_cui(cui: str):
    """Verificare CUI la ANAF — returnează date firmă (denumire, adresa, TVA, stare)."""
    clean_cui = cui.strip().upper().replace("RO", "").strip()
    if not clean_cui.isdigit():
        raise HTTPException(400, "CUI invalid — trebuie să conțină doar cifre")

    today = date.today().strftime("%Y-%m-%d")
    payload = [{"cui": int(clean_cui), "data": today}]

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                "https://webservicesp.anaf.ro/api/PlatitorTvaRest/api/v8/ws/tva",
                json=payload,
            )
            resp.raise_for_status()

        data = resp.json()
        found = data.get("found", [])
        if not found:
            return {"found": False, "cui": clean_cui, "message": "CUI negăsit în baza ANAF"}

        info = found[0]
        return {
            "found": True,
            "cui": clean_cui,
            "denumire": info.get("date_generale", {}).get("denumire", ""),
            "adresa": info.get("date_generale", {}).get("adresa", ""),
            "telefon": info.get("date_generale", {}).get("telefon", ""),
            "cod_postal": info.get("date_generale", {}).get("codPostal", ""),
            "stare": info.get("date_generale", {}).get("stare_inregistrare", ""),
            "tva": info.get("inregistrare_scop_Tva", {}).get("scpTVA", False),
            "data_verificare": today,
        }
    except httpx.HTTPError as exc:
        logger.error("Eroare ANAF API: %s", exc)
        raise HTTPException(502, f"Nu s-a putut verifica CUI la ANAF: {exc}")


# ═══════════════════════════════════════════
# Feature 1: Articole favorite / predefinite
# ═══════════════════════════════════════════

async def _ensure_presets_table():
    """Create invoice_item_presets table if it doesn't exist."""
    async with get_db() as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS invoice_item_presets (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                unit_price  REAL NOT NULL DEFAULT 0,
                unit        TEXT DEFAULT 'buc',
                category    TEXT DEFAULT 'general',
                created_at  TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()


@crud_router.get("/items/presets")
async def list_item_presets():
    """Lista toate articolele predefinite."""
    await _ensure_presets_table()
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM invoice_item_presets ORDER BY category, description"
        )
        rows = await cursor.fetchall()
    return [dict(row) for row in rows]


@crud_router.post("/items/presets", status_code=201)
async def create_item_preset(data: ItemPresetCreate):
    """Salvare articol predefinit pentru reutilizare in facturi."""
    await _ensure_presets_table()
    if not data.description.strip():
        raise HTTPException(400, "Descrierea este obligatorie.")
    if data.unit_price < 0:
        raise HTTPException(400, "Pretul nu poate fi negativ.")

    async with get_db() as db:
        cursor = await db.execute(
            """INSERT INTO invoice_item_presets (description, unit_price, unit, category)
               VALUES (?, ?, ?, ?)""",
            (data.description.strip(), data.unit_price, data.unit, data.category),
        )
        await db.commit()
        preset_id = cursor.lastrowid

    await log_activity(
        action="invoice.preset_create",
        summary=f"Articol predefinit creat: {data.description}",
        details={"preset_id": preset_id, "unit_price": data.unit_price, "category": data.category},
    )
    return {"id": preset_id, "message": f"Articol predefinit '{data.description}' salvat cu succes."}


@crud_router.delete("/items/presets/{preset_id}")
async def delete_item_preset(preset_id: int):
    """Stergere articol predefinit."""
    await _ensure_presets_table()
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT description FROM invoice_item_presets WHERE id = ?", (preset_id,)
        )
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(404, "Articol predefinit negasit.")
        desc = row["description"]
        await db.execute("DELETE FROM invoice_item_presets WHERE id = ?", (preset_id,))
        await db.commit()

    await log_activity(
        action="invoice.preset_delete",
        summary=f"Articol predefinit sters: {desc}",
        details={"preset_id": preset_id},
    )
    return {"message": f"Articol predefinit '{desc}' sters cu succes."}


# ═══════════════════════════════════════════
# Feature 2: Facturi recurente
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


@crud_router.post("/{invoice_id}/set-recurring")
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


@crud_router.get("/recurring/list")
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


# ═══════════════════════════════════════════
# Feature 4: Plati partiale
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


@crud_router.post("/{invoice_id}/payments")
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


@crud_router.get("/{invoice_id}/payments")
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


# ═══════════════════════════════════════════
# Feature 5: Factura din inspectie ITP
# ═══════════════════════════════════════════

@crud_router.post("/from-itp/{inspection_id}")
async def create_from_itp(inspection_id: int):
    """
    Creeaza factura draft pre-completata din datele unei inspectii ITP.
    [SYNC: ITP -> Invoice]
    """
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM itp_inspections WHERE id = ?", (inspection_id,)
        )
        inspection = await cursor.fetchone()
        if not inspection:
            raise HTTPException(404, "Inspectia ITP negasita.")

        inspection = dict(inspection)
        owner_name = inspection.get("owner_name") or "Client ITP"
        plate = inspection.get("plate_number", "N/A")
        price = inspection.get("price", 0) or 0
        brand = inspection.get("brand") or ""
        model = inspection.get("model") or ""

        vehicle_desc = f"{brand} {model}".strip()
        if vehicle_desc:
            vehicle_desc = f" ({vehicle_desc})"

        # Find or create client by owner_name
        cursor = await db.execute(
            "SELECT id, name FROM clients WHERE name = ? COLLATE NOCASE LIMIT 1",
            (owner_name,),
        )
        client_row = await cursor.fetchone()

        if client_row:
            client_id = client_row["id"]
        else:
            cursor = await db.execute(
                """INSERT INTO clients (name, phone, notes)
                   VALUES (?, ?, ?)""",
                (owner_name, inspection.get("owner_phone"), f"Client creat automat din ITP - {plate}"),
            )
            await db.commit()
            client_id = cursor.lastrowid

        # Build invoice items
        items = [{
            "description": f"Inspectie ITP - {plate}{vehicle_desc}",
            "quantity": 1,
            "unit_price": round(float(price), 2),
            "total": round(float(price), 2),
        }]
        items_json = json.dumps(items, ensure_ascii=False)
        subtotal = round(float(price), 2)

        invoice_number = await _next_invoice_number()
        inv_date = inspection.get("inspection_date") or date.today().isoformat()

        cursor = await db.execute(
            """INSERT INTO invoices
               (client_id, invoice_number, date, items_json,
                subtotal, vat_percent, vat_amount, total, notes, status)
               VALUES (?, ?, ?, ?, ?, 0, 0, ?, ?, 'draft')""",
            (
                client_id, invoice_number, inv_date, items_json,
                subtotal, subtotal,
                f"Generat automat din inspectia ITP #{inspection_id} - {plate}",
            ),
        )
        await db.commit()
        invoice_id = cursor.lastrowid

    await log_activity(
        action="invoice.from_itp",
        summary=f"Factura {invoice_number} creata din ITP #{inspection_id} ({plate})",
        details={
            "invoice_id": invoice_id,
            "inspection_id": inspection_id,
            "plate": plate,
            "total": subtotal,
        },
    )
    return {
        "id": invoice_id,
        "invoice_number": invoice_number,
        "client_id": client_id,
        "total": subtotal,
        "message": f"Factura {invoice_number} creata din inspectia ITP pentru {plate}.",
    }


# ═══════════════════════════════════════════
# Feature 6: Factura din calcul pret traducere
# ═══════════════════════════════════════════

@crud_router.post("/from-calculation")
async def create_from_calculation(data: FromCalculationRequest):
    """
    Creeaza factura draft pre-completata din datele unui calcul de pret traducere.
    Accepta word_count, price, document_type, source_lang, target_lang, client_id optional.
    """
    if data.price <= 0:
        raise HTTPException(400, "Pretul trebuie sa fie pozitiv.")
    if data.word_count <= 0:
        raise HTTPException(400, "Numarul de cuvinte trebuie sa fie pozitiv.")

    async with get_db() as db:
        # Validate client if provided
        client_id = data.client_id
        if client_id:
            cursor = await db.execute(
                "SELECT id, name FROM clients WHERE id = ?", (client_id,)
            )
            client_row = await cursor.fetchone()
            if not client_row:
                raise HTTPException(404, "Client negasit.")

        if not client_id:
            # Create/find a generic translation client
            cursor = await db.execute(
                "SELECT id FROM clients WHERE name = 'Client traducere' COLLATE NOCASE LIMIT 1"
            )
            generic = await cursor.fetchone()
            if generic:
                client_id = generic["id"]
            else:
                cursor = await db.execute(
                    "INSERT INTO clients (name, notes) VALUES (?, ?)",
                    ("Client traducere", "Client generic creat automat pentru facturi din calcul pret"),
                )
                await db.commit()
                client_id = cursor.lastrowid

        doc_type = data.document_type or "document"
        description = (
            f"Traducere {doc_type} {data.source_lang} -> {data.target_lang} "
            f"({data.word_count} cuvinte)"
        )

        items = [{
            "description": description,
            "quantity": 1,
            "unit_price": round(data.price, 2),
            "total": round(data.price, 2),
        }]
        items_json = json.dumps(items, ensure_ascii=False)
        subtotal = round(data.price, 2)

        invoice_number = await _next_invoice_number()

        cursor = await db.execute(
            """INSERT INTO invoices
               (client_id, invoice_number, date, items_json,
                subtotal, vat_percent, vat_amount, total, notes, status)
               VALUES (?, ?, ?, ?, ?, 0, 0, ?, ?, 'draft')""",
            (
                client_id, invoice_number, date.today().isoformat(), items_json,
                subtotal, subtotal,
                f"Generat din calcul pret: {data.word_count} cuvinte, {data.source_lang}->{data.target_lang}",
            ),
        )
        await db.commit()
        invoice_id = cursor.lastrowid

    await log_activity(
        action="invoice.from_calculation",
        summary=f"Factura {invoice_number} creata din calcul pret ({data.word_count} cuv, {subtotal} RON)",
        details={
            "invoice_id": invoice_id,
            "word_count": data.word_count,
            "price": subtotal,
            "source_lang": data.source_lang,
            "target_lang": data.target_lang,
        },
    )
    return {
        "id": invoice_id,
        "invoice_number": invoice_number,
        "client_id": client_id,
        "total": subtotal,
        "message": f"Factura {invoice_number} creata din calcul pret ({data.word_count} cuvinte).",
    }
