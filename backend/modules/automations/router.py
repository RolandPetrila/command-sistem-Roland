"""
Automations module endpoints: Task Scheduler, Shortcuts, Uptime Monitor,
API Tester, Health Monitor.

Endpoints:
  GET    /api/automations/tasks              — List scheduled tasks
  POST   /api/automations/tasks              — Create task
  PUT    /api/automations/tasks/:id          — Update task
  DELETE /api/automations/tasks/:id          — Delete task
  POST   /api/automations/tasks/:id/run      — Run task manually

  GET    /api/automations/shortcuts           — List shortcuts
  POST   /api/automations/shortcuts           — Create shortcut
  DELETE /api/automations/shortcuts/:id       — Delete shortcut

  GET    /api/automations/monitors            — List uptime monitors
  POST   /api/automations/monitors            — Add monitor
  DELETE /api/automations/monitors/:id        — Remove monitor
  GET    /api/automations/monitors/:id/history — Ping history

  POST   /api/automations/api-test            — Execute HTTP request
  GET    /api/automations/api-test/history     — Last 20 requests
  POST   /api/automations/api-test/save        — Save as template
  GET    /api/automations/api-test/saved        — List saved templates

  GET    /api/automations/health              — Comprehensive health check
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.activity_log import log_activity
from app.db.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/automations", tags=["Automations"])

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

VALID_ACTION_TYPES = [
    "backup_db",
    "cleanup_temp",
    "reindex_documents",
    "health_check",
    "custom_script",
]


class TaskCreate(BaseModel):
    name: str
    schedule_cron: Optional[str] = None
    action_type: str
    action_config: Optional[dict] = None
    enabled: bool = True


class TaskUpdate(BaseModel):
    name: Optional[str] = None
    schedule_cron: Optional[str] = None
    action_type: Optional[str] = None
    action_config: Optional[dict] = None
    enabled: Optional[bool] = None


class ShortcutCreate(BaseModel):
    name: str
    icon: str = "Zap"
    color: str = "#3b82f6"
    url_or_action: str
    sort_order: int = 0


class MonitorCreate(BaseModel):
    name: str
    url: str
    interval_seconds: int = 300
    enabled: bool = True


class ApiTestRequest(BaseModel):
    method: str = "GET"
    url: str
    headers: Optional[dict] = None
    body: Optional[str] = None


class ApiTestSave(BaseModel):
    name: str
    method: str = "GET"
    url: str
    headers: Optional[dict] = None
    body: Optional[str] = None


# ---------------------------------------------------------------------------
# Helper: row to dict
# ---------------------------------------------------------------------------

def _row_dict(row) -> dict:
    """Convert an aiosqlite.Row to a plain dict."""
    return dict(row)


# ---------------------------------------------------------------------------
# Task action implementations
# ---------------------------------------------------------------------------

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
        health = await _build_health_report()
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


# ---------------------------------------------------------------------------
# 16.1 Task Scheduler
# ---------------------------------------------------------------------------

@router.get("/tasks")
async def list_tasks():
    """List all scheduled tasks with their last run info."""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM scheduled_tasks ORDER BY created_at DESC"
        )
        tasks = [_row_dict(r) for r in await cursor.fetchall()]

        # Attach last run info to each task
        for task in tasks:
            cur2 = await db.execute(
                "SELECT * FROM task_runs WHERE task_id = ? ORDER BY started_at DESC LIMIT 1",
                (task["id"],),
            )
            last_run_row = await cur2.fetchone()
            task["last_run_info"] = _row_dict(last_run_row) if last_run_row else None
            # Parse action_config from JSON string
            if task.get("action_config"):
                try:
                    task["action_config"] = json.loads(task["action_config"])
                except (json.JSONDecodeError, TypeError):
                    pass

        return tasks


@router.post("/tasks")
async def create_task(body: TaskCreate):
    """Create a new scheduled task."""
    if body.action_type not in VALID_ACTION_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Tip actiune invalid. Valide: {', '.join(VALID_ACTION_TYPES)}",
        )

    config_json = json.dumps(body.action_config) if body.action_config else None

    async with get_db() as db:
        cursor = await db.execute(
            """INSERT INTO scheduled_tasks (name, schedule_cron, action_type, action_config, enabled)
               VALUES (?, ?, ?, ?, ?)""",
            (body.name, body.schedule_cron, body.action_type, config_json, int(body.enabled)),
        )
        await db.commit()
        task_id = cursor.lastrowid

    await log_activity(
        action="automations.task_create",
        summary=f"Task creat: {body.name} ({body.action_type})",
    )
    return {"id": task_id, "status": "created"}


@router.put("/tasks/{task_id}")
async def update_task(task_id: int, body: TaskUpdate):
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

        task_dict = _row_dict(task)

    # Insert run record
    async with get_db() as db:
        cursor = await db.execute(
            "INSERT INTO task_runs (task_id, status) VALUES (?, 'running')",
            (task_id,),
        )
        await db.commit()
        run_id = cursor.lastrowid

    # Execute in background
    async def _execute():
        try:
            config = None
            if task_dict.get("action_config"):
                try:
                    config = json.loads(task_dict["action_config"])
                except (json.JSONDecodeError, TypeError):
                    config = None

            output = await _run_action(task_dict["action_type"], config)

            async with get_db() as db2:
                now = datetime.now(timezone.utc).isoformat()
                await db2.execute(
                    """UPDATE task_runs
                       SET status = 'success', output = ?, finished_at = ?
                       WHERE id = ?""",
                    (output, now, run_id),
                )
                await db2.execute(
                    "UPDATE scheduled_tasks SET last_run = ? WHERE id = ?",
                    (now, task_id),
                )
                await db2.commit()

            await log_activity(
                action="automations.task_run",
                summary=f"Task executat: {task_dict['name']} - succes",
                details={"output": output[:500]},
            )
        except Exception as exc:
            logger.error("Task run failed: %s", exc)
            async with get_db() as db2:
                now = datetime.now(timezone.utc).isoformat()
                await db2.execute(
                    """UPDATE task_runs
                       SET status = 'failed', error = ?, finished_at = ?
                       WHERE id = ?""",
                    (str(exc)[:1000], now, run_id),
                )
                await db2.commit()

    asyncio.create_task(_execute())

    return {"run_id": run_id, "status": "started"}


# ---------------------------------------------------------------------------
# 16.3 Shortcuts
# ---------------------------------------------------------------------------

@router.get("/shortcuts")
async def list_shortcuts():
    """List all custom shortcuts."""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM shortcuts ORDER BY sort_order, created_at"
        )
        return [_row_dict(r) for r in await cursor.fetchall()]


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


# ---------------------------------------------------------------------------
# 16.7 Uptime Monitor
# ---------------------------------------------------------------------------

# Background monitor tasks keyed by monitor ID
_monitor_tasks: dict[int, asyncio.Task] = {}


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


async def _monitor_loop(monitor_id: int, url: str, interval: int):
    """Background loop that pings a URL at intervals."""
    while True:
        try:
            result = await _ping_url(monitor_id, url)
            now = datetime.now(timezone.utc).isoformat()

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
        except Exception as exc:
            logger.warning("Monitor %d ping error: %s", monitor_id, exc)

        await asyncio.sleep(interval)


def _start_monitor(monitor_id: int, url: str, interval: int):
    """Start a background monitor task."""
    if monitor_id in _monitor_tasks:
        _monitor_tasks[monitor_id].cancel()
    _monitor_tasks[monitor_id] = asyncio.create_task(
        _monitor_loop(monitor_id, url, interval)
    )


def _stop_monitor(monitor_id: int):
    """Stop a background monitor task."""
    task = _monitor_tasks.pop(monitor_id, None)
    if task:
        task.cancel()


@router.get("/monitors")
async def list_monitors():
    """List all uptime monitors."""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM uptime_monitors ORDER BY created_at DESC"
        )
        monitors = [_row_dict(r) for r in await cursor.fetchall()]

        # Mark which are actively running
        for m in monitors:
            m["running"] = m["id"] in _monitor_tasks

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

    # Start background monitoring if enabled
    if body.enabled:
        _start_monitor(monitor_id, body.url, body.interval_seconds)

    await log_activity(
        action="automations.monitor_create",
        summary=f"Monitor creat: {body.name} ({body.url})",
    )
    return {"id": monitor_id, "status": "created"}


@router.delete("/monitors/{monitor_id}")
async def delete_monitor(monitor_id: int):
    """Remove a monitor and its history."""
    async with get_db() as db:
        cursor = await db.execute("SELECT id FROM uptime_monitors WHERE id = ?", (monitor_id,))
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="Monitor negasit")

        _stop_monitor(monitor_id)

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
        return [_row_dict(r) for r in await cursor.fetchall()]


# ---------------------------------------------------------------------------
# 16.8 API Tester
# ---------------------------------------------------------------------------

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
            start = time.monotonic()
            resp = await client.request(
                method=method,
                url=body.url,
                headers=headers,
                content=req_body.encode("utf-8") if req_body else None,
            )
            elapsed_ms = int((time.monotonic() - start) * 1000)

            response_headers = dict(resp.headers)
            response_body = resp.text[:50000]  # limit to 50KB

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

    # Save to history
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
        return [_row_dict(r) for r in await cursor.fetchall()]


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
        templates = [_row_dict(r) for r in await cursor.fetchall()]
        for t in templates:
            if t.get("headers"):
                try:
                    t["headers"] = json.loads(t["headers"])
                except (json.JSONDecodeError, TypeError):
                    pass
        return templates


# ---------------------------------------------------------------------------
# 16.10 Health Monitor
# ---------------------------------------------------------------------------

async def _build_health_report() -> dict[str, Any]:
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
            cursor = await db.execute(
                "SELECT name FROM vault_keys"
            )
            keys = [_row_dict(r)["name"] for r in await cursor.fetchall()]
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
            errors = [_row_dict(r) for r in await cursor.fetchall()]
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


@router.get("/health")
async def health_check():
    """Comprehensive health check: DB, disk, modules, API keys, errors."""
    report = await _build_health_report()

    # Overall status
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
