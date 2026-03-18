"""
Modul AI — Chat AI, analiză documente, OCR inteligent, comparare documente.

Features: chat streaming (SSE), rezumat, Q&A, clasificare, extragere date,
redenumire inteligentă, OCR+AI, comparare diff.
Providers: Gemini Flash (principal) → OpenAI (fallback) → Groq (fallback).
"""

from .router import router as ai_router

MODULE_INFO = {
    "name": "ai",
    "description": "Inteligenta Artificiala pe documente",
    "routers": [ai_router],
    "category": "AI",
    "icon": "Bot",
    "order": 2,
}
