"""
Translation Memory (TM) — cautare FTS5, adaugare segmente, statistici.

Segmenteaza textul in propozitii, cauta in TM inainte de traducere,
salveaza traducerile noi in TM pentru reutilizare ulterioara.
"""

from __future__ import annotations

import logging
import re
from difflib import SequenceMatcher
from typing import Callable, Awaitable

from app.db.database import get_db

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Text segmentation
# ---------------------------------------------------------------------------

def segment_text(text: str) -> list[str]:
    """
    Split text into sentences for TM lookup.

    Uses simple regex: split on `.`, `!`, `?` followed by space or end-of-string.
    Preserves the punctuation with the sentence.
    Filters out empty/whitespace-only segments.
    """
    # Split on sentence-ending punctuation followed by whitespace or end
    segments = re.split(r'(?<=[.!?])\s+', text.strip())
    # Filter empty segments and strip whitespace
    return [s.strip() for s in segments if s.strip()]


# ---------------------------------------------------------------------------
# Similarity scoring
# ---------------------------------------------------------------------------

def _similarity(a: str, b: str) -> float:
    """Compute similarity ratio between two strings (0.0 - 1.0)."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


# ---------------------------------------------------------------------------
# TM Search
# ---------------------------------------------------------------------------

async def search_tm(
    text: str,
    source_lang: str,
    target_lang: str,
    threshold: float = 0.7,
    limit: int = 10,
) -> list[dict]:
    """
    Search Translation Memory for similar segments using FTS5 + similarity scoring.

    Returns list of matches with confidence score, sorted by relevance.
    """
    matches = []

    async with get_db() as db:
        # First try FTS5 search with key words from the text
        # Extract significant words (>3 chars) for FTS query
        words = [w for w in re.findall(r'\b\w{3,}\b', text.lower()) if w]
        if not words:
            return []

        # Use OR query for FTS5 — match any word
        fts_query = " OR ".join(words[:10])  # limit to 10 words

        try:
            cursor = await db.execute(
                """
                SELECT tm.id, tm.source_segment, tm.target_segment,
                       tm.source_lang, tm.target_lang, tm.domain,
                       tm.confidence, tm.usage_count
                FROM tm_fts fts
                JOIN translation_memory tm ON fts.rowid = tm.id
                WHERE tm_fts MATCH ?
                  AND tm.source_lang = ?
                  AND tm.target_lang = ?
                LIMIT 50
                """,
                (fts_query, source_lang.lower(), target_lang.lower()),
            )
            rows = await cursor.fetchall()
        except Exception as e:
            logger.warning("FTS5 search error, falling back to LIKE: %s", e)
            # Fallback to LIKE search
            cursor = await db.execute(
                """
                SELECT id, source_segment, target_segment,
                       source_lang, target_lang, domain,
                       confidence, usage_count
                FROM translation_memory
                WHERE source_lang = ? AND target_lang = ?
                  AND source_segment LIKE ?
                LIMIT 50
                """,
                (source_lang.lower(), target_lang.lower(), f"%{words[0]}%"),
            )
            rows = await cursor.fetchall()

        for row in rows:
            sim = _similarity(text, row["source_segment"])
            if sim >= threshold:
                matches.append({
                    "id": row["id"],
                    "source_segment": row["source_segment"],
                    "target_segment": row["target_segment"],
                    "source_lang": row["source_lang"],
                    "target_lang": row["target_lang"],
                    "domain": row["domain"],
                    "confidence": round(sim, 3),
                    "usage_count": row["usage_count"],
                })

    # Sort by similarity descending
    matches.sort(key=lambda m: m["confidence"], reverse=True)
    return matches[:limit]


# ---------------------------------------------------------------------------
# TM CRUD
# ---------------------------------------------------------------------------

async def add_to_tm(
    source: str,
    target: str,
    source_lang: str,
    target_lang: str,
    domain: str = "general",
) -> int:
    """
    Add a source-target segment pair to Translation Memory.

    If an identical source segment already exists (same langs), update the target
    and increment usage_count instead of creating a duplicate.

    Returns the row id.
    """
    async with get_db() as db:
        # Check for existing identical source segment
        cursor = await db.execute(
            """
            SELECT id, usage_count FROM translation_memory
            WHERE source_segment = ? AND source_lang = ? AND target_lang = ?
            """,
            (source.strip(), source_lang.lower(), target_lang.lower()),
        )
        existing = await cursor.fetchone()

        if existing:
            # Update existing entry
            await db.execute(
                """
                UPDATE translation_memory
                SET target_segment = ?, domain = ?,
                    usage_count = usage_count + 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (target.strip(), domain, existing["id"]),
            )
            await db.commit()
            return existing["id"]
        else:
            # Insert new entry
            cursor = await db.execute(
                """
                INSERT INTO translation_memory
                    (source_segment, target_segment, source_lang, target_lang, domain)
                VALUES (?, ?, ?, ?, ?)
                """,
                (source.strip(), target.strip(), source_lang.lower(), target_lang.lower(), domain),
            )
            await db.commit()
            return cursor.lastrowid


async def get_tm_entries(
    source_lang: str | None = None,
    target_lang: str | None = None,
    domain: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[dict]:
    """List TM entries with optional filters and pagination."""
    conditions = []
    params: list = []

    if source_lang:
        conditions.append("source_lang = ?")
        params.append(source_lang.lower())
    if target_lang:
        conditions.append("target_lang = ?")
        params.append(target_lang.lower())
    if domain:
        conditions.append("domain = ?")
        params.append(domain)

    where = ""
    if conditions:
        where = "WHERE " + " AND ".join(conditions)

    async with get_db() as db:
        cursor = await db.execute(
            f"""
            SELECT id, source_segment, target_segment, source_lang, target_lang,
                   domain, confidence, usage_count, created_at, updated_at
            FROM translation_memory
            {where}
            ORDER BY updated_at DESC
            LIMIT ? OFFSET ?
            """,
            (*params, limit, skip),
        )
        rows = await cursor.fetchall()

        # Get total count
        cursor_count = await db.execute(
            f"SELECT COUNT(*) as cnt FROM translation_memory {where}",
            tuple(params),
        )
        total_row = await cursor_count.fetchone()
        total = total_row["cnt"] if total_row else 0

    return {
        "items": [dict(r) for r in rows],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


async def delete_tm_entry(tm_id: int) -> bool:
    """Delete a TM entry by ID."""
    async with get_db() as db:
        cursor = await db.execute(
            "DELETE FROM translation_memory WHERE id = ?", (tm_id,)
        )
        await db.commit()
        return cursor.rowcount > 0


# ---------------------------------------------------------------------------
# TM Statistics
# ---------------------------------------------------------------------------

async def get_tm_stats() -> dict:
    """Get Translation Memory statistics."""
    async with get_db() as db:
        # Total segments
        cursor = await db.execute("SELECT COUNT(*) as cnt FROM translation_memory")
        total = (await cursor.fetchone())["cnt"]

        # Per language pair
        cursor = await db.execute(
            """
            SELECT source_lang, target_lang, COUNT(*) as cnt
            FROM translation_memory
            GROUP BY source_lang, target_lang
            ORDER BY cnt DESC
            """
        )
        lang_pairs = [dict(r) for r in await cursor.fetchall()]

        # Per domain
        cursor = await db.execute(
            """
            SELECT domain, COUNT(*) as cnt
            FROM translation_memory
            GROUP BY domain
            ORDER BY cnt DESC
            """
        )
        domains = [dict(r) for r in await cursor.fetchall()]

        # Most used segments (top 10)
        cursor = await db.execute(
            """
            SELECT source_segment, target_segment, usage_count
            FROM translation_memory
            ORDER BY usage_count DESC
            LIMIT 10
            """
        )
        top_used = [dict(r) for r in await cursor.fetchall()]

    return {
        "total_segments": total,
        "language_pairs": lang_pairs,
        "domains": domains,
        "top_used": top_used,
    }


# ---------------------------------------------------------------------------
# Translate with TM
# ---------------------------------------------------------------------------

async def translate_with_tm(
    text: str,
    source_lang: str,
    target_lang: str,
    translate_fn: Callable[[str, str, str], Awaitable[dict]],
    domain: str = "general",
    tm_threshold: float = 0.85,
) -> dict:
    """
    Translate text using TM first, then fallback to translate_fn.

    For each sentence segment:
    1. Search TM for a match above threshold
    2. If found, use TM result
    3. If not found, call translate_fn and save result to TM

    Returns: {
        "translated_text": str,
        "segments": [...],
        "tm_hits": int,
        "tm_misses": int,
        "provider": str,
    }
    """
    segments = segment_text(text)
    if not segments:
        return {
            "translated_text": "",
            "segments": [],
            "tm_hits": 0,
            "tm_misses": 0,
            "provider": "none",
        }

    translated_segments = []
    tm_hits = 0
    tm_misses = 0
    provider_used = "tm"

    for segment in segments:
        # Search TM
        tm_matches = await search_tm(segment, source_lang, target_lang, threshold=tm_threshold, limit=1)

        if tm_matches:
            # TM hit — use the best match
            best = tm_matches[0]
            translated_segments.append({
                "source": segment,
                "target": best["target_segment"],
                "from_tm": True,
                "confidence": best["confidence"],
            })
            tm_hits += 1

            # Increment usage count
            async with get_db() as db:
                await db.execute(
                    "UPDATE translation_memory SET usage_count = usage_count + 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (best["id"],),
                )
                await db.commit()
        else:
            # TM miss — translate with provider
            try:
                result = await translate_fn(segment, source_lang, target_lang)
                translated = result["translated_text"]
                provider_used = result.get("provider", "unknown")

                translated_segments.append({
                    "source": segment,
                    "target": translated,
                    "from_tm": False,
                    "provider": provider_used,
                })

                # Save to TM for future use
                await add_to_tm(segment, translated, source_lang, target_lang, domain)
                tm_misses += 1
            except Exception as e:
                logger.error("Eroare la traducerea segmentului: %s", e)
                translated_segments.append({
                    "source": segment,
                    "target": segment,  # Keep original on failure
                    "from_tm": False,
                    "error": str(e),
                })
                tm_misses += 1

    # Reconstruct full translated text
    translated_text = " ".join(seg["target"] for seg in translated_segments)

    return {
        "translated_text": translated_text,
        "segments": translated_segments,
        "tm_hits": tm_hits,
        "tm_misses": tm_misses,
        "provider": provider_used if tm_misses > 0 else "tm",
    }
