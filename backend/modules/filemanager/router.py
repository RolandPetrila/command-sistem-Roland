"""
File Manager API — browse, preview, CRUD, upload, download, duplicate finder.

Endpoints:
  GET    /api/fm/browse           — list directory contents
  GET    /api/fm/serve            — serve file for inline preview (PDF, images)
  GET    /api/fm/download         — serve file as download attachment
  POST   /api/fm/upload           — upload files to directory
  POST   /api/fm/mkdir            — create directory
  POST   /api/fm/rename           — rename file/directory
  POST   /api/fm/move             — move file/directory
  DELETE /api/fm/delete           — delete file/directory
  POST   /api/fm/duplicates       — find duplicate files by hash
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import mimetypes
import shutil
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.core.activity_log import log_activity

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


def _resolve(rel_path: str) -> Path:
    """Resolve relative path safely within project root."""
    clean = rel_path.replace("\\", "/").strip("/")
    target = (_PROJECT_ROOT / clean).resolve()

    if target.is_symlink():
        raise HTTPException(403, "Acces interzis: symlink detectat")

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
    try:
        for entry in sorted(target.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower())):
            if entry.name.startswith("."):
                continue
            if entry.is_dir() and entry.name in IGNORED_DIRS:
                continue
            entries.append(_file_info(entry))
    except PermissionError:
        raise HTTPException(403, "Acces interzis la director")

    parent = _rel(target.parent) if target != _PROJECT_ROOT.resolve() else None

    return {
        "path": path or ".",
        "parent": parent,
        "entries": entries,
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


# ---------- Download ----------

@router.get("/download")
async def download_file(path: str = Query(...)):
    target = _resolve(path)
    if not target.is_file():
        raise HTTPException(404, "Fisierul nu exista")

    mime = mimetypes.guess_type(target.name)[0] or "application/octet-stream"

    await log_activity(action="filemanager", summary=f"Download: {target.name}",
                       details={"type": "download", "path": path})

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

    await log_activity(action="filemanager", summary=f"Upload: {len(files)} fisiere in {directory or '/'}",
                       details={"type": "upload", "files": [u["name"] for u in uploaded]})

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
    await log_activity(action="filemanager", summary=f"Mkdir: {req.name}",
                       details={"type": "mkdir", "path": _rel(new_dir)})

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
    if new_path.exists():
        raise HTTPException(409, f"Exista deja: {req.new_name}")

    # Validate new path is still within project root
    _resolve(_rel(target.parent) + "/" + req.new_name)

    target.rename(new_path)
    old_name = target.name

    await log_activity(action="filemanager", summary=f"Rename: {old_name} -> {req.new_name}",
                       details={"type": "rename", "old": req.path, "new": _rel(new_path)})

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

    await log_activity(action="filemanager", summary=f"Move: {source.name} -> {req.destination}",
                       details={"type": "move", "old": req.path, "new": _rel(new_path)})

    return {"old": req.path, "new": _rel(new_path)}


# ---------- Delete ----------

@router.delete("/delete")
async def delete_item(path: str = Query(...)):
    target = _resolve(path)
    if not target.exists():
        raise HTTPException(404, "Nu exista")

    # Don't allow deleting the project root or top-level important dirs
    if target == _PROJECT_ROOT.resolve():
        raise HTTPException(403, "Nu se poate sterge directorul radacina")

    name = target.name
    if target.is_dir():
        shutil.rmtree(target)
    else:
        target.unlink()

    await log_activity(action="filemanager", summary=f"Delete: {name}",
                       details={"type": "delete", "path": path})

    return {"deleted": path}


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

    await log_activity(action="filemanager", summary=f"Duplicates: {len(groups)} grupuri gasite",
                       details={"type": "duplicates", "path": req.path, "groups": len(groups),
                                "wasted_bytes": total_waste})

    return {"groups": groups, "total_wasted": total_waste}
