"""
Sistem centralizat de logare a activității din panoul de control.

Salvează fiecare acțiune utilizator într-un fișier JSON persistent:
  backend/data/activity_log.json

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
from pathlib import Path
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)

LOG_FILE = settings.data_dir / "activity_log.json"
MAX_ENTRIES = 1000  # Păstrează ultimele 1000 de intrări


def log_activity(
    action: str,
    status: str = "success",
    summary: str = "",
    details: dict[str, Any] | None = None,
) -> None:
    """
    Adaugă o intrare în logul de activitate.

    Args:
        action: Tipul acțiunii (upload, calculate, calibrate, etc.)
        status: success / error / warning / rejected
        summary: Descriere scurtă, o linie
        details: Date suplimentare (opțional)
    """
    try:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "status": status,
            "summary": summary,
        }
        if details:
            entry["details"] = details

        # Citește log existent
        entries: list[dict] = []
        if LOG_FILE.exists():
            try:
                with open(LOG_FILE, "r", encoding="utf-8") as f:
                    entries = json.load(f)
            except (json.JSONDecodeError, OSError):
                entries = []

        entries.append(entry)

        # Trunchiază la MAX_ENTRIES
        if len(entries) > MAX_ENTRIES:
            entries = entries[-MAX_ENTRIES:]

        # Salvează
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(entries, f, indent=2, ensure_ascii=False)

    except Exception as exc:
        logger.warning("Nu s-a putut scrie în activity_log: %s", exc)


def get_activity_log(
    limit: int = 50,
    action_filter: str | None = None,
) -> list[dict[str, Any]]:
    """
    Citește ultimele *limit* intrări din logul de activitate.

    Args:
        limit: Numărul maxim de intrări returnate (cele mai recente).
        action_filter: Filtrează doar acțiunile de un anumit tip.

    Returns:
        Lista de intrări (cele mai recente primele).
    """
    if not LOG_FILE.exists():
        return []
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            entries = json.load(f)
    except (json.JSONDecodeError, OSError):
        return []

    if action_filter:
        entries = [e for e in entries if e.get("action") == action_filter]

    # Returnează cele mai recente primele
    return list(reversed(entries[-limit:]))
