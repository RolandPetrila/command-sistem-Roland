"""
Shared helper functions for the Translator module:
file extraction, upload handling, translation cache, latency tracking.
"""

from __future__ import annotations

import hashlib
import logging
import tempfile
from pathlib import Path

from fastapi import UploadFile

from app.db.database import get_db

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# File text extraction
# ---------------------------------------------------------------------------

def extract_text_from_file(file_path: str) -> str:
    """Extract text from PDF, DOCX, or text file."""
    import fitz  # PyMuPDF  — lazy import to cut cold-start time
    from docx import Document as DocxDocument

    p = file_path.lower()
    if p.endswith(".pdf"):
        doc = fitz.open(file_path)
        text = "\n".join(page.get_text() for page in doc)
        doc.close()
        return text.strip()
    elif p.endswith(".docx"):
        doc = DocxDocument(file_path)
        return "\n".join(para.text for para in doc.paragraphs if para.text.strip()).strip()
    elif p.endswith((".txt", ".md", ".csv", ".html", ".xml")):
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read().strip()
    else:
        raise ValueError(f"Tip fisier nesuportat: {Path(file_path).suffix}")


# ---------------------------------------------------------------------------
# Upload handling
# ---------------------------------------------------------------------------

async def save_upload(file: UploadFile) -> str:
    """Save UploadFile to temp and return path."""
    suffix = Path(file.filename or "file").suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir=tempfile.gettempdir()) as tmp:
        content = await file.read()
        tmp.write(content)
        return tmp.name


# ---------------------------------------------------------------------------
# Translation cache
# ---------------------------------------------------------------------------

def compute_cache_hash(text: str, source_lang: str, target_lang: str) -> str:
    """Compute SHA-256 hash for translation cache key."""
    key = f"{text}|{source_lang.lower()}|{target_lang.lower()}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


async def ensure_cache_table() -> None:
    """Create translation_cache table if it does not exist."""
    async with get_db() as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS translation_cache (
                hash        TEXT PRIMARY KEY,
                source_text TEXT NOT NULL,
                target_text TEXT NOT NULL,
                source_lang TEXT NOT NULL,
                target_lang TEXT NOT NULL,
                provider    TEXT NOT NULL,
                created_at  TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        await db.commit()


# ---------------------------------------------------------------------------
# Provider latency tracking (in-memory)
# ---------------------------------------------------------------------------

# {provider_name: [latency_ms, ...]}
_provider_latencies: dict[str, list[float]] = {}


def record_latency(provider_name: str, latency_ms: float) -> None:
    """Record a provider latency measurement (keep last 20)."""
    if provider_name not in _provider_latencies:
        _provider_latencies[provider_name] = []
    _provider_latencies[provider_name].append(latency_ms)
    # Keep only last 20 measurements
    if len(_provider_latencies[provider_name]) > 20:
        _provider_latencies[provider_name] = _provider_latencies[provider_name][-20:]


def get_provider_latencies() -> dict[str, list[float]]:
    """Return the latency store (read-only reference)."""
    return _provider_latencies
