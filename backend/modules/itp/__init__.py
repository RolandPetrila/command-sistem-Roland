"""
Modul ITP (Inspectie Tehnica Periodica) — evidenta inspectii auto.

CIP Inspection SRL — gestionare inspectii ITP, statistici,
alerte expirare, import/export date.
"""

from .router import router as itp_router

MODULE_INFO = {
    "name": "itp",
    "description": "ITP — Inspectie Tehnica Periodica",
    "routers": [itp_router],
    "category": "ITP",
    "icon": "Car",
    "order": 25,
}
