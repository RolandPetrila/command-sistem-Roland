"""
Modul Facturare — generare facturi PDF + evidenta clienti.

Endpoints split across 4 sub-routers:
  - crud.py          — Client CRUD, Invoice CRUD, series, overdue, email, ANAF
  - ai_extraction.py — OCR scan, AI extract, generate-from-calc
  - pdf_generation.py — PDF, offer PDF, export CSV/Excel, templates
  - reports.py        — Monthly report, summary report
"""

from .crud import crud_router
from .ai_extraction import ai_router
from .pdf_generation import pdf_router
from .reports import reports_router

MODULE_INFO = {
    "name": "invoice",
    "description": "Facturare simplificata — generare facturi PDF + evidenta clienti",
    "category": "Productivitate",
    "icon": "Receipt",
    "order": 16,
    "routers": [crud_router, ai_router, pdf_router, reports_router],
}
