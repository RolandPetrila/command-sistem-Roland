"""
Modul Quick Tools — tool-uri rapide utile zilnic.

Conține: Notepad cu auto-save.
QR Generator și Command Palette sunt frontend-only (fără backend).
"""

from .router_notepad import router as notepad_router

MODULE_INFO = {
    "name": "quick_tools",
    "description": "Tool-uri rapide (notepad, QR, etc.)",
    "routers": [notepad_router],
    "category": "Quick Tools",
    "icon": "Wrench",
    "order": 2,
}
