"""
Modul Traducator — Traducator integrat multi-provider cu Translation Memory si Glosar.

Features: traducere text/fisiere (PDF, DOCX, TXT), detectie limba,
Translation Memory cu FTS5, glosar cu import CSV, fallback chain
DeepL -> Azure -> Google -> Gemini -> OpenAI.
"""

from .router import router

MODULE_INFO = {
    "name": "translator",
    "description": "Traducator integrat multi-provider cu Translation Memory si Glosar",
    "category": "Productivitate",
    "icon": "Languages",
    "order": 15,
    "routers": [router],
}
