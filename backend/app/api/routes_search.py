"""
Global search endpoint — search across all major tables.

GET /api/search?q=term&limit=10
Searches invoices, clients, ITP inspections, notes, AI chat sessions,
and time entries. Returns unified results with type, id, title, subtitle, url.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query

from app.db.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Search"])


@router.get("/search")
async def global_search(
    q: str = Query(..., min_length=2, description="Termen de cautare (minim 2 caractere)"),
    limit: int = Query(10, ge=1, le=50, description="Numar maxim de rezultate per categorie"),
):
    """
    Cautare globala in toate modulele principale.

    Cauta in: facturi, clienti, inspectii ITP, notite, sesiuni AI chat, time entries.
    Returneaza rezultate unificate sortate pe tip.
    """
    pattern = f"%{q}%"
    results: list[dict] = []

    async with get_db() as db:
        # 1. Invoices — search in invoice_number, notes
        try:
            cursor = await db.execute(
                """SELECT id, invoice_number, notes, total, status
                   FROM invoices
                   WHERE invoice_number LIKE ? OR notes LIKE ?
                   ORDER BY date DESC
                   LIMIT ?""",
                (pattern, pattern, limit),
            )
            for row in await cursor.fetchall():
                r = dict(row)
                subtitle_parts = []
                if r.get("total"):
                    subtitle_parts.append(f"{r['total']:.2f} RON")
                if r.get("status"):
                    subtitle_parts.append(r["status"])
                results.append({
                    "type": "invoice",
                    "id": r["id"],
                    "title": r["invoice_number"],
                    "subtitle": " — ".join(subtitle_parts) if subtitle_parts else (r.get("notes") or "")[:80],
                    "url": "/invoices",
                })
        except Exception as exc:
            logger.warning("Search invoices failed: %s", exc)

        # 2. Clients — search in name, cui, email
        try:
            cursor = await db.execute(
                """SELECT id, name, cui, email
                   FROM clients
                   WHERE name LIKE ? OR cui LIKE ? OR email LIKE ?
                   ORDER BY name ASC
                   LIMIT ?""",
                (pattern, pattern, pattern, limit),
            )
            for row in await cursor.fetchall():
                r = dict(row)
                subtitle_parts = []
                if r.get("cui"):
                    subtitle_parts.append(f"CUI: {r['cui']}")
                if r.get("email"):
                    subtitle_parts.append(r["email"])
                results.append({
                    "type": "client",
                    "id": r["id"],
                    "title": r["name"],
                    "subtitle": " — ".join(subtitle_parts) if subtitle_parts else "",
                    "url": "/invoices?tab=clients",
                })
        except Exception as exc:
            logger.warning("Search clients failed: %s", exc)

        # 3. ITP Inspections — search in plate_number, owner_name
        try:
            cursor = await db.execute(
                """SELECT id, plate_number, owner_name, inspection_date, result
                   FROM itp_inspections
                   WHERE plate_number LIKE ? OR owner_name LIKE ?
                   ORDER BY inspection_date DESC
                   LIMIT ?""",
                (pattern, pattern, limit),
            )
            for row in await cursor.fetchall():
                r = dict(row)
                subtitle_parts = []
                if r.get("owner_name"):
                    subtitle_parts.append(r["owner_name"])
                if r.get("inspection_date"):
                    subtitle_parts.append(r["inspection_date"])
                if r.get("result"):
                    subtitle_parts.append(r["result"])
                results.append({
                    "type": "itp",
                    "id": r["id"],
                    "title": r["plate_number"],
                    "subtitle": " — ".join(subtitle_parts) if subtitle_parts else "",
                    "url": "/itp",
                })
        except Exception as exc:
            logger.warning("Search itp_inspections failed: %s", exc)

        # 4. Notes — search in title, content
        try:
            cursor = await db.execute(
                """SELECT id, title, content
                   FROM notes
                   WHERE title LIKE ? OR content LIKE ?
                   ORDER BY updated_at DESC
                   LIMIT ?""",
                (pattern, pattern, limit),
            )
            for row in await cursor.fetchall():
                r = dict(row)
                content_preview = (r.get("content") or "")[:80]
                results.append({
                    "type": "note",
                    "id": r["id"],
                    "title": r["title"],
                    "subtitle": content_preview,
                    "url": "/notepad",
                })
        except Exception as exc:
            logger.warning("Search notes failed: %s", exc)

        # 5. AI Chat Sessions — search in title
        try:
            cursor = await db.execute(
                """SELECT id, title, created_at
                   FROM chat_sessions
                   WHERE title LIKE ?
                   ORDER BY updated_at DESC
                   LIMIT ?""",
                (pattern, limit),
            )
            for row in await cursor.fetchall():
                r = dict(row)
                results.append({
                    "type": "ai_chat",
                    "id": r["id"],
                    "title": r["title"],
                    "subtitle": r.get("created_at", ""),
                    "url": "/ai-chat",
                })
        except Exception as exc:
            logger.warning("Search chat_sessions failed: %s", exc)

        # 6. Time Entries — search in project, description
        try:
            cursor = await db.execute(
                """SELECT id, project, description, start_time, duration_minutes
                   FROM time_entries
                   WHERE project LIKE ? OR description LIKE ?
                   ORDER BY start_time DESC
                   LIMIT ?""",
                (pattern, pattern, limit),
            )
            for row in await cursor.fetchall():
                r = dict(row)
                subtitle_parts = []
                if r.get("description"):
                    subtitle_parts.append(r["description"][:60])
                if r.get("duration_minutes"):
                    subtitle_parts.append(f"{r['duration_minutes']} min")
                results.append({
                    "type": "time",
                    "id": r["id"],
                    "title": r["project"],
                    "subtitle": " — ".join(subtitle_parts) if subtitle_parts else "",
                    "url": "/time-tracking",
                })
        except Exception as exc:
            logger.warning("Search time_entries failed: %s", exc)

    # Sort by type for grouped display
    type_order = {"invoice": 0, "client": 1, "itp": 2, "note": 3, "ai_chat": 4, "time": 5}
    results.sort(key=lambda r: type_order.get(r["type"], 99))

    return {
        "query": q,
        "total": len(results),
        "results": results,
    }
