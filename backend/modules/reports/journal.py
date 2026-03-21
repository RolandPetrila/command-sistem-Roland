"""
Journal & Bookmarks — CRUD pentru jurnal personal si bookmark-uri.

Endpoints:
  GET    /api/reports/journal
  POST   /api/reports/journal
  PUT    /api/reports/journal/{entry_id}
  DELETE /api/reports/journal/{entry_id}
  GET    /api/reports/bookmarks
  POST   /api/reports/bookmarks
  PUT    /api/reports/bookmarks/{bookmark_id}
  DELETE /api/reports/bookmarks/{bookmark_id}
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.core.activity_log import log_activity
from app.db.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/reports", tags=["Reports — Journal"])


# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------

class JournalEntryCreate(BaseModel):
    title: str
    content: str = ""
    mood: str = "neutral"
    tags: list[str] = []


class JournalEntryUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    mood: str | None = None
    tags: list[str] | None = None


class BookmarkCreate(BaseModel):
    title: str
    url: str
    category: str = "general"
    description: str = ""


class BookmarkUpdate(BaseModel):
    title: str | None = None
    url: str | None = None
    category: str | None = None
    description: str | None = None


# ===========================================================================
# JOURNAL
# ===========================================================================

@router.get("/journal")
async def journal_list(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    """Listeaza intrarile din jurnal, paginat."""
    offset = (page - 1) * per_page

    try:
        async with get_db() as db:
            cursor = await db.execute(
                "SELECT COUNT(*) as cnt FROM journal_entries"
            )
            count_row = await cursor.fetchone()
            total = count_row["cnt"] if count_row else 0

            cursor = await db.execute(
                """SELECT * FROM journal_entries
                   ORDER BY created_at DESC
                   LIMIT ? OFFSET ?""",
                (per_page, offset),
            )
            rows = await cursor.fetchall()

            entries = []
            for row in rows:
                tags = []
                try:
                    tags = json.loads(row["tags"]) if row["tags"] else []
                except (json.JSONDecodeError, TypeError):
                    pass

                entries.append({
                    "id": row["id"],
                    "title": row["title"],
                    "content": row["content"],
                    "mood": row["mood"],
                    "tags": tags,
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                })

        return {
            "entries": entries,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": max(1, (total + per_page - 1) // per_page),
        }

    except Exception as exc:
        logger.error("Eroare jurnal list: %s", exc)
        raise HTTPException(500, f"Eroare citire jurnal: {exc}")


@router.post("/journal")
async def journal_create(req: JournalEntryCreate):
    """Adauga o intrare noua in jurnal."""
    tags_json = json.dumps(req.tags, ensure_ascii=False)
    now = datetime.now(timezone.utc).isoformat()

    try:
        async with get_db() as db:
            cursor = await db.execute(
                """INSERT INTO journal_entries (title, content, mood, tags, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (req.title, req.content, req.mood, tags_json, now, now),
            )
            await db.commit()
            entry_id = cursor.lastrowid

        await log_activity(
            action="reports.journal.create",
            summary=f"Intrare jurnal creata: {req.title}",
            details={"id": entry_id, "mood": req.mood},
        )

        return {
            "status": "ok",
            "message": "Intrare adaugata in jurnal.",
            "id": entry_id,
        }

    except Exception as exc:
        logger.error("Eroare creare jurnal: %s", exc)
        raise HTTPException(500, f"Eroare creare intrare jurnal: {exc}")


@router.put("/journal/{entry_id}")
async def journal_update(entry_id: int, req: JournalEntryUpdate):
    """Actualizeaza o intrare din jurnal."""
    updates = []
    params: list[Any] = []

    if req.title is not None:
        updates.append("title = ?")
        params.append(req.title)
    if req.content is not None:
        updates.append("content = ?")
        params.append(req.content)
    if req.mood is not None:
        updates.append("mood = ?")
        params.append(req.mood)
    if req.tags is not None:
        updates.append("tags = ?")
        params.append(json.dumps(req.tags, ensure_ascii=False))

    if not updates:
        raise HTTPException(400, "Niciun camp de actualizat.")

    updates.append("updated_at = ?")
    params.append(datetime.now(timezone.utc).isoformat())
    params.append(entry_id)

    try:
        async with get_db() as db:
            cursor = await db.execute(
                f"UPDATE journal_entries SET {', '.join(updates)} WHERE id = ?",
                tuple(params),
            )
            await db.commit()

            if cursor.rowcount == 0:
                raise HTTPException(404, "Intrare negasita.")

        await log_activity(
            action="reports.journal.update",
            summary=f"Intrare jurnal actualizata: #{entry_id}",
        )

        return {"status": "ok", "message": "Intrare actualizata."}

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Eroare actualizare jurnal: %s", exc)
        raise HTTPException(500, f"Eroare actualizare jurnal: {exc}")


@router.delete("/journal/{entry_id}")
async def journal_delete(entry_id: int):
    """Sterge o intrare din jurnal."""
    try:
        async with get_db() as db:
            cursor = await db.execute(
                "DELETE FROM journal_entries WHERE id = ?", (entry_id,)
            )
            await db.commit()

            if cursor.rowcount == 0:
                raise HTTPException(404, "Intrare negasita.")

        await log_activity(
            action="reports.journal.delete",
            summary=f"Intrare jurnal stearsa: #{entry_id}",
        )

        return {"status": "ok", "message": "Intrare stearsa din jurnal."}

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Eroare stergere jurnal: %s", exc)
        raise HTTPException(500, f"Eroare stergere jurnal: {exc}")


# ===========================================================================
# BOOKMARKS
# ===========================================================================

@router.get("/bookmarks")
async def bookmarks_list(
    category: str = Query("", description="Filtreaza pe categorie"),
):
    """Listeaza toate bookmark-urile."""
    try:
        async with get_db() as db:
            if category:
                cursor = await db.execute(
                    "SELECT * FROM bookmarks WHERE category = ? ORDER BY created_at DESC",
                    (category,),
                )
            else:
                cursor = await db.execute(
                    "SELECT * FROM bookmarks ORDER BY created_at DESC"
                )
            rows = await cursor.fetchall()

            bookmarks = []
            for row in rows:
                bookmarks.append({
                    "id": row["id"],
                    "title": row["title"],
                    "url": row["url"],
                    "category": row["category"],
                    "description": row["description"],
                    "created_at": row["created_at"],
                })

        return {"bookmarks": bookmarks, "total": len(bookmarks)}

    except Exception as exc:
        logger.error("Eroare bookmarks list: %s", exc)
        raise HTTPException(500, f"Eroare citire bookmark-uri: {exc}")


@router.post("/bookmarks")
async def bookmarks_create(req: BookmarkCreate):
    """Adauga un bookmark nou."""
    now = datetime.now(timezone.utc).isoformat()

    try:
        async with get_db() as db:
            cursor = await db.execute(
                """INSERT INTO bookmarks (title, url, category, description, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (req.title, req.url, req.category, req.description, now),
            )
            await db.commit()
            bookmark_id = cursor.lastrowid

        await log_activity(
            action="reports.bookmark.create",
            summary=f"Bookmark adaugat: {req.title}",
            details={"id": bookmark_id, "url": req.url},
        )

        return {
            "status": "ok",
            "message": "Bookmark adaugat.",
            "id": bookmark_id,
        }

    except Exception as exc:
        logger.error("Eroare creare bookmark: %s", exc)
        raise HTTPException(500, f"Eroare creare bookmark: {exc}")


@router.put("/bookmarks/{bookmark_id}")
async def bookmarks_update(bookmark_id: int, req: BookmarkUpdate):
    """Actualizeaza un bookmark."""
    updates = []
    params: list[Any] = []

    if req.title is not None:
        updates.append("title = ?")
        params.append(req.title)
    if req.url is not None:
        updates.append("url = ?")
        params.append(req.url)
    if req.category is not None:
        updates.append("category = ?")
        params.append(req.category)
    if req.description is not None:
        updates.append("description = ?")
        params.append(req.description)

    if not updates:
        raise HTTPException(400, "Niciun camp de actualizat.")

    params.append(bookmark_id)

    try:
        async with get_db() as db:
            cursor = await db.execute(
                f"UPDATE bookmarks SET {', '.join(updates)} WHERE id = ?",
                tuple(params),
            )
            await db.commit()

            if cursor.rowcount == 0:
                raise HTTPException(404, "Bookmark negasit.")

        await log_activity(
            action="reports.bookmark.update",
            summary=f"Bookmark actualizat: #{bookmark_id}",
        )

        return {"status": "ok", "message": "Bookmark actualizat."}

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Eroare actualizare bookmark: %s", exc)
        raise HTTPException(500, f"Eroare actualizare bookmark: {exc}")


@router.delete("/bookmarks/{bookmark_id}")
async def bookmarks_delete(bookmark_id: int):
    """Sterge un bookmark."""
    try:
        async with get_db() as db:
            cursor = await db.execute(
                "DELETE FROM bookmarks WHERE id = ?", (bookmark_id,)
            )
            await db.commit()

            if cursor.rowcount == 0:
                raise HTTPException(404, "Bookmark negasit.")

        await log_activity(
            action="reports.bookmark.delete",
            summary=f"Bookmark sters: #{bookmark_id}",
        )

        return {"status": "ok", "message": "Bookmark sters."}

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Eroare stergere bookmark: %s", exc)
        raise HTTPException(500, f"Eroare stergere bookmark: {exc}")
