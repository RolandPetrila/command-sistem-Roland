"""
API endpoints pentru Notepad — note rapide cu auto-save.

Endpoints:
  GET    /api/notes              — lista note (id, title, preview, updated_at) + filtru category
  GET    /api/notes/search       — cautare in titlu si continut
  GET    /api/notes/export       — export toate notele ca JSON (backup)
  GET    /api/notes/:id          — notă completă
  POST   /api/notes              — creează notă nouă (cu category)
  PUT    /api/notes/:id          — actualizează titlu/conținut/category
  DELETE /api/notes/:id          — șterge notă
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.core.activity_log import log_activity
from app.db.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["notepad"])

# ---------------------------------------------------------------------------
# Category column migration — adds column pragmatically if missing
# ---------------------------------------------------------------------------
_category_col_ensured = False


async def _ensure_category_column():
    """Add 'category' column to notes table if it does not exist yet."""
    global _category_col_ensured
    if _category_col_ensured:
        return
    async with get_db() as db:
        cursor = await db.execute("PRAGMA table_info(notes)")
        columns = [row[1] for row in await cursor.fetchall()]
        if "category" not in columns:
            await db.execute(
                "ALTER TABLE notes ADD COLUMN category TEXT NOT NULL DEFAULT 'general'"
            )
            await db.commit()
            logger.info("Coloana 'category' adaugata la tabela 'notes'")
    _category_col_ensured = True


class NoteCreate(BaseModel):
    title: str = "Notă nouă"
    content: str = ""
    category: str = "general"


class NoteUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    category: str | None = None


@router.get("/notes")
async def list_notes(category: str | None = Query(None, description="Filtru dupa categorie")):
    """Returnează toate notele (id, title, preview, category, updated_at)."""
    await _ensure_category_column()
    async with get_db() as db:
        if category:
            cursor = await db.execute(
                "SELECT id, title, substr(content, 1, 100) as preview, category, updated_at "
                "FROM notes WHERE category = ? ORDER BY updated_at DESC",
                (category,),
            )
        else:
            cursor = await db.execute(
                "SELECT id, title, substr(content, 1, 100) as preview, category, updated_at "
                "FROM notes ORDER BY updated_at DESC"
            )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


@router.get("/notes/search")
async def search_notes(q: str = Query(..., min_length=1, description="Termen de cautare")):
    """Cautare in titlu si continut note."""
    await _ensure_category_column()
    pattern = f"%{q}%"
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT id, title, substr(content, 1, 100) as preview, category, updated_at "
            "FROM notes WHERE title LIKE ? OR content LIKE ? "
            "ORDER BY updated_at DESC",
            (pattern, pattern),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


@router.get("/notes/export")
async def export_notes():
    """Export toate notele ca JSON (pentru backup)."""
    await _ensure_category_column()
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT id, title, content, category, created_at, updated_at "
            "FROM notes ORDER BY id"
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


@router.get("/notes/{note_id}")
async def get_note(note_id: int):
    """Returnează o notă completă."""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM notes WHERE id = ?", (note_id,)
        )
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(404, "Nota nu a fost găsită")
        return dict(row)


@router.post("/notes")
async def create_note(note: NoteCreate):
    """Creează o notă nouă."""
    await _ensure_category_column()
    async with get_db() as db:
        cursor = await db.execute(
            "INSERT INTO notes (title, content, category) VALUES (?, ?, ?)",
            (note.title, note.content, note.category),
        )
        await db.commit()
        note_id = cursor.lastrowid

    await log_activity(
        action="notepad_create",
        summary=f"Notă creată: {note.title}",
        details={"note_id": note_id, "category": note.category},
    )
    return {"id": note_id, "title": note.title, "category": note.category}


@router.put("/notes/{note_id}")
async def update_note(note_id: int, note: NoteUpdate):
    """Actualizează titlul și/sau conținutul unei note."""
    await _ensure_category_column()
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT id FROM notes WHERE id = ?", (note_id,)
        )
        if not await cursor.fetchone():
            raise HTTPException(404, "Nota nu a fost găsită")

        updates = []
        params = []
        if note.title is not None:
            updates.append("title = ?")
            params.append(note.title)
        if note.content is not None:
            updates.append("content = ?")
            params.append(note.content)
        if note.category is not None:
            updates.append("category = ?")
            params.append(note.category)
        if not updates:
            raise HTTPException(400, "Nimic de actualizat")

        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(note_id)

        await db.execute(
            f"UPDATE notes SET {', '.join(updates)} WHERE id = ?",
            params,
        )
        await db.commit()

    await log_activity(
        action="notepad_update",
        summary=f"Nota #{note_id} actualizata",
        details={"note_id": note_id},
    )
    return {"status": "updated", "id": note_id}


@router.delete("/notes/{note_id}")
async def delete_note(note_id: int):
    """Șterge o notă."""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT id FROM notes WHERE id = ?", (note_id,)
        )
        if not await cursor.fetchone():
            raise HTTPException(404, "Nota nu a fost găsită")

        await db.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        await db.commit()

    await log_activity(
        action="notepad_delete",
        summary=f"Notă #{note_id} ștearsă",
        details={"note_id": note_id},
    )
    return {"status": "deleted", "id": note_id}
