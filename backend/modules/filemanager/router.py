"""
File Manager API — browse, preview, CRUD, upload, download, duplicate finder,
fulltext search, tags, favorites, auto-organize, batch operations, trash.

Endpoints:
  GET    /api/fm/browse               — list directory contents (with total_size, file_count, dir_count)
  GET    /api/fm/serve                — serve file for inline preview (PDF, images)
  GET    /api/fm/preview              — preview DOCX/TXT inline as text, redirect PDF/images to /serve
  GET    /api/fm/download             — serve file as download attachment
  POST   /api/fm/upload               — upload files to directory (MIME validation)
  POST   /api/fm/mkdir                — create directory
  POST   /api/fm/rename               — rename file/directory
  POST   /api/fm/move                 — move file/directory
  DELETE /api/fm/delete               — soft-delete file/directory (move to .trash)
  POST   /api/fm/batch                — batch delete/move/tag operations
  POST   /api/fm/batch-rename         — batch rename with prefix/suffix/replace
  POST   /api/fm/duplicates           — find duplicate files by hash
  GET    /api/fm/search/fulltext      — search file contents using FTS5 (recursive)
  POST   /api/fm/tags                 — add tag to file
  DELETE /api/fm/tags                 — remove tag from file
  GET    /api/fm/tags                 — list all tags with file count
  GET    /api/fm/tags/{tag}/files     — list files with specific tag
  POST   /api/fm/favorites            — toggle favorite on file
  GET    /api/fm/favorites            — list all favorited files
  POST   /api/fm/auto-organize        — auto-organize files by extension
  GET    /api/fm/trash                — list trashed files
  POST   /api/fm/trash/restore        — restore file from trash
  POST   /api/fm/trash/empty          — permanently delete all trash
  POST   /api/fm/trash/purge-old      — delete trash items older than 7 days
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import mimetypes
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

from typing import Literal, Optional

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, PlainTextResponse, RedirectResponse
from pydantic import BaseModel

from app.core.activity_log import log_activity
from app.db.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/fm", tags=["filemanager"])

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

IGNORED_DIRS = {
    "__pycache__", ".git", "node_modules", ".venv", "venv",
    ".mypy_cache", ".pytest_cache", ".ruff_cache", "dist", "build",
    ".next", ".nuxt", ".tox", "certs",
}

# Max file size for hashing in duplicate finder (50 MB)
_MAX_HASH_SIZE = 50 * 1024 * 1024

# Allowed upload extensions (whitelist)
_ALLOWED_UPLOAD_EXTENSIONS = {
    ".pdf", ".docx", ".doc", ".txt", ".csv", ".xlsx", ".xls",
    ".json", ".xml", ".png", ".jpg", ".jpeg", ".gif", ".webp",
    ".bmp", ".tiff", ".zip", ".md", ".html",
}

# Max preview file size (1 MB)
_MAX_PREVIEW_SIZE = 1 * 1024 * 1024

# Trash directory (inside project root)
_TRASH_DIR = _PROJECT_ROOT / ".trash"
_TRASH_MANIFEST = _TRASH_DIR / "manifest.json"
_TRASH_MAX_AGE_DAYS = 7


def _resolve(rel_path: str) -> Path:
    """Resolve relative path safely within project root."""
    clean = rel_path.replace("\\", "/").strip("/")
    # Check for symlink BEFORE resolving — .resolve() follows symlinks and would
    # return the target path, making is_symlink() always return False afterward.
    unresolved = _PROJECT_ROOT / clean
    if unresolved.is_symlink():
        raise HTTPException(403, "Acces interzis: symlink detectat")
    target = unresolved.resolve()

    try:
        target.relative_to(_PROJECT_ROOT.resolve())
    except ValueError:
        raise HTTPException(403, "Acces interzis: cale in afara directorului permis")

    return target


def _rel(absolute: Path) -> str:
    """Convert absolute path to relative (forward slashes)."""
    return str(absolute.relative_to(_PROJECT_ROOT.resolve())).replace("\\", "/")


def _file_info(entry: Path) -> dict:
    """Build file info dict."""
    stat = entry.stat()
    return {
        "name": entry.name,
        "type": "directory" if entry.is_dir() else "file",
        "path": _rel(entry),
        "extension": entry.suffix.lower() if entry.is_file() else None,
        "size": stat.st_size if entry.is_file() else None,
        "modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
    }


# ---------- Browse ----------

@router.get("/browse")
async def browse(
    path: str = Query("", description="Relative path"),
):
    target = _resolve(path)
    if not target.exists():
        raise HTTPException(404, f"Nu exista: {path}")
    if not target.is_dir():
        raise HTTPException(400, "Nu este director")

    entries = []
    total_size = 0
    file_count = 0
    dir_count = 0
    try:
        for entry in sorted(target.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower())):
            if entry.name.startswith("."):
                continue
            if entry.is_dir() and entry.name in IGNORED_DIRS:
                continue
            info = _file_info(entry)
            entries.append(info)
            if entry.is_file():
                file_count += 1
                total_size += info.get("size") or 0
            elif entry.is_dir():
                dir_count += 1
    except PermissionError:
        raise HTTPException(403, "Acces interzis la director")

    parent = _rel(target.parent) if target != _PROJECT_ROOT.resolve() else None

    return {
        "path": path or ".",
        "parent": parent,
        "entries": entries,
        "total_size": total_size,
        "file_count": file_count,
        "dir_count": dir_count,
    }


# ---------- Serve (inline preview) ----------

@router.get("/serve")
async def serve_file(path: str = Query(...)):
    target = _resolve(path)
    if not target.is_file():
        raise HTTPException(404, "Fisierul nu exista")

    mime = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
    return FileResponse(
        str(target),
        media_type=mime,
        headers={"Content-Disposition": f'inline; filename="{target.name}"'},
    )


# ---------- Preview (DOCX, TXT inline) ----------

@router.get("/preview")
async def preview_file(path: str = Query(..., description="Cale relativa catre fisier")):
    """Preview inline pentru TXT, DOCX. PDF si imagini redirecteaza la /serve."""
    target = _resolve(path)
    if not target.is_file():
        raise HTTPException(404, "Fisierul nu exista")

    ext = target.suffix.lower()

    # PDF and images — redirect to existing /serve endpoint
    if ext in {".pdf", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tiff", ".svg"}:
        return RedirectResponse(url=f"/api/fm/serve?path={path}", status_code=307)

    # Check file size limit (1 MB)
    if target.stat().st_size > _MAX_PREVIEW_SIZE:
        raise HTTPException(400, "Fisierul este prea mare pentru preview (max 1MB)")

    # TXT and similar text files
    if ext in {".txt", ".md", ".csv", ".log", ".json", ".xml", ".html", ".ini", ".cfg",
               ".yaml", ".yml", ".toml"}:
        try:
            content = target.read_text(encoding="utf-8", errors="replace")
        except (PermissionError, OSError) as e:
            raise HTTPException(500, f"Nu se poate citi fisierul: {e}")
        return PlainTextResponse(content)

    # DOCX — extract text from paragraphs using python-docx
    if ext == ".docx":
        try:
            from docx import Document
        except ImportError:
            raise HTTPException(500, "python-docx nu este instalat — nu se poate previzualiza DOCX")
        try:
            doc = Document(str(target))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            content = "\n\n".join(paragraphs)
            if not content:
                content = "(Document gol sau fara text extractibil)"
        except Exception as e:
            raise HTTPException(500, f"Eroare la citirea DOCX: {e}")
        return PlainTextResponse(content)

    # Unsupported type
    raise HTTPException(400, f"Tip de fisier nepermis pentru preview: {ext}")


# ---------- Download ----------

@router.get("/download")
async def download_file(path: str = Query(...)):
    target = _resolve(path)
    if not target.is_file():
        raise HTTPException(404, "Fisierul nu exista")

    mime = mimetypes.guess_type(target.name)[0] or "application/octet-stream"

    await log_activity(action="filemanager.download", summary=f"Download: {target.name}",
                       details={"path": path})

    return FileResponse(
        str(target),
        media_type=mime,
        filename=target.name,
    )


# ---------- Upload ----------

@router.post("/upload")
async def upload_files(
    files: list[UploadFile] = File(...),
    directory: str = Form(""),
):
    target_dir = _resolve(directory)
    if not target_dir.is_dir():
        raise HTTPException(400, f"Directorul nu exista: {directory}")

    uploaded = []
    for f in files:
        safe_name = Path(f.filename).name  # strip any path components
        file_ext = Path(safe_name).suffix.lower()
        if file_ext not in _ALLOWED_UPLOAD_EXTENSIONS:
            raise HTTPException(
                400,
                f"Tip de fisier nepermis: '{file_ext}' ({safe_name}). "
                f"Extensii permise: {', '.join(sorted(_ALLOWED_UPLOAD_EXTENSIONS))}",
            )
        dest = target_dir / safe_name

        # Don't overwrite without suffix
        if dest.exists():
            stem, ext = dest.stem, dest.suffix
            counter = 1
            while dest.exists():
                dest = target_dir / f"{stem}_{counter}{ext}"
                counter += 1

        content = await f.read()
        dest.write_bytes(content)
        uploaded.append({"name": dest.name, "path": _rel(dest), "size": len(content)})

    await log_activity(action="filemanager.upload", summary=f"Upload: {len(files)} fisiere in {directory or '/'}",
                       details={"directory": directory or "/", "files": [u["name"] for u in uploaded], "count": len(uploaded)})

    return {"uploaded": uploaded}


# ---------- Mkdir ----------

class MkdirRequest(BaseModel):
    path: str = ""
    name: str


@router.post("/mkdir")
async def make_directory(req: MkdirRequest):
    parent = _resolve(req.path)
    if not parent.is_dir():
        raise HTTPException(400, "Directorul parinte nu exista")

    new_dir = parent / req.name
    if new_dir.exists():
        raise HTTPException(409, f"Exista deja: {req.name}")

    new_dir.mkdir()
    await log_activity(action="filemanager.create_dir", summary=f"Mkdir: {req.name}",
                       details={"path": _rel(new_dir), "name": req.name})

    return {"created": _rel(new_dir)}


# ---------- Rename ----------

class RenameRequest(BaseModel):
    path: str
    new_name: str


@router.post("/rename")
async def rename_item(req: RenameRequest):
    target = _resolve(req.path)
    if not target.exists():
        raise HTTPException(404, "Nu exista")

    new_path = target.parent / req.new_name

    # On Windows, two names that differ only in case refer to the same filesystem
    # entry. Skip the collision check in that case and use a two-step rename to
    # allow case-only renames (e.g. file.txt → File.txt).
    case_only_rename = (
        os.path.normcase(str(target)) == os.path.normcase(str(new_path))
        and target.name != req.new_name
    )

    if not case_only_rename and new_path.exists():
        raise HTTPException(409, f"Exista deja: {req.new_name}")

    # Validate new path is still within project root
    _resolve(_rel(target.parent) + "/" + req.new_name)

    if case_only_rename:
        # Two-step rename to avoid Windows case-insensitive collision
        tmp_path = target.parent / (target.name + ".__tmp__")
        target.rename(tmp_path)
        tmp_path.rename(new_path)
    else:
        target.rename(new_path)
    old_name = target.name

    # Update FTS5 index: rename old path entry to new path
    async with get_db() as db:
        await db.execute(
            "UPDATE file_index SET file_path = ? WHERE file_path = ?",
            (_rel(new_path), req.path),
        )
        await db.commit()

    await log_activity(action="filemanager.rename", summary=f"Rename: {old_name} -> {req.new_name}",
                       details={"old_path": req.path, "new_path": _rel(new_path), "old_name": old_name, "new_name": req.new_name})

    return {"old": req.path, "new": _rel(new_path)}


# ---------- Move ----------

class MoveRequest(BaseModel):
    path: str
    destination: str


@router.post("/move")
async def move_item(req: MoveRequest):
    source = _resolve(req.path)
    if not source.exists():
        raise HTTPException(404, "Sursa nu exista")

    dest_dir = _resolve(req.destination)
    if not dest_dir.is_dir():
        raise HTTPException(400, "Destinatia nu este director")

    new_path = dest_dir / source.name
    if new_path.exists():
        raise HTTPException(409, f"Exista deja in destinatie: {source.name}")

    shutil.move(str(source), str(new_path))

    # Update FTS5 index: old path entry moves to new location
    async with get_db() as db:
        await db.execute(
            "UPDATE file_index SET file_path = ? WHERE file_path = ?",
            (_rel(new_path), req.path),
        )
        await db.commit()

    await log_activity(action="filemanager.move", summary=f"Move: {source.name} -> {req.destination}",
                       details={"old_path": req.path, "new_path": _rel(new_path), "name": source.name})

    return {"old": req.path, "new": _rel(new_path)}


# ---------- Delete ----------

async def _cascade_delete_db_entries(file_path: str) -> None:
    """Remove orphaned DB entries (tags, favorites, FTS) for a deleted file path."""
    async with get_db() as db:
        await db.execute("DELETE FROM file_tags WHERE file_path = ?", (file_path,))
        await db.execute("DELETE FROM file_favorites WHERE file_path = ?", (file_path,))
        await db.execute("DELETE FROM file_index WHERE file_path = ?", (file_path,))
        await db.commit()


async def _cascade_delete_dir_entries(dir_path: str) -> None:
    """Remove orphaned DB entries for all files under a deleted directory."""
    prefix = dir_path.rstrip("/") + "/"
    async with get_db() as db:
        await db.execute("DELETE FROM file_tags WHERE file_path LIKE ?", (prefix + "%",))
        await db.execute("DELETE FROM file_favorites WHERE file_path LIKE ?", (prefix + "%",))
        await db.execute("DELETE FROM file_index WHERE file_path LIKE ?", (prefix + "%",))
        await db.commit()


def _load_trash_manifest() -> list[dict]:
    """Load the trash manifest file."""
    if not _TRASH_MANIFEST.exists():
        return []
    try:
        return json.loads(_TRASH_MANIFEST.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def _save_trash_manifest(entries: list[dict]) -> None:
    """Save the trash manifest file."""
    _TRASH_DIR.mkdir(exist_ok=True)
    _TRASH_MANIFEST.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")


def _move_to_trash(target: Path, rel_path: str) -> dict:
    """Move a file/directory to .trash/ and return manifest entry."""
    _TRASH_DIR.mkdir(exist_ok=True)
    # Use timestamp to avoid name collisions in trash
    ts = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
    trash_name = f"{ts}__{target.name}"
    trash_dest = _TRASH_DIR / trash_name
    shutil.move(str(target), str(trash_dest))
    return {
        "filename": target.name,
        "trash_name": trash_name,
        "original_path": rel_path,
        "is_dir": target.is_dir() if target.exists() else trash_dest.is_dir(),
        "deleted_at": datetime.now(tz=timezone.utc).isoformat(),
    }


@router.delete("/delete")
async def delete_item(path: str = Query(...)):
    target = _resolve(path)
    if not target.exists():
        raise HTTPException(404, "Nu exista")

    # Don't allow deleting the project root or top-level important dirs
    if target == _PROJECT_ROOT.resolve():
        raise HTTPException(403, "Nu se poate sterge directorul radacina")

    name = target.name
    is_dir = target.is_dir()

    # Soft delete: move to .trash/
    entry = _move_to_trash(target, path)
    manifest = _load_trash_manifest()
    manifest.append(entry)
    _save_trash_manifest(manifest)

    # Cascade: clean up orphaned DB entries (tags, favorites, FTS)
    try:
        if is_dir:
            await _cascade_delete_dir_entries(path)
        else:
            await _cascade_delete_db_entries(path)
    except Exception as exc:
        logger.warning("Cascade delete DB cleanup failed for %s: %s", path, exc)

    await log_activity(action="filemanager.delete", summary=f"Delete (trash): {name}",
                       details={"path": path, "name": name})

    return {"deleted": path, "trash": True}


# ---------- Batch Operations ----------

class BatchRequest(BaseModel):
    action: Literal["delete", "move", "tag"]
    paths: list[str]
    destination: Optional[str] = None  # required for move
    tag: Optional[str] = None  # required for tag


@router.post("/batch")
async def batch_operations(req: BatchRequest):
    """Operatii in lot: delete, move sau tag pe mai multe fisiere."""
    if not req.paths:
        raise HTTPException(400, "Lista de cai este goala")

    if req.action == "move" and not req.destination:
        raise HTTPException(400, "Destinatia este obligatorie pentru actiunea 'move'")
    if req.action == "tag" and not req.tag:
        raise HTTPException(400, "Tag-ul este obligatoriu pentru actiunea 'tag'")

    success = []
    errors = []

    if req.action == "delete":
        manifest = _load_trash_manifest()
        for p in req.paths:
            try:
                target = _resolve(p)
                if not target.exists():
                    errors.append({"path": p, "error": "Nu exista"})
                    continue
                if target == _PROJECT_ROOT.resolve():
                    errors.append({"path": p, "error": "Nu se poate sterge directorul radacina"})
                    continue
                name = target.name
                is_dir = target.is_dir()
                # Soft delete: move to .trash/
                trash_entry = _move_to_trash(target, p)
                manifest.append(trash_entry)
                # Cascade: clean up orphaned DB entries
                try:
                    if is_dir:
                        await _cascade_delete_dir_entries(p)
                    else:
                        await _cascade_delete_db_entries(p)
                except Exception:
                    pass  # best-effort cleanup
                success.append({"path": p, "name": name})
            except Exception as e:
                errors.append({"path": p, "error": str(e)})
        _save_trash_manifest(manifest)

    elif req.action == "move":
        dest_dir = _resolve(req.destination)
        if not dest_dir.is_dir():
            raise HTTPException(400, f"Destinatia nu este director: {req.destination}")
        for p in req.paths:
            try:
                source = _resolve(p)
                if not source.exists():
                    errors.append({"path": p, "error": "Sursa nu exista"})
                    continue
                new_path = dest_dir / source.name
                if new_path.exists():
                    errors.append({"path": p, "error": f"Exista deja in destinatie: {source.name}"})
                    continue
                shutil.move(str(source), str(new_path))
                success.append({"path": p, "new_path": _rel(new_path), "name": source.name})
            except Exception as e:
                errors.append({"path": p, "error": str(e)})

    elif req.action == "tag":
        tag = req.tag.strip().lower()
        if not tag:
            raise HTTPException(400, "Tag-ul nu poate fi gol")
        async with get_db() as db:
            for p in req.paths:
                try:
                    target = _resolve(p)
                    if not target.exists():
                        errors.append({"path": p, "error": "Fisierul nu exista"})
                        continue
                    try:
                        await db.execute(
                            "INSERT INTO file_tags (file_path, tag) VALUES (?, ?)",
                            (p, tag),
                        )
                        success.append({"path": p, "tag": tag})
                    except Exception as e:
                        if "UNIQUE constraint" in str(e):
                            errors.append({"path": p, "error": f"Tag-ul '{tag}' exista deja"})
                        else:
                            errors.append({"path": p, "error": str(e)})
                except Exception as e:
                    errors.append({"path": p, "error": str(e)})
            await db.commit()

    await log_activity(
        action=f"filemanager.batch_{req.action}",
        summary=f"Batch {req.action}: {len(success)} reusit, {len(errors)} erori din {len(req.paths)} total",
        details={
            "action": req.action,
            "total": len(req.paths),
            "success_count": len(success),
            "error_count": len(errors),
        },
    )

    return {
        "success": success,
        "errors": errors,
        "total": len(req.paths),
    }


# ---------- Batch Rename ----------

class BatchRenameRequest(BaseModel):
    files: list[str]
    operation: Literal["prefix", "suffix", "replace"]
    value: str = ""
    replace_from: str = ""
    replace_to: str = ""
    path: str = ""


@router.post("/batch-rename")
async def batch_rename(req: BatchRenameRequest):
    """Batch rename files with prefix, suffix, or find & replace."""
    if not req.files:
        raise HTTPException(400, "Lista de fisiere este goala")

    if req.operation in ("prefix", "suffix") and not req.value:
        raise HTTPException(400, "Valoarea este obligatorie pentru prefix/suffix")
    if req.operation == "replace" and not req.replace_from:
        raise HTTPException(400, "'replace_from' este obligatoriu pentru operatia replace")

    renamed = []
    errors = []

    # Pre-compute all new names first to check for conflicts
    planned: list[tuple[Path, str]] = []
    for fname in req.files:
        # Validate: no path separators in filename
        if "/" in fname or "\\" in fname:
            errors.append({"old_name": fname, "error": "Numele nu trebuie sa contina separatori de cale"})
            continue

        file_path = _resolve(f"{req.path}/{fname}" if req.path else fname)
        if not file_path.exists():
            errors.append({"old_name": fname, "error": "Fisierul nu exista"})
            continue

        stem = file_path.stem
        ext = file_path.suffix

        if req.operation == "prefix":
            new_name = f"{req.value}{fname}"
        elif req.operation == "suffix":
            new_name = f"{stem}{req.value}{ext}"
        elif req.operation == "replace":
            new_name = fname.replace(req.replace_from, req.replace_to)
        else:
            new_name = fname

        if new_name == fname:
            errors.append({"old_name": fname, "error": "Nicio modificare"})
            continue

        # Validate new name doesn't have path separators
        if "/" in new_name or "\\" in new_name:
            errors.append({"old_name": fname, "error": "Noul nume nu poate contine separatori de cale"})
            continue

        planned.append((file_path, new_name))

    # Check for conflicts among planned renames and existing files
    new_names_set: set[str] = set()
    for file_path, new_name in planned:
        dest = file_path.parent / new_name
        if new_name.lower() in new_names_set:
            errors.append({"old_name": file_path.name, "error": f"Conflict: '{new_name}' apare de mai multe ori"})
            continue
        if dest.exists() and dest != file_path:
            errors.append({"old_name": file_path.name, "error": f"Exista deja: {new_name}"})
            continue
        new_names_set.add(new_name.lower())

    # Now perform the renames (only for entries not in errors)
    error_names = {e["old_name"] for e in errors}
    for file_path, new_name in planned:
        if file_path.name in error_names:
            continue
        try:
            dest = file_path.parent / new_name
            file_path.rename(dest)
            renamed.append({"old_name": file_path.name, "new_name": new_name})
        except Exception as e:
            errors.append({"old_name": file_path.name, "error": str(e)})

    await log_activity(
        action="filemanager.batch_rename",
        summary=f"Batch rename ({req.operation}): {len(renamed)} redenumit, {len(errors)} erori",
        details={
            "operation": req.operation,
            "total": len(req.files),
            "renamed_count": len(renamed),
            "error_count": len(errors),
        },
    )

    return {"renamed": renamed, "errors": errors}


# ---------- Trash ----------

@router.get("/trash")
async def list_trash():
    """List files in trash with deletion dates and total size."""
    manifest = _load_trash_manifest()
    items = []
    total_size = 0
    for entry in manifest:
        trash_path = _TRASH_DIR / entry["trash_name"]
        if trash_path.exists():
            size = trash_path.stat().st_size if trash_path.is_file() else sum(
                f.stat().st_size for f in trash_path.rglob("*") if f.is_file()
            )
            total_size += size
            items.append({
                "filename": entry["filename"],
                "trash_name": entry["trash_name"],
                "original_path": entry["original_path"],
                "is_dir": entry.get("is_dir", False),
                "deleted_at": entry["deleted_at"],
                "size": size,
            })
    # Purge old entries automatically
    await _purge_old_trash_entries()
    return {"items": items, "count": len(items), "total_size": total_size}


class TrashRestoreRequest(BaseModel):
    trash_name: str


@router.post("/trash/restore")
async def restore_from_trash(req: TrashRestoreRequest):
    """Restore a file from trash to its original location."""
    manifest = _load_trash_manifest()
    entry = next((e for e in manifest if e["trash_name"] == req.trash_name), None)
    if not entry:
        raise HTTPException(404, "Fisierul nu a fost gasit in cos")

    trash_path = _TRASH_DIR / entry["trash_name"]
    if not trash_path.exists():
        # Remove stale entry from manifest
        manifest = [e for e in manifest if e["trash_name"] != req.trash_name]
        _save_trash_manifest(manifest)
        raise HTTPException(404, "Fisierul nu mai exista in cos")

    # Restore to original location
    original = _PROJECT_ROOT / entry["original_path"].replace("\\", "/").strip("/")
    # Ensure parent directory exists
    original.parent.mkdir(parents=True, exist_ok=True)
    if original.exists():
        raise HTTPException(409, f"Fisierul exista deja la locatia originala: {entry['original_path']}")

    shutil.move(str(trash_path), str(original))

    # Remove from manifest
    manifest = [e for e in manifest if e["trash_name"] != req.trash_name]
    _save_trash_manifest(manifest)

    await log_activity(
        action="filemanager.trash_restore",
        summary=f"Restaurat din cos: {entry['filename']}",
        details={"filename": entry["filename"], "original_path": entry["original_path"]},
    )

    return {"restored": entry["filename"], "path": entry["original_path"]}


@router.post("/trash/empty")
async def empty_trash():
    """Permanently delete all files in trash."""
    manifest = _load_trash_manifest()
    deleted_count = 0
    for entry in manifest:
        trash_path = _TRASH_DIR / entry["trash_name"]
        if trash_path.exists():
            if trash_path.is_dir():
                shutil.rmtree(trash_path)
            else:
                trash_path.unlink()
            deleted_count += 1

    _save_trash_manifest([])

    await log_activity(
        action="filemanager.trash_empty",
        summary=f"Cos golit: {deleted_count} fisiere sterse permanent",
        details={"count": deleted_count},
    )

    return {"deleted_count": deleted_count}


async def _purge_old_trash_entries() -> int:
    """Remove trash entries older than 7 days. Returns count purged."""
    manifest = _load_trash_manifest()
    now = datetime.now(tz=timezone.utc)
    keep = []
    purged = 0
    for entry in manifest:
        try:
            deleted_at = datetime.fromisoformat(entry["deleted_at"])
            age_days = (now - deleted_at).days
        except (KeyError, ValueError):
            age_days = _TRASH_MAX_AGE_DAYS + 1  # invalid entry -> purge

        if age_days > _TRASH_MAX_AGE_DAYS:
            trash_path = _TRASH_DIR / entry["trash_name"]
            if trash_path.exists():
                if trash_path.is_dir():
                    shutil.rmtree(trash_path)
                else:
                    trash_path.unlink()
            purged += 1
        else:
            keep.append(entry)

    if purged > 0:
        _save_trash_manifest(keep)
    return purged


@router.post("/trash/purge-old")
async def purge_old_trash():
    """Delete trash items older than 7 days."""
    purged = await _purge_old_trash_entries()

    if purged > 0:
        await log_activity(
            action="filemanager.trash_purge",
            summary=f"Purge cos: {purged} fisiere vechi sterse",
            details={"purged": purged, "max_age_days": _TRASH_MAX_AGE_DAYS},
        )

    return {"purged": purged, "max_age_days": _TRASH_MAX_AGE_DAYS}


# ---------- Duplicate Finder ----------

class DuplicateRequest(BaseModel):
    path: str = ""


@router.post("/duplicates")
async def find_duplicates(req: DuplicateRequest):
    target = _resolve(req.path)
    if not target.is_dir():
        raise HTTPException(400, "Trebuie sa fie director")

    def _scan(directory: Path) -> list[dict]:
        hashes: dict[str, list[dict]] = {}

        for entry in directory.rglob("*"):
            if not entry.is_file():
                continue
            if entry.stat().st_size > _MAX_HASH_SIZE:
                continue
            if any(part in IGNORED_DIRS for part in entry.parts):
                continue
            if entry.name.startswith("."):
                continue

            try:
                h = hashlib.md5(entry.read_bytes()).hexdigest()
                info = {
                    "name": entry.name,
                    "path": _rel(entry),
                    "size": entry.stat().st_size,
                }
                hashes.setdefault(h, []).append(info)
            except (PermissionError, OSError):
                continue

        # Only groups with duplicates
        groups = []
        for h, files in hashes.items():
            if len(files) > 1:
                groups.append({
                    "hash": h,
                    "size": files[0]["size"],
                    "count": len(files),
                    "files": files,
                })
        groups.sort(key=lambda g: g["size"], reverse=True)
        return groups

    try:
        groups = await asyncio.to_thread(_scan, target)
    except Exception as e:
        raise HTTPException(500, f"Scanare esuata: {e}")

    total_waste = sum(g["size"] * (g["count"] - 1) for g in groups)

    await log_activity(action="filemanager.duplicates", summary=f"Duplicates: {len(groups)} grupuri gasite in {req.path or '/'}",
                       details={"path": req.path or "/", "groups": len(groups),
                                "wasted_bytes": total_waste})

    return {"groups": groups, "total_wasted": total_waste}


# ---------- Fulltext Search (FTS5) ----------

# Extensions that can be indexed for fulltext search
_INDEXABLE_EXTENSIONS = {
    ".txt", ".md", ".csv", ".html", ".xml", ".json", ".py", ".js",
    ".jsx", ".ts", ".tsx", ".css", ".sql", ".yml", ".yaml", ".toml",
    ".ini", ".cfg", ".log", ".bat", ".sh", ".env.example",
}

_MAX_INDEX_SIZE = 5 * 1024 * 1024  # 5 MB max for indexing


async def _index_file(file_path: Path) -> bool:
    """Index a single text file into FTS5. Returns True if indexed."""
    if file_path.suffix.lower() not in _INDEXABLE_EXTENSIONS:
        return False
    if not file_path.is_file():
        return False
    if file_path.stat().st_size > _MAX_INDEX_SIZE:
        return False

    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
    except (PermissionError, OSError):
        return False

    rel_path = _rel(file_path)

    async with get_db() as db:
        # Remove old entry if exists
        await db.execute("DELETE FROM file_index WHERE file_path = ?", (rel_path,))
        # Insert new
        await db.execute(
            "INSERT INTO file_index (file_path, content) VALUES (?, ?)",
            (rel_path, content),
        )
        await db.commit()

    return True


@router.get("/search/fulltext")
async def fulltext_search(
    q: str = Query(..., min_length=2, description="Termen de cautare"),
    path: str = Query("", description="Cale relativa (optional, limiteaza cautarea)"),
    limit: int = Query(50, ge=1, le=200),
    max_files: int = Query(500, ge=1, le=5000, description="Numar maxim de fisiere de indexat"),
):
    """Cautare fulltext in continutul fisierelor (FTS5) — recursiv prin subdirectoare."""
    # First, index files in the target directory if not already indexed
    target = _resolve(path)
    if not target.is_dir():
        raise HTTPException(400, "Calea trebuie sa fie un director")

    # Index files recursively through subdirectories, skip IGNORED_DIRS
    indexed_count = 0
    scanned_count = 0
    for entry in target.rglob("*"):
        if scanned_count >= max_files:
            break
        # Skip files inside ignored directories
        if any(part in IGNORED_DIRS for part in entry.parts):
            continue
        if entry.is_file() and entry.suffix.lower() in _INDEXABLE_EXTENSIONS:
            scanned_count += 1
            if await _index_file(entry):
                indexed_count += 1

    # Search using FTS5
    async with get_db() as db:
        if path:
            # Filter results by path prefix
            cursor = await db.execute(
                """
                SELECT file_path, highlight(file_index, 1, '<mark>', '</mark>') as snippet,
                       rank
                FROM file_index
                WHERE file_index MATCH ?
                  AND file_path LIKE ?
                ORDER BY rank
                LIMIT ?
                """,
                (q, f"{path}%", limit),
            )
        else:
            cursor = await db.execute(
                """
                SELECT file_path, highlight(file_index, 1, '<mark>', '</mark>') as snippet,
                       rank
                FROM file_index
                WHERE file_index MATCH ?
                ORDER BY rank
                LIMIT ?
                """,
                (q, limit),
            )

        rows = [dict(r) for r in await cursor.fetchall()]

    # Truncate snippets to reasonable length
    for row in rows:
        if row.get("snippet") and len(row["snippet"]) > 500:
            # Find a window around the first <mark>
            mark_pos = row["snippet"].find("<mark>")
            if mark_pos > 200:
                row["snippet"] = "..." + row["snippet"][mark_pos - 100:]
            if len(row["snippet"]) > 500:
                row["snippet"] = row["snippet"][:500] + "..."

    await log_activity(
        action="filemanager.fulltext_search",
        summary=f"Cautare fulltext: '{q}' — {len(rows)} rezultate",
        details={"query": q, "path": path or "/", "results": len(rows), "indexed": indexed_count},
    )

    return {"query": q, "results": rows, "count": len(rows), "indexed_now": indexed_count}


# ---------- Tags ----------

class TagRequest(BaseModel):
    file_path: str
    tag: str


class TagDeleteRequest(BaseModel):
    file_path: str
    tag: str


@router.post("/tags")
async def add_tag(req: TagRequest):
    """Adauga un tag la un fisier."""
    # Validate the file exists
    target = _resolve(req.file_path)
    if not target.exists():
        raise HTTPException(404, f"Fisierul nu exista: {req.file_path}")

    tag = req.tag.strip().lower()
    if not tag:
        raise HTTPException(400, "Tag-ul nu poate fi gol")

    async with get_db() as db:
        try:
            await db.execute(
                "INSERT INTO file_tags (file_path, tag) VALUES (?, ?)",
                (req.file_path, tag),
            )
            await db.commit()
        except Exception as e:
            if "UNIQUE constraint" in str(e):
                raise HTTPException(409, f"Tag-ul '{tag}' exista deja pe acest fisier")
            raise

    await log_activity(
        action="filemanager.tag_add",
        summary=f"Tag adaugat: '{tag}' pe {Path(req.file_path).name}",
        details={"file_path": req.file_path, "tag": tag},
    )

    return {"status": "adaugat", "file_path": req.file_path, "tag": tag}


@router.delete("/tags")
async def remove_tag(req: TagDeleteRequest):
    """Sterge un tag de pe un fisier."""
    tag = req.tag.strip().lower()

    async with get_db() as db:
        cursor = await db.execute(
            "DELETE FROM file_tags WHERE file_path = ? AND tag = ?",
            (req.file_path, tag),
        )
        await db.commit()

        if cursor.rowcount == 0:
            raise HTTPException(404, "Tag-ul nu a fost gasit pe acest fisier")

    await log_activity(
        action="filemanager.tag_remove",
        summary=f"Tag sters: '{tag}' de pe {Path(req.file_path).name}",
        details={"file_path": req.file_path, "tag": tag},
    )

    return {"status": "sters", "file_path": req.file_path, "tag": tag}


@router.get("/tags")
async def list_tags():
    """Lista toate tag-urile cu numarul de fisiere."""
    async with get_db() as db:
        cursor = await db.execute(
            """
            SELECT tag, COUNT(*) as file_count
            FROM file_tags
            GROUP BY tag
            ORDER BY file_count DESC, tag ASC
            """
        )
        rows = [dict(r) for r in await cursor.fetchall()]

    return {"tags": rows, "total": len(rows)}


@router.get("/tags/{tag}/files")
async def list_files_by_tag(tag: str):
    """Lista fisierele cu un anumit tag."""
    tag = tag.strip().lower()

    async with get_db() as db:
        cursor = await db.execute(
            "SELECT file_path, created_at FROM file_tags WHERE tag = ? ORDER BY created_at DESC",
            (tag,),
        )
        rows = [dict(r) for r in await cursor.fetchall()]

    # Enrich with file info where possible
    files = []
    for row in rows:
        try:
            target = _resolve(row["file_path"])
            if target.exists():
                info = _file_info(target)
                info["tagged_at"] = row["created_at"]
                files.append(info)
            else:
                files.append({
                    "path": row["file_path"],
                    "name": Path(row["file_path"]).name,
                    "exists": False,
                    "tagged_at": row["created_at"],
                })
        except Exception:
            files.append({
                "path": row["file_path"],
                "name": Path(row["file_path"]).name,
                "exists": False,
                "tagged_at": row["created_at"],
            })

    return {"tag": tag, "files": files, "count": len(files)}


# ---------- Favorites ----------

class FavoriteRequest(BaseModel):
    file_path: str


@router.post("/favorites")
async def toggle_favorite(req: FavoriteRequest):
    """Adauga sau sterge un fisier din favorite (toggle)."""
    target = _resolve(req.file_path)
    if not target.exists():
        raise HTTPException(404, f"Fisierul nu exista: {req.file_path}")

    async with get_db() as db:
        cursor = await db.execute(
            "SELECT id FROM file_favorites WHERE file_path = ?",
            (req.file_path,),
        )
        existing = await cursor.fetchone()

        if existing:
            await db.execute(
                "DELETE FROM file_favorites WHERE file_path = ?",
                (req.file_path,),
            )
            await db.commit()
            action = "sters_din_favorite"
        else:
            await db.execute(
                "INSERT INTO file_favorites (file_path) VALUES (?)",
                (req.file_path,),
            )
            await db.commit()
            action = "adaugat_la_favorite"

    await log_activity(
        action=f"filemanager.favorite_{action}",
        summary=f"Favorite: {target.name} — {action.replace('_', ' ')}",
        details={"file_path": req.file_path, "action": action},
    )

    return {"status": action, "file_path": req.file_path, "is_favorite": action == "adaugat_la_favorite"}


@router.get("/favorites")
async def list_favorites():
    """Lista tuturor fisierelor favorite."""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT file_path, created_at FROM file_favorites ORDER BY created_at DESC"
        )
        rows = [dict(r) for r in await cursor.fetchall()]

    files = []
    for row in rows:
        try:
            target = _resolve(row["file_path"])
            if target.exists():
                info = _file_info(target)
                info["favorited_at"] = row["created_at"]
                files.append(info)
            else:
                files.append({
                    "path": row["file_path"],
                    "name": Path(row["file_path"]).name,
                    "exists": False,
                    "favorited_at": row["created_at"],
                })
        except Exception:
            files.append({
                "path": row["file_path"],
                "name": Path(row["file_path"]).name,
                "exists": False,
                "favorited_at": row["created_at"],
            })

    return {"favorites": files, "count": len(files)}


# ---------- Auto-organize ----------

class AutoOrganizeRequest(BaseModel):
    path: str = ""
    dry_run: bool = False


@router.post("/auto-organize")
async def auto_organize(req: AutoOrganizeRequest):
    """Organizeaza automat fisierele dintr-un folder pe subfoldere dupa extensie."""
    target = _resolve(req.path)
    if not target.is_dir():
        raise HTTPException(400, "Calea trebuie sa fie un director")

    # Don't allow organizing the project root
    if target == _PROJECT_ROOT.resolve():
        raise HTTPException(403, "Nu se poate organiza directorul radacina al proiectului")

    moves = []
    errors = []

    for entry in target.iterdir():
        if not entry.is_file():
            continue
        if entry.name.startswith("."):
            continue

        ext = entry.suffix.lower().lstrip(".")
        if not ext:
            ext = "fara_extensie"

        subfolder = target / ext
        dest = subfolder / entry.name

        if req.dry_run:
            moves.append({
                "file": entry.name,
                "from": _rel(entry),
                "to": f"{_rel(target)}/{ext}/{entry.name}",
                "extension": ext,
            })
        else:
            try:
                subfolder.mkdir(exist_ok=True)
                if dest.exists():
                    # Add counter to avoid overwrite
                    stem, suffix = dest.stem, dest.suffix
                    counter = 1
                    while dest.exists():
                        dest = subfolder / f"{stem}_{counter}{suffix}"
                        counter += 1
                shutil.move(str(entry), str(dest))
                moves.append({
                    "file": entry.name,
                    "from": _rel(entry) if entry.exists() else str(entry),
                    "to": _rel(dest),
                    "extension": ext,
                })
            except Exception as e:
                errors.append({"file": entry.name, "error": str(e)})

    if not req.dry_run and moves:
        await log_activity(
            action="filemanager.auto_organize",
            summary=f"Auto-organizare: {len(moves)} fisiere mutate in {req.path or '/'}",
            details={
                "path": req.path or "/",
                "moved_count": len(moves),
                "error_count": len(errors),
                "extensions": list({m["extension"] for m in moves}),
            },
        )

    return {
        "dry_run": req.dry_run,
        "moved": moves,
        "errors": errors,
        "total_moved": len(moves),
        "total_errors": len(errors),
    }
