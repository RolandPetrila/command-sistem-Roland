"""
Rute pentru navigare fișiere (browser de fișiere read-only).

GET /api/files          — structura directorului proiectului
GET /api/files/content  — conținutul unui fișier text (max 100 KB)
"""

import os
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/api", tags=["files"])

# Directorul de bază = rădăcina proiectului
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# Extensii permise pentru afișare și citire
SAFE_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".json", ".md", ".txt",
    ".csv", ".cfg", ".toml", ".yaml", ".yml", ".html", ".css",
    ".ini", ".sh", ".bat", ".env.example",
}

# Dimensiune maximă pentru citire conținut (100 KB)
MAX_CONTENT_SIZE = 100 * 1024

# Directoare ignorate
IGNORED_DIRS = {
    "__pycache__", ".git", "node_modules", ".venv", "venv",
    ".mypy_cache", ".pytest_cache", ".ruff_cache", "dist", "build",
    ".next", ".nuxt",
}


@router.get("/files")
async def list_files(
    path: str = Query("", description="Cale relativă față de rădăcina proiectului"),
    depth: int = Query(2, ge=1, le=5, description="Adâncime maximă de scanare"),
):
    """
    Returnează structura de directoare și fișiere a proiectului.

    Doar fișierele cu extensii sigure sunt incluse.
    """
    base = _PROJECT_ROOT
    target = (base / path).resolve()

    # Securitate: nu permite symlink-uri
    if target.is_symlink():
        raise HTTPException(
            status_code=403,
            detail="Acces interzis: symlink detectat",
        )

    # Securitate: nu permite navigarea în afara proiectului
    try:
        target.relative_to(base.resolve())
    except ValueError:
        raise HTTPException(
            status_code=403,
            detail="Acces interzis: cale în afara directorului permis",
        )

    if not target.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Calea nu a fost găsită: {path}",
        )

    if not target.is_dir():
        raise HTTPException(
            status_code=400,
            detail="Calea specificată nu este un director.",
        )

    tree = _scan_directory(target, base, current_depth=0, max_depth=depth)
    return {
        "base_path": str(base),
        "relative_path": path or ".",
        "tree": tree,
    }


@router.get("/files/content")
async def get_file_content(
    path: str = Query(..., description="Cale relativă către fișier"),
):
    """
    Returnează conținutul unui fișier text.

    Doar fișiere cu extensii sigure și sub 100 KB.
    """
    base = _PROJECT_ROOT
    target = (base / path).resolve()

    # Securitate: nu permite symlink-uri
    if target.is_symlink():
        raise HTTPException(
            status_code=403,
            detail="Acces interzis: symlink detectat",
        )

    # Securitate
    try:
        target.relative_to(base.resolve())
    except ValueError:
        raise HTTPException(
            status_code=403,
            detail="Acces interzis: cale în afara directorului permis",
        )

    if not target.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Fișierul nu a fost găsit: {path}",
        )

    if not target.is_file():
        raise HTTPException(
            status_code=400,
            detail="Calea specificată nu este un fișier.",
        )

    # Verificare extensie
    if target.suffix.lower() not in SAFE_EXTENSIONS:
        raise HTTPException(
            status_code=403,
            detail=(
                f"Extensia '{target.suffix}' nu este permisă pentru vizualizare. "
                f"Extensii acceptate: {', '.join(sorted(SAFE_EXTENSIONS))}"
            ),
        )

    # Verificare dimensiune
    file_size = target.stat().st_size
    if file_size > MAX_CONTENT_SIZE:
        raise HTTPException(
            status_code=413,
            detail=(
                f"Fișierul este prea mare ({file_size / 1024:.1f} KB). "
                f"Limita maximă: {MAX_CONTENT_SIZE // 1024} KB."
            ),
        )

    try:
        content = target.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            content = target.read_text(encoding="latin-1")
        except Exception:
            raise HTTPException(
                status_code=422,
                detail="Fișierul nu poate fi citit ca text.",
            )

    return {
        "path": path,
        "filename": target.name,
        "extension": target.suffix,
        "size": file_size,
        "content": content,
        "lines": content.count("\n") + 1,
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _scan_directory(
    directory: Path,
    base: Path,
    current_depth: int,
    max_depth: int,
) -> list[dict]:
    """Scanează recursiv un director și returnează structura arborescentă."""
    items = []

    try:
        entries = sorted(directory.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower()))
    except PermissionError:
        return items

    for entry in entries:
        if entry.name.startswith(".") and entry.name not in {".env.example"}:
            continue

        if entry.is_dir():
            if entry.name in IGNORED_DIRS:
                continue
            item = {
                "name": entry.name,
                "type": "directory",
                "path": str(entry.relative_to(base)).replace("\\", "/"),
            }
            if current_depth < max_depth:
                item["children"] = _scan_directory(
                    entry, base, current_depth + 1, max_depth,
                )
            else:
                item["children"] = []
                item["truncated"] = True
            items.append(item)

        elif entry.is_file():
            if entry.suffix.lower() in SAFE_EXTENSIONS:
                items.append({
                    "name": entry.name,
                    "type": "file",
                    "path": str(entry.relative_to(base)).replace("\\", "/"),
                    "extension": entry.suffix,
                    "size": entry.stat().st_size,
                })

    return items
