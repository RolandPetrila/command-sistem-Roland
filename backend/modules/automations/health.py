"""Health check: comprehensive system health report."""

from __future__ import annotations

import shutil
from datetime import datetime, timezone
from typing import Any

from app.db.database import get_db

from .models import row_dict


async def build_health_report() -> dict[str, Any]:
    """Build a comprehensive health report."""
    report: dict[str, Any] = {}

    # Database
    try:
        async with get_db() as db:
            cursor = await db.execute("SELECT COUNT(*) as cnt FROM schema_version")
            row = await cursor.fetchone()
            migrations = row["cnt"] if row else 0
            report["database"] = {
                "status": "ok",
                "migrations_applied": migrations,
            }
    except Exception as exc:
        report["database"] = {"status": "error", "error": str(exc)[:200]}

    # Disk space
    try:
        from app.config import settings
        usage = shutil.disk_usage(str(settings.data_dir))
        free_gb = usage.free / (1024 ** 3)
        total_gb = usage.total / (1024 ** 3)
        used_pct = ((usage.total - usage.free) / usage.total) * 100
        report["disk"] = {
            "status": "ok" if free_gb > 1 else ("warning" if free_gb > 0.2 else "error"),
            "free_gb": round(free_gb, 2),
            "total_gb": round(total_gb, 2),
            "used_percent": round(used_pct, 1),
        }
    except Exception as exc:
        report["disk"] = {"status": "error", "error": str(exc)[:200]}

    # Modules
    try:
        from app.module_discovery import discover_modules
        modules = discover_modules()
        report["modules"] = {
            "status": "ok",
            "count": len(modules),
            "names": [m["name"] for m in modules],
        }
    except Exception as exc:
        report["modules"] = {"status": "error", "error": str(exc)[:200]}

    # API keys configured (from vault)
    try:
        async with get_db() as db:
            cursor = await db.execute("SELECT name FROM vault_keys")
            keys = [row_dict(r)["name"] for r in await cursor.fetchall()]
            report["api_keys"] = {
                "status": "ok" if keys else "warning",
                "count": len(keys),
                "configured": keys,
            }
    except Exception:
        report["api_keys"] = {"status": "info", "count": 0, "configured": []}

    # Recent errors from activity log
    try:
        async with get_db() as db:
            cursor = await db.execute(
                """SELECT action, summary, timestamp
                   FROM activity_log
                   WHERE status = 'error'
                   ORDER BY timestamp DESC
                   LIMIT 5"""
            )
            errors = [row_dict(r) for r in await cursor.fetchall()]
            report["recent_errors"] = {
                "status": "ok" if not errors else "warning",
                "count": len(errors),
                "items": errors,
            }
    except Exception:
        report["recent_errors"] = {"status": "info", "count": 0, "items": []}

    # Uptime monitors summary
    try:
        async with get_db() as db:
            cursor = await db.execute("SELECT COUNT(*) as cnt FROM uptime_monitors")
            row = await cursor.fetchone()
            total = row["cnt"] if row else 0

            cursor2 = await db.execute(
                "SELECT COUNT(*) as cnt FROM uptime_monitors WHERE last_status >= 200 AND last_status < 400"
            )
            row2 = await cursor2.fetchone()
            healthy = row2["cnt"] if row2 else 0

            report["uptime_monitors"] = {
                "status": "ok" if total == 0 or healthy == total else "warning",
                "total": total,
                "healthy": healthy,
            }
    except Exception:
        report["uptime_monitors"] = {"status": "info", "total": 0, "healthy": 0}

    return report
