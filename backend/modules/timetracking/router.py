"""
Time Tracking router — cronometru, CRUD inregistrari timp, statistici, integrare facturare.

Tabela: time_entries (migration 024)
Coloane: id, project, description, client_id, start_time, end_time,
         duration_minutes, invoiced, invoice_id, created_at
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.activity_log import log_activity
from app.db.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/time", tags=["Time Tracking"])


# ═══════════════════════════════════════════
# Pydantic models
# ═══════════════════════════════════════════

class TimerStartRequest(BaseModel):
    """Body pentru pornirea cronometrului."""
    project: str
    description: str = ""
    client_id: Optional[int] = None


class ManualEntryRequest(BaseModel):
    """Body pentru inregistrare manuala de timp."""
    project: str
    description: str = ""
    client_id: Optional[int] = None
    start_time: str  # ISO format
    end_time: Optional[str] = None  # ISO format
    duration_minutes: Optional[int] = None


class EntryUpdateRequest(BaseModel):
    """Body pentru actualizare inregistrare."""
    project: Optional[str] = None
    description: Optional[str] = None
    client_id: Optional[int] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration_minutes: Optional[int] = None


class ToInvoiceItemsRequest(BaseModel):
    """Body pentru conversie inregistrari in articole factura."""
    entry_ids: list[int]
    hourly_rate: float = 50.0


class MarkInvoicedRequest(BaseModel):
    """Body pentru marcarea inregistrarilor ca facturate."""
    entry_ids: list[int]
    invoice_id: int


# ═══════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════

def _row_to_dict(row) -> dict:
    """Converteste aiosqlite.Row in dict."""
    return dict(row)


def _parse_iso(dt_str: str) -> datetime:
    """Parseaza string ISO in datetime. Arunca HTTPException daca invalid."""
    try:
        return datetime.fromisoformat(dt_str)
    except (ValueError, TypeError):
        raise HTTPException(400, detail=f"Format data invalid: {dt_str}. Foloseste ISO 8601.")


def _calc_duration_minutes(start_str: str, end_str: str) -> int:
    """Calculeaza durata in minute intre doua datetimes ISO."""
    start = _parse_iso(start_str)
    end = _parse_iso(end_str)
    if end < start:
        raise HTTPException(400, detail="end_time trebuie sa fie dupa start_time.")
    delta = end - start
    return max(1, int(delta.total_seconds() / 60))


# ═══════════════════════════════════════════
# Timer Control
# ═══════════════════════════════════════════

@router.post("/start")
async def start_timer(body: TimerStartRequest):
    """
    Porneste un cronometru nou.

    Verifica mai intai daca exista un timer activ (end_time IS NULL).
    Daca da, returneaza eroare — opreste mai intai timer-ul curent.
    """
    async with get_db() as db:
        # Verifica daca exista timer activ
        cursor = await db.execute(
            "SELECT id, project, start_time FROM time_entries WHERE end_time IS NULL LIMIT 1"
        )
        active = await cursor.fetchone()
        if active:
            raise HTTPException(
                409,
                detail=f"Timer activ deja pe proiectul '{active['project']}' "
                       f"(id={active['id']}, start={active['start_time']}). "
                       f"Opreste-l mai intai cu POST /api/time/stop."
            )

        now = datetime.utcnow().isoformat()
        cursor = await db.execute(
            """INSERT INTO time_entries (project, description, client_id, start_time)
               VALUES (?, ?, ?, ?)""",
            (body.project, body.description, body.client_id, now),
        )
        await db.commit()
        entry_id = cursor.lastrowid

    await log_activity(
        action="time.start",
        summary=f"Timer pornit: {body.project}",
        details={"entry_id": entry_id, "project": body.project, "client_id": body.client_id},
    )
    return {
        "id": entry_id,
        "project": body.project,
        "description": body.description,
        "client_id": body.client_id,
        "start_time": now,
        "status": "running",
    }


@router.post("/stop")
async def stop_timer():
    """
    Opreste timer-ul activ curent.

    Gaseste inregistrarea cu end_time IS NULL, seteaza end_time si
    calculeaza duration_minutes. Returneaza eroare daca nu exista timer activ.
    """
    now = datetime.utcnow().isoformat()
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT id, project, start_time FROM time_entries WHERE end_time IS NULL LIMIT 1"
        )
        active = await cursor.fetchone()
        if not active:
            raise HTTPException(404, detail="Niciun timer activ de oprit.")

        entry_id = active["id"]
        start_time = active["start_time"]
        project = active["project"]
        duration = _calc_duration_minutes(start_time, now)

        await db.execute(
            "UPDATE time_entries SET end_time = ?, duration_minutes = ? WHERE id = ?",
            (now, duration, entry_id),
        )
        await db.commit()

        # Refetch full entry
        cursor = await db.execute("SELECT * FROM time_entries WHERE id = ?", (entry_id,))
        entry = await cursor.fetchone()

    await log_activity(
        action="time.stop",
        summary=f"Timer oprit: {project} ({duration} min)",
        details={"entry_id": entry_id, "duration_minutes": duration},
    )
    return _row_to_dict(entry)


@router.get("/active")
async def get_active_timer():
    """
    Returneaza timer-ul activ curent (end_time IS NULL).

    Returneaza null daca nu exista timer activ, plus elapsed_minutes
    calculat dinamic pentru afisare in UI.
    """
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM time_entries WHERE end_time IS NULL LIMIT 1"
        )
        active = await cursor.fetchone()

    if not active:
        return {"active": None}

    entry = _row_to_dict(active)
    # Calculeaza elapsed_minutes dinamic
    start = _parse_iso(entry["start_time"])
    now = datetime.utcnow()
    elapsed = max(0, int((now - start).total_seconds() / 60))
    entry["elapsed_minutes"] = elapsed
    return {"active": entry}


# ═══════════════════════════════════════════
# CRUD
# ═══════════════════════════════════════════

@router.get("/entries")
async def list_entries(
    client_id: Optional[int] = Query(None, description="Filtreaza dupa client"),
    start_date: Optional[str] = Query(None, description="Data start (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Data sfarsit (YYYY-MM-DD)"),
    invoiced: Optional[bool] = Query(None, description="Filtreaza dupa status facturare"),
    limit: int = Query(100, ge=1, le=1000, description="Nr. maxim rezultate"),
):
    """
    Lista inregistrari de timp cu filtre optionale.

    Sorteaza descrescator dupa start_time. Suporta filtrare pe client,
    interval date, status facturare.
    """
    conditions = []
    params = []

    if client_id is not None:
        conditions.append("client_id = ?")
        params.append(client_id)

    if start_date:
        conditions.append("start_time >= ?")
        params.append(start_date)

    if end_date:
        # Include tot end_date (pana la 23:59:59)
        conditions.append("start_time < ?")
        params.append(end_date + "T23:59:59")

    if invoiced is not None:
        conditions.append("invoiced = ?")
        params.append(1 if invoiced else 0)

    where_clause = " AND ".join(conditions) if conditions else "1=1"
    params.append(limit)

    async with get_db() as db:
        cursor = await db.execute(
            f"SELECT * FROM time_entries WHERE {where_clause} ORDER BY start_time DESC LIMIT ?",
            tuple(params),
        )
        rows = await cursor.fetchall()

    return {"entries": [_row_to_dict(r) for r in rows], "count": len(rows)}


@router.post("/entries")
async def create_manual_entry(body: ManualEntryRequest):
    """
    Creeaza o inregistrare manuala de timp.

    Fie end_time fie duration_minutes trebuie sa fie furnizat.
    Daca ambele sunt furnizate, duration_minutes are prioritate.
    Daca doar end_time e furnizat, calculeaza durata automat.
    """
    _parse_iso(body.start_time)  # Validate format

    duration = body.duration_minutes
    end_time = body.end_time

    if duration is None and end_time is None:
        raise HTTPException(
            400,
            detail="Furnizeaza end_time sau duration_minutes (sau ambele)."
        )

    if duration is None and end_time is not None:
        duration = _calc_duration_minutes(body.start_time, end_time)

    if end_time is None and duration is not None:
        # Calculeaza end_time din start_time + duration
        start_dt = _parse_iso(body.start_time)
        end_dt = start_dt + timedelta(minutes=duration)
        end_time = end_dt.isoformat()

    if duration is not None and duration <= 0:
        raise HTTPException(400, detail="duration_minutes trebuie sa fie > 0.")

    async with get_db() as db:
        cursor = await db.execute(
            """INSERT INTO time_entries (project, description, client_id, start_time, end_time, duration_minutes)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (body.project, body.description, body.client_id, body.start_time, end_time, duration),
        )
        await db.commit()
        entry_id = cursor.lastrowid

        cursor = await db.execute("SELECT * FROM time_entries WHERE id = ?", (entry_id,))
        entry = await cursor.fetchone()

    await log_activity(
        action="time.create",
        summary=f"Inregistrare manuala: {body.project} ({duration} min)",
        details={"entry_id": entry_id, "project": body.project, "duration": duration},
    )
    return _row_to_dict(entry)


@router.put("/entries/{entry_id}")
async def update_entry(entry_id: int, body: EntryUpdateRequest):
    """
    Actualizeaza o inregistrare de timp existenta.

    Doar campurile furnizate sunt modificate. Daca se schimba start_time
    sau end_time fara duration_minutes, durata se recalculeaza automat.
    """
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM time_entries WHERE id = ?", (entry_id,))
        existing = await cursor.fetchone()
        if not existing:
            raise HTTPException(404, detail=f"Inregistrare {entry_id} nu exista.")

        existing = _row_to_dict(existing)

        # Aplica update-uri
        project = body.project if body.project is not None else existing["project"]
        description = body.description if body.description is not None else existing["description"]
        client_id = body.client_id if body.client_id is not None else existing["client_id"]
        start_time = body.start_time if body.start_time is not None else existing["start_time"]
        end_time = body.end_time if body.end_time is not None else existing["end_time"]
        duration = body.duration_minutes if body.duration_minutes is not None else existing["duration_minutes"]

        # Validate formats if changed
        if body.start_time is not None:
            _parse_iso(body.start_time)
        if body.end_time is not None:
            _parse_iso(body.end_time)

        # Recalculate duration if times changed but duration not explicitly set
        if (body.start_time is not None or body.end_time is not None) and body.duration_minutes is None:
            if start_time and end_time:
                duration = _calc_duration_minutes(start_time, end_time)

        await db.execute(
            """UPDATE time_entries
               SET project = ?, description = ?, client_id = ?,
                   start_time = ?, end_time = ?, duration_minutes = ?
               WHERE id = ?""",
            (project, description, client_id, start_time, end_time, duration, entry_id),
        )
        await db.commit()

        cursor = await db.execute("SELECT * FROM time_entries WHERE id = ?", (entry_id,))
        updated = await cursor.fetchone()

    await log_activity(
        action="time.update",
        summary=f"Inregistrare {entry_id} actualizata",
        details={"entry_id": entry_id, "project": project},
    )
    return _row_to_dict(updated)


@router.delete("/entries/{entry_id}")
async def delete_entry(entry_id: int):
    """
    Sterge o inregistrare de timp.

    Nu permite stergerea inregistrarilor deja facturate (invoiced=1).
    """
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM time_entries WHERE id = ?", (entry_id,))
        existing = await cursor.fetchone()
        if not existing:
            raise HTTPException(404, detail=f"Inregistrare {entry_id} nu exista.")

        if existing["invoiced"]:
            raise HTTPException(
                409,
                detail=f"Inregistrare {entry_id} e deja facturata (invoice_id={existing['invoice_id']}). "
                       f"Nu se poate sterge."
            )

        await db.execute("DELETE FROM time_entries WHERE id = ?", (entry_id,))
        await db.commit()

    await log_activity(
        action="time.delete",
        summary=f"Inregistrare {entry_id} stearsa",
        details={"entry_id": entry_id, "project": existing["project"]},
    )
    return {"deleted": True, "id": entry_id}


# ═══════════════════════════════════════════
# Stats
# ═══════════════════════════════════════════

@router.get("/stats")
async def get_stats():
    """
    Sumar statistici timp lucrat.

    Returneaza: total_hours_today, total_hours_week, total_hours_month,
    top 5 proiecte (by_project), top 5 clienti (by_client).
    """
    now = datetime.utcnow()
    today = now.strftime("%Y-%m-%d")
    # Luni = inceputul saptamanii (Monday)
    week_start = (now - timedelta(days=now.weekday())).strftime("%Y-%m-%d")
    month_start = now.strftime("%Y-%m-01")

    async with get_db() as db:
        # Total azi
        cursor = await db.execute(
            "SELECT COALESCE(SUM(duration_minutes), 0) as total FROM time_entries "
            "WHERE start_time >= ? AND end_time IS NOT NULL",
            (today,),
        )
        row = await cursor.fetchone()
        total_today = row["total"]

        # Total saptamana
        cursor = await db.execute(
            "SELECT COALESCE(SUM(duration_minutes), 0) as total FROM time_entries "
            "WHERE start_time >= ? AND end_time IS NOT NULL",
            (week_start,),
        )
        row = await cursor.fetchone()
        total_week = row["total"]

        # Total luna
        cursor = await db.execute(
            "SELECT COALESCE(SUM(duration_minutes), 0) as total FROM time_entries "
            "WHERE start_time >= ? AND end_time IS NOT NULL",
            (month_start,),
        )
        row = await cursor.fetchone()
        total_month = row["total"]

        # Top 5 proiecte (all time, completed entries)
        cursor = await db.execute(
            "SELECT project, SUM(duration_minutes) as total_minutes, COUNT(*) as entries "
            "FROM time_entries WHERE end_time IS NOT NULL "
            "GROUP BY project ORDER BY total_minutes DESC LIMIT 5"
        )
        by_project = [
            {
                "project": r["project"],
                "total_minutes": r["total_minutes"],
                "total_hours": round(r["total_minutes"] / 60, 2),
                "entries": r["entries"],
            }
            for r in await cursor.fetchall()
        ]

        # Top 5 clienti (all time, completed entries)
        cursor = await db.execute(
            "SELECT te.client_id, c.name as client_name, "
            "SUM(te.duration_minutes) as total_minutes, COUNT(*) as entries "
            "FROM time_entries te "
            "LEFT JOIN clients c ON te.client_id = c.id "
            "WHERE te.end_time IS NOT NULL AND te.client_id IS NOT NULL "
            "GROUP BY te.client_id ORDER BY total_minutes DESC LIMIT 5"
        )
        by_client = [
            {
                "client_id": r["client_id"],
                "client_name": r["client_name"] or f"Client #{r['client_id']}",
                "total_minutes": r["total_minutes"],
                "total_hours": round(r["total_minutes"] / 60, 2),
                "entries": r["entries"],
            }
            for r in await cursor.fetchall()
        ]

    return {
        "total_hours_today": round(total_today / 60, 2),
        "total_hours_week": round(total_week / 60, 2),
        "total_hours_month": round(total_month / 60, 2),
        "total_minutes_today": total_today,
        "total_minutes_week": total_week,
        "total_minutes_month": total_month,
        "by_project": by_project,
        "by_client": by_client,
    }


@router.get("/stats/daily")
async def get_daily_stats():
    """
    Ore lucrate pe zi, pentru ultimele 30 de zile.

    Returneaza lista cu {date, total_minutes, total_hours} pentru fiecare zi
    care are inregistrari. Zilele fara activitate nu apar.
    """
    cutoff = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")

    async with get_db() as db:
        cursor = await db.execute(
            "SELECT DATE(start_time) as day, "
            "SUM(duration_minutes) as total_minutes, COUNT(*) as entries "
            "FROM time_entries "
            "WHERE start_time >= ? AND end_time IS NOT NULL "
            "GROUP BY DATE(start_time) ORDER BY day DESC",
            (cutoff,),
        )
        rows = await cursor.fetchall()

    daily = [
        {
            "date": r["day"],
            "total_minutes": r["total_minutes"],
            "total_hours": round(r["total_minutes"] / 60, 2),
            "entries": r["entries"],
        }
        for r in rows
    ]
    return {"daily": daily, "days_count": len(daily)}


# ═══════════════════════════════════════════
# Invoice Integration
# ═══════════════════════════════════════════

@router.post("/to-invoice-items")
async def to_invoice_items(body: ToInvoiceItemsRequest):
    """
    Converteste inregistrari de timp in articole de factura.

    Primeste lista de entry_ids si hourly_rate, returneaza un array de items
    compatibil cu formatul de creare factura (description, quantity, unit_price, total).
    Fiecare inregistrare devine o linie separata in factura.
    """
    if not body.entry_ids:
        raise HTTPException(400, detail="entry_ids nu poate fi gol.")

    if body.hourly_rate <= 0:
        raise HTTPException(400, detail="hourly_rate trebuie sa fie > 0.")

    placeholders = ",".join("?" for _ in body.entry_ids)

    async with get_db() as db:
        cursor = await db.execute(
            f"SELECT * FROM time_entries WHERE id IN ({placeholders}) AND end_time IS NOT NULL",
            tuple(body.entry_ids),
        )
        rows = await cursor.fetchall()

    if not rows:
        raise HTTPException(404, detail="Nicio inregistrare gasita cu ID-urile furnizate.")

    found_ids = {r["id"] for r in rows}
    missing_ids = [eid for eid in body.entry_ids if eid not in found_ids]
    if missing_ids:
        logger.warning("ID-uri negasite sau incomplete: %s", missing_ids)

    items = []
    total_minutes = 0
    for row in rows:
        entry = _row_to_dict(row)
        minutes = entry["duration_minutes"] or 0
        hours = round(minutes / 60, 2)
        total_minutes += minutes

        desc_parts = [entry["project"]]
        if entry["description"]:
            desc_parts.append(entry["description"])
        desc_parts.append(f"({entry['start_time'][:10]}, {minutes} min)")

        items.append({
            "description": " - ".join(desc_parts),
            "quantity": hours,
            "unit_price": body.hourly_rate,
            "total": round(hours * body.hourly_rate, 2),
        })

    return {
        "items": items,
        "summary": {
            "entries_count": len(rows),
            "total_minutes": total_minutes,
            "total_hours": round(total_minutes / 60, 2),
            "hourly_rate": body.hourly_rate,
            "grand_total": round(sum(i["total"] for i in items), 2),
            "missing_ids": missing_ids,
        },
    }


@router.post("/mark-invoiced")
async def mark_invoiced(body: MarkInvoicedRequest):
    """
    Marcheaza inregistrarile de timp ca facturate.

    Seteaza invoiced=1 si invoice_id pe inregistrarile specificate.
    Inregistrarile deja facturate sunt ignorate (nu suprascrie invoice_id).
    """
    if not body.entry_ids:
        raise HTTPException(400, detail="entry_ids nu poate fi gol.")

    placeholders = ",".join("?" for _ in body.entry_ids)

    async with get_db() as db:
        # Verifica cate exista si cate sunt deja facturate
        cursor = await db.execute(
            f"SELECT id, invoiced FROM time_entries WHERE id IN ({placeholders})",
            tuple(body.entry_ids),
        )
        rows = await cursor.fetchall()

        found_ids = {r["id"] for r in rows}
        missing_ids = [eid for eid in body.entry_ids if eid not in found_ids]
        already_invoiced = [r["id"] for r in rows if r["invoiced"]]
        to_update = [r["id"] for r in rows if not r["invoiced"]]

        if not to_update:
            return {
                "updated": 0,
                "already_invoiced": already_invoiced,
                "missing_ids": missing_ids,
            }

        update_placeholders = ",".join("?" for _ in to_update)
        await db.execute(
            f"UPDATE time_entries SET invoiced = 1, invoice_id = ? WHERE id IN ({update_placeholders})",
            (body.invoice_id, *to_update),
        )
        await db.commit()

    await log_activity(
        action="time.mark_invoiced",
        summary=f"{len(to_update)} inregistrari marcate ca facturate (factura #{body.invoice_id})",
        details={
            "invoice_id": body.invoice_id,
            "updated_ids": to_update,
            "already_invoiced": already_invoiced,
            "missing_ids": missing_ids,
        },
    )
    return {
        "updated": len(to_update),
        "invoice_id": body.invoice_id,
        "updated_ids": to_update,
        "already_invoiced": already_invoiced,
        "missing_ids": missing_ids,
    }
