"""
Sistem centralizat de logare a activității — SQLite-backed.

Salvează fiecare acțiune utilizator în tabelul activity_log din SQLite.

Format per intrare:
  {timestamp, action, status, summary, details}

Acțiuni logabile:
  - upload           — fișier încărcat
  - calculate        — calcul preț executat
  - validate_price   — preț validat de utilizator (self-learning)
  - calibrate        — calibrare executată
  - calibrate_revert — calibrare restaurată din backup
  - calibrate_reset  — calibrare resetată la defaults
  - delete_history   — calcul șters din istoric
  - update_settings  — setări modificate
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from app.db.database import get_db

logger = logging.getLogger(__name__)


async def log_activity(
    action: str,
    status: str = "success",
    summary: str = "",
    details: dict[str, Any] | None = None,
) -> None:
    """
    Adaugă o intrare în logul de activitate (SQLite).

    Args:
        action: Tipul acțiunii (upload, calculate, calibrate, etc.)
        status: success / error / warning / rejected
        summary: Descriere scurtă, o linie
        details: Date suplimentare (opțional)
    """
    try:
        details_json = json.dumps(details, ensure_ascii=False) if details else None
        async with get_db() as db:
            await db.execute(
                """INSERT INTO activity_log (timestamp, action, status, summary, details)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    datetime.now(timezone.utc).isoformat(),
                    action,
                    status,
                    summary,
                    details_json,
                ),
            )
            await db.commit()
    except Exception as exc:
        logger.warning("Nu s-a putut scrie în activity_log: %s", exc)


async def get_activity_log(
    limit: int = 50,
    action_filter: str | None = None,
) -> list[dict[str, Any]]:
    """
    Citește ultimele *limit* intrări din logul de activitate.

    Args:
        limit: Numărul maxim de intrări returnate (cele mai recente primele).
        action_filter: Filtrează doar acțiunile de un anumit tip.

    Returns:
        Lista de intrări (cele mai recente primele).
    """
    try:
        async with get_db() as db:
            if action_filter:
                cursor = await db.execute(
                    "SELECT * FROM activity_log WHERE action = ? ORDER BY timestamp DESC LIMIT ?",
                    (action_filter, limit),
                )
            else:
                cursor = await db.execute(
                    "SELECT * FROM activity_log ORDER BY timestamp DESC LIMIT ?",
                    (limit,),
                )
            rows = await cursor.fetchall()

            result = []
            for row in rows:
                entry = {
                    "timestamp": row["timestamp"],
                    "action": row["action"],
                    "status": row["status"],
                    "summary": row["summary"],
                }
                if row["details"]:
                    try:
                        entry["details"] = json.loads(row["details"])
                    except json.JSONDecodeError:
                        entry["details"] = row["details"]
                result.append(entry)
            return result
    except Exception as exc:
        logger.warning("Nu s-a putut citi activity_log: %s", exc)
        return []
