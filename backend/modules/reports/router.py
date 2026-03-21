"""
Reports module — router aggregator.

Sub-routers:
  system_reports.py  — disk-stats, system-info, file-stats, unused-files,
                        dashboard-summary, exchange-rates, backup/zip
  journal.py         — journal CRUD, bookmarks CRUD
  timeline.py        — timeline, timeline/stats, export/full
"""

from .system_reports import router as system_router
from .journal import router as journal_router
from .timeline import router as timeline_router

# Expose a single `router` for backward compatibility with any code that
# does `from modules.reports.router import router`.  We use the system_router
# as the canonical one; the other two are registered separately in __init__.py.
router = system_router

__all__ = ["router", "system_router", "journal_router", "timeline_router"]
