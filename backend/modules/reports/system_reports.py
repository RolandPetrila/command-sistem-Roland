"""
System Reports — disk stats, system info, file analysis,
dashboard summary, BNR exchange rates, backup ZIP, dashboard widgets,
DB backup & integrity, critical JSON export.

Endpoints:
  GET  /api/reports/disk-stats
  GET  /api/reports/system-info
  GET  /api/reports/file-stats
  GET  /api/reports/unused-files
  GET  /api/reports/dashboard-summary
  GET  /api/reports/exchange-rates
  GET  /api/reports/backup/zip
  POST /api/reports/backup
  GET  /api/reports/db-integrity
  GET  /api/reports/export/critical-json
  GET  /api/reports/dashboard/receivable
  GET  /api/reports/dashboard/alerts
  GET  /api/reports/dashboard/quick-stats
  GET  /api/reports/dashboard/revenue-comparison
  GET  /api/reports/dashboard/itp-trend
  GET  /api/reports/revenue-by-client
  GET  /api/reports/export/pdf
  GET  /api/reports/dashboard/my-day
"""

from __future__ import annotations

import io
import json
import logging
import os
import platform
import shutil
import sqlite3
import sys
import time
import xml.etree.ElementTree as ET
import zipfile
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import httpx

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse

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
_BACKUPS_DIR = _DATA_DIR / "backups"
_GDRIVE_BACKUP_DIR = Path(
    r"G:\My Drive\Roly\4. Artificial Inteligence"
    r"\1.0_Traduceri\NOU_Calculator_Pret_Traduceri\backups"
)

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
            if rate_el.text is None:
                continue
            multiplier = int(rate_el.get("multiplier", "1"))
            try:
                value = float(rate_el.text)
            except (TypeError, ValueError):
                continue
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


# ===========================================================================
# DB BACKUP & INTEGRITY
# ===========================================================================

def _run_integrity_check(db_file: Path) -> tuple[bool, str]:
    """Run PRAGMA integrity_check on a SQLite file (sync, separate connection)."""
    try:
        conn = sqlite3.connect(str(db_file))
        cursor = conn.execute("PRAGMA integrity_check")
        result = cursor.fetchone()[0]
        conn.close()
        return (result == "ok", result)
    except Exception as exc:
        return (False, str(exc))


def _cleanup_old_backups(max_age_days: int = 30, max_files: int = 30) -> int:
    """Delete backups older than max_age_days, keep at most max_files. Returns count deleted."""
    if not _BACKUPS_DIR.exists():
        return 0

    backup_files = sorted(
        _BACKUPS_DIR.glob("backup_*.db"),
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )

    cutoff = datetime.now() - timedelta(days=max_age_days)
    deleted = 0

    for i, f in enumerate(backup_files):
        try:
            mtime = datetime.fromtimestamp(f.stat().st_mtime)
            if i >= max_files or mtime < cutoff:
                f.unlink()
                deleted += 1
        except OSError:
            continue

    return deleted


async def run_backup_logic() -> dict[str, Any]:
    """Core backup logic — usable from endpoint or cron job directly.

    Returns dict with backup result metadata.
    """
    db_path = settings.db_path
    if not db_path.exists():
        raise FileNotFoundError(f"Baza de date nu exista: {db_path}")

    _BACKUPS_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    backup_name = f"backup_{timestamp}.db"
    backup_path = _BACKUPS_DIR / backup_name

    # Copy with metadata preserved
    shutil.copy2(str(db_path), str(backup_path))

    # Integrity check on the copy
    integrity_ok, integrity_result = _run_integrity_check(backup_path)

    size_bytes = backup_path.stat().st_size

    # Cleanup old backups
    deleted = _cleanup_old_backups()

    # Google Drive copy (best-effort)
    gdrive_copied = False
    gdrive_error = None
    try:
        if _GDRIVE_BACKUP_DIR.parent.exists():
            _GDRIVE_BACKUP_DIR.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(backup_path), str(_GDRIVE_BACKUP_DIR / backup_name))
            gdrive_copied = True
        else:
            gdrive_error = "Google Drive nu este montat"
            logger.warning(
                "Google Drive backup skip — calea nu exista: %s",
                _GDRIVE_BACKUP_DIR.parent,
            )
    except Exception as exc:
        gdrive_error = str(exc)
        logger.warning("Google Drive backup esuat: %s", exc)

    await log_activity(
        action="reports.backup.db",
        summary=(
            f"Backup DB creat: {backup_name} ({_format_size(size_bytes)}), "
            f"integritate: {'OK' if integrity_ok else 'FAIL'}"
            f"{', GDrive: OK' if gdrive_copied else ''}"
        ),
        details={
            "filename": backup_name,
            "size_bytes": size_bytes,
            "integrity_ok": integrity_ok,
            "old_deleted": deleted,
            "gdrive_copied": gdrive_copied,
        },
    )

    return {
        "filename": backup_name,
        "path": str(backup_path),
        "size_bytes": size_bytes,
        "size_human": _format_size(size_bytes),
        "integrity_ok": integrity_ok,
        "integrity_result": integrity_result,
        "timestamp": timestamp,
        "old_backups_deleted": deleted,
        "gdrive_copied": gdrive_copied,
        "gdrive_error": gdrive_error,
    }


@router.post("/backup")
async def create_backup():
    """Creaza un backup al bazei de date SQLite cu verificare integritate."""
    try:
        result = await run_backup_logic()
        return result
    except FileNotFoundError as exc:
        raise HTTPException(404, str(exc))
    except Exception as exc:
        logger.error("Eroare backup DB: %s", exc)
        raise HTTPException(500, f"Eroare creare backup: {exc}")


@router.get("/db-integrity")
async def db_integrity():
    """Verificare integritate baza de date live + informatii dimensiune."""
    db_path = settings.db_path
    if not db_path.exists():
        raise HTTPException(404, "Baza de date nu exista")

    # Integrity check on live DB
    integrity_ok, integrity_result = _run_integrity_check(db_path)

    db_size = db_path.stat().st_size

    # Count tables
    tables_count = 0
    try:
        async with get_db() as db:
            cursor = await db.execute(
                "SELECT COUNT(*) AS cnt FROM sqlite_master WHERE type='table'"
            )
            row = await cursor.fetchone()
            tables_count = row["cnt"] if row else 0
    except Exception:
        pass

    # Find last backup
    last_backup = None
    if _BACKUPS_DIR.exists():
        backups = sorted(
            _BACKUPS_DIR.glob("backup_*.db"),
            key=lambda f: f.stat().st_mtime,
            reverse=True,
        )
        if backups:
            latest = backups[0]
            last_backup = {
                "filename": latest.name,
                "timestamp": datetime.fromtimestamp(
                    latest.stat().st_mtime
                ).isoformat(),
                "size_bytes": latest.stat().st_size,
            }

    return {
        "ok": integrity_ok,
        "result": integrity_result,
        "db_size_bytes": db_size,
        "db_size_human": _format_size(db_size),
        "tables_count": tables_count,
        "db_path": str(db_path),
        "last_backup": last_backup,
    }


@router.get("/export/critical-json")
async def export_critical_json():
    """Export tabelele critice ca fisier JSON descarcabil."""
    export_data: dict[str, Any] = {
        "exported_at": datetime.now().isoformat(),
        "tables": {},
    }

    table_configs = [
        ("clients", "SELECT * FROM clients"),
        ("invoices", "SELECT * FROM invoices"),
        ("itp_inspections", "SELECT * FROM itp_inspections"),
        (
            "vault_entries",
            "SELECT id, name, category, username, url, created_at, updated_at "
            "FROM vault_entries",
        ),
        ("ai_config", "SELECT key FROM ai_config"),
    ]

    try:
        async with get_db() as db:
            for table_name, query in table_configs:
                try:
                    cursor = await db.execute(query)
                    rows = await cursor.fetchall()
                    export_data["tables"][table_name] = {
                        "count": len(rows),
                        "rows": [dict(row) for row in rows],
                    }
                except Exception:
                    # Table doesn't exist yet — skip gracefully
                    export_data["tables"][table_name] = {
                        "count": 0,
                        "rows": [],
                        "note": "Tabelul nu exista inca",
                    }
    except Exception as exc:
        logger.error("Eroare export critical JSON: %s", exc)
        raise HTTPException(500, f"Eroare export: {exc}")

    json_bytes = json.dumps(
        export_data, ensure_ascii=False, indent=2, default=str
    ).encode("utf-8")
    buf = io.BytesIO(json_bytes)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"critical_export_{timestamp}.json"

    await log_activity(
        action="reports.export.critical_json",
        summary=(
            f"Export JSON critic: {filename} ({len(json_bytes)} bytes, "
            f"{sum(t['count'] for t in export_data['tables'].values())} randuri)"
        ),
    )

    return StreamingResponse(
        buf,
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


# ---------------------------------------------------------------------------
# CRON: Register daily backup job at 02:00 AM
# ---------------------------------------------------------------------------

async def register_backup_cron_job() -> None:
    """Insert a daily backup job into scheduled_tasks if not already present.

    Called once at application startup (from module init or main).
    """
    try:
        async with get_db() as db:
            # Check if job already exists
            cursor = await db.execute(
                "SELECT id FROM scheduled_tasks WHERE name = ?",
                ("backup_db_daily",),
            )
            existing = await cursor.fetchone()
            if existing:
                return  # Already registered

            await db.execute(
                "INSERT INTO scheduled_tasks "
                "(name, schedule_cron, action_type, action_config, enabled) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    "backup_db_daily",
                    "0 2 * * *",
                    "internal",
                    json.dumps({
                        "function": "modules.reports.system_reports.run_backup_logic",
                        "description": "Backup automat SQLite zilnic la 02:00",
                    }),
                    1,
                ),
            )
            await db.commit()
            logger.info("Cron job backup_db_daily inregistrat (0 2 * * *)")
    except Exception as exc:
        # Don't fail startup if scheduled_tasks table doesn't exist yet
        logger.warning("Nu s-a putut inregistra cron backup_db_daily: %s", exc)


# ===========================================================================
# DASHBOARD WIDGETS — Receivable, Alerts, Quick Stats, Revenue, ITP Trend
# ===========================================================================

@router.get("/dashboard/receivable")
async def dashboard_receivable():
    """Total RON de incasat — facturi trimise/restante, neanulate si neplatite."""
    result = {"total_receivable": 0.0, "count": 0, "currency": "RON"}
    try:
        async with get_db() as db:
            cursor = await db.execute(
                "SELECT COALESCE(SUM(total), 0) AS total_sum, COUNT(*) AS cnt "
                "FROM invoices "
                "WHERE status NOT IN ('paid', 'cancelled', 'draft')"
            )
            row = await cursor.fetchone()
            if row:
                result["total_receivable"] = round(row["total_sum"], 2)
                result["count"] = row["cnt"]
    except Exception as exc:
        logger.error("Eroare dashboard receivable: %s", exc)
    return result


@router.get("/dashboard/alerts")
async def dashboard_alerts():
    """Alerte combinate: ITP ce expira in 30 zile + facturi restante."""
    result = {"itp_expiring": 0, "invoices_overdue": 0, "alerts": []}
    try:
        async with get_db() as db:
            # ITP-uri ce expira in urmatoarele 30 de zile
            try:
                cursor = await db.execute(
                    "SELECT COUNT(*) AS cnt FROM itp_inspections "
                    "WHERE expiry_date <= date('now', '+30 days') "
                    "AND expiry_date >= date('now')"
                )
                row = await cursor.fetchone()
                result["itp_expiring"] = row["cnt"] if row else 0

                # Detalii ITP-uri ce expira
                cursor = await db.execute(
                    "SELECT plate_number, brand, model, expiry_date "
                    "FROM itp_inspections "
                    "WHERE expiry_date <= date('now', '+30 days') "
                    "AND expiry_date >= date('now') "
                    "ORDER BY expiry_date ASC LIMIT 20"
                )
                rows = await cursor.fetchall()
                for r in rows:
                    result["alerts"].append({
                        "type": "itp_expiring",
                        "message": f"ITP expira: {r['plate_number']} ({r['brand'] or ''} {r['model'] or ''}) — {r['expiry_date']}",
                        "date": r["expiry_date"],
                        "plate_number": r["plate_number"],
                    })
            except Exception:
                pass

            # Facturi restante (due_date trecut, neplatite, neanulate)
            try:
                cursor = await db.execute(
                    "SELECT COUNT(*) AS cnt FROM invoices "
                    "WHERE due_date < date('now') "
                    "AND status NOT IN ('paid', 'cancelled')"
                )
                row = await cursor.fetchone()
                result["invoices_overdue"] = row["cnt"] if row else 0

                # Detalii facturi restante
                cursor = await db.execute(
                    "SELECT invoice_number, total, due_date, currency "
                    "FROM invoices "
                    "WHERE due_date < date('now') "
                    "AND status NOT IN ('paid', 'cancelled') "
                    "ORDER BY due_date ASC LIMIT 20"
                )
                rows = await cursor.fetchall()
                for r in rows:
                    result["alerts"].append({
                        "type": "invoice_overdue",
                        "message": f"Factura restanta: {r['invoice_number']} — {r['total']} {r['currency'] or 'RON'} (scadenta {r['due_date']})",
                        "date": r["due_date"],
                        "invoice_number": r["invoice_number"],
                        "total": r["total"],
                    })
            except Exception:
                pass

            # Sorteaza alertele dupa data (cele mai urgente primele)
            result["alerts"].sort(key=lambda a: a.get("date", ""))

    except Exception as exc:
        logger.error("Eroare dashboard alerts: %s", exc)
    return result


@router.get("/dashboard/quick-stats")
async def dashboard_quick_stats():
    """Statistici rapide: total clienti, facturi/ITP/traduceri luna curenta."""
    result = {
        "total_clients": 0,
        "invoices_this_month": 0,
        "itp_this_month": 0,
        "translations_this_month": 0,
    }
    try:
        async with get_db() as db:
            # Total clienti
            try:
                cursor = await db.execute("SELECT COUNT(*) AS cnt FROM clients")
                row = await cursor.fetchone()
                result["total_clients"] = row["cnt"] if row else 0
            except Exception:
                pass

            # Facturi luna curenta
            try:
                cursor = await db.execute(
                    "SELECT COUNT(*) AS cnt FROM invoices "
                    "WHERE created_at >= date('now', 'start of month')"
                )
                row = await cursor.fetchone()
                result["invoices_this_month"] = row["cnt"] if row else 0
            except Exception:
                pass

            # ITP luna curenta
            try:
                cursor = await db.execute(
                    "SELECT COUNT(*) AS cnt FROM itp_inspections "
                    "WHERE inspection_date >= date('now', 'start of month')"
                )
                row = await cursor.fetchone()
                result["itp_this_month"] = row["cnt"] if row else 0
            except Exception:
                pass

            # Traduceri luna curenta (din activity_log)
            try:
                cursor = await db.execute(
                    "SELECT COUNT(*) AS cnt FROM activity_log "
                    "WHERE action LIKE 'translator%' "
                    "AND timestamp >= date('now', 'start of month')"
                )
                row = await cursor.fetchone()
                result["translations_this_month"] = row["cnt"] if row else 0
            except Exception:
                pass

    except Exception as exc:
        logger.error("Eroare dashboard quick-stats: %s", exc)
    return result


@router.get("/dashboard/revenue-comparison")
async def dashboard_revenue_comparison():
    """Comparatie venituri: luna curenta vs luna precedenta."""
    result = {
        "current_month": 0.0,
        "previous_month": 0.0,
        "change_percent": 0.0,
        "current_month_label": "",
        "previous_month_label": "",
    }
    try:
        async with get_db() as db:
            # Venituri luna curenta (facturi platite)
            try:
                cursor = await db.execute(
                    "SELECT COALESCE(SUM(total), 0) AS total_sum "
                    "FROM invoices "
                    "WHERE status = 'paid' "
                    "AND date >= date('now', 'start of month')"
                )
                row = await cursor.fetchone()
                result["current_month"] = round(row["total_sum"], 2) if row else 0.0
            except Exception:
                pass

            # Venituri luna precedenta (facturi platite)
            try:
                cursor = await db.execute(
                    "SELECT COALESCE(SUM(total), 0) AS total_sum "
                    "FROM invoices "
                    "WHERE status = 'paid' "
                    "AND date >= date('now', 'start of month', '-1 month') "
                    "AND date < date('now', 'start of month')"
                )
                row = await cursor.fetchone()
                result["previous_month"] = round(row["total_sum"], 2) if row else 0.0
            except Exception:
                pass

            # Calculeaza procentul de schimbare
            if result["previous_month"] > 0:
                change = (
                    (result["current_month"] - result["previous_month"])
                    / result["previous_month"]
                    * 100
                )
                result["change_percent"] = round(change, 1)
            elif result["current_month"] > 0:
                result["change_percent"] = 100.0

            # Etichete luna
            try:
                cursor = await db.execute(
                    "SELECT strftime('%Y-%m', 'now') AS current_m, "
                    "strftime('%Y-%m', 'now', '-1 month') AS prev_m"
                )
                row = await cursor.fetchone()
                if row:
                    result["current_month_label"] = row["current_m"]
                    result["previous_month_label"] = row["prev_m"]
            except Exception:
                pass

    except Exception as exc:
        logger.error("Eroare dashboard revenue-comparison: %s", exc)
    return result


@router.get("/dashboard/itp-trend")
async def dashboard_itp_trend():
    """Trend ITP saptamanal — inspectii pe saptamana, ultimele 4 saptamani."""
    result = {"weeks": []}
    try:
        async with get_db() as db:
            cursor = await db.execute(
                "SELECT strftime('%Y-W%W', inspection_date) AS week, "
                "COUNT(*) AS cnt "
                "FROM itp_inspections "
                "WHERE inspection_date >= date('now', '-28 days') "
                "GROUP BY week "
                "ORDER BY week ASC"
            )
            rows = await cursor.fetchall()
            result["weeks"] = [
                {"week": r["week"], "count": r["cnt"]} for r in rows
            ]

            # Daca nu sunt date, returneaza 4 saptamani cu 0
            if not result["weeks"]:
                try:
                    cursor = await db.execute(
                        "SELECT strftime('%Y-W%W', date('now', '-21 days')) AS w1, "
                        "strftime('%Y-W%W', date('now', '-14 days')) AS w2, "
                        "strftime('%Y-W%W', date('now', '-7 days')) AS w3, "
                        "strftime('%Y-W%W', date('now')) AS w4"
                    )
                    row = await cursor.fetchone()
                    if row:
                        result["weeks"] = [
                            {"week": row["w1"], "count": 0},
                            {"week": row["w2"], "count": 0},
                            {"week": row["w3"], "count": 0},
                            {"week": row["w4"], "count": 0},
                        ]
                except Exception:
                    pass

    except Exception as exc:
        logger.error("Eroare dashboard itp-trend: %s", exc)
    return result


# ===========================================================================
# REVENUE BY CLIENT (R4-36)
# ===========================================================================

@router.get("/revenue-by-client")
async def revenue_by_client(
    date_from: str = "",
    date_to: str = "",
):
    """Venituri per client — SUM(total), COUNT, AVG grupat pe client."""
    conditions: list[str] = []
    params: list = []

    if date_from:
        conditions.append("i.date >= ?")
        params.append(date_from)
    if date_to:
        conditions.append("i.date <= ?")
        params.append(date_to)

    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    try:
        async with get_db() as db:
            sql = f"""
                SELECT
                    i.client_id,
                    COALESCE(c.name, 'Fara client') AS client_name,
                    SUM(i.total) AS total_revenue,
                    COUNT(*) AS invoice_count,
                    AVG(i.total) AS avg_invoice
                FROM invoices i
                LEFT JOIN clients c ON i.client_id = c.id
                {where_clause}
                GROUP BY i.client_id
                ORDER BY total_revenue DESC
            """
            cursor = await db.execute(sql, tuple(params))
            rows = await cursor.fetchall()

            clients = []
            period_total = 0.0
            for r in rows:
                rev = round(r["total_revenue"] or 0, 2)
                period_total += rev
                clients.append({
                    "client_id": r["client_id"],
                    "client_name": r["client_name"],
                    "total_revenue": rev,
                    "invoice_count": r["invoice_count"],
                    "avg_invoice": round(r["avg_invoice"] or 0, 2),
                })

        return {
            "clients": clients,
            "period_total": round(period_total, 2),
            "date_from": date_from or None,
            "date_to": date_to or None,
        }

    except Exception as exc:
        logger.error("Eroare revenue-by-client: %s", exc)
        return {"clients": [], "period_total": 0.0}


# ===========================================================================
# EXPORT PDF REPORT
# ===========================================================================

@router.get("/export/pdf")
async def export_pdf_report():
    """Genereaza un raport PDF cu statistici sistem, facturi, activitate zilnica."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib.enums import TA_CENTER
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        )
    except ImportError as exc:
        raise HTTPException(500, f"ReportLab indisponibil: {exc}")

    today = datetime.now().strftime("%d.%m.%Y %H:%M")
    buf = io.BytesIO()

    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontSize=16,
        alignment=TA_CENTER,
        spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontSize=9,
        alignment=TA_CENTER,
        textColor=colors.grey,
        spaceAfter=20,
    )
    section_style = ParagraphStyle(
        "SectionHeader",
        parent=styles["Heading2"],
        fontSize=11,
        spaceBefore=14,
        spaceAfter=6,
        textColor=colors.HexColor("#1d4ed8"),
    )

    _TABLE_STYLE = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a5f")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4f8")]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ])

    story = []

    # --- Title ---
    story.append(Paragraph(f"Raport Sistem — {today}", title_style))
    story.append(Paragraph("Roland Command Center — CIP Inspection SRL", subtitle_style))

    # --- 1. Disk stats ---
    story.append(Paragraph("1. Utilizare Disk", section_style))
    disk = shutil.disk_usage(str(_PROJECT_DIR))
    data_sz = _get_folder_size(_DATA_DIR)
    uploads_sz = _get_folder_size(_UPLOADS_DIR)
    db_path = settings.db_path
    db_sz = db_path.stat().st_size if db_path.exists() else 0

    disk_data = [
        ["Metric", "Valoare"],
        ["Spatiu total disk", _format_size(disk.total)],
        ["Spatiu folosit disk", f"{_format_size(disk.used)} ({round(disk.used / disk.total * 100, 1)}%)"],
        ["Spatiu liber disk", _format_size(disk.free)],
        ["Folder data/", _format_size(data_sz)],
        ["Folder uploads/", _format_size(uploads_sz)],
        ["Baza de date SQLite", _format_size(db_sz)],
    ]
    t = Table(disk_data, colWidths=[9 * cm, 8 * cm])
    t.setStyle(_TABLE_STYLE)
    story.append(t)

    # --- 2. Statistici fisiere ---
    story.append(Paragraph("2. Statistici Fisiere", section_style))
    file_count_data = {"data": 0, "uploads": 0}
    for folder_name, folder_path in [("data", _DATA_DIR), ("uploads", _UPLOADS_DIR)]:
        if folder_path.exists():
            try:
                file_count_data[folder_name] = sum(1 for f in folder_path.rglob("*") if f.is_file())
            except (OSError, PermissionError):
                pass

    files_data = [
        ["Folder", "Numar fisiere", "Dimensiune totala"],
        ["data/", str(file_count_data["data"]), _format_size(data_sz)],
        ["uploads/", str(file_count_data["uploads"]), _format_size(uploads_sz)],
    ]
    t2 = Table(files_data, colWidths=[6 * cm, 5 * cm, 6 * cm])
    t2.setStyle(_TABLE_STYLE)
    story.append(t2)

    # --- 3. Statistici facturi si activitate ---
    story.append(Paragraph("3. Facturi si Activitate", section_style))

    inv_total_month = 0
    inv_count_month = 0
    inv_count_all = 0
    inv_revenue_month = 0.0
    daily_activity: list[dict] = []
    monthly_revenue: list[dict] = []

    try:
        async with get_db() as db:
            # Facturi luna curenta
            try:
                cur = await db.execute(
                    "SELECT COUNT(*) AS cnt, COALESCE(SUM(total), 0) AS rev "
                    "FROM invoices WHERE created_at >= date('now', 'start of month')"
                )
                row = await cur.fetchone()
                if row:
                    inv_count_month = row["cnt"]
                    inv_revenue_month = round(row["rev"], 2)
            except Exception:
                pass

            # Total facturi
            try:
                cur = await db.execute("SELECT COUNT(*) AS cnt FROM invoices")
                row = await cur.fetchone()
                inv_count_all = row["cnt"] if row else 0
            except Exception:
                pass

            # Activitate zilnica — ultimele 7 zile
            try:
                cur = await db.execute(
                    "SELECT date(timestamp) AS day, COUNT(*) AS cnt "
                    "FROM activity_log "
                    "WHERE timestamp >= date('now', '-7 days') "
                    "GROUP BY day ORDER BY day ASC"
                )
                rows = await cur.fetchall()
                daily_activity = [{"day": r["day"], "count": r["cnt"]} for r in rows]
            except Exception:
                pass

            # Venituri lunare — ultimele 6 luni (facturi platite)
            try:
                cur = await db.execute(
                    "SELECT strftime('%Y-%m', date) AS month, "
                    "COUNT(*) AS cnt, COALESCE(SUM(total), 0) AS rev "
                    "FROM invoices WHERE status = 'paid' "
                    "AND date >= date('now', '-6 months') "
                    "GROUP BY month ORDER BY month ASC"
                )
                rows = await cur.fetchall()
                monthly_revenue = [
                    {"month": r["month"], "count": r["cnt"], "revenue": round(r["rev"], 2)}
                    for r in rows
                ]
            except Exception:
                pass
    except Exception as exc:
        logger.error("Eroare PDF export DB query: %s", exc)

    inv_data = [
        ["Metric", "Valoare"],
        ["Total facturi (toate)", str(inv_count_all)],
        ["Facturi luna curenta", str(inv_count_month)],
        ["Venituri luna curenta (platite)", f"{inv_revenue_month:.2f} RON"],
    ]
    t3 = Table(inv_data, colWidths=[9 * cm, 8 * cm])
    t3.setStyle(_TABLE_STYLE)
    story.append(t3)

    # --- 4. Activitate zilnica (ultimele 7 zile) ---
    story.append(Paragraph("4. Activitate Zilnica (ultimele 7 zile)", section_style))
    if daily_activity:
        act_data = [["Data", "Actiuni inregistrate"]]
        for item in daily_activity:
            act_data.append([item["day"], str(item["count"])])
        t4 = Table(act_data, colWidths=[9 * cm, 8 * cm])
        t4.setStyle(_TABLE_STYLE)
        story.append(t4)
    else:
        story.append(Paragraph("Nu exista date de activitate in ultimele 7 zile.", styles["Normal"]))

    # --- 5. Venituri lunare (ultimele 6 luni) ---
    story.append(Paragraph("5. Venituri Lunare — Facturi Platite (ultimele 6 luni)", section_style))
    if monthly_revenue:
        rev_data = [["Luna", "Facturi platite", "Total RON"]]
        for item in monthly_revenue:
            rev_data.append([item["month"], str(item["count"]), f"{item['revenue']:.2f}"])
        t5 = Table(rev_data, colWidths=[6 * cm, 5 * cm, 6 * cm])
        t5.setStyle(_TABLE_STYLE)
        story.append(t5)
    else:
        story.append(Paragraph("Nu exista facturi platite in ultimele 6 luni.", styles["Normal"]))

    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph(
        f"Generat automat de Roland Command Center — {today}",
        ParagraphStyle("Footer", parent=styles["Normal"], fontSize=7,
                       textColor=colors.grey, alignment=TA_CENTER),
    ))

    doc.build(story)
    buf.seek(0)

    filename = f"raport_sistem_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

    await log_activity(
        action="reports.export.pdf",
        summary=f"Raport PDF exportat: {filename}",
    )

    return StreamingResponse(
        buf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ===========================================================================
# DASHBOARD "ZIUA MEA" (My Day)
# ===========================================================================

@router.get("/dashboard/my-day")
async def dashboard_my_day():
    """Sumar zilnic: salut, programari ITP, facturi restante, activitate recenta, statistici luna."""
    now = datetime.now()
    hour = now.hour
    if 5 <= hour < 12:
        greeting = "Buna dimineata, Roland!"
    elif 12 <= hour < 18:
        greeting = "Buna ziua, Roland!"
    else:
        greeting = "Buna seara, Roland!"

    today_str = now.strftime("%Y-%m-%d")

    result: dict[str, Any] = {
        "date": today_str,
        "greeting": greeting,
        "itp": {
            "appointments_today": [],
            "expiring_7_days": 0,
            "overdue_count": 0,
        },
        "invoices": {
            "overdue": [],
            "due_this_week": [],
            "total_receivable": 0.0,
        },
        "recent_activity": [],
        "quick_stats": {
            "invoices_this_month": 0,
            "revenue_this_month": 0.0,
            "translations_this_month": 0,
            "itp_this_month": 0,
        },
    }

    try:
        async with get_db() as db:
            # --- ITP: programari azi ---
            try:
                cursor = await db.execute(
                    "SELECT id, plate_number, owner_name, scheduled_time, status, notes "
                    "FROM itp_appointments "
                    "WHERE scheduled_date = ? "
                    "ORDER BY scheduled_time ASC",
                    (today_str,),
                )
                rows = await cursor.fetchall()
                result["itp"]["appointments_today"] = [
                    {
                        "id": r["id"],
                        "plate_number": r["plate_number"],
                        "owner_name": r["owner_name"],
                        "scheduled_time": r["scheduled_time"],
                        "status": r["status"],
                        "notes": r["notes"],
                    }
                    for r in rows
                ]
            except Exception:
                pass

            # --- ITP: expira in 7 zile ---
            try:
                cursor = await db.execute(
                    "SELECT COUNT(*) AS cnt FROM itp_inspections "
                    "WHERE expiry_date BETWEEN date('now') AND date('now', '+7 days')"
                )
                row = await cursor.fetchone()
                result["itp"]["expiring_7_days"] = row["cnt"] if row else 0
            except Exception:
                pass

            # --- ITP: expirate (overdue) ---
            try:
                cursor = await db.execute(
                    "SELECT COUNT(*) AS cnt FROM itp_inspections "
                    "WHERE expiry_date < date('now')"
                )
                row = await cursor.fetchone()
                result["itp"]["overdue_count"] = row["cnt"] if row else 0
            except Exception:
                pass

            # --- Facturi restante (overdue) ---
            try:
                cursor = await db.execute(
                    "SELECT id, invoice_number, total, due_date, currency "
                    "FROM invoices "
                    "WHERE due_date < date('now') "
                    "AND status NOT IN ('paid', 'cancelled') "
                    "ORDER BY due_date ASC LIMIT 5"
                )
                rows = await cursor.fetchall()
                result["invoices"]["overdue"] = [
                    {
                        "id": r["id"],
                        "invoice_number": r["invoice_number"],
                        "total": r["total"],
                        "due_date": r["due_date"],
                        "currency": r["currency"] or "RON",
                    }
                    for r in rows
                ]
            except Exception:
                pass

            # --- Facturi scadente saptamana aceasta ---
            try:
                cursor = await db.execute(
                    "SELECT id, invoice_number, total, due_date, currency "
                    "FROM invoices "
                    "WHERE due_date BETWEEN date('now') AND date('now', '+7 days') "
                    "AND status NOT IN ('paid', 'cancelled') "
                    "ORDER BY due_date ASC LIMIT 5"
                )
                rows = await cursor.fetchall()
                result["invoices"]["due_this_week"] = [
                    {
                        "id": r["id"],
                        "invoice_number": r["invoice_number"],
                        "total": r["total"],
                        "due_date": r["due_date"],
                        "currency": r["currency"] or "RON",
                    }
                    for r in rows
                ]
            except Exception:
                pass

            # --- Total de incasat ---
            try:
                cursor = await db.execute(
                    "SELECT COALESCE(SUM(total), 0) AS total_sum "
                    "FROM invoices "
                    "WHERE status NOT IN ('paid', 'cancelled', 'draft')"
                )
                row = await cursor.fetchone()
                result["invoices"]["total_receivable"] = round(row["total_sum"], 2) if row else 0.0
            except Exception:
                pass

            # --- Activitate recenta (azi) ---
            try:
                cursor = await db.execute(
                    "SELECT action, summary, status, timestamp "
                    "FROM activity_log "
                    "WHERE date(timestamp) = date('now') "
                    "ORDER BY timestamp DESC LIMIT 5"
                )
                rows = await cursor.fetchall()
                result["recent_activity"] = [
                    {
                        "action": r["action"],
                        "summary": r["summary"],
                        "status": r["status"],
                        "timestamp": r["timestamp"],
                    }
                    for r in rows
                ]
            except Exception:
                pass

            # --- Quick stats: luna curenta ---
            try:
                cursor = await db.execute(
                    "SELECT COUNT(*) AS cnt FROM invoices "
                    "WHERE created_at >= date('now', 'start of month')"
                )
                row = await cursor.fetchone()
                result["quick_stats"]["invoices_this_month"] = row["cnt"] if row else 0
            except Exception:
                pass

            try:
                cursor = await db.execute(
                    "SELECT COALESCE(SUM(total), 0) AS rev FROM invoices "
                    "WHERE status = 'paid' "
                    "AND date >= date('now', 'start of month')"
                )
                row = await cursor.fetchone()
                result["quick_stats"]["revenue_this_month"] = round(row["rev"], 2) if row else 0.0
            except Exception:
                pass

            try:
                cursor = await db.execute(
                    "SELECT COUNT(*) AS cnt FROM activity_log "
                    "WHERE action LIKE 'translator%' "
                    "AND timestamp >= date('now', 'start of month')"
                )
                row = await cursor.fetchone()
                result["quick_stats"]["translations_this_month"] = row["cnt"] if row else 0
            except Exception:
                pass

            try:
                cursor = await db.execute(
                    "SELECT COUNT(*) AS cnt FROM itp_inspections "
                    "WHERE inspection_date >= date('now', 'start of month')"
                )
                row = await cursor.fetchone()
                result["quick_stats"]["itp_this_month"] = row["cnt"] if row else 0
            except Exception:
                pass

    except Exception as exc:
        logger.error("Eroare dashboard my-day: %s", exc)

    return result
