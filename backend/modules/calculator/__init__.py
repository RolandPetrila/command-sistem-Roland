"""
Modul Calculator Preț Traduceri — modulul fondator al aplicației.

Expune routerele existente din app/api/ prin MODULE_INFO
pentru auto-discovery în main.py.
"""

from app.api.routes_upload import router as upload_router
from app.api.routes_price import router as price_router
from app.api.routes_history import router as history_router
from app.api.routes_calibrate import router as calibrate_router
from app.api.routes_files import router as files_router
from app.api.routes_settings import router as settings_router
from app.api.routes_competitors import router as competitors_router

MODULE_INFO = {
    "name": "calculator",
    "description": "Calculator Preț Traduceri",
    "routers": [
        upload_router,
        price_router,
        history_router,
        calibrate_router,
        files_router,
        settings_router,
        competitors_router,
    ],
    "category": "Traduceri",
    "icon": "Calculator",
    "order": 1,
}
