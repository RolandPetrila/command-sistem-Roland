"""
API endpoints pentru Rapoarte — Statistici disk/sistem, Timeline activitate,
Jurnal personal, Bookmark-uri, Analiză fișiere, Export complet.

Endpoints:
  GET  /api/reports/disk-stats       — utilizare disk
  GET  /api/reports/system-info      — informații sistem
  GET  /api/reports/timeline         — timeline activitate (paginat)
  GET  /api/reports/timeline/stats   — agregare activitate pe zi/săptămână/lună
  GET  /api/reports/unused-files     — fișiere nefolosite în data/
  GET  /api/reports/file-stats       — statistici fișiere
  CRUD /api/reports/journal          — jurnal personal
  CRUD /api/reports/bookmarks        — bookmark-uri
  GET  /api/reports/export/full      — export complet JSON
"""

from __future__ import annotations

import io
import json
import logging
import os
import platform
import shutil
import sys
import time
import xml.etree.ElementTree as ET
import zipfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.config import settings
from app.core.activity_log import log_activity
from app.db.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/reports", tags=["reports"])

# Directorul backend
_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
_DATA_DIR = _BACKEND_DIR / "data"
_UPLOADS_DIR = _BACKEND_DIR / "uploads"
_PROJECT_DIR = _BACKEND_DIR.parent

# Timpul de start al procesului (pentru calcul uptime)
_START_TIME = time.time()

# Cache curs BNR (se actualizează o dată pe oră)
_bnr_cache: dict[str, Any] = {"data": None, "fetched_at": 0.0}


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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_folder_size(folder: Path) -> int:
    """Calculează dimensiunea totală a unui folder (bytes)."""
    total = 0
    try:
        for entry in folder.rglob("*"):
            if entry.is_file():
                try:
                    total += entry.stat().st_size
                except (OSError, PermissionError):
                    continue
    except (OSError, PermissionError):
        pass
    return total


def _format_size(size_bytes: int) -> str:
    """Formatează dimensiunea în format human-readable."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def _get_file_extension_stats(folder: Path) -> dict[str, dict[str, Any]]:
    """Colectează statistici pe extensie pentru un folder."""
    stats: dict[str, dict[str, Any]] = defaultdict(lambda: {"count": 0, "total_size": 0})
    try:
        for entry in folder.rglob("*"):
            if entry.is_file():
                try:
                    ext = entry.suffix.lower() or "(fără extensie)"
                    size = entry.stat().st_size
                    stats[ext]["count"] += 1
                    stats[ext]["total_size"] += size
                except (OSError, PermissionError):
                    continue
    except (OSError, PermissionError):
        pass
    return dict(stats)


# ===========================================================================
# DISK & SYSTEM
# ===========================================================================

@router.get("/disk-stats")
async def disk_stats():
    """Statistici utilizare disk — spațiu total, liber, folosit, dimensiuni foldere cheie."""
    # Disk usage general
    disk = shutil.disk_usage(str(_PROJECT_DIR))

    # Dimensiuni foldere individuale
    data_size = _get_folder_size(_DATA_DIR)
    uploads_size = _get_folder_size(_UPLOADS_DIR)
    backend_size = _get_folder_size(_BACKEND_DIR)
    frontend_size = _get_folder_size(_PROJECT_DIR / "frontend")

    # DB size
    db_path = settings.db_path
    db_size = db_path.stat().st_size if db_path.exists() else 0

    return {
        "disk": {
            "total": disk.total,
            "total_human": _format_size(disk.total),
            "used": disk.used,
            "used_human": _format_size(disk.used),
            "free": disk.free,
            "free_human": _format_size(disk.free),
            "used_percent": round(disk.used / disk.total * 100, 1),
        },
        "folders": {
            "data": {"size": data_size, "size_human": _format_size(data_size)},
            "uploads": {"size": uploads_size, "size_human": _format_size(uploads_size)},
            "backend": {"size": backend_size, "size_human": _format_size(backend_size)},
            "frontend": {"size": frontend_size, "size_human": _format_size(frontend_size)},
        },
        "database": {
            "path": str(db_path),
            "size": db_size,
            "size_human": _format_size(db_size),
        },
    }


@router.get("/system-info")
async def system_info():
    """Informații despre sistem — Python, OS, uptime, module, tabele DB."""
    # Uptime
    uptime_seconds = int(time.time() - _START_TIME)
    hours, remainder = divmod(uptime_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    uptime_str = f"{hours}h {minutes}m {seconds}s"

    # Module count
    modules_dir = _BACKEND_DIR / "modules"
    module_count = 0
    if modules_dir.exists():
        module_count = sum(
            1 for d in modules_dir.iterdir()
            if d.is_dir() and not d.name.startswith("_") and (d / "__init__.py").exists()
        )

    # DB tables count
    tables_count = 0
    try:
        async with get_db() as db:
            cursor = await db.execute(
                "SELECT COUNT(*) as cnt FROM sqlite_master WHERE type='table'"
            )
            row = await cursor.fetchone()
            tables_count = row["cnt"] if row else 0
    except Exception:
        pass

    return {
        "python_version": sys.version,
        "platform": platform.platform(),
        "os": platform.system(),
        "architecture": platform.architecture()[0],
        "hostname": platform.node(),
        "uptime": uptime_str,
        "uptime_seconds": uptime_seconds,
        "module_count": module_count,
        "db_tables_count": tables_count,
        "backend_dir": str(_BACKEND_DIR),
        "project_dir": str(_PROJECT_DIR),
    }


# ===========================================================================
# ACTIVITY TIMELINE
# ===========================================================================

@router.get("/timeline")
async def activity_timeline(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    date_from: str = Query("", description="Data început (YYYY-MM-DD)"),
    date_to: str = Query("", description="Data sfârșit (YYYY-MM-DD)"),
    action_filter: str = Query("", description="Filtrează pe acțiune"),
):
    """Timeline activitate din activity_log, paginat cu filtre pe dată."""
    offset = (page - 1) * per_page

    conditions = []
    params: list[Any] = []

    if date_from:
        conditions.append("timestamp >= ?")
        params.append(date_from)
    if date_to:
        conditions.append("timestamp <= ?")
        params.append(date_to + "T23:59:59")
    if action_filter:
        conditions.append("action = ?")
        params.append(action_filter)

    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    try:
        async with get_db() as db:
            # Total count
            count_sql = f"SELECT COUNT(*) as cnt FROM activity_log {where_clause}"
            cursor = await db.execute(count_sql, tuple(params))
            count_row = await cursor.fetchone()
            total = count_row["cnt"] if count_row else 0

            # Paginated results
            data_sql = f"""
                SELECT * FROM activity_log {where_clause}
                ORDER BY timestamp DESC
                LIMIT ? OFFSET ?
            """
            cursor = await db.execute(data_sql, tuple(params) + (per_page, offset))
            rows = await cursor.fetchall()

            entries = []
            for row in rows:
                entry: dict[str, Any] = {
                    "id": row["id"] if "id" in row.keys() else None,
                    "timestamp": row["timestamp"],
                    "action": row["action"],
                    "status": row["status"],
                    "summary": row["summary"],
                }
                if row["details"]:
                    try:
                        entry["details"] = json.loads(row["details"])
                    except (json.JSONDecodeError, TypeError):
                        entry["details"] = row["details"]
                entries.append(entry)

        return {
            "entries": entries,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": max(1, (total + per_page - 1) // per_page),
        }

    except Exception as exc:
        logger.error("Eroare timeline: %s", exc)
        raise HTTPException(500, f"Eroare citire timeline: {exc}")


@router.get("/timeline/stats")
async def activity_timeline_stats(
    group_by: str = Query("day", description="Grupare: day, week, month"),
    days: int = Query(30, ge=1, le=365, description="Ultimele N zile"),
):
    """Agregare activitate pe zi/săptămână/lună."""
    try:
        async with get_db() as db:
            # SQLite date grouping
            if group_by == "month":
                date_expr = "strftime('%Y-%m', timestamp)"
            elif group_by == "week":
                date_expr = "strftime('%Y-W%W', timestamp)"
            else:
                date_expr = "strftime('%Y-%m-%d', timestamp)"

            cutoff = datetime.now(timezone.utc).isoformat()[:10]
            sql = f"""
                SELECT
                    {date_expr} as period,
                    COUNT(*) as count,
                    action,
                    status
                FROM activity_log
                WHERE timestamp >= date('now', '-{days} days')
                GROUP BY period, action, status
                ORDER BY period DESC
            """
            cursor = await db.execute(sql)
            rows = await cursor.fetchall()

            # Agregare
            periods: dict[str, dict[str, Any]] = defaultdict(
                lambda: {"total": 0, "actions": defaultdict(int), "statuses": defaultdict(int)}
            )
            for row in rows:
                p = row["period"]
                cnt = row["count"]
                periods[p]["total"] += cnt
                periods[p]["actions"][row["action"]] += cnt
                periods[p]["statuses"][row["status"]] += cnt

            result = []
            for period, data in sorted(periods.items(), reverse=True):
                result.append({
                    "period": period,
                    "total": data["total"],
                    "actions": dict(data["actions"]),
                    "statuses": dict(data["statuses"]),
                })

        return {
            "stats": result,
            "group_by": group_by,
            "days": days,
            "total_periods": len(result),
        }

    except Exception as exc:
        logger.error("Eroare timeline stats: %s", exc)
        raise HTTPException(500, f"Eroare statistici timeline: {exc}")


# ===========================================================================
# FILE ANALYSIS
# ===========================================================================

@router.get("/unused-files")
async def unused_files():
    """Identifică fișierele din data/ care nu sunt referite în nicio tabelă DB."""
    if not _DATA_DIR.exists():
        return {"unused_files": [], "total": 0}

    # Colectează fișierele din data/
    data_files = []
    for entry in _DATA_DIR.iterdir():
        if entry.is_file() and entry.name != "calculator.db":
            data_files.append(entry.name)

    # Colectează referințele din DB
    referenced = set()
    try:
        async with get_db() as db:
            # Caută în tabele comune unde ar putea fi referite fișiere
            tables_to_check = [
                ("uploads", "filename"),
                ("uploads", "filepath"),
            ]
            for table, column in tables_to_check:
                try:
                    cursor = await db.execute(f"SELECT {column} FROM {table}")
                    rows = await cursor.fetchall()
                    for row in rows:
                        val = row[0]
                        if val:
                            # Extrage doar numele fișierului
                            referenced.add(Path(val).name)
                except Exception:
                    continue  # tabelul/coloana nu există
    except Exception:
        pass

    unused = [
        {
            "name": f,
            "path": str(_DATA_DIR / f),
            "size": os.path.getsize(_DATA_DIR / f),
            "size_human": _format_size(os.path.getsize(_DATA_DIR / f)),
        }
        for f in data_files
        if f not in referenced
    ]

    return {
        "unused_files": unused,
        "total": len(unused),
        "data_dir": str(_DATA_DIR),
        "message": f"{len(unused)} fișiere potențial nefolosite în data/.",
    }


@router.get("/file-stats")
async def file_stats():
    """Statistici fișiere — contorizare pe extensie, dimensiune totală, cele mai mari."""
    all_stats = {}

    for folder_name, folder_path in [("data", _DATA_DIR), ("uploads", _UPLOADS_DIR)]:
        if not folder_path.exists():
            continue

        ext_stats = _get_file_extension_stats(folder_path)

        # Cele mai mari fișiere
        largest = []
        try:
            files = [(f, f.stat().st_size) for f in folder_path.rglob("*") if f.is_file()]
            files.sort(key=lambda x: x[1], reverse=True)
            for f, size in files[:10]:
                largest.append({
                    "name": f.name,
                    "path": str(f),
                    "size": size,
                    "size_human": _format_size(size),
                })
        except (OSError, PermissionError):
            pass

        total_size = sum(s["total_size"] for s in ext_stats.values())
        total_files = sum(s["count"] for s in ext_stats.values())

        by_type = []
        for ext, data in sorted(ext_stats.items(), key=lambda x: x[1]["total_size"], reverse=True):
            by_type.append({
                "extension": ext,
                "count": data["count"],
                "total_size": data["total_size"],
                "total_size_human": _format_size(data["total_size"]),
            })

        all_stats[folder_name] = {
            "total_files": total_files,
            "total_size": total_size,
            "total_size_human": _format_size(total_size),
            "by_type": by_type,
            "largest_files": largest,
        }

    return {"folders": all_stats}


# ===========================================================================
# JOURNAL
# ===========================================================================

@router.get("/journal")
async def journal_list(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    """Listează intrările din jurnal, paginat."""
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
    """Adaugă o intrare nouă în jurnal."""
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
            summary=f"Intrare jurnal creată: {req.title}",
            details={"id": entry_id, "mood": req.mood},
        )

        return {
            "status": "ok",
            "message": "Intrare adăugată în jurnal.",
            "id": entry_id,
        }

    except Exception as exc:
        logger.error("Eroare creare jurnal: %s", exc)
        raise HTTPException(500, f"Eroare creare intrare jurnal: {exc}")


@router.put("/journal/{entry_id}")
async def journal_update(entry_id: int, req: JournalEntryUpdate):
    """Actualizează o intrare din jurnal."""
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
        raise HTTPException(400, "Niciun câmp de actualizat.")

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
                raise HTTPException(404, "Intrare negăsită.")

        await log_activity(
            action="reports.journal.update",
            summary=f"Intrare jurnal actualizată: #{entry_id}",
        )

        return {"status": "ok", "message": "Intrare actualizată."}

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Eroare actualizare jurnal: %s", exc)
        raise HTTPException(500, f"Eroare actualizare jurnal: {exc}")


@router.delete("/journal/{entry_id}")
async def journal_delete(entry_id: int):
    """Șterge o intrare din jurnal."""
    try:
        async with get_db() as db:
            cursor = await db.execute(
                "DELETE FROM journal_entries WHERE id = ?", (entry_id,)
            )
            await db.commit()

            if cursor.rowcount == 0:
                raise HTTPException(404, "Intrare negăsită.")

        await log_activity(
            action="reports.journal.delete",
            summary=f"Intrare jurnal ștearsă: #{entry_id}",
        )

        return {"status": "ok", "message": "Intrare ștearsă din jurnal."}

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Eroare ștergere jurnal: %s", exc)
        raise HTTPException(500, f"Eroare ștergere jurnal: {exc}")


# ===========================================================================
# BOOKMARKS
# ===========================================================================

@router.get("/bookmarks")
async def bookmarks_list(
    category: str = Query("", description="Filtrează pe categorie"),
):
    """Listează toate bookmark-urile."""
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
    """Adaugă un bookmark nou."""
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
            summary=f"Bookmark adăugat: {req.title}",
            details={"id": bookmark_id, "url": req.url},
        )

        return {
            "status": "ok",
            "message": "Bookmark adăugat.",
            "id": bookmark_id,
        }

    except Exception as exc:
        logger.error("Eroare creare bookmark: %s", exc)
        raise HTTPException(500, f"Eroare creare bookmark: {exc}")


@router.put("/bookmarks/{bookmark_id}")
async def bookmarks_update(bookmark_id: int, req: BookmarkUpdate):
    """Actualizează un bookmark."""
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
        raise HTTPException(400, "Niciun câmp de actualizat.")

    params.append(bookmark_id)

    try:
        async with get_db() as db:
            cursor = await db.execute(
                f"UPDATE bookmarks SET {', '.join(updates)} WHERE id = ?",
                tuple(params),
            )
            await db.commit()

            if cursor.rowcount == 0:
                raise HTTPException(404, "Bookmark negăsit.")

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
    """Șterge un bookmark."""
    try:
        async with get_db() as db:
            cursor = await db.execute(
                "DELETE FROM bookmarks WHERE id = ?", (bookmark_id,)
            )
            await db.commit()

            if cursor.rowcount == 0:
                raise HTTPException(404, "Bookmark negăsit.")

        await log_activity(
            action="reports.bookmark.delete",
            summary=f"Bookmark șters: #{bookmark_id}",
        )

        return {"status": "ok", "message": "Bookmark șters."}

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Eroare ștergere bookmark: %s", exc)
        raise HTTPException(500, f"Eroare ștergere bookmark: {exc}")


# ===========================================================================
# EXPORT
# ===========================================================================

@router.get("/export/full")
async def export_full():
    """Export complet al tuturor datelor ca JSON — clienți, facturi, activitate, jurnal, bookmark-uri."""
    export_data: dict[str, Any] = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "tables": {},
    }

    tables_to_export = [
        "activity_log",
        "uploads",
        "settings",
        "journal_entries",
        "bookmarks",
        "clients",
        "invoices",
        "invoice_items",
        "itp_inspections",
        "notepad_entries",
    ]

    try:
        async with get_db() as db:
            for table in tables_to_export:
                try:
                    cursor = await db.execute(f"SELECT * FROM {table}")
                    rows = await cursor.fetchall()
                    export_data["tables"][table] = [dict(row) for row in rows]
                except Exception:
                    # Tabelul nu există — skip
                    export_data["tables"][table] = []

        # Statistici
        total_records = sum(len(v) for v in export_data["tables"].values())
        export_data["stats"] = {
            "total_tables": len(export_data["tables"]),
            "total_records": total_records,
        }

        await log_activity(
            action="reports.export",
            summary=f"Export complet: {total_records} înregistrări din {len(export_data['tables'])} tabele",
        )

        return export_data

    except Exception as exc:
        logger.error("Eroare export: %s", exc)
        raise HTTPException(500, f"Eroare export date: {exc}")


# ---------------------------------------------------------------------------
# BNR Exchange Rate — Curs valutar live (NEW3 — zero auth, free)
# ---------------------------------------------------------------------------

_BNR_URL = "https://www.bnr.ro/nbrfxrates.xml"
_BNR_NS = {"bnr": "http://www.bnr.ro/xsd"}


@router.get("/exchange-rates")
async def get_exchange_rates():
    """Curs valutar BNR — cache 1 oră. Returnează EUR, USD, GBP, CHF, HUF."""
    now = time.time()
    if _bnr_cache["data"] and (now - _bnr_cache["fetched_at"]) < 3600:
        return _bnr_cache["data"]

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(_BNR_URL)
            resp.raise_for_status()

        root = ET.fromstring(resp.text)
        body = root.find(".//bnr:Body", _BNR_NS)
        if body is None:
            raise HTTPException(502, "Format BNR invalid — Body lipsă")

        cube = body.find("bnr:Cube", _BNR_NS)
        if cube is None:
            raise HTTPException(502, "Format BNR invalid — Cube lipsă")

        date_str = cube.get("date", "")
        rates = {}
        for rate_el in cube.findall("bnr:Rate", _BNR_NS):
            currency = rate_el.get("currency", "")
            multiplier = int(rate_el.get("multiplier", "1"))
            value = float(rate_el.text)
            rates[currency] = round(value / multiplier, 4)

        result = {
            "date": date_str,
            "base": "RON",
            "rates": rates,
            "key_rates": {
                "EUR": rates.get("EUR"),
                "USD": rates.get("USD"),
                "GBP": rates.get("GBP"),
                "CHF": rates.get("CHF"),
                "HUF": rates.get("HUF"),
            },
            "source": "BNR (Banca Națională a României)",
            "cached": False,
        }
        _bnr_cache["data"] = result
        _bnr_cache["fetched_at"] = now
        return result

    except httpx.HTTPError as exc:
        logger.error("Eroare BNR fetch: %s", exc)
        if _bnr_cache["data"]:
            cached = {**_bnr_cache["data"], "cached": True}
            return cached
        raise HTTPException(502, f"Nu s-a putut accesa BNR: {exc}")


# ===========================================================================
# BACKUP ZIP — Export complet (DB + uploads)
# ===========================================================================

@router.get("/backup/zip")
async def backup_zip():
    """Export complet: baza de date SQLite + fisierele uploadate intr-un ZIP."""
    buf = io.BytesIO()
    db_path = settings.db_path

    try:
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            # Adauga baza de date
            if db_path.exists():
                zf.write(str(db_path), "calculator.db")

            # Adauga fisierele uploadate
            if _UPLOADS_DIR.exists():
                for fpath in _UPLOADS_DIR.rglob("*"):
                    if fpath.is_file():
                        arcname = f"uploads/{fpath.relative_to(_UPLOADS_DIR)}"
                        zf.write(str(fpath), arcname)

        buf.seek(0)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"roland_backup_{timestamp}.zip"

        await log_activity(
            action="reports.backup.zip",
            summary=f"Backup ZIP creat: {filename}",
        )

        return StreamingResponse(
            buf,
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as exc:
        logger.error("Eroare backup ZIP: %s", exc)
        raise HTTPException(500, f"Eroare creare backup: {exc}")


# ===========================================================================
# DASHBOARD SUMMARY — Date agregate pentru dashboard
# ===========================================================================

@router.get("/dashboard-summary")
async def dashboard_summary():
    """Date agregate pentru dashboard-ul profesional."""
    result = {
        "invoices_month": 0,
        "translations_count": 0,
        "itp_active": 0,
        "recent_activity": [],
        "last_invoice": None,
        "last_translation": None,
    }

    try:
        async with get_db() as db:
            # Facturi luna curenta
            try:
                cursor = await db.execute(
                    "SELECT COUNT(*) as cnt FROM invoices WHERE created_at >= date('now', 'start of month')"
                )
                row = await cursor.fetchone()
                result["invoices_month"] = row["cnt"] if row else 0
            except Exception:
                pass

            # Traduceri totale (din activity_log)
            try:
                cursor = await db.execute(
                    "SELECT COUNT(*) as cnt FROM activity_log WHERE action LIKE 'translator%'"
                )
                row = await cursor.fetchone()
                result["translations_count"] = row["cnt"] if row else 0
            except Exception:
                pass

            # ITP active
            try:
                cursor = await db.execute(
                    "SELECT COUNT(*) as cnt FROM itp_inspections WHERE expiry_date >= date('now')"
                )
                row = await cursor.fetchone()
                result["itp_active"] = row["cnt"] if row else 0
            except Exception:
                pass

            # Ultima factura
            try:
                cursor = await db.execute(
                    "SELECT invoice_number, created_at FROM invoices ORDER BY created_at DESC LIMIT 1"
                )
                row = await cursor.fetchone()
                if row:
                    result["last_invoice"] = {
                        "number": row["invoice_number"],
                        "date": row["created_at"],
                    }
            except Exception:
                pass

            # Activitate recenta (ultimele 5)
            try:
                cursor = await db.execute(
                    "SELECT timestamp, action, summary FROM activity_log ORDER BY timestamp DESC LIMIT 5"
                )
                rows = await cursor.fetchall()
                result["recent_activity"] = [
                    {"timestamp": r["timestamp"], "action": r["action"], "summary": r["summary"]}
                    for r in rows
                ]
            except Exception:
                pass

    except Exception as exc:
        logger.error("Eroare dashboard summary: %s", exc)

    return result
