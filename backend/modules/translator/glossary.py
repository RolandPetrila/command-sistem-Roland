"""
Glossary CRUD — gestionare termeni tehnici cu import/export CSV.

Aplica glosarul pe text inainte de traducere pentru a asigura
consistenta terminologiei tehnice (mai ales automotive/ITP).
"""

from __future__ import annotations

import csv
import io
import logging
import re
from typing import Optional

from app.db.database import get_db

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# List / Search
# ---------------------------------------------------------------------------

async def get_glossary(
    domain: str | None = None,
    search: str | None = None,
    source_lang: str | None = None,
    target_lang: str | None = None,
    client_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
) -> dict:
    """
    List glossary terms with optional filters.

    Returns: {"items": [...], "total": int, "skip": int, "limit": int}
    """
    conditions = []
    params: list = []

    if domain:
        conditions.append("domain = ?")
        params.append(domain)
    if source_lang:
        conditions.append("source_lang = ?")
        params.append(source_lang.lower())
    if target_lang:
        conditions.append("target_lang = ?")
        params.append(target_lang.lower())
    if client_id is not None:
        conditions.append("client_id = ?")
        params.append(client_id)
    if search:
        conditions.append("(term_source LIKE ? OR term_target LIKE ? OR notes LIKE ?)")
        like_param = f"%{search}%"
        params.extend([like_param, like_param, like_param])

    where = ""
    if conditions:
        where = "WHERE " + " AND ".join(conditions)

    async with get_db() as db:
        cursor = await db.execute(
            f"""
            SELECT id, term_source, term_target, source_lang, target_lang,
                   domain, notes, created_at
            FROM glossary_terms
            {where}
            ORDER BY term_source ASC
            LIMIT ? OFFSET ?
            """,
            (*params, limit, skip),
        )
        rows = await cursor.fetchall()

        cursor_count = await db.execute(
            f"SELECT COUNT(*) as cnt FROM glossary_terms {where}",
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


# ---------------------------------------------------------------------------
# Add term
# ---------------------------------------------------------------------------

async def add_term(
    source: str,
    target: str,
    source_lang: str = "en",
    target_lang: str = "ro",
    domain: str = "general",
    notes: str | None = None,
    client_id: int | None = None,
) -> dict:
    """Add a term to the glossary. Returns the created term."""
    async with get_db() as db:
        # Check for duplicate (within same client scope)
        if client_id is not None:
            cursor = await db.execute(
                "SELECT id FROM glossary_terms WHERE term_source = ? AND source_lang = ? AND target_lang = ? AND client_id = ?",
                (source.strip(), source_lang.lower(), target_lang.lower(), client_id),
            )
        else:
            cursor = await db.execute(
                "SELECT id FROM glossary_terms WHERE term_source = ? AND source_lang = ? AND target_lang = ? AND client_id IS NULL",
                (source.strip(), source_lang.lower(), target_lang.lower()),
            )
        existing = await cursor.fetchone()
        if existing:
            raise ValueError(
                f"Termenul '{source}' exista deja in glosar (ID: {existing['id']}). "
                f"Foloseste PUT pentru actualizare."
            )

        cursor = await db.execute(
            """INSERT INTO glossary_terms (term_source, term_target, source_lang, target_lang, domain, notes, client_id)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (source.strip(), target.strip(), source_lang.lower(), target_lang.lower(), domain, notes, client_id),
        )
        await db.commit()
        term_id = cursor.lastrowid

        cursor = await db.execute(
            "SELECT * FROM glossary_terms WHERE id = ?", (term_id,)
        )
        row = await cursor.fetchone()
        return dict(row)


# ---------------------------------------------------------------------------
# Update term
# ---------------------------------------------------------------------------

async def update_term(
    term_id: int,
    source: str | None = None,
    target: str | None = None,
    source_lang: str | None = None,
    target_lang: str | None = None,
    domain: str | None = None,
    notes: str | None = None,
) -> dict | None:
    """Update an existing glossary term. Returns updated term or None if not found."""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM glossary_terms WHERE id = ?", (term_id,)
        )
        existing = await cursor.fetchone()
        if not existing:
            return None

        # Build update fields
        updates = []
        params = []
        if source is not None:
            updates.append("term_source = ?")
            params.append(source.strip())
        if target is not None:
            updates.append("term_target = ?")
            params.append(target.strip())
        if source_lang is not None:
            updates.append("source_lang = ?")
            params.append(source_lang.lower())
        if target_lang is not None:
            updates.append("target_lang = ?")
            params.append(target_lang.lower())
        if domain is not None:
            updates.append("domain = ?")
            params.append(domain)
        if notes is not None:
            updates.append("notes = ?")
            params.append(notes)

        if not updates:
            return dict(existing)

        params.append(term_id)
        await db.execute(
            f"UPDATE glossary_terms SET {', '.join(updates)} WHERE id = ?",
            tuple(params),
        )
        await db.commit()

        cursor = await db.execute(
            "SELECT * FROM glossary_terms WHERE id = ?", (term_id,)
        )
        row = await cursor.fetchone()
        return dict(row)


# ---------------------------------------------------------------------------
# Delete term
# ---------------------------------------------------------------------------

async def delete_term(term_id: int) -> bool:
    """Delete a glossary term by ID. Returns True if deleted."""
    async with get_db() as db:
        cursor = await db.execute(
            "DELETE FROM glossary_terms WHERE id = ?", (term_id,)
        )
        await db.commit()
        return cursor.rowcount > 0


# ---------------------------------------------------------------------------
# Import CSV
# ---------------------------------------------------------------------------

async def import_glossary_csv(
    file_content: str,
    source_lang: str = "en",
    target_lang: str = "ro",
    default_domain: str = "general",
) -> dict:
    """
    Import glossary terms from CSV content.

    Expected CSV columns: source, target, domain (optional)
    First row can be header (auto-detected).

    Returns: {"imported": int, "skipped": int, "errors": [...]}
    """
    imported = 0
    skipped = 0
    errors = []

    reader = csv.reader(io.StringIO(file_content))
    rows = list(reader)

    if not rows:
        return {"imported": 0, "skipped": 0, "errors": ["Fisierul CSV este gol"]}

    # Auto-detect header
    first_row = [c.strip().lower() for c in rows[0]]
    has_header = any(
        h in first_row for h in ["source", "target", "sursa", "traducere", "termen", "term"]
    )
    start_idx = 1 if has_header else 0

    for i, row in enumerate(rows[start_idx:], start=start_idx + 1):
        if not row or not row[0].strip():
            continue

        try:
            source_term = row[0].strip()
            target_term = row[1].strip() if len(row) > 1 else ""
            domain = row[2].strip() if len(row) > 2 and row[2].strip() else default_domain

            if not source_term or not target_term:
                errors.append(f"Rand {i}: sursa sau traducerea lipseste")
                skipped += 1
                continue

            await add_term(
                source=source_term,
                target=target_term,
                source_lang=source_lang,
                target_lang=target_lang,
                domain=domain,
            )
            imported += 1
        except ValueError:
            # Duplicate — skip silently
            skipped += 1
        except Exception as e:
            errors.append(f"Rand {i}: {str(e)}")
            skipped += 1

    return {"imported": imported, "skipped": skipped, "errors": errors}


# ---------------------------------------------------------------------------
# Apply glossary
# ---------------------------------------------------------------------------

async def apply_glossary(
    text: str,
    source_lang: str,
    target_lang: str,
) -> dict:
    """
    Apply glossary terms to text — replace known source terms with target translations.

    Uses word-boundary matching (case-insensitive) to avoid partial replacements.

    Returns: {"text": modified_text, "replacements": [{source, target}, ...]}
    """
    async with get_db() as db:
        cursor = await db.execute(
            """
            SELECT term_source, term_target
            FROM glossary_terms
            WHERE source_lang = ? AND target_lang = ?
            ORDER BY LENGTH(term_source) DESC
            """,
            (source_lang.lower(), target_lang.lower()),
        )
        terms = await cursor.fetchall()

    if not terms:
        return {"text": text, "replacements": []}

    replacements = []
    modified = text

    for term in terms:
        source_term = term["term_source"]
        target_term = term["term_target"]

        # Case-insensitive word boundary match
        pattern = re.compile(
            r'\b' + re.escape(source_term) + r'\b',
            re.IGNORECASE,
        )

        if pattern.search(modified):
            modified = pattern.sub(target_term, modified)
            replacements.append({
                "source": source_term,
                "target": target_term,
            })

    return {"text": modified, "replacements": replacements}


# ---------------------------------------------------------------------------
# Get glossary domains
# ---------------------------------------------------------------------------

async def get_glossary_domains() -> list[str]:
    """Get list of unique domains in the glossary."""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT DISTINCT domain FROM glossary_terms ORDER BY domain"
        )
        rows = await cursor.fetchall()
    return [r["domain"] for r in rows]
