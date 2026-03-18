"""
Modul Vault — stocare criptată chei API cu master password.
"""

from .router import router as vault_router

MODULE_INFO = {
    "name": "vault",
    "description": "API Key Vault — stocare criptată chei API",
    "routers": [vault_router],
    "category": "Sistem",
    "icon": "KeyRound",
    "order": 10,
}
