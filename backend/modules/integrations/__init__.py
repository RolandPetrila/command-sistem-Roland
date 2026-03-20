"""
Modul Integrations — integrări externe: Gmail, Google Drive, Google Calendar, GitHub.

Folosește chei API stocate în tabelul ai_config din SQLite.
Permite trimitere/citire email, gestionare fișiere Drive,
evenimente Calendar, și interacțiune cu repo-uri GitHub.
"""

from .router import router as integrations_router

MODULE_INFO = {
    "name": "integrations",
    "description": "Integrări externe — Gmail, Drive, Calendar, GitHub",
    "routers": [integrations_router],
    "category": "Sistem",
    "icon": "Plug",
    "order": 22,
}
