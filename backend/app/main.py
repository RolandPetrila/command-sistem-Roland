"""
Roland Command Center — FastAPI Backend.

Punctul de intrare principal al aplicației.
Module auto-discovery din backend/modules/.
Servire frontend static din frontend/dist/ (producție).
"""

import logging
import os
import time

# Load .env before anything else reads os.environ
from dotenv import load_dotenv
load_dotenv()
from collections import defaultdict
from contextlib import asynccontextmanager
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.gzip import GZipMiddleware
from starlette.responses import Response as StarletteResponse

from app.config import settings
from app.core.activity_log import log_activity
from app.db.database import init_db
from app.module_discovery import discover_modules

# Directorul frontend/dist/ (build producție)
_DIST_DIR = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"

# --- Logging: console + fișier persistent ---
_LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
_LOG_DIR.mkdir(exist_ok=True)

_log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
logging.basicConfig(level=logging.INFO, format=_log_format)

# Suppress noisy Windows asyncio pipe errors (cosmetic, non-critical)
logging.getLogger("asyncio").setLevel(logging.WARNING)

_file_handler = RotatingFileHandler(
    _LOG_DIR / "backend.log",
    maxBytes=5 * 1024 * 1024,  # 5 MB
    backupCount=3,
    encoding="utf-8",
    delay=True,  # open file only when first write (avoids PermissionError on reload)
)
_file_handler.setFormatter(logging.Formatter(_log_format))
logging.getLogger().addHandler(_file_handler)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# WebSocket connection manager (pentru progres live)
# ---------------------------------------------------------------------------

class ConnectionManager:
    """Gestionează conexiunile WebSocket active per task_id."""

    def __init__(self) -> None:
        self.active: dict[str, list[WebSocket]] = {}

    async def connect(self, task_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        if task_id not in self.active:
            self.active[task_id] = []
        self.active[task_id].append(websocket)

    def disconnect(self, task_id: str, websocket: WebSocket) -> None:
        if task_id in self.active:
            self.active[task_id] = [
                ws for ws in self.active[task_id] if ws is not websocket
            ]
            if not self.active[task_id]:
                del self.active[task_id]

    async def send_progress(self, task_id: str, data: dict) -> None:
        """Trimite actualizare de progres la toți clienții conectați pe task_id."""
        if task_id not in self.active:
            return
        disconnected = []
        for ws in self.active[task_id]:
            try:
                await ws.send_json(data)
            except Exception:
                disconnected.append(ws)
        for ws in disconnected:
            self.disconnect(task_id, ws)


ws_manager = ConnectionManager()


# ---------------------------------------------------------------------------
# Lifespan (startup / shutdown)
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Evenimente la pornire și oprire."""
    # --- Startup ---
    logger.info("Inițializare bază de date...")
    await init_db()

    logger.info("Verificare directoare...")
    settings.ensure_dirs()

    logger.info("Server pornit. Uploads: %s", settings.uploads_dir)
    yield
    # --- Shutdown ---
    logger.info("Server oprit.")


# ---------------------------------------------------------------------------
# Aplicația FastAPI
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Roland Command Center",
    description="Panou personal multifuncțional — traduceri, facturare, tool-uri, AI pe documente.",
    version="0.3.0",
    lifespan=lifespan,
)


# --- CORS (dinamic: localhost dev + Tailscale producție) ---
_cors_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
]
_tailscale_origin = os.environ.get("TAILSCALE_ORIGIN")
if _tailscale_origin:
    _cors_origins.append(_tailscale_origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- GZip compression (Z2.9 — reduce response sizes 60-80%) ---
app.add_middleware(GZipMiddleware, minimum_size=500)


# ---------------------------------------------------------------------------
# Request stats (in-memory, reset on restart) + Request Logger Middleware
# ---------------------------------------------------------------------------

_request_stats: dict = {
    "total": 0,
    "errors": 0,
    "by_status": defaultdict(int),
    "slow_requests": [],  # top 10 slowest
    "started_at": time.time(),
}


@app.middleware("http")
async def request_logger(request: Request, call_next):
    """Log ALL API errors (4xx/5xx) to activity_log + track stats."""
    path = request.url.path

    # Skip non-API and health/frontend-log (too noisy)
    if not path.startswith("/api/") or path in ("/api/health", "/api/log/frontend"):
        return await call_next(request)

    start = time.perf_counter()
    method = request.method
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")[:200]

    try:
        response = await call_next(request)
    except Exception as exc:
        duration_ms = (time.perf_counter() - start) * 1000
        _request_stats["total"] += 1
        _request_stats["errors"] += 1
        _request_stats["by_status"]["500"] += 1
        await log_activity(
            action="api.error",
            status="error",
            summary=f"{method} {path} -> 500 ({duration_ms:.0f}ms) {str(exc)[:100]}",
            details={
                "method": method, "path": path,
                "query": str(request.url.query)[:200],
                "status_code": 500, "duration_ms": round(duration_ms),
                "error": str(exc)[:500],
                "client": client_ip, "user_agent": user_agent,
            },
        )
        raise

    duration_ms = (time.perf_counter() - start) * 1000
    status = response.status_code

    # Track stats
    _request_stats["total"] += 1
    _request_stats["by_status"][str(status)] += 1

    # Track slow requests (>2s)
    if duration_ms > 2000:
        _request_stats["slow_requests"].append({
            "path": path, "method": method,
            "duration_ms": round(duration_ms), "status": status,
        })
        _request_stats["slow_requests"] = _request_stats["slow_requests"][-10:]

    # Log errors (4xx/5xx) to activity_log
    if status >= 400:
        _request_stats["errors"] += 1
        error_body = ""
        try:
            body_bytes = b""
            async for chunk in response.body_iterator:
                body_bytes += chunk
            error_body = body_bytes.decode("utf-8", errors="replace")[:500]

            await log_activity(
                action="api.error",
                status="error",
                summary=f"{method} {path} -> {status} ({duration_ms:.0f}ms)",
                details={
                    "method": method, "path": path,
                    "query": str(request.url.query)[:200],
                    "status_code": status, "duration_ms": round(duration_ms),
                    "response_body": error_body,
                    "client": client_ip, "user_agent": user_agent,
                },
            )

            return StarletteResponse(
                content=body_bytes,
                status_code=status,
                headers=dict(response.headers),
                media_type=response.media_type,
            )
        except Exception as log_exc:
            logger.warning("Request logger error: %s", log_exc)

    return response


# --- Rate Limiting middleware (D4 — securitate) ---
_rate_limit_store: dict[str, list[float]] = defaultdict(list)

# Paths with stricter limits (10 req/min instead of 60)
_STRICT_RATE_PATHS = {"/api/ai/", "/api/translator/text", "/api/translator/file", "/api/translator/quality-check"}


@app.middleware("http")
async def rate_limiter(request: Request, call_next):
    """Simple in-memory rate limiting: 60 req/min global, 10 req/min for AI/translate."""
    path = request.url.path
    if not path.startswith("/api/") or path in ("/api/health", "/api/log/frontend"):
        return await call_next(request)

    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    window = 60  # 1 minute

    # Determine limit based on path
    is_strict = any(path.startswith(p) for p in _STRICT_RATE_PATHS)
    limit = 10 if is_strict else 60
    bucket_key = f"{client_ip}:{'strict' if is_strict else 'global'}"

    # Clean old entries and check
    _rate_limit_store[bucket_key] = [t for t in _rate_limit_store[bucket_key] if now - t < window]

    if len(_rate_limit_store[bucket_key]) >= limit:
        return JSONResponse(
            status_code=429,
            content={"detail": f"Prea multe cereri ({limit}/min). Incearca din nou in cateva secunde."},
        )

    _rate_limit_store[bucket_key].append(now)
    return await call_next(request)


# --- CSP Headers middleware (Z1.11 — prevent XSS in PWA) ---
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response: Response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if not request.url.path.startswith("/api/"):
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: blob:; "
            "connect-src 'self' ws: wss: https://*.deepl.com https://api.cognitive.microsofttranslator.com "
            "https://translation.googleapis.com https://generativelanguage.googleapis.com "
            "https://api.groq.com https://api.cerebras.ai https://api.mistral.ai https://api.sambanova.ai; "
            "font-src 'self'; "
            "object-src 'none'; "
            "base-uri 'self'"
        )
    return response

# --- Module auto-discovery ---
_modules = discover_modules()
for _mod_info in _modules:
    for _router in _mod_info["routers"]:
        app.include_router(_router)


# ---------------------------------------------------------------------------
# Endpoint-uri de bază
# ---------------------------------------------------------------------------

@app.get("/api/health")
async def health_check():
    """Verificare stare server."""
    return {
        "status": "ok",
        "message": "Serverul funcționează corect.",
        "version": app.version,
    }


@app.get("/api/network/speed-payload")
async def speed_payload():
    """Return ~500KB payload for client-side download speed measurement."""
    payload = b"X" * (500 * 1024)  # 500 KB
    return Response(
        content=payload,
        media_type="application/octet-stream",
        headers={"Cache-Control": "no-store"},
    )


@app.get("/api/diagnostics")
async def diagnostics():
    """Diagnostic complet: erori recente, stats request-uri, stare sistem."""
    from app.core.activity_log import get_activity_log
    import shutil

    # Recent errors from activity_log
    errors = await get_activity_log(limit=30, action_filter="api.error")
    frontend_errors = await get_activity_log(limit=20, action_filter="frontend.error")

    # Disk space
    disk = shutil.disk_usage(Path(__file__).resolve().drive or "/")

    uptime_sec = time.time() - _request_stats["started_at"]

    return {
        "request_stats": {
            "total_requests": _request_stats["total"],
            "total_errors": _request_stats["errors"],
            "error_rate": f"{(_request_stats['errors'] / max(1, _request_stats['total'])) * 100:.1f}%",
            "by_status": dict(_request_stats["by_status"]),
            "slow_requests": _request_stats["slow_requests"],
            "uptime_seconds": round(uptime_sec),
            "uptime_human": f"{int(uptime_sec // 3600)}h {int((uptime_sec % 3600) // 60)}m",
        },
        "recent_api_errors": errors,
        "recent_frontend_errors": frontend_errors,
        "system": {
            "disk_total_gb": round(disk.total / (1024**3), 1),
            "disk_free_gb": round(disk.free / (1024**3), 1),
            "disk_used_pct": f"{((disk.total - disk.free) / disk.total) * 100:.0f}%",
            "python_version": os.sys.version.split()[0],
            "server_version": app.version,
            "modules_loaded": len(_modules),
        },
    }


@app.get("/api/modules")
async def list_modules():
    """Returnează modulele descoperite (fără obiectele router)."""
    return [
        {
            "name": m.get("name"),
            "description": m.get("description"),
            "category": m.get("category"),
            "icon": m.get("icon"),
            "order": m.get("order"),
        }
        for m in _modules
    ]


@app.post("/api/log/frontend")
async def frontend_log(request: Request):
    """Primește erori și events de la frontend pentru logging persistent."""
    body = await request.json()
    level = body.get("level", "error")
    message = body.get("message", "")
    details = body.get("details", {})
    page = body.get("page", "")

    if level == "error":
        logger.error("Frontend: %s [%s] %s", message, page, details)
        await log_activity(
            action="frontend.error",
            summary=f"{page}: {message[:200]}",
            details=details,
            status="error",
        )
    elif level == "pageview":
        logger.info("Pageview: %s", page)
        await log_activity(
            action="frontend.pageview",
            summary=f"Vizită: {page}",
            details={"page": page, "timestamp": details.get("timestamp", "")},
        )
    else:
        logger.info("Frontend [%s]: %s", level, message)

    return {"status": "ok"}


@app.websocket("/ws/progress")
async def ws_progress_generic(websocket: WebSocket):
    """
    WebSocket generic pentru actualizări de progres.
    Clientul trimite un mesaj cu task_id pentru a se abona.
    """
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            task_id = data.get("task_id")
            if task_id:
                if task_id not in ws_manager.active:
                    ws_manager.active[task_id] = []
                ws_manager.active[task_id].append(websocket)
                await websocket.send_json({
                    "status": "subscribed",
                    "task_id": task_id,
                    "message": f"Abonat la actualizări pentru task {task_id}.",
                })
    except WebSocketDisconnect:
        pass


@app.websocket("/ws/progress/{task_id}")
async def ws_progress_task(websocket: WebSocket, task_id: str):
    """
    WebSocket dedicat unui task specific.
    Trimite actualizări de progres în timp real.
    """
    await ws_manager.connect(task_id, websocket)
    try:
        while True:
            # Menținem conexiunea deschisă; serverul trimite date prin ws_manager
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(task_id, websocket)


# ---------------------------------------------------------------------------
# Servire frontend static (producție — din frontend/dist/)
# ---------------------------------------------------------------------------

if _DIST_DIR.exists():
    logger.info("Mod producție: servire frontend din %s", _DIST_DIR)

    # Fișiere statice (JS, CSS, imagini) din assets/
    _assets_dir = _DIST_DIR / "assets"
    if _assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(_assets_dir)), name="static-assets")

    # Fișiere din rădăcina dist/ (icons, manifest, sw.js, etc.)
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """SPA fallback — rutele non-API servesc frontend-ul."""
        file_path = _DIST_DIR / full_path
        if full_path and file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(_DIST_DIR / "index.html"))
