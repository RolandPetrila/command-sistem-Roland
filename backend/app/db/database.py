"""
Bază de date SQLite cu aiosqlite pentru operații asincrone.

Funcționalități:
- init_db(): Creează tabelele dacă nu există.
- get_db(): Context manager async pentru conexiunea la baza de date.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import aiosqlite

from app.config import settings
from app.db.models import CREATE_TABLES

logger = logging.getLogger(__name__)


async def init_db() -> None:
    """
    Inițializează baza de date: creează tabelele și setările implicite.

    Se apelează la pornirea aplicației.
    """
    settings.ensure_dirs()
    db_path = str(settings.db_path)

    async with aiosqlite.connect(db_path) as db:
        # Activare foreign keys + performance
        await db.execute("PRAGMA foreign_keys = ON")
        await db.execute("PRAGMA journal_mode = WAL")
        await db.execute("PRAGMA busy_timeout = 5000")

        # Creează tabelele
        for table_sql in CREATE_TABLES:
            await db.execute(table_sql)

        # Inserare setări implicite (doar dacă nu există)
        default_settings = {
            "invoice_percent": str(settings.default_invoice_percent),
            "currency": "RON",
            "language": "ro",
        }
        for key, value in default_settings.items():
            await db.execute(
                """
                INSERT OR IGNORE INTO settings (key, value)
                VALUES (?, ?)
                """,
                (key, value),
            )

        await db.commit()

    logger.info("Baza de date inițializată: %s", db_path)


@asynccontextmanager
async def get_db() -> AsyncGenerator[aiosqlite.Connection, None]:
    """
    Context manager async pentru conexiunea la baza de date.

    Exemplu utilizare:
        async with get_db() as db:
            cursor = await db.execute("SELECT * FROM uploads")
            rows = await cursor.fetchall()
    """
    db_path = str(settings.db_path)
    db = await aiosqlite.connect(db_path)
    db.row_factory = aiosqlite.Row
    try:
        await db.execute("PRAGMA foreign_keys = ON")
        await db.execute("PRAGMA busy_timeout = 5000")
        yield db
    finally:
        await db.close()


async def execute_query(
    query: str,
    params: tuple = (),
    fetch: bool = True,
) -> list[dict] | int:
    """
    Execută o interogare SQL și returnează rezultatele.

    Args:
        query: Interogarea SQL.
        params: Parametri pentru interogare.
        fetch: Dacă True, returnează rândurile. Dacă False, returnează lastrowid.

    Returns:
        Lista de dicționare (fetch=True) sau lastrowid (fetch=False).
    """
    async with get_db() as db:
        cursor = await db.execute(query, params)

        if fetch:
            rows = await cursor.fetchall()
            if rows:
                return [dict(row) for row in rows]
            return []
        else:
            await db.commit()
            return cursor.lastrowid


async def get_setting(key: str, default: str | None = None) -> str | None:
    """Returnează o setare din baza de date."""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        )
        row = await cursor.fetchone()
        return row["value"] if row else default


async def update_setting(key: str, value: str) -> None:
    """Actualizează sau inserează o setare."""
    async with get_db() as db:
        await db.execute(
            """
            INSERT INTO settings (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = CURRENT_TIMESTAMP
            """,
            (key, value),
        )
        await db.commit()
