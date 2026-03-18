"""
API endpoints pentru Notepad — note rapide cu auto-save.

Endpoints:
  GET    /api/notes          — lista note (id, title, preview, updated_at)
  GET    /api/notes/:id      — notă completă
  POST   /api/notes          — creează notă nouă
  PUT    /api/notes/:id      — actualizează titlu/conținut
  DELETE /api/notes/:id      — șterge notă
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.db.database import get_db

router = APIRouter(prefix="/api", tags=["notepad"])


class NoteCreate(BaseModel):
    title: str = "Notă nouă"
    content: str = ""


class NoteUpdate(BaseModel):
    title: str | None = None
    content: str | None = None


@router.get("/notes")
async def list_notes():
    """Returnează toate notele (id, title, preview, updated_at)."""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT id, title, substr(content, 1, 100) as preview, updated_at "
            "FROM notes ORDER BY updated_at DESC"
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
    async with get_db() as db:
        cursor = await db.execute(
            "INSERT INTO notes (title, content) VALUES (?, ?)",
            (note.title, note.content),
        )
        await db.commit()
        return {"id": cursor.lastrowid, "title": note.title}


@router.put("/notes/{note_id}")
async def update_note(note_id: int, note: NoteUpdate):
    """Actualizează titlul și/sau conținutul unei note."""
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
        if not updates:
            raise HTTPException(400, "Nimic de actualizat")

        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(note_id)

        await db.execute(
            f"UPDATE notes SET {', '.join(updates)} WHERE id = ?",
            params,
        )
        await db.commit()
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
        return {"status": "deleted", "id": note_id}
