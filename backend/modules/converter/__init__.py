"""
Modul Convertor Fișiere — conversii între formate de documente, imagini și date.

Suportă: PDF↔DOCX, merge/split PDF, compresie/resize imagini,
CSV/Excel→JSON, ZIP, extragere text (OCR).
"""

from .router import router as converter_router

MODULE_INFO = {
    "name": "converter",
    "description": "Convertor fisiere — PDF, DOCX, imagini, date",
    "routers": [converter_router],
    "category": "Instrumente",
    "icon": "ArrowRightLeft",
    "order": 3,
}
