"""
Modul Facturare — generare facturi PDF + evidenta clienti.

Lightweight Faza 10 necesar pentru 15B.7 (AI-generated invoices).
"""

from .router import router

MODULE_INFO = {
    "name": "invoice",
    "description": "Facturare simplificata — generare facturi PDF + evidenta clienti",
    "category": "Productivitate",
    "icon": "Receipt",
    "order": 16,
    "routers": [router],
}
