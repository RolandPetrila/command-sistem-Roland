"""
AI module extension endpoints.

This file contains token/provider management endpoints and re-exports the
sub-routers from document_ops.py and tools.py so that __init__.py only needs
to import from this single file.

Endpoints owned here:
  GET    /api/ai/token-usage          — Usage per provider with limits
  POST   /api/ai/provider-select      — Set preferred AI provider
  GET    /api/ai/provider-select      — Get preferred AI provider

Endpoints in sub-modules (re-exported via router_ext include):
  document_ops.py  — auto-classify, index-document, search-documents, rag-query
  tools.py         — explain-price, context-data, notepad/{action},
                     dashboard-insights, compare-price
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.activity_log import log_activity
from app.db.database import get_db
from .token_tracker import get_usage_summary, get_provider_usage, get_deepl_usage_remote

# Sub-routers re-exported so __init__.py can register them all at once
from .document_ops import router_doc_ops
from .tools import router_tools

router_ext = APIRouter(prefix="/api/ai", tags=["AI Extensions"])


# --- Pydantic models ---

class ProviderSelectRequest(BaseModel):
    provider: str = Field(..., description="Provider name: gemini, openai, groq, or 'auto'")


# ==========================================
# TOKEN & PROVIDER ENDPOINTS
# ==========================================

@router_ext.get("/token-usage")
async def get_token_usage():
    """Returnează utilizarea per provider cu limitele configurate."""
    summary = await get_usage_summary()

    # Also get DeepL remote usage if available
    deepl_remote = await get_deepl_usage_remote()

    # Enrich DeepL entry with remote data
    for entry in summary:
        if entry["provider"] == "deepl" and "error" not in deepl_remote:
            entry["remote_chars_used"] = deepl_remote.get("character_count", 0)
            entry["remote_chars_limit"] = deepl_remote.get("character_limit", 0)
            entry["remote_percent"] = deepl_remote.get("percent_used", 0)

    return {"providers": summary, "deepl_remote": deepl_remote}


@router_ext.post("/provider-select")
async def set_preferred_provider(req: ProviderSelectRequest):
    """Setează provider-ul AI preferat (sau 'auto' pentru fallback chain)."""
    valid = ["auto", "gemini", "openai", "groq"]
    if req.provider not in valid:
        raise HTTPException(400, f"Provider invalid. Opțiuni: {', '.join(valid)}")

    async with get_db() as db:
        await db.execute(
            "INSERT INTO ai_config (key, value) VALUES ('preferred_provider', ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value, "
            "updated_at = CURRENT_TIMESTAMP",
            (req.provider,),
        )
        await db.commit()

    await log_activity(
        action="ai.provider_select",
        summary=f"Provider AI preferat setat: {req.provider}",
    )
    return {"status": "saved", "provider": req.provider}


@router_ext.get("/provider-select")
async def get_preferred_provider():
    """Returnează provider-ul AI preferat curent."""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT value FROM ai_config WHERE key = 'preferred_provider'"
        )
        row = await cursor.fetchone()

    provider = row["value"] if row else "auto"
    return {"provider": provider}
