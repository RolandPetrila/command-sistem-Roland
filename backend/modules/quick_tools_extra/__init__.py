"""
Modul Quick Tools Extra — Calculator avansat, Generator parole, Generator coduri de bare.

Endpoints:
  POST /api/tools/calculate              — evaluare expresii matematice (safe, fara eval)
  GET  /api/tools/calc-history           — istoric ultimele 20 calcule
  POST /api/tools/generate-password      — generare parola securizata
  POST /api/tools/check-password-strength — verificare forta parola
  POST /api/tools/generate-barcode       — generare cod de bare (PNG)
"""

from .router import router

MODULE_INFO = {
    "name": "quick_tools_extra",
    "description": "Calculator avansat, Generator parole, Generator coduri de bare",
    "routers": [router],
    "category": "Productivitate",
    "icon": "Wrench",
    "order": 17,
}
