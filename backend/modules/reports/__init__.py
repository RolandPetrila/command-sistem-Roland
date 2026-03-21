"""
Modul Reports — rapoarte, statistici, timeline activitate,
jurnal personal, bookmark-uri, export date.
"""

from .system_reports import router as system_router
from .journal import router as journal_router
from .timeline import router as timeline_router

# Keep backward-compat alias used by any code doing
# `from modules.reports.router import router`
from .router import router as reports_router

MODULE_INFO = {
    "name": "reports",
    "description": "Rapoarte — Statistici, Timeline, Export",
    "routers": [system_router, journal_router, timeline_router],
    "category": "Sistem",
    "icon": "BarChart3",
    "order": 23,
}
