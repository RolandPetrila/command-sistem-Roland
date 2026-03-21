"""
Bază de date SQLite cu aiosqlite + sistem de migrare SQL.

Funcționalități:
- run_migrations(): Rulează migrări SQL pendinte din migrations/.
- init_db(): Inițializează DB cu migrări + setări implicite.
- get_db(): Context manager async pentru conexiunea la baza de date.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

import aiosqlite

from app.config import settings

logger = logging.getLogger(__name__)

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent.parent / "migrations"


async def run_migrations(db: aiosqlite.Connection) -> None:
    """
    Rulează migrările SQL pendinte din directorul migrations/.

    Fiecare fișier SQL trebuie să fie prefixat cu un număr de versiune
    (ex: 001_initial.sql, 002_add_clients.sql) și să conțină la final
    un INSERT INTO schema_version cu versiunea aplicată.
    """
    await db.execute("""
        CREATE TABLE IF NOT EXISTS schema_version (
            version     INTEGER PRIMARY KEY,
            name        TEXT NOT NULL,
            applied_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    await db.commit()

    cursor = await db.execute("SELECT MAX(version) FROM schema_version")
    row = await cursor.fetchone()
    current_version = row[0] if row[0] is not None else 0

    if not MIGRATIONS_DIR.exists():
        logger.warning("Director migrări inexistent: %s", MIGRATIONS_DIR)
        return

    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    applied = 0

    for mig_file in migration_files:
        try:
            version = int(mig_file.stem.split("_")[0])
        except (ValueError, IndexError):
            continue

        if version <= current_version:
            continue

        logger.info("Rulez migrarea %s...", mig_file.name)
        sql = mig_file.read_text(encoding="utf-8")
        await db.executescript(sql)
        applied += 1
        logger.info("Migrare aplicată: %s (v%d)", mig_file.name, version)

    if applied:
        logger.info("Total migrări aplicate: %d", applied)


async def init_db() -> None:
    """
    Inițializează baza de date: rulează migrări + setări implicite.

    Se apelează la pornirea aplicației.
    """
    settings.ensure_dirs()
    db_path = str(settings.db_path)

    async with aiosqlite.connect(db_path) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        await db.execute("PRAGMA journal_mode = WAL")
        await db.execute("PRAGMA busy_timeout = 5000")

        await run_migrations(db)

        # Z2.2 — VACUUM + ANALYZE for smaller DB and faster queries
        try:
            await db.execute("PRAGMA optimize")
            logger.info("PRAGMA optimize executat.")
        except Exception:
            pass  # optimize not available on older SQLite

        default_settings = {
            "invoice_percent": str(settings.default_invoice_percent),
            "currency": "RON",
            "language": "ro",
        }
        for key, value in default_settings.items():
            await db.execute(
                "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
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
        await db.execute("PRAGMA cache_size = -8000")  # 8MB cache
        await db.execute("PRAGMA temp_store = MEMORY")
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
