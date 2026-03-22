"""
AI module — Document operations endpoints.

Endpoints:
  POST   /api/ai/auto-classify        — Auto-classify uploaded file with AI
  POST   /api/ai/index-document       — Index document for RAG search
  GET    /api/ai/search-documents     — FTS5 search indexed documents
  POST   /api/ai/rag-query            — RAG: search docs + AI answer
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.core.activity_log import log_activity
from app.core.file_utils import extract_text as _extract_text
from app.db.database import get_db
from .providers import ai_generate
from .token_tracker import track_usage

logger = logging.getLogger(__name__)
router_doc_ops = APIRouter(prefix="/api/ai", tags=["AI Document Ops"])


def _truncate_text(text: str, max_chars: int = 60000) -> str:
    """Truncate text to fit within AI context window."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + f"\n\n[... truncat, {len(text) - max_chars} caractere omise]"


# --- Pydantic models ---

class AutoClassifyRequest(BaseModel):
    file_path: str
    file_name: str


class IndexDocumentRequest(BaseModel):
    file_path: str


class RagQueryRequest(BaseModel):
    question: str
    max_docs: int | None = None  # Override via body (1-10)


# ==========================================
# 15B.5 — AUTO-CLASSIFY ON UPLOAD
# ==========================================

@router_doc_ops.post("/auto-classify")
async def auto_classify(req: AutoClassifyRequest):
    """
    Clasifică automat un fișier uploadat cu AI.
    Extrage text, cere AI să clasifice, salvează în file_classifications.
    """
    if not os.path.exists(req.file_path):
        raise HTTPException(404, f"Fișierul nu există: {req.file_path}")

    try:
        text = await asyncio.to_thread(_extract_text, req.file_path)
    except ValueError as e:
        raise HTTPException(400, str(e))

    if not text.strip():
        raise HTTPException(400, "Nu s-a putut extrage text din fișier")

    # Compute file hash for cache check
    try:
        with open(req.file_path, "rb") as f:
            file_hash = hashlib.md5(f.read(65536)).hexdigest()
    except Exception:
        file_hash = None

    # Check cache
    if file_hash:
        async with get_db() as db:
            cursor = await db.execute(
                "SELECT classification, suggested_name, tags_json, language "
                "FROM file_classifications WHERE file_hash = ?",
                (file_hash,),
            )
            cached = await cursor.fetchone()
            if cached:
                cached = dict(cached)
                tags = json.loads(cached["tags_json"]) if cached["tags_json"] else []
                return {
                    "classification": cached["classification"],
                    "suggested_name": cached["suggested_name"],
                    "tags": tags,
                    "language": cached["language"],
                    "cached": True,
                }

    # AI classification
    system = (
        "Clasifică documentul și răspunde STRICT în JSON valid:\n"
        '{"classification": "tip document", "suggested_name": "Nume_Descriptiv.ext", '
        '"tags": ["tag1", "tag2"], "language": "ro/en/mixed"}\n\n'
        "Tipuri posibile: factura, contract, certificat, raport, manual_tehnic, "
        "scrisoare, proces_verbal, oferta, comanda, document_auto, ITP, alt_document.\n"
        "Taguri relevante: automotive, constructii, IT, juridic, financiar, tehnic, medical.\n"
        "Numele sugerat: Tip_Detaliu_Data.extensie (fără spații, fără diacritice)."
    )
    prompt = f"Fișier: {req.file_name}\n\nConținut (primele 10.000 caractere):\n{_truncate_text(text, 10000)}"

    result = await ai_generate(prompt, system)
    await track_usage(result["provider"], chars=len(prompt) + len(result["text"]))

    # Parse AI response
    classification = "necunoscut"
    suggested_name = req.file_name
    tags = []
    language = "necunoscut"

    try:
        resp_text = result["text"]
        if "```" in resp_text:
            resp_text = resp_text.split("```")[1]
            if resp_text.startswith("json"):
                resp_text = resp_text[4:]
        parsed = json.loads(resp_text.strip())
        classification = parsed.get("classification", classification)
        suggested_name = parsed.get("suggested_name", suggested_name)
        tags = parsed.get("tags", tags)
        language = parsed.get("language", language)
    except (json.JSONDecodeError, IndexError):
        classification = result["text"][:100]

    # Store in file_classifications
    tags_json = json.dumps(tags, ensure_ascii=False)
    async with get_db() as db:
        await db.execute(
            "INSERT INTO file_classifications (file_path, file_hash, classification, suggested_name, tags_json, language) "
            "VALUES (?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(file_path) DO UPDATE SET "
            "  file_hash = excluded.file_hash, "
            "  classification = excluded.classification, "
            "  suggested_name = excluded.suggested_name, "
            "  tags_json = excluded.tags_json, "
            "  language = excluded.language, "
            "  classified_at = CURRENT_TIMESTAMP",
            (req.file_path, file_hash, classification, suggested_name, tags_json, language),
        )
        await db.commit()

    await log_activity(
        action="ai.auto_classify",
        summary=f"Clasificare automată: {req.file_name} → {classification}",
        details={"file_name": req.file_name, "classification": classification, "provider": result["provider"]},
    )

    return {
        "classification": classification,
        "suggested_name": suggested_name,
        "tags": tags,
        "language": language,
        "provider": result["provider"],
        "cached": False,
    }


# ==========================================
# 15B.3 — RAG DOCUMENT SEARCH
# ==========================================

@router_doc_ops.post("/index-document")
async def index_document(req: IndexDocumentRequest):
    """
    Indexează un document pentru căutare RAG.
    Extrage text și salvează în document_index + FTS5.
    """
    if not os.path.exists(req.file_path):
        raise HTTPException(404, f"Fișierul nu există: {req.file_path}")

    try:
        text = await asyncio.to_thread(_extract_text, req.file_path)
    except ValueError as e:
        raise HTTPException(400, str(e))

    if not text.strip():
        raise HTTPException(400, "Nu s-a putut extrage text din fișier")

    file_name = Path(req.file_path).name
    file_type = Path(req.file_path).suffix.lstrip(".")
    file_size = os.path.getsize(req.file_path)

    # Auto-classify for tags
    classification = ""
    tags_json = "[]"
    language = ""

    # Quick heuristic classification (no AI call to save quota)
    lower_text = text[:2000].lower()
    if any(w in lower_text for w in ["factura", "invoice", "serie", "nr."]):
        classification = "factura"
    elif any(w in lower_text for w in ["contract", "acord", "clauza"]):
        classification = "contract"
    elif any(w in lower_text for w in ["certificat", "certificate", "conformitate"]):
        classification = "certificat"
    elif any(w in lower_text for w in ["raport", "report", "concluzii"]):
        classification = "raport"
    elif any(w in lower_text for w in ["manual", "instructiuni", "ghid"]):
        classification = "manual"
    else:
        classification = "document"

    # Language detection heuristic
    ro_markers = sum(1 for w in ["și", "sau", "pentru", "care", "este", "într", "din"] if w in lower_text)
    en_markers = sum(1 for w in ["the", "and", "for", "which", "this", "from", "with"] if w in lower_text)
    language = "ro" if ro_markers > en_markers else "en" if en_markers > ro_markers else "mixed"

    async with get_db() as db:
        await db.execute(
            "INSERT INTO document_index (file_path, file_name, content_text, file_type, "
            "classification, tags, language, file_size) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(file_path) DO UPDATE SET "
            "  file_name = excluded.file_name, "
            "  content_text = excluded.content_text, "
            "  file_type = excluded.file_type, "
            "  classification = excluded.classification, "
            "  tags = excluded.tags, "
            "  language = excluded.language, "
            "  file_size = excluded.file_size, "
            "  indexed_at = CURRENT_TIMESTAMP",
            (req.file_path, file_name, text, file_type, classification, tags_json, language, file_size),
        )
        await db.commit()

        # Get document count
        cursor = await db.execute("SELECT COUNT(*) AS cnt FROM document_index")
        total = (await cursor.fetchone())["cnt"]

    await log_activity(
        action="ai.index_document",
        summary=f"Document indexat: {file_name} ({classification})",
        details={"file_name": file_name, "file_type": file_type, "language": language},
    )

    return {
        "status": "indexed",
        "file_name": file_name,
        "classification": classification,
        "language": language,
        "text_length": len(text),
        "total_indexed": total,
    }


@router_doc_ops.get("/search-documents")
async def search_documents(
    q: str = Query(..., min_length=2, description="Termen de căutare"),
    limit: int = Query(10, ge=1, le=50),
):
    """
    Căutare FTS5 în documentele indexate. Returnează documente cu snippet-uri.
    """
    async with get_db() as db:
        try:
            # FTS5 search with snippets
            cursor = await db.execute(
                "SELECT d.id, d.file_name, d.file_path, d.classification, d.language, "
                "  d.file_type, d.indexed_at, "
                "  snippet(document_fts, 1, '<b>', '</b>', '...', 40) AS snippet "
                "FROM document_fts "
                "JOIN document_index d ON d.id = document_fts.rowid "
                "WHERE document_fts MATCH ? "
                "ORDER BY rank "
                "LIMIT ?",
                (q, limit),
            )
            results = [dict(r) for r in await cursor.fetchall()]
        except Exception as e:
            # Fallback: LIKE search if FTS fails (e.g., syntax error in query)
            logger.warning("FTS search failed, falling back to LIKE: %s", e)
            cursor = await db.execute(
                "SELECT id, file_name, file_path, classification, language, "
                "  file_type, indexed_at, "
                "  substr(content_text, 1, 200) AS snippet "
                "FROM document_index "
                "WHERE file_name LIKE ? OR content_text LIKE ? "
                "ORDER BY indexed_at DESC LIMIT ?",
                (f"%{q}%", f"%{q}%", limit),
            )
            results = [dict(r) for r in await cursor.fetchall()]

    return {"query": q, "count": len(results), "results": results}


@router_doc_ops.post("/rag-query")
async def rag_query(
    req: RagQueryRequest,
    max_docs: int = Query(3, ge=1, le=10, description="Nr. maxim documente pentru context RAG"),
):
    """
    RAG: caută documente relevante, injectează top N ca context, AI răspunde.
    max_docs controlabil via query param (default 3, max 10).
    """
    if not req.question.strip():
        raise HTTPException(400, "Întrebarea este goală")

    # Body field overrides query param if provided
    doc_limit = req.max_docs if req.max_docs is not None else max_docs
    doc_limit = max(1, min(10, doc_limit))

    # Search for relevant documents
    context_docs = []
    async with get_db() as db:
        try:
            cursor = await db.execute(
                "SELECT d.file_name, d.content_text, d.classification "
                "FROM document_fts "
                "JOIN document_index d ON d.id = document_fts.rowid "
                "WHERE document_fts MATCH ? "
                "ORDER BY rank "
                "LIMIT ?",
                (req.question, doc_limit),
            )
            context_docs = [dict(r) for r in await cursor.fetchall()]
        except Exception as e:
            # Fallback: LIKE search
            logger.warning("FTS RAG search failed, falling back to LIKE: %s", e)
            search_terms = req.question.split()[:3]
            like_clause = " OR ".join(["content_text LIKE ?"] * len(search_terms))
            like_params = [f"%{t}%" for t in search_terms]
            like_params.append(doc_limit)
            cursor = await db.execute(
                f"SELECT file_name, content_text, classification "
                f"FROM document_index WHERE {like_clause} "
                f"ORDER BY indexed_at DESC LIMIT ?",
                like_params,
            )
            context_docs = [dict(r) for r in await cursor.fetchall()]

    if not context_docs:
        # No documents found, answer without context
        system = (
            "Ești un asistent AI integrat în Roland Command Center. "
            "Răspunzi în limba română. Nu ai găsit documente relevante în baza de date."
        )
        prompt = (
            f"Întrebare: {req.question}\n\n"
            "Nu am găsit documente relevante în indexul local. "
            "Răspunde pe baza cunoștințelor tale generale, menționând că nu ai acces la documente specifice."
        )
    else:
        # Build context from top documents
        context_parts = []
        sources = []
        for doc in context_docs:
            truncated = _truncate_text(doc["content_text"], 15000)
            context_parts.append(
                f"--- Document: {doc['file_name']} (Tip: {doc['classification']}) ---\n{truncated}"
            )
            sources.append(doc["file_name"])

        context_text = "\n\n".join(context_parts)

        system = (
            "Ești un asistent AI cu acces la documente locale din Roland Command Center. "
            "Răspunzi la întrebări bazat pe conținutul documentelor furnizate. "
            "Dacă răspunsul nu se găsește în documente, spune clar. "
            "Citează documentul sursă când e relevant. Limba: română."
        )
        prompt = (
            f"Documente relevante:\n{context_text}\n\n"
            f"---\nÎntrebare: {req.question}"
        )

    result = await ai_generate(prompt, system)
    await track_usage(result["provider"], chars=len(prompt) + len(result["text"]))

    await log_activity(
        action="ai.rag_query",
        summary=f"RAG query: {req.question[:80]}",
        details={
            "question": req.question,
            "docs_found": len(context_docs),
            "provider": result["provider"],
        },
    )

    return {
        "answer": result["text"],
        "sources": [doc["file_name"] for doc in context_docs],
        "docs_searched": len(context_docs),
        "provider": result["provider"],
    }
