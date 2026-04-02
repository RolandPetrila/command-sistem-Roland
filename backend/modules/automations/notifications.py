"""Notification CRUD, daily digest, and activity log cleanup."""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone

import httpx

from app.core.activity_log import log_activity
from app.db.database import get_db

from .models import row_dict

logger = logging.getLogger(__name__)


async def send_daily_digest() -> None:
    """Send a daily stats summary via Telegram."""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not bot_token or not chat_id:
        logger.debug("Telegram credentials not set, skipping daily digest")
        return

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    stats = {
        "invoices_count": 0,
        "invoices_total": 0.0,
        "translations_count": 0,
        "itp_count": 0,
        "time_tracked_hours": 0.0,
    }

    try:
        async with get_db() as db:
            try:
                cursor = await db.execute(
                    "SELECT COUNT(*) AS cnt, COALESCE(SUM(total), 0) AS total_sum "
                    "FROM invoices WHERE date(created_at) = ?",
                    (today,),
                )
                row = await cursor.fetchone()
                if row:
                    stats["invoices_count"] = row["cnt"]
                    stats["invoices_total"] = round(row["total_sum"], 2)
            except Exception:
                pass

            try:
                cursor = await db.execute(
                    "SELECT COUNT(*) AS cnt FROM activity_log "
                    "WHERE action LIKE 'translator%' AND date(timestamp) = ?",
                    (today,),
                )
                row = await cursor.fetchone()
                stats["translations_count"] = row["cnt"] if row else 0
            except Exception:
                pass

            try:
                cursor = await db.execute(
                    "SELECT COUNT(*) AS cnt FROM itp_inspections "
                    "WHERE date(inspection_date) = ?",
                    (today,),
                )
                row = await cursor.fetchone()
                stats["itp_count"] = row["cnt"] if row else 0
            except Exception:
                pass

            try:
                cursor = await db.execute(
                    "SELECT COALESCE(SUM(duration_minutes), 0) AS total_min "
                    "FROM time_entries WHERE date(start_time) = ?",
                    (today,),
                )
                row = await cursor.fetchone()
                stats["time_tracked_hours"] = round((row["total_min"] or 0) / 60, 1)
            except Exception:
                pass

        message = (
            f"Sumar zilnic - {today}\n\n"
            f"Facturi: {stats['invoices_count']} ({stats['invoices_total']:.2f} RON)\n"
            f"Traduceri: {stats['translations_count']}\n"
            f"ITP: {stats['itp_count']}\n"
            f"Timp lucrat: {stats['time_tracked_hours']}h\n"
        )

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json={
                "chat_id": chat_id,
                "text": message,
            })
            if resp.status_code == 200:
                await log_activity(
                    action="automations.daily_digest",
                    summary=f"Sumar zilnic trimis: {stats['invoices_count']} facturi, "
                            f"{stats['translations_count']} traduceri, {stats['itp_count']} ITP",
                    details=stats,
                )
                logger.info("Daily digest sent successfully")
            else:
                logger.warning("Daily digest Telegram send failed: HTTP %d", resp.status_code)

    except Exception as exc:
        logger.error("Error sending daily digest: %s", exc)


async def cleanup_old_activity_logs() -> None:
    """Delete activity_log entries older than 90 days (180 for errors), then VACUUM."""
    try:
        async with get_db() as db:
            cursor = await db.execute(
                "DELETE FROM activity_log "
                "WHERE status != 'error' AND timestamp < datetime('now', '-90 days')"
            )
            deleted_normal = cursor.rowcount

            cursor = await db.execute(
                "DELETE FROM activity_log "
                "WHERE status = 'error' AND timestamp < datetime('now', '-180 days')"
            )
            deleted_errors = cursor.rowcount

            await db.commit()

            try:
                await db.execute("VACUUM")
            except Exception as vac_exc:
                logger.warning("VACUUM failed (non-critical): %s", vac_exc)

        total = deleted_normal + deleted_errors
        if total > 0:
            await log_activity(
                action="automations.cleanup_activity_log",
                summary=f"Cleanup activity_log: {total} intrari sterse "
                        f"({deleted_normal} normale >90 zile, {deleted_errors} erori >180 zile)",
                details={"deleted_normal": deleted_normal, "deleted_errors": deleted_errors},
            )
        logger.info(
            "Activity log cleanup: %d normal + %d errors deleted",
            deleted_normal, deleted_errors,
        )

    except Exception as exc:
        logger.error("Error cleaning up activity logs: %s", exc)
