"""Uptime monitor: background ping loops, downtime/recovery notifications."""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timezone

import httpx

from app.db.database import get_db

from .models import row_dict

logger = logging.getLogger(__name__)

# Background monitor tasks keyed by monitor ID
_monitor_tasks: dict[int, asyncio.Task] = {}

# Downtime notification cooldown (30 min per monitor)
_downtime_cooldowns: dict[int, float] = {}
_DOWNTIME_COOLDOWN_SECS = 30 * 60


async def _create_downtime_notification(
    monitor_name: str, url: str, error: str | None, monitor_id: int | None = None,
) -> None:
    """Insert a notification when a monitor transitions to down state."""
    if monitor_id is not None:
        last_notified = _downtime_cooldowns.get(monitor_id, 0)
        if (time.time() - last_notified) < _DOWNTIME_COOLDOWN_SECS:
            logger.debug("Cooldown activ pentru monitor %d, skip notificare DOWN", monitor_id)
            return
        _downtime_cooldowns[monitor_id] = time.time()

    try:
        msg = f"Monitorul '{monitor_name}' ({url}) este DOWN."
        if error:
            msg += f" Eroare: {error[:200]}"
        async with get_db() as db:
            await db.execute(
                """INSERT INTO notifications (title, message, type, source, link)
                   VALUES (?, ?, 'error', 'uptime_monitor', NULL)""",
                (f"Downtime: {monitor_name}", msg),
            )
            await db.commit()
        logger.info("Notificare downtime creata pentru: %s", monitor_name)
    except Exception as exc:
        logger.warning("Eroare creare notificare downtime: %s", exc)


async def _create_recovery_notification(monitor_name: str, url: str) -> None:
    """Insert a notification when a monitor recovers (FAIL -> OK transition)."""
    try:
        msg = f"Monitorul '{monitor_name}' ({url}) este din nou UP."
        async with get_db() as db:
            await db.execute(
                """INSERT INTO notifications (title, message, type, source, link)
                   VALUES (?, ?, 'success', 'uptime_monitor', NULL)""",
                (f"Recovery: {monitor_name}", msg),
            )
            await db.commit()
        logger.info("Notificare recovery creata pentru: %s", monitor_name)
    except Exception as exc:
        logger.warning("Eroare creare notificare recovery: %s", exc)


async def _ping_url(monitor_id: int, url: str) -> dict:
    """Ping a URL and return status info."""
    try:
        async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
            start = time.monotonic()
            resp = await client.get(url)
            elapsed_ms = int((time.monotonic() - start) * 1000)
            return {
                "status_code": resp.status_code,
                "response_ms": elapsed_ms,
                "error": None,
            }
    except Exception as exc:
        return {
            "status_code": 0,
            "response_ms": 0,
            "error": str(exc)[:500],
        }


async def _monitor_loop(monitor_id: int, url: str, interval: int) -> None:
    """Background loop that pings a URL at intervals, with downtime alerting."""
    prev_ok = True

    try:
        async with get_db() as db:
            cursor = await db.execute(
                "SELECT last_status, name FROM uptime_monitors WHERE id = ?",
                (monitor_id,),
            )
            row = await cursor.fetchone()
            if row:
                last_status = row_dict(row).get("last_status")
                if last_status is not None:
                    prev_ok = 200 <= last_status < 400
    except Exception:
        pass

    while True:
        try:
            result = await _ping_url(monitor_id, url)
            now = datetime.now(timezone.utc).isoformat()

            current_ok = (200 <= result["status_code"] < 400) and result["error"] is None

            async with get_db() as db:
                await db.execute(
                    """INSERT INTO uptime_history (monitor_id, status_code, response_ms, error, checked_at)
                       VALUES (?, ?, ?, ?, ?)""",
                    (monitor_id, result["status_code"], result["response_ms"], result["error"], now),
                )
                await db.execute(
                    """UPDATE uptime_monitors
                       SET last_status = ?, last_response_ms = ?, last_check = ?
                       WHERE id = ?""",
                    (result["status_code"], result["response_ms"], now, monitor_id),
                )
                await db.commit()

                cursor = await db.execute(
                    "SELECT name FROM uptime_monitors WHERE id = ?", (monitor_id,)
                )
                mon_row = await cursor.fetchone()
                mon_name = row_dict(mon_row)["name"] if mon_row else f"Monitor #{monitor_id}"

                if prev_ok and not current_ok:
                    await _create_downtime_notification(
                        mon_name, url, result.get("error"), monitor_id=monitor_id
                    )

                if not prev_ok and current_ok:
                    await _create_recovery_notification(mon_name, url)

            prev_ok = current_ok

        except Exception as exc:
            logger.warning("Monitor %d ping error: %s", monitor_id, exc)

        await asyncio.sleep(interval)


def start_monitor(monitor_id: int, url: str, interval: int) -> None:
    """Start a background monitor task."""
    if monitor_id in _monitor_tasks:
        _monitor_tasks[monitor_id].cancel()
    _monitor_tasks[monitor_id] = asyncio.create_task(
        _monitor_loop(monitor_id, url, interval)
    )


def stop_monitor(monitor_id: int) -> None:
    """Stop a background monitor task."""
    task = _monitor_tasks.pop(monitor_id, None)
    if task:
        task.cancel()


def is_monitor_running(monitor_id: int) -> bool:
    """Check if a monitor background task is running."""
    return monitor_id in _monitor_tasks


async def resume_uptime_monitors() -> None:
    """Resume all enabled uptime monitors after server restart."""
    try:
        async with get_db() as db:
            cursor = await db.execute(
                "SELECT id, url, interval_seconds FROM uptime_monitors WHERE enabled = 1"
            )
            monitors = await cursor.fetchall()

        resumed = 0
        for row in monitors:
            monitor_id, url, interval = row[0], row[1], row[2]
            start_monitor(monitor_id, url, interval)
            resumed += 1

        if resumed:
            logger.info("Uptime monitors resumed: %d monitors restarted.", resumed)
    except Exception as exc:
        logger.warning("Nu s-au putut relua uptime monitors: %s", exc)
