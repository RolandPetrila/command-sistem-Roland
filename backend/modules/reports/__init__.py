"""
Modul Reports — rapoarte, statistici, timeline activitate,
jurnal personal, bookmark-uri, export date.
"""

from .router import router as reports_router

MODULE_INFO = {
    "name": "reports",
    "description": "Rapoarte — Statistici, Timeline, Export",
    "routers": [reports_router],
    "category": "Sistem",
    "icon": "BarChart3",
    "order": 23,
}
