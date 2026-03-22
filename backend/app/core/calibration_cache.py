"""
Shared calibration data cache — single source of truth.

Both routes_price.py and routes_quick_quote.py import from here
instead of maintaining separate caches.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)

_calibration_cache: dict = {"data": None, "mtime": 0.0}


def load_calibration_data() -> dict[str, Any] | None:
    """Load calibration data from JSON file, cached until file changes on disk."""
    cal_file = settings.calibration_file
    if not cal_file.exists():
        return None
    try:
        current_mtime = cal_file.stat().st_mtime
        if _calibration_cache["data"] is not None and current_mtime == _calibration_cache["mtime"]:
            return _calibration_cache["data"]
        with open(cal_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        result = data.get("calibration", data)
        _calibration_cache["data"] = result
        _calibration_cache["mtime"] = current_mtime
        return result
    except (json.JSONDecodeError, OSError):
        return None


def invalidate_calibration_cache() -> None:
    """Force-clear the calibration cache so next load reads from disk."""
    _calibration_cache["data"] = None
    _calibration_cache["mtime"] = 0.0
    logger.info("Calibration cache invalidated.")
