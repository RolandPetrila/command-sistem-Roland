"""
File Manager API — browse, preview, CRUD, upload, download, duplicate finder,
fulltext search, tags, favorites, auto-organize.

Endpoints:
  GET    /api/fm/browse               — list directory contents
  GET    /api/fm/serve                — serve file for inline preview (PDF, images)
  GET    /api/fm/download             — serve file as download attachment
  POST   /api/fm/upload               — upload files to directory
  POST   /api/fm/mkdir                — create directory
  POST   /api/fm/rename               — rename file/directory
  POST   /api/fm/move                 — move file/directory
  DELETE /api/fm/delete               — delete file/directory
  POST   /api/fm/duplicates           — find duplicate files by hash
  GET    /api/fm/search/fulltext      — search file contents using FTS5
  POST   /api/fm/tags                 — add tag to file
  DELETE /api/fm/tags                 — remove tag from file
  GET    /api/fm/tags                 — list all tags with file count
  GET    /api/fm/tags/{tag}/files     — list files with specific tag
  POST   /api/fm/favorites            — toggle favorite on file
  GET    /api/fm/favorites            — list all favorited files
  POST   /api/fm/auto-organize        — auto-organize files by extension
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
    if new_path.exists():
        raise HTTPException(409, f"Exista deja: {req.new_name}")

    # Validate new path is still within project root
    _resolve(_rel(target.parent) + "/" + req.new_name)

    target.rename(new_path)
    old_name = target.name

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

    await log_activity(action="filemanager.move", summary=f"Move: {source.name} -> {req.destination}",
                       details={"old_path": req.path, "new_path": _rel(new_path), "name": source.name})

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

    await log_activity(action="filemanager.delete", summary=f"Delete: {name}",
                       details={"path": path, "name": name})

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
):
    """Cautare fulltext in continutul fisierelor (FTS5)."""
    # First, index files in the target directory if not already indexed
    target = _resolve(path)
    if not target.is_dir():
        raise HTTPException(400, "Calea trebuie sa fie un director")

    # Index files in the directory (shallow — only current dir level for speed)
    indexed_count = 0
    for entry in target.iterdir():
        if entry.is_file() and entry.suffix.lower() in _INDEXABLE_EXTENSIONS:
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
