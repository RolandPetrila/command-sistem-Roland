"""
System Reports — disk stats, system info, file analysis,
dashboard summary, BNR exchange rates, backup ZIP.

Endpoints:
  GET /api/reports/disk-stats
  GET /api/reports/system-info
  GET /api/reports/file-stats
  GET /api/reports/unused-files
  GET /api/reports/dashboard-summary
  GET /api/reports/exchange-rates
  GET /api/reports/backup/zip
"""

from __future__ import annotations

import io
import logging
import os
import platform
import shutil
import sys
import time
import xml.etree.ElementTree as ET
import zipfile
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.config import settings
from app.core.activity_log import log_activity
from app.db.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/reports", tags=["Reports — System"])

# Directorul backend
_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
_DATA_DIR = _BACKEND_DIR / "data"
_UPLOADS_DIR = _BACKEND_DIR / "uploads"
_PROJECT_DIR = _BACKEND_DIR.parent

# Timpul de start al procesului (pentru calcul uptime)
_START_TIME = time.time()

# Cache curs BNR (se actualizeaza o data pe ora)
_bnr_cache: dict[str, Any] = {"data": None, "fetched_at": 0.0}

_BNR_URL = "https://www.bnr.ro/nbrfxrates.xml"
_BNR_NS = {"bnr": "http://www.bnr.ro/xsd"}


# ---------------------------------------------------------------------------
# Helpers (path/size utilities — also imported by other sub-routers if needed)
# ---------------------------------------------------------------------------

def _get_folder_size(folder: Path) -> int:
    """Calculeaza dimensiunea totala a unui folder (bytes)."""
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
    """Formateaza dimensiunea in format human-readable."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def _get_file_extension_stats(folder: Path) -> dict[str, dict[str, Any]]:
    """Colecteaza statistici pe extensie pentru un folder."""
    stats: dict[str, dict[str, Any]] = defaultdict(lambda: {"count": 0, "total_size": 0})
    try:
        for entry in folder.rglob("*"):
            if entry.is_file():
                try:
                    ext = entry.suffix.lower() or "(fara extensie)"
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
    """Statistici utilizare disk — spatiu total, liber, folosit, dimensiuni foldere cheie."""
    disk = shutil.disk_usage(str(_PROJECT_DIR))

    data_size = _get_folder_size(_DATA_DIR)
    uploads_size = _get_folder_size(_UPLOADS_DIR)
    backend_size = _get_folder_size(_BACKEND_DIR)
    frontend_size = _get_folder_size(_PROJECT_DIR / "frontend")

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
    """Informatii despre sistem — Python, OS, uptime, module, tabele DB."""
    uptime_seconds = int(time.time() - _START_TIME)
    hours, remainder = divmod(uptime_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    uptime_str = f"{hours}h {minutes}m {seconds}s"

    modules_dir = _BACKEND_DIR / "modules"
    module_count = 0
    if modules_dir.exists():
        module_count = sum(
            1 for d in modules_dir.iterdir()
            if d.is_dir() and not d.name.startswith("_") and (d / "__init__.py").exists()
        )

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
# FILE ANALYSIS
# ===========================================================================

@router.get("/unused-files")
async def unused_files():
    """Identifica fisierele din data/ care nu sunt referite in nicio tabela DB."""
    if not _DATA_DIR.exists():
        return {"unused_files": [], "total": 0}

    data_files = []
    for entry in _DATA_DIR.iterdir():
        if entry.is_file() and entry.name != "calculator.db":
            data_files.append(entry.name)

    referenced = set()
    try:
        async with get_db() as db:
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
                            referenced.add(Path(val).name)
                except Exception:
                    continue
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
        "message": f"{len(unused)} fisiere potential nefolosite in data/.",
    }


@router.get("/file-stats")
async def file_stats():
    """Statistici fisiere — contorizare pe extensie, dimensiune totala, cele mai mari."""
    all_stats = {}

    for folder_name, folder_path in [("data", _DATA_DIR), ("uploads", _UPLOADS_DIR)]:
        if not folder_path.exists():
            continue

        ext_stats = _get_file_extension_stats(folder_path)

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
# DASHBOARD SUMMARY
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
            try:
                cursor = await db.execute(
                    "SELECT COUNT(*) as cnt FROM invoices WHERE created_at >= date('now', 'start of month')"
                )
                row = await cursor.fetchone()
                result["invoices_month"] = row["cnt"] if row else 0
            except Exception:
                pass

            try:
                cursor = await db.execute(
                    "SELECT COUNT(*) as cnt FROM activity_log WHERE action LIKE 'translator%'"
                )
                row = await cursor.fetchone()
                result["translations_count"] = row["cnt"] if row else 0
            except Exception:
                pass

            try:
                cursor = await db.execute(
                    "SELECT COUNT(*) as cnt FROM itp_inspections WHERE expiry_date >= date('now')"
                )
                row = await cursor.fetchone()
                result["itp_active"] = row["cnt"] if row else 0
            except Exception:
                pass

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


# ===========================================================================
# BNR EXCHANGE RATES
# ===========================================================================

@router.get("/exchange-rates")
async def get_exchange_rates():
    """Curs valutar BNR — cache 1 ora. Returneaza EUR, USD, GBP, CHF, HUF."""
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
            raise HTTPException(502, "Format BNR invalid — Body lipsa")

        cube = body.find("bnr:Cube", _BNR_NS)
        if cube is None:
            raise HTTPException(502, "Format BNR invalid — Cube lipsa")

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
            "source": "BNR (Banca Nationala a Romaniei)",
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
# BACKUP ZIP
# ===========================================================================

@router.get("/backup/zip")
async def backup_zip():
    """Export complet: baza de date SQLite + fisierele uploadate intr-un ZIP."""
    buf = io.BytesIO()
    db_path = settings.db_path

    try:
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            if db_path.exists():
                zf.write(str(db_path), "calculator.db")

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
