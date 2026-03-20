"""
Modul Automatizari — Task Scheduler, Shortcut-uri, Uptime Monitor,
API Tester (Postman-like), Health Monitor.

Features: programare taskuri (cron), executie manuala, shortcut-uri rapide,
monitorizare uptime URL-uri, testare API-uri HTTP, health check sistem.
"""

from .router import router as automations_router

MODULE_INFO = {
    "name": "automations",
    "description": "Automatizari — Scheduler, Shortcuts, Uptime, API Tester, Health",
    "routers": [automations_router],
    "category": "Sistem",
    "icon": "Zap",
    "order": 20,
}
