"""
Modul File Manager Avansat — browse, preview, CRUD, upload, download, duplicate finder.

Extinde file browser-ul existent cu operații complete pe fișiere,
accesibil de pe orice device via Tailscale.
"""

from .router import router as fm_router

MODULE_INFO = {
    "name": "filemanager",
    "description": "Manager fisiere avansat — preview, CRUD, upload, download",
    "routers": [fm_router],
    "category": "Sistem",
    "icon": "FolderOpen",
    "order": 8,
}
