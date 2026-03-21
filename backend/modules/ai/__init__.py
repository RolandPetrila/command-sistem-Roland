"""
Modul AI — Chat AI, analiză documente, OCR inteligent, comparare documente,
RAG search, dashboard insights, auto-classify, notepad AI, token tracking.

Features: chat streaming (SSE), rezumat, Q&A, clasificare, extragere date,
redenumire inteligentă, OCR+AI, comparare diff, explicație preț, comparare
competitori, acțiuni notepad (improve/summarize/translate), RAG pe documente.
Providers: Gemini Flash (principal) → OpenAI (fallback) → Groq (fallback).
"""

from .router import router as ai_router
from .router_extensions import router_ext, router_doc_ops, router_tools

MODULE_INFO = {
    "name": "ai",
    "description": "Inteligență Artificială — Chat, Analiză Documente, RAG, Insights",
    "routers": [ai_router, router_ext, router_doc_ops, router_tools],
    "category": "AI",
    "icon": "Brain",
    "order": 2,
}
