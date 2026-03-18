"""
Roland Command Center — FastAPI Backend.

Punctul de intrare principal al aplicației.
Module auto-discovery din backend/modules/.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db.database import init_db
from app.module_discovery import discover_modules

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
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
    version="0.2.0",
    lifespan=lifespan,
)

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
