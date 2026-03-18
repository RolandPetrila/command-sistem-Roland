"""
Modul de încărcare date piață competitori.

Încarcă datele din market_data.json (populat separat prin Playwright).
NU face scraping direct — acesta va fi implementat separat.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Calea către fișierul cu date de piață
_SCRAPER_DIR = Path(__file__).resolve().parent
MARKET_DATA_FILE = _SCRAPER_DIR / "market_data.json"
MARKET_RATES_FILE = _SCRAPER_DIR.parent / "data" / "market_rates.json"


def load_market_data() -> dict[str, Any]:
    """
    Încarcă datele de piață din market_data.json.

    Returns:
        Dicționar cu datele colectate de la competitori.
        Returnează dict gol dacă fișierul nu există sau e gol.
    """
    if not MARKET_DATA_FILE.exists():
        logger.info("Fișierul market_data.json nu există încă.")
        return {}

    try:
        with open(MARKET_DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Eroare la citirea market_data.json: %s", exc)
        return {}

    if not data:
        logger.info("market_data.json este gol.")
        return {}

    logger.info(
        "Date de piață încărcate: %d competitori.",
        len(data.get("competitors", [])),
    )
    return data


def load_market_rates() -> dict[str, Any]:
    """
    Încarcă tarifele medii de piață din market_rates.json.

    Returns:
        Dicționar cu tarifele medii per categorie.
    """
    if not MARKET_RATES_FILE.exists():
        logger.warning("Fișierul market_rates.json nu există.")
        return _default_market_rates()

    try:
        with open(MARKET_RATES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Eroare la citirea market_rates.json: %s", exc)
        return _default_market_rates()

    return data


def get_competitor_prices(
    document_type: str = "technical",
) -> dict[str, Any]:
    """
    Returnează prețurile competitorilor pentru un tip de document.

    Args:
        document_type: Tipul documentului (technical, general, legal).

    Returns:
        Dicționar cu prețuri medii, min, max de la competitori.
    """
    market_data = load_market_data()
    rates = load_market_rates()

    # Tarife din market_rates.json
    avg_per_page = rates.get("avg_rate_per_page", {}).get(document_type, 25)
    avg_per_word = rates.get("avg_rate_per_word", {}).get(document_type, 0.08)

    # Date de la competitori (dacă există)
    competitors = market_data.get("competitors", [])
    competitor_prices_per_page: list[float] = []
    competitor_prices_per_word: list[float] = []

    for comp in competitors:
        rates_comp = comp.get("rates", {})
        if document_type in rates_comp:
            doc_rates = rates_comp[document_type]
            if "per_page" in doc_rates:
                competitor_prices_per_page.append(doc_rates["per_page"])
            if "per_word" in doc_rates:
                competitor_prices_per_word.append(doc_rates["per_word"])

    result = {
        "document_type": document_type,
        "market_avg_per_page": avg_per_page,
        "market_avg_per_word": avg_per_word,
        "competitors_count": len(competitors),
        "data_available": len(competitors) > 0,
    }

    if competitor_prices_per_page:
        result["competitor_per_page"] = {
            "min": min(competitor_prices_per_page),
            "max": max(competitor_prices_per_page),
            "avg": round(
                sum(competitor_prices_per_page) / len(competitor_prices_per_page), 2
            ),
        }

    if competitor_prices_per_word:
        result["competitor_per_word"] = {
            "min": min(competitor_prices_per_word),
            "max": max(competitor_prices_per_word),
            "avg": round(
                sum(competitor_prices_per_word) / len(competitor_prices_per_word), 4
            ),
        }

    return result


def _default_market_rates() -> dict[str, Any]:
    """Tarife implicite dacă fișierul nu e disponibil."""
    return {
        "sources": [],
        "avg_rate_per_page": {"technical": 28, "general": 20, "legal": 35},
        "avg_rate_per_word": {"technical": 0.09, "general": 0.06, "legal": 0.12},
        "last_updated": None,
        "note": "Valori implicite — datele de piață nu sunt disponibile.",
    }
