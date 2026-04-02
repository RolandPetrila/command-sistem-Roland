"""
Automations module endpoints: Task Scheduler, Shortcuts, Uptime Monitor,
API Tester, Health Monitor, Notifications, Cron Scheduler.

Endpoints:
  GET    /api/automations/tasks              — List scheduled tasks
  POST   /api/automations/tasks              — Create task
  PUT    /api/automations/tasks/:id          — Update task
  DELETE /api/automations/tasks/:id          — Delete task
  POST   /api/automations/tasks/:id/run      — Run task manually

  GET    /api/automations/shortcuts           — List shortcuts
  POST   /api/automations/shortcuts           — Create shortcut
  PUT    /api/automations/shortcuts/:id       — Update shortcut
  DELETE /api/automations/shortcuts/:id       — Delete shortcut

  GET    /api/automations/monitors            — List uptime monitors
  POST   /api/automations/monitors            — Add monitor
  PUT    /api/automations/monitors/:id        — Update monitor
  DELETE /api/automations/monitors/:id        — Remove monitor
  GET    /api/automations/monitors/:id/history — Ping history

  POST   /api/automations/api-test            — Execute HTTP request
  GET    /api/automations/api-test/history     — Last 20 requests
  POST   /api/automations/api-test/save        — Save as template
  GET    /api/automations/api-test/saved        — List saved templates

  GET    /api/automations/health              — Comprehensive health check

  GET    /api/automations/scheduler/status    — Cron scheduler status
  POST   /api/automations/cleanup             — Cleanup old history records

  GET    /api/automations/notifications       — List notifications
  POST   /api/automations/notifications       — Create notification (internal)
  PUT    /api/automations/notifications/:id/read — Mark notification read
  PUT    /api/automations/notifications/read-all — Mark all read
  DELETE /api/automations/notifications/:id   — Delete notification
  POST   /api/automations/notify              — Internal: create notification from any module
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, HTTPException

from app.core.activity_log import log_activity
from app.db.database import get_db

from .health import build_health_report
from .models import (
    VALID_ACTION_TYPES,
    ApiTestRequest,
    ApiTestSave,
    MonitorCreate,
    MonitorUpdate,
    NotificationCreate,
    NotifyRequest,
    ShortcutCreate,
    ShortcutUpdate,
    TaskCreateModel,
    TaskUpdateModel,
    row_dict,
)
from .monitors import is_monitor_running, start_monitor, stop_monitor
from .scheduler import (
    _execute_with_timeout,
    _record_run_result,
    _send_task_failure_telegram,
    get_scheduler_status,
    validate_cron_expr,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/automations", tags=["Automations"])

# Re-export lifecycle functions so main.py imports still work
from .monitors import resume_uptime_monitors as resume_uptime_monitors  # noqa: E402, F401
from .scheduler import start_cron_scheduler as start_cron_scheduler  # noqa: E402, F401
from .scheduler import stop_cron_scheduler as stop_cron_scheduler  # noqa: E402, F401

# Also re-export notifications functions used externally
from .notifications import cleanup_old_activity_logs as cleanup_old_activity_logs  # noqa: E402, F401
from .notifications import send_daily_digest as send_daily_digest  # noqa: E402, F401


# ═══════════════════════════════════════════
# Task Scheduler CRUD
# ═══════════════════════════════════════════


@router.get("/tasks")
async def list_tasks():
    """List all scheduled tasks with their last run info."""
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT t.*,
                   lr.id as lr_id, lr.started_at as lr_started_at,
                   lr.finished_at as lr_finished_at, lr.status as lr_status,
                   lr.output as lr_output, lr.error as lr_error
            FROM scheduled_tasks t
            LEFT JOIN (
                SELECT *, ROW_NUMBER() OVER (PARTITION BY task_id ORDER BY started_at DESC) as rn
                FROM task_runs
            ) lr ON lr.task_id = t.id AND lr.rn = 1
            ORDER BY t.created_at DESC
        """)
        rows = await cursor.fetchall()
        tasks = []
        for r in rows:
            rd = row_dict(r)
            last_run = None
            if rd.get("lr_id"):
                last_run = {
                    "id": rd.pop("lr_id"),
                    "started_at": rd.pop("lr_started_at"),
                    "finished_at": rd.pop("lr_finished_at"),
                    "status": rd.pop("lr_status"),
                    "output": rd.pop("lr_output"),
                    "error": rd.pop("lr_error"),
                }
            else:
                rd.pop("lr_id", None)
                rd.pop("lr_started_at", None)
                rd.pop("lr_finished_at", None)
                rd.pop("lr_status", None)
                rd.pop("lr_output", None)
                rd.pop("lr_error", None)
            rd.pop("rn", None)
            rd["last_run_info"] = last_run
            if rd.get("action_config"):
                try:
                    rd["action_config"] = json.loads(rd["action_config"])
                except (json.JSONDecodeError, TypeError):
                    pass
            tasks.append(rd)

        return tasks


@router.post("/tasks")
async def create_task(body: TaskCreateModel):
    """Create a new scheduled task."""
    if body.action_type not in VALID_ACTION_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Tip actiune invalid. Valide: {', '.join(VALID_ACTION_TYPES)}",
        )

    if body.schedule_cron:
        cron_error = validate_cron_expr(body.schedule_cron)
        if cron_error:
            raise HTTPException(status_code=400, detail=f"Expresie cron invalida: {cron_error}")

    config_json = json.dumps(body.action_config) if body.action_config else None

    async with get_db() as db:
        cursor = await db.execute(
            """INSERT INTO scheduled_tasks
               (name, schedule_cron, action_type, action_config, enabled, timeout_seconds, max_retries)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (body.name, body.schedule_cron, body.action_type, config_json,
             int(body.enabled), body.timeout_seconds, body.max_retries),
        )
        await db.commit()
        task_id = cursor.lastrowid

    await log_activity(
        action="automations.task_create",
        summary=f"Task creat: {body.name} ({body.action_type})",
    )
    return {"id": task_id, "status": "created"}


@router.put("/tasks/{task_id}")
async def update_task(task_id: int, body: TaskUpdateModel):
    """Update an existing scheduled task."""
    async with get_db() as db:
        cursor = await db.execute("SELECT id FROM scheduled_tasks WHERE id = ?", (task_id,))
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="Task negasit")

        updates = []
        params = []

        if body.name is not None:
            updates.append("name = ?")
            params.append(body.name)
        if body.schedule_cron is not None:
            cron_error = validate_cron_expr(body.schedule_cron)
            if cron_error:
                raise HTTPException(status_code=400, detail=f"Expresie cron invalida: {cron_error}")
            updates.append("schedule_cron = ?")
            params.append(body.schedule_cron)
        if body.action_type is not None:
            if body.action_type not in VALID_ACTION_TYPES:
                raise HTTPException(
                    status_code=400,
                    detail=f"Tip actiune invalid. Valide: {', '.join(VALID_ACTION_TYPES)}",
                )
            updates.append("action_type = ?")
            params.append(body.action_type)
        if body.action_config is not None:
            updates.append("action_config = ?")
            params.append(json.dumps(body.action_config))
        if body.enabled is not None:
            updates.append("enabled = ?")
            params.append(int(body.enabled))
        if body.timeout_seconds is not None:
            updates.append("timeout_seconds = ?")
            params.append(body.timeout_seconds)
        if body.max_retries is not None:
            updates.append("max_retries = ?")
            params.append(body.max_retries)

        if not updates:
            raise HTTPException(status_code=400, detail="Nimic de actualizat")

        params.append(task_id)
        await db.execute(
            f"UPDATE scheduled_tasks SET {', '.join(updates)} WHERE id = ?",
            tuple(params),
        )
        await db.commit()

    await log_activity(
        action="automations.task_update",
        summary=f"Task actualizat: #{task_id}",
    )
    return {"status": "updated"}


@router.delete("/tasks/{task_id}")
async def delete_task(task_id: int):
    """Delete a scheduled task and its run history."""
    async with get_db() as db:
        cursor = await db.execute("SELECT id FROM scheduled_tasks WHERE id = ?", (task_id,))
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="Task negasit")

        await db.execute("DELETE FROM task_runs WHERE task_id = ?", (task_id,))
        await db.execute("DELETE FROM scheduled_tasks WHERE id = ?", (task_id,))
        await db.commit()

    await log_activity(
        action="automations.task_delete",
        summary=f"Task sters: #{task_id}",
    )
    return {"status": "deleted"}


@router.post("/tasks/{task_id}/run")
async def run_task_now(task_id: int):
    """Run a task manually right now (background execution)."""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM scheduled_tasks WHERE id = ?", (task_id,)
        )
        task = await cursor.fetchone()
        if not task:
            raise HTTPException(status_code=404, detail="Task negasit")

        task_dict = row_dict(task)

    async with get_db() as db:
        cursor = await db.execute(
            "INSERT INTO task_runs (task_id, status) VALUES (?, 'running')",
            (task_id,),
        )
        await db.commit()
        run_id = cursor.lastrowid

    async def _execute():
        try:
            config = None
            if task_dict.get("action_config"):
                try:
                    config = json.loads(task_dict["action_config"])
                except (json.JSONDecodeError, TypeError):
                    config = None

            timeout_secs = task_dict.get("timeout_seconds") or 300
            output = await _execute_with_timeout(
                task_dict["action_type"], config, timeout_secs
            )
            await _record_run_result(run_id, task_id, "success", output=output)

            await log_activity(
                action="automations.task_run",
                summary=f"Task executat: {task_dict['name']} - succes",
                details={"output": output[:500]},
            )
        except asyncio.TimeoutError:
            timeout_secs = task_dict.get("timeout_seconds") or 300
            error_msg = f"Timeout dupa {timeout_secs}s"
            await _record_run_result(run_id, task_id, "timeout", error=error_msg)
            logger.warning("Task manual timeout: #%d '%s'", task_id, task_dict["name"])
        except Exception as exc:
            logger.error("Task run failed: %s", exc)
            await _record_run_result(run_id, task_id, "failed", error=str(exc)[:1000])
            try:
                await log_activity(
                    action="scheduler.error",
                    summary=f"Task manual esuat: #{task_id} '{task_dict['name']}' — {task_dict['action_type']}",
                    details={
                        "task_id": task_id,
                        "task_name": task_dict["name"],
                        "action_type": task_dict["action_type"],
                        "error": str(exc)[:500],
                        "run_id": run_id,
                    },
                )
            except Exception:
                pass
            if task_dict.get("notify_on_failure"):
                try:
                    await _send_task_failure_telegram(
                        task_dict["name"], task_id, str(exc)[:300],
                    )
                except Exception:
                    pass

    asyncio.create_task(_execute())

    return {"run_id": run_id, "status": "started"}


@router.get("/scheduler/status")
async def scheduler_status():
    """Return the cron scheduler status."""
    status = get_scheduler_status()
    active_tasks = 0
    try:
        async with get_db() as db:
            cursor = await db.execute(
                "SELECT COUNT(*) as cnt FROM scheduled_tasks WHERE enabled = 1"
            )
            row = await cursor.fetchone()
            active_tasks = row["cnt"] if row else 0
    except Exception:
        pass

    return {
        "running": status.get("running", False) and not status.get("paused", False),
        "paused": status.get("paused", False),
        "paused_at": status.get("paused_at"),
        "last_check": status.get("last_check"),
        "tasks_due": status.get("tasks_due", 0),
        "tasks_executed": status.get("tasks_executed", 0),
        "active_tasks": active_tasks,
        "last_error": status.get("last_error"),
    }


@router.post("/scheduler/toggle")
async def toggle_scheduler():
    """Pause or resume the cron scheduler."""
    status = get_scheduler_status()
    currently_paused = status.get("paused", False)
    status["paused"] = not currently_paused
    status["paused_at"] = (
        datetime.now(timezone.utc).isoformat() if not currently_paused else None
    )

    action = "paused" if status["paused"] else "resumed"
    logger.info("Scheduler %s by user.", action)

    await log_activity(
        action=f"automations.scheduler_{action}",
        summary=f"Scheduler {action}",
    )
    return {
        "paused": status["paused"],
        "paused_at": status["paused_at"],
        "message": f"Scheduler {action}",
    }


@router.get("/tasks/{task_id}/history")
async def task_execution_history(task_id: int, limit: int = 50):
    """Return the last N executions for a specific task."""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT id FROM scheduled_tasks WHERE id = ?", (task_id,)
        )
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="Task negasit")

        cursor = await db.execute(
            """SELECT id, task_id, started_at, finished_at, status, output, error
               FROM task_runs
               WHERE task_id = ?
               ORDER BY started_at DESC
               LIMIT ?""",
            (task_id, limit),
        )
        runs = []
        for r in await cursor.fetchall():
            rd = row_dict(r)
            if rd.get("started_at") and rd.get("finished_at"):
                try:
                    start_str = rd["started_at"]
                    end_str = rd["finished_at"]
                    if "T" in start_str:
                        start_dt = datetime.fromisoformat(start_str.replace("Z", "+00:00")).replace(tzinfo=None)
                    else:
                        start_dt = datetime.strptime(start_str, "%Y-%m-%d %H:%M:%S")
                    if "T" in end_str:
                        end_dt = datetime.fromisoformat(end_str.replace("Z", "+00:00")).replace(tzinfo=None)
                    else:
                        end_dt = datetime.strptime(end_str, "%Y-%m-%d %H:%M:%S")
                    rd["duration_seconds"] = round((end_dt - start_dt).total_seconds(), 1)
                except (ValueError, TypeError):
                    rd["duration_seconds"] = None
            else:
                rd["duration_seconds"] = None
            runs.append(rd)

        return {"task_id": task_id, "runs": runs, "count": len(runs)}


@router.post("/cleanup")
async def cleanup_old_records(days: int = 90):
    """Delete old records: task_runs, uptime_history, activity_log older than N days."""
    if days < 1:
        raise HTTPException(status_code=400, detail="Numarul de zile trebuie sa fie minim 1")

    deleted = {}
    async with get_db() as db:
        cursor = await db.execute(
            "DELETE FROM task_runs WHERE started_at < datetime('now', ?)",
            (f"-{days} days",),
        )
        deleted["task_runs"] = cursor.rowcount

        cursor = await db.execute(
            "DELETE FROM uptime_history WHERE checked_at < datetime('now', ?)",
            (f"-{days} days",),
        )
        deleted["uptime_history"] = cursor.rowcount

        cursor = await db.execute(
            "DELETE FROM activity_log WHERE timestamp < datetime('now', ?)",
            (f"-{days} days",),
        )
        deleted["activity_log"] = cursor.rowcount

        await db.commit()

    total = sum(deleted.values())
    await log_activity(
        action="automations.cleanup",
        summary=f"Cleanup: {total} inregistrari sterse (mai vechi de {days} zile)",
        details=deleted,
    )
    return {"deleted": deleted, "total": total, "days": days}


# ═══════════════════════════════════════════
# Shortcuts CRUD
# ═══════════════════════════════════════════


@router.get("/shortcuts")
async def list_shortcuts():
    """List all custom shortcuts."""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM shortcuts ORDER BY sort_order, created_at"
        )
        return [row_dict(r) for r in await cursor.fetchall()]


@router.post("/shortcuts")
async def create_shortcut(body: ShortcutCreate):
    """Create a new shortcut."""
    async with get_db() as db:
        cursor = await db.execute(
            """INSERT INTO shortcuts (name, icon, color, url_or_action, sort_order)
               VALUES (?, ?, ?, ?, ?)""",
            (body.name, body.icon, body.color, body.url_or_action, body.sort_order),
        )
        await db.commit()
        shortcut_id = cursor.lastrowid

    await log_activity(
        action="automations.shortcut_create",
        summary=f"Shortcut creat: {body.name}",
    )
    return {"id": shortcut_id, "status": "created"}


@router.put("/shortcuts/{shortcut_id}")
async def update_shortcut(shortcut_id: int, body: ShortcutUpdate):
    """Update an existing shortcut."""
    async with get_db() as db:
        cursor = await db.execute("SELECT id FROM shortcuts WHERE id = ?", (shortcut_id,))
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="Shortcut negasit")

        updates = []
        params = []

        if body.name is not None:
            updates.append("name = ?")
            params.append(body.name)
        if body.icon is not None:
            updates.append("icon = ?")
            params.append(body.icon)
        if body.color is not None:
            updates.append("color = ?")
            params.append(body.color)
        if body.url_or_action is not None:
            updates.append("url_or_action = ?")
            params.append(body.url_or_action)
        if body.sort_order is not None:
            updates.append("sort_order = ?")
            params.append(body.sort_order)

        if not updates:
            raise HTTPException(status_code=400, detail="Nimic de actualizat")

        params.append(shortcut_id)
        await db.execute(
            f"UPDATE shortcuts SET {', '.join(updates)} WHERE id = ?",
            tuple(params),
        )
        await db.commit()

    await log_activity(
        action="automations.shortcut_update",
        summary=f"Shortcut actualizat: #{shortcut_id}",
    )
    return {"status": "updated"}


@router.delete("/shortcuts/{shortcut_id}")
async def delete_shortcut(shortcut_id: int):
    """Delete a shortcut."""
    async with get_db() as db:
        cursor = await db.execute("SELECT id FROM shortcuts WHERE id = ?", (shortcut_id,))
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="Shortcut negasit")

        await db.execute("DELETE FROM shortcuts WHERE id = ?", (shortcut_id,))
        await db.commit()

    await log_activity(
        action="automations.shortcut_delete",
        summary=f"Shortcut sters: #{shortcut_id}",
    )
    return {"status": "deleted"}


# ═══════════════════════════════════════════
# Uptime Monitors CRUD
# ═══════════════════════════════════════════


@router.get("/monitors")
async def list_monitors():
    """List all uptime monitors."""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM uptime_monitors ORDER BY created_at DESC"
        )
        monitors = [row_dict(r) for r in await cursor.fetchall()]
        for m in monitors:
            m["running"] = is_monitor_running(m["id"])
        return monitors


@router.post("/monitors")
async def create_monitor(body: MonitorCreate):
    """Add a new URL to monitor."""
    async with get_db() as db:
        cursor = await db.execute(
            """INSERT INTO uptime_monitors (name, url, interval_seconds, enabled)
               VALUES (?, ?, ?, ?)""",
            (body.name, body.url, body.interval_seconds, int(body.enabled)),
        )
        await db.commit()
        monitor_id = cursor.lastrowid

    if body.enabled:
        start_monitor(monitor_id, body.url, body.interval_seconds)

    await log_activity(
        action="automations.monitor_create",
        summary=f"Monitor creat: {body.name} ({body.url})",
    )
    return {"id": monitor_id, "status": "created"}


@router.put("/monitors/{monitor_id}")
async def update_monitor(monitor_id: int, body: MonitorUpdate):
    """Update an existing uptime monitor."""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM uptime_monitors WHERE id = ?", (monitor_id,)
        )
        existing = await cursor.fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Monitor negasit")

        existing_dict = row_dict(existing)

        updates = []
        params = []

        if body.name is not None:
            updates.append("name = ?")
            params.append(body.name)
        if body.url is not None:
            updates.append("url = ?")
            params.append(body.url)
        if body.interval_seconds is not None:
            updates.append("interval_seconds = ?")
            params.append(body.interval_seconds)
        if body.enabled is not None:
            updates.append("enabled = ?")
            params.append(int(body.enabled))

        if not updates:
            raise HTTPException(status_code=400, detail="Nimic de actualizat")

        params.append(monitor_id)
        await db.execute(
            f"UPDATE uptime_monitors SET {', '.join(updates)} WHERE id = ?",
            tuple(params),
        )
        await db.commit()

    new_enabled = body.enabled if body.enabled is not None else bool(existing_dict.get("enabled", 1))
    new_url = body.url if body.url is not None else existing_dict["url"]
    new_interval = body.interval_seconds if body.interval_seconds is not None else existing_dict["interval_seconds"]

    if new_enabled:
        start_monitor(monitor_id, new_url, new_interval)
    else:
        stop_monitor(monitor_id)

    await log_activity(
        action="automations.monitor_update",
        summary=f"Monitor actualizat: #{monitor_id}",
    )
    return {"status": "updated"}


@router.delete("/monitors/{monitor_id}")
async def delete_monitor(monitor_id: int):
    """Remove a monitor and its history."""
    async with get_db() as db:
        cursor = await db.execute("SELECT id FROM uptime_monitors WHERE id = ?", (monitor_id,))
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="Monitor negasit")

        stop_monitor(monitor_id)

        await db.execute("DELETE FROM uptime_history WHERE monitor_id = ?", (monitor_id,))
        await db.execute("DELETE FROM uptime_monitors WHERE id = ?", (monitor_id,))
        await db.commit()

    await log_activity(
        action="automations.monitor_delete",
        summary=f"Monitor sters: #{monitor_id}",
    )
    return {"status": "deleted"}


@router.get("/monitors/{monitor_id}/history")
async def monitor_history(monitor_id: int, limit: int = 288):
    """Get ping history for a monitor (default: last 288 = 24h at 5min interval)."""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT id FROM uptime_monitors WHERE id = ?", (monitor_id,)
        )
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="Monitor negasit")

        cursor = await db.execute(
            """SELECT * FROM uptime_history
               WHERE monitor_id = ?
               ORDER BY checked_at DESC
               LIMIT ?""",
            (monitor_id, limit),
        )
        return [row_dict(r) for r in await cursor.fetchall()]


# ═══════════════════════════════════════════
# API Tester
# ═══════════════════════════════════════════


@router.post("/api-test")
async def execute_api_test(body: ApiTestRequest):
    """Execute an HTTP request and return the response."""
    method = body.method.upper()
    if method not in ("GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"):
        raise HTTPException(status_code=400, detail="Metoda HTTP invalida")

    headers = body.headers or {}
    req_body = body.body

    try:
        async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
            start_ms = __import__("time").monotonic()
            resp = await client.request(
                method=method,
                url=body.url,
                headers=headers,
                content=req_body.encode("utf-8") if req_body else None,
            )
            elapsed_ms = int((__import__("time").monotonic() - start_ms) * 1000)

            response_headers = dict(resp.headers)
            response_body = resp.text[:50000]

            result = {
                "status_code": resp.status_code,
                "headers": response_headers,
                "body": response_body,
                "response_ms": elapsed_ms,
            }
    except Exception as exc:
        result = {
            "status_code": 0,
            "headers": {},
            "body": "",
            "response_ms": 0,
            "error": str(exc)[:1000],
        }

    try:
        async with get_db() as db:
            await db.execute(
                """INSERT INTO api_test_history
                   (method, url, headers, body, response_status, response_headers, response_body, response_ms)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    method,
                    body.url,
                    json.dumps(headers) if headers else None,
                    req_body,
                    result.get("status_code", 0),
                    json.dumps(result.get("headers", {})),
                    result.get("body", "")[:10000],
                    result.get("response_ms", 0),
                ),
            )
            await db.commit()
    except Exception as exc:
        logger.warning("Failed to save API test history: %s", exc)

    return result


@router.get("/api-test/history")
async def api_test_history():
    """Get last 20 API test requests."""
    async with get_db() as db:
        cursor = await db.execute(
            """SELECT id, method, url, response_status, response_ms, created_at
               FROM api_test_history
               ORDER BY created_at DESC
               LIMIT 20"""
        )
        return [row_dict(r) for r in await cursor.fetchall()]


@router.post("/api-test/save")
async def save_api_template(body: ApiTestSave):
    """Save an API request as a reusable template."""
    headers_json = json.dumps(body.headers) if body.headers else None

    async with get_db() as db:
        cursor = await db.execute(
            """INSERT INTO api_test_saved (name, method, url, headers, body)
               VALUES (?, ?, ?, ?, ?)""",
            (body.name, body.method, body.url, headers_json, body.body),
        )
        await db.commit()
        template_id = cursor.lastrowid

    return {"id": template_id, "status": "saved"}


@router.get("/api-test/saved")
async def list_api_templates():
    """List saved API request templates."""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM api_test_saved ORDER BY created_at DESC"
        )
        templates = [row_dict(r) for r in await cursor.fetchall()]
        for t in templates:
            if t.get("headers"):
                try:
                    t["headers"] = json.loads(t["headers"])
                except (json.JSONDecodeError, TypeError):
                    pass
        return templates


# ═══════════════════════════════════════════
# Health Monitor
# ═══════════════════════════════════════════


@router.get("/health")
async def health_check():
    """Comprehensive health check: DB, disk, modules, API keys, errors."""
    report = await build_health_report()

    statuses = [
        v.get("status", "ok")
        for v in report.values()
        if isinstance(v, dict)
    ]
    if "error" in statuses:
        overall = "error"
    elif "warning" in statuses:
        overall = "warning"
    else:
        overall = "ok"

    return {
        "overall": overall,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "components": report,
    }


# ═══════════════════════════════════════════
# Notifications CRUD
# ═══════════════════════════════════════════


@router.get("/notifications")
async def list_notifications(unread_only: bool = False, limit: int = 50):
    """List notifications, optionally only unread."""
    async with get_db() as db:
        if unread_only:
            cursor = await db.execute(
                "SELECT * FROM notifications WHERE is_read = 0 ORDER BY created_at DESC LIMIT ?",
                (limit,),
            )
        else:
            cursor = await db.execute(
                "SELECT * FROM notifications ORDER BY created_at DESC LIMIT ?",
                (limit,),
            )
        rows = await cursor.fetchall()
        cursor2 = await db.execute("SELECT COUNT(*) as cnt FROM notifications WHERE is_read = 0")
        unread_count = (await cursor2.fetchone())["cnt"]
    return {"items": [dict(r) for r in rows], "unread_count": unread_count}


@router.post("/notifications", status_code=201)
async def create_notification(data: NotificationCreate):
    """Create a new notification."""
    async with get_db() as db:
        cursor = await db.execute(
            "INSERT INTO notifications (title, message, type, source, link) VALUES (?, ?, ?, ?, ?)",
            (data.title, data.message, data.type, data.source, data.link),
        )
        await db.commit()
        notif_id = cursor.lastrowid
    return {"id": notif_id, "message": "Notificare creata."}


@router.put("/notifications/{notif_id}/read")
async def mark_notification_read(notif_id: int):
    """Mark a notification as read."""
    async with get_db() as db:
        await db.execute(
            "UPDATE notifications SET is_read = 1 WHERE id = ?", (notif_id,)
        )
        await db.commit()
    return {"message": "Notificare marcata ca citita."}


@router.put("/notifications/read-all")
async def mark_all_notifications_read():
    """Mark all notifications as read."""
    async with get_db() as db:
        await db.execute("UPDATE notifications SET is_read = 1 WHERE is_read = 0")
        await db.commit()
    return {"message": "Toate notificarile marcate ca citite."}


@router.delete("/notifications/{notif_id}")
async def delete_notification(notif_id: int):
    """Delete a notification."""
    async with get_db() as db:
        await db.execute("DELETE FROM notifications WHERE id = ?", (notif_id,))
        await db.commit()
    return {"message": "Notificare stearsa."}


@router.post("/notify", status_code=201)
async def notify_internal(data: NotifyRequest):
    """Internal endpoint: any module can create a notification."""
    type_map = {"info": "info", "warning": "warning", "error": "error", "success": "success"}
    notif_type = type_map.get(data.severity, "info")

    async with get_db() as db:
        cursor = await db.execute(
            """INSERT INTO notifications (title, message, type, source)
               VALUES (?, ?, ?, ?)""",
            (data.title, data.message, notif_type, data.source),
        )
        await db.commit()
        notif_id = cursor.lastrowid

    return {"id": notif_id, "message": "Notificare creata."}
