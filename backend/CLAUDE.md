# Backend — Developer Guide

## Adding a New Module

1. Create folder: `modules/[name]/`
2. Create `__init__.py` with `MODULE_INFO`:
```python
from .router import router

MODULE_INFO = {
    "name": "module_name",
    "prefix": "/api/module-name",
    "tags": ["Module Name"],
    "router": router
}
```
3. Create `router.py` with FastAPI router:
```python
from fastapi import APIRouter
router = APIRouter()

@router.get("/endpoint")
async def my_endpoint():
    return {"status": "ok"}
```
4. Module is auto-discovered by `app/module_discovery.py` — no manual registration needed

## Database Conventions
- SQLite via aiosqlite (async)
- `busy_timeout = 5000` for concurrency
- Migrations: numbered SQL files in `migrations/` (e.g., `005_new_table.sql`)
- Schema version tracked in `schema_version` table
- When adding/modifying tables → MUST create migration file

## Activity Logging
```python
from app.core.activity_log import log_activity
await log_activity(action="module.action", summary="What happened", details={...})
```

## Key Patterns
- Config: `app/config.py` uses `Path(__file__).resolve()` for relative paths
- Windows: always `set PYTHONIOENCODING=utf-8` before running
- Use `python -m pip` and `python -m uvicorn` (not bare commands)
- Entry point: `app/main.py` — CORS, WebSocket, module auto-discovery
