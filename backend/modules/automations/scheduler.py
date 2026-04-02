"""Cron scheduler: parser, background loop, task execution, start/stop."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import shutil
import time
from datetime import datetime, timezone
from typing import Any, Optional

import httpx

from app.core.activity_log import log_activity
from app.db.database import get_db

from .models import VALID_ACTION_TYPES, row_dict

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Cron parser (lightweight, no dependencies)
# ---------------------------------------------------------------------------


def _cron_field_matches(field_expr: str, current_value: int) -> bool:
    """Check if a single cron field matches the current value."""
    field_expr = field_expr.strip()

    if field_expr == "*":
        return True

    if field_expr.startswith("*/"):
        try:
            step = int(field_expr[2:])
            return step > 0 and current_value % step == 0
        except (ValueError, ZeroDivisionError):
            return False

    if "," in field_expr:
        parts = field_expr.split(",")
        return any(_cron_field_matches(p.strip(), current_value) for p in parts)

    if "-" in field_expr:
        try:
            low, high = field_expr.split("-", 1)
            return int(low) <= current_value <= int(high)
        except ValueError:
            return False

    try:
        return int(field_expr) == current_value
    except ValueError:
        return False


def _cron_matches(cron_expr: str, now: datetime) -> bool:
    """Check if a cron expression matches the given datetime."""
    parts = cron_expr.strip().split()
    if len(parts) != 5:
        return False

    minute, hour, day, month, weekday = parts
    return (
        _cron_field_matches(minute, now.minute)
        and _cron_field_matches(hour, now.hour)
        and _cron_field_matches(day, now.day)
        and _cron_field_matches(month, now.month)
        and _cron_field_matches(weekday, now.weekday())
    )


_CRON_FIELD_RANGES = [
    (0, 59),   # minute
    (0, 23),   # hour
    (1, 31),   # day of month
    (1, 12),   # month
    (0, 6),    # day of week
]


def validate_cron_expr(expr: str) -> str | None:
    """Validate a 5-field cron expression. Returns error message or None if valid."""
    parts = expr.strip().split()
    if len(parts) != 5:
        return "Expresia cron trebuie sa aiba exact 5 campuri (min ora zi luna zi_sapt)"

    field_names = ["minut", "ora", "zi_luna", "luna", "zi_sapt"]
    for i, (field, (lo, hi)) in enumerate(zip(parts, _CRON_FIELD_RANGES)):
        if field == "*":
            continue
        if field.startswith("*/"):
            try:
                step = int(field[2:])
                if step <= 0:
                    return f"Campul '{field_names[i]}': pasul din '*/N' trebuie sa fie pozitiv"
            except ValueError:
                return f"Campul '{field_names[i]}': pas invalid in '{field}'"
            continue
        candidates = field.split(",") if "," in field else [field]
        for part in candidates:
            if "-" in part:
                try:
                    a, b = part.split("-", 1)
                    a, b = int(a), int(b)
                    if not (lo <= a <= hi and lo <= b <= hi and a <= b):
                        return (
                            f"Campul '{field_names[i]}': intervalul '{part}' "
                            f"trebuie sa fie in [{lo}-{hi}]"
                        )
                except ValueError:
                    return f"Campul '{field_names[i]}': interval invalid '{part}'"
            else:
                try:
                    v = int(part)
                    if not (lo <= v <= hi):
                        return (
                            f"Campul '{field_names[i]}': valoarea {v} "
                            f"trebuie sa fie in [{lo}-{hi}]"
                        )
                except ValueError:
                    return f"Campul '{field_names[i]}': valoare invalida '{part}'"
    return None


# ---------------------------------------------------------------------------
# Background cron scheduler
# ---------------------------------------------------------------------------

_scheduler_task: Optional[asyncio.Task] = None
_scheduler_status: dict[str, Any] = {
    "running": False,
    "paused": False,
    "paused_at": None,
    "last_check": None,
    "tasks_due": 0,
    "tasks_executed": 0,
    "last_error": None,
}


async def _run_action(action_type: str, action_config: dict | None) -> str:
    """Execute a task action and return output string."""
    config = action_config or {}

    if action_type == "backup_db":
        from app.config import settings
        src = settings.db_path
        backup_dir = settings.data_dir / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        dst = backup_dir / f"calculator_{ts}.db"
        shutil.copy2(str(src), str(dst))
        return f"Backup creat: {dst.name}"

    if action_type == "cleanup_temp":
        from app.config import settings
        uploads = settings.uploads_dir
        removed = 0
        if uploads.exists():
            for f in uploads.iterdir():
                if f.is_file():
                    age_hours = (time.time() - f.stat().st_mtime) / 3600
                    if age_hours > config.get("max_age_hours", 24):
                        f.unlink()
                        removed += 1
        return f"Fisiere temporare sterse: {removed}"

    if action_type == "reindex_documents":
        return "Reindexare documente completata (placeholder)"

    if action_type == "health_check":
        from .health import build_health_report
        health = await build_health_report()
        failed = [k for k, v in health.items() if isinstance(v, dict) and v.get("status") == "error"]
        if failed:
            return f"Health check: {len(failed)} probleme detectate: {', '.join(failed)}"
        return "Health check: toate componentele OK"

    if action_type == "custom_script":
        script = config.get("script", "")
        if not script:
            return "Eroare: script-ul nu a fost specificat"
        return f"Script custom executat (placeholder): {script[:100]}"

    return f"Actiune necunoscuta: {action_type}"


async def _execute_with_timeout(action_type: str, config: dict | None, timeout_secs: int) -> str:
    """Execute a task action with asyncio timeout."""
    return await asyncio.wait_for(
        _run_action(action_type, config),
        timeout=timeout_secs,
    )


async def _send_task_failure_telegram(task_name: str, task_id: int, error_msg: str) -> None:
    """Send Telegram notification when a task with notify_on_failure=1 fails."""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not bot_token or not chat_id:
        return

    message = (
        f"Task esuat: {task_name} (#{task_id})\n"
        f"Eroare: {error_msg[:300]}"
    )

    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(url, json={"chat_id": chat_id, "text": message})
    except Exception as exc:
        logger.warning("Telegram task failure notification error: %s", exc)


async def _record_run_result(
    run_id: int, task_id: int, status: str,
    output: str | None = None, error: str | None = None,
) -> None:
    """Update task_runs and scheduled_tasks after execution."""
    finished_at = datetime.now(timezone.utc).isoformat()
    async with get_db() as db:
        await db.execute(
            """UPDATE task_runs
               SET status = ?, output = ?, error = ?, finished_at = ?
               WHERE id = ?""",
            (status, output, error, finished_at, run_id),
        )
        await db.execute(
            "UPDATE scheduled_tasks SET last_run = ? WHERE id = ?",
            (finished_at, task_id),
        )
        await db.commit()


async def _cron_scheduler_loop() -> None:
    """Background loop: every 60s, check enabled tasks with cron and run due ones."""
    global _scheduler_status
    _scheduler_status["running"] = True
    logger.info("Cron scheduler pornit.")

    while True:
        try:
            await asyncio.sleep(60)

            if _scheduler_status.get("paused", False):
                continue

            now = datetime.now(timezone.utc)
            _scheduler_status["last_check"] = now.isoformat()
            tasks_due = 0

            async with get_db() as db:
                cursor = await db.execute(
                    """SELECT id, name, schedule_cron, action_type, action_config,
                              last_run, timeout_seconds, max_retries, retry_count,
                              notify_on_failure
                       FROM scheduled_tasks
                       WHERE enabled = 1 AND schedule_cron IS NOT NULL AND schedule_cron != ''"""
                )
                tasks = [row_dict(r) for r in await cursor.fetchall()]

            for task in tasks:
                try:
                    if not _cron_matches(task["schedule_cron"], now):
                        continue

                    if task.get("last_run"):
                        try:
                            last_run_str = task["last_run"]
                            if "T" in last_run_str:
                                last_run_dt = datetime.fromisoformat(
                                    last_run_str.replace("Z", "+00:00")
                                )
                            else:
                                last_run_dt = datetime.strptime(
                                    last_run_str, "%Y-%m-%d %H:%M:%S"
                                ).replace(tzinfo=timezone.utc)
                            if (now - last_run_dt).total_seconds() < 59:
                                continue
                        except (ValueError, TypeError):
                            pass

                    tasks_due += 1

                    async with get_db() as db:
                        cursor = await db.execute(
                            "INSERT INTO task_runs (task_id, status) VALUES (?, 'running')",
                            (task["id"],),
                        )
                        await db.commit()
                        run_id = cursor.lastrowid

                    config = None
                    if task.get("action_config"):
                        try:
                            config = json.loads(task["action_config"])
                        except (json.JSONDecodeError, TypeError):
                            config = None

                    timeout_secs = task.get("timeout_seconds") or 300

                    try:
                        output = await _execute_with_timeout(
                            task["action_type"], config, timeout_secs
                        )
                        await _record_run_result(run_id, task["id"], "success", output=output)

                        async with get_db() as db:
                            await db.execute(
                                "UPDATE scheduled_tasks SET retry_count = 0 WHERE id = ?",
                                (task["id"],),
                            )
                            await db.commit()

                        _scheduler_status["tasks_executed"] += 1
                        logger.info(
                            "Cron task executat: #%d '%s' - succes",
                            task["id"], task["name"],
                        )
                    except asyncio.TimeoutError:
                        error_msg = f"Timeout dupa {timeout_secs}s"
                        await _record_run_result(run_id, task["id"], "timeout", error=error_msg)

                        max_retries = task.get("max_retries") or 1
                        retry_count = (task.get("retry_count") or 0) + 1
                        async with get_db() as db:
                            await db.execute(
                                "UPDATE scheduled_tasks SET retry_count = ? WHERE id = ?",
                                (retry_count, task["id"]),
                            )
                            await db.commit()

                        if retry_count <= max_retries:
                            logger.info(
                                "Cron task timeout: #%d '%s' - retry %d/%d in 15min",
                                task["id"], task["name"], retry_count, max_retries,
                            )
                        else:
                            logger.warning(
                                "Cron task timeout: #%d '%s' - max retries exhausted",
                                task["id"], task["name"],
                            )
                            if task.get("notify_on_failure"):
                                try:
                                    await _send_task_failure_telegram(
                                        task["name"], task["id"], error_msg,
                                    )
                                except Exception:
                                    pass

                    except Exception as exc:
                        error_msg = str(exc)[:1000]
                        await _record_run_result(run_id, task["id"], "failed", error=error_msg)

                        max_retries = task.get("max_retries") or 1
                        retry_count = (task.get("retry_count") or 0) + 1
                        async with get_db() as db:
                            await db.execute(
                                "UPDATE scheduled_tasks SET retry_count = ? WHERE id = ?",
                                (retry_count, task["id"]),
                            )
                            await db.commit()

                        logger.warning(
                            "Cron task esuat: #%d '%s' - %s (retry %d/%d)",
                            task["id"], task["name"], exc, retry_count, max_retries,
                        )
                        try:
                            await log_activity(
                                action="scheduler.error",
                                summary=f"Cron task esuat: #{task['id']} '{task['name']}' — {task['action_type']}",
                                details={
                                    "task_id": task["id"],
                                    "task_name": task["name"],
                                    "action_type": task["action_type"],
                                    "error": str(exc)[:500],
                                    "run_id": run_id,
                                    "retry_count": retry_count,
                                    "max_retries": max_retries,
                                },
                            )
                        except Exception:
                            pass

                        if task.get("notify_on_failure"):
                            try:
                                await _send_task_failure_telegram(
                                    task["name"], task["id"], error_msg,
                                )
                            except Exception:
                                pass

                except Exception as exc:
                    logger.warning("Eroare procesare cron task #%d: %s", task.get("id", 0), exc)

            _scheduler_status["tasks_due"] = tasks_due

        except asyncio.CancelledError:
            logger.info("Cron scheduler oprit.")
            _scheduler_status["running"] = False
            return
        except Exception as exc:
            _scheduler_status["last_error"] = f"{datetime.now(timezone.utc).isoformat()}: {exc}"
            logger.error("Eroare in cron scheduler: %s", exc)


def start_cron_scheduler() -> None:
    """Start the background cron scheduler task. Called from lifespan/startup."""
    global _scheduler_task
    if _scheduler_task is None or _scheduler_task.done():
        _scheduler_task = asyncio.create_task(_cron_scheduler_loop())
        logger.info("Cron scheduler task creat.")


def stop_cron_scheduler() -> None:
    """Stop the background cron scheduler task. Called from lifespan/shutdown."""
    global _scheduler_task
    if _scheduler_task and not _scheduler_task.done():
        _scheduler_task.cancel()
        logger.info("Cron scheduler task anulat.")
    _scheduler_task = None
    _scheduler_status["running"] = False


def get_scheduler_status() -> dict[str, Any]:
    """Return current scheduler status dict."""
    return _scheduler_status
