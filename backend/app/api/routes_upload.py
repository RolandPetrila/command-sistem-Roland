"""
Rute pentru încărcarea fișierelor (upload).

POST /api/upload — acceptă fișiere PDF și DOCX via multipart.
"""

import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File

from app.config import settings
from app.core.activity_log import log_activity
from app.db.database import get_db

router = APIRouter(prefix="/api", tags=["upload"])

ALLOWED_EXTENSIONS = {".pdf", ".docx"}
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Încarcă un fișier PDF sau DOCX.

    Validează tipul fișierului, salvează pe disc,
    creează intrarea în baza de date și returnează metadatele.
    """
    # --- Validare extensie ---
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Numele fișierului lipsește.",
        )

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Tip de fișier neacceptat: '{ext}'. "
                f"Sunt acceptate doar fișiere PDF (.pdf) și DOCX (.docx)."
            ),
        )

    # --- Validare content type (informativ, nu blocant) ---
    if file.content_type and file.content_type not in ALLOWED_CONTENT_TYPES:
        pass  # unele browsere trimit content type generic

    # --- Validare magic bytes ---
    MAGIC_BYTES = {
        ".pdf": b"%PDF",
        ".docx": b"PK",
    }
    first_bytes = await file.read(8)
    await file.seek(0)
    expected = MAGIC_BYTES.get(ext)
    if expected and not first_bytes.startswith(expected):
        raise HTTPException(
            status_code=400,
            detail=f"Fișier invalid: semnătura nu corespunde extensiei {ext}",
        )

    # --- Validare dimensiune ---
    content = await file.read()
    file_size = len(content)
    max_bytes = settings.max_upload_size_mb * 1024 * 1024

    if file_size > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=(
                f"Fișierul este prea mare ({file_size / (1024*1024):.1f} MB). "
                f"Limita maximă: {settings.max_upload_size_mb} MB."
            ),
        )

    if file_size == 0:
        raise HTTPException(
            status_code=400,
            detail="Fișierul este gol (0 bytes).",
        )

    # --- Salvare pe disc ---
    unique_prefix = uuid.uuid4().hex[:8]
    safe_filename = f"{unique_prefix}_{file.filename}"
    settings.ensure_dirs()
    save_path = settings.uploads_dir / safe_filename
    save_path.write_bytes(content)

    file_type = "pdf" if ext == ".pdf" else "docx"

    # --- Salvare în baza de date (tabela uploads) ---
    async with get_db() as db:
        cursor = await db.execute(
            """
            INSERT INTO uploads (filename, filepath, file_type, file_size)
            VALUES (?, ?, ?, ?)
            """,
            (file.filename, str(save_path), file_type, file_size),
        )
        await db.commit()
        upload_id = cursor.lastrowid

    log_activity(
        action="upload",
        summary=f"{file.filename} ({_format_size(file_size)}, {file_type})",
        details={"upload_id": upload_id, "filename": file.filename, "file_type": file_type, "file_size": file_size},
    )

    return {
        "upload_id": upload_id,
        "filename": file.filename,
        "file_type": file_type,
        "file_size": file_size,
        "file_size_display": _format_size(file_size),
        "message": f"Fișierul '{file.filename}' a fost încărcat cu succes.",
    }


def _format_size(size_bytes: int) -> str:
    """Formatează dimensiunea fișierului într-un format citibil."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
