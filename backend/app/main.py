"""
Calculator Preț Traduceri — FastAPI Backend.

Punctul de intrare principal al aplicației.
Include toate rutele, middleware-urile și evenimentele de pornire.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db.database import init_db
from app.api.routes_upload import router as upload_router
from app.api.routes_price import router as price_router
from app.api.routes_history import router as history_router
from app.api.routes_calibrate import router as calibrate_router
from app.api.routes_files import router as files_router
from app.api.routes_settings import router as settings_router
from app.api.routes_competitors import router as competitors_router

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
    title="Calculator Preț Traduceri",
    description="API pentru calcularea automată a prețurilor de traducere pe piața românească.",
    version="0.1.0",
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

# --- Routere ---
app.include_router(upload_router)
app.include_router(price_router)
app.include_router(history_router)
app.include_router(calibrate_router)
app.include_router(files_router)
app.include_router(settings_router)
app.include_router(competitors_router)


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
