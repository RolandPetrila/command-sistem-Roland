"""
Module auto-discovery — scanează backend/modules/ pentru routere FastAPI.

Fiecare modul trebuie să aibă:
  modules/[name]/__init__.py cu MODULE_INFO dict:
    {
      "name": "...",
      "description": "...",
      "routers": [router1, router2, ...],
      "category": "...",
      "icon": "...",
      "order": int,
    }
"""

from __future__ import annotations

import importlib
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

MODULES_DIR = Path(__file__).resolve().parent.parent / "modules"


def discover_modules() -> list[dict[str, Any]]:
    """
    Scanează backend/modules/ pentru module cu MODULE_INFO.

    Returns:
        Lista de MODULE_INFO dicts, sortate după 'order'.
    """
    discovered: list[dict[str, Any]] = []

    if not MODULES_DIR.exists():
        logger.warning("Director module inexistent: %s", MODULES_DIR)
        return discovered

    for module_dir in sorted(MODULES_DIR.iterdir()):
        if not module_dir.is_dir() or module_dir.name.startswith("_"):
            continue

        init_file = module_dir / "__init__.py"
        if not init_file.exists():
            continue

        try:
            mod = importlib.import_module(f"modules.{module_dir.name}")
            info = getattr(mod, "MODULE_INFO", None)
            if info and "routers" in info:
                discovered.append(info)
                logger.info(
                    "Modul descoperit: %s (%d routere)",
                    info.get("name", module_dir.name),
                    len(info["routers"]),
                )
        except Exception as exc:
            logger.warning("Nu s-a putut încărca modulul %s: %s", module_dir.name, exc)

    discovered.sort(key=lambda m: m.get("order", 999))
    return discovered
