"""
Rute pentru compararea prețurilor cu competitorii.

GET /api/competitors/compare — compară prețul nostru cu piața
"""

import json
import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["competitors"])

# Locația fișierului cu date de piață (scraper output)
_MARKET_DATA_FILE = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "scraper"
    / "market_data.json"
)

# Date de piață implicite (backup dacă fișierul nu există)
DEFAULT_COMPETITOR_DATA = {
    "competitors": [
        {
            "name": "Agenție Traduceri A",
            "rate_per_word_eur": 0.08,
            "rate_per_page_eur": 20.0,
            "min_order_eur": 30.0,
        },
        {
            "name": "Agenție Traduceri B",
            "rate_per_word_eur": 0.07,
            "rate_per_page_eur": 18.0,
            "min_order_eur": 25.0,
        },
        {
            "name": "Agenție Traduceri C",
            "rate_per_word_eur": 0.10,
            "rate_per_page_eur": 25.0,
            "min_order_eur": 35.0,
        },
        {
            "name": "Agenție Traduceri D",
            "rate_per_word_eur": 0.09,
            "rate_per_page_eur": 22.0,
            "min_order_eur": 30.0,
        },
        {
            "name": "Agenție Traduceri E",
            "rate_per_word_eur": 0.06,
            "rate_per_page_eur": 15.0,
            "min_order_eur": 20.0,
        },
    ],
    "last_updated": "2025-01-01",
    "source": "date estimative piață românească",
}


@router.get("/competitors/compare")
async def compare_with_competitors(
    market_price: float = Query(..., gt=0, description="Prețul de piață calculat (EUR)"),
    invoice_percent: float = Query(75.0, gt=0, le=100, description="Procentul de facturare"),
    word_count: int | None = Query(None, ge=0, description="Număr cuvinte (opțional)"),
    page_count: int | None = Query(None, ge=0, description="Număr pagini (opțional)"),
):
    """
    Compară prețul nostru cu prețurile competitorilor.

    Returnează:
    - Prețul nostru (la invoice_percent din piață)
    - Media competitorilor
    - Intervalul de prețuri pe piață
    - Procentul de economisire
    """
    # --- Încarcă date competitori ---
    data = _load_market_data()
    competitors = data.get("competitors", [])

    if not competitors:
        raise HTTPException(
            status_code=404,
            detail="Nu sunt disponibile date despre competitori.",
        )

    # --- Calculează prețul nostru ---
    our_price = round(market_price * (invoice_percent / 100.0), 2)

    # --- Calculează prețurile competitorilor ---
    competitor_prices = []
    competitor_details = []

    for comp in competitors:
        # Calculăm prețul fiecărui competitor pe baza informațiilor disponibile
        comp_price = _estimate_competitor_price(
            comp, market_price, word_count, page_count,
        )
        if comp_price is not None and comp_price > 0:
            competitor_prices.append(comp_price)
            competitor_details.append({
                "name": comp.get("name", "Necunoscut"),
                "estimated_price": comp_price,
                "rate_per_word": comp.get("rate_per_word_eur"),
                "rate_per_page": comp.get("rate_per_page_eur"),
            })

    if not competitor_prices:
        return {
            "our_price": our_price,
            "market_price": market_price,
            "invoice_percent": invoice_percent,
            "competitor_avg": None,
            "competitor_range": None,
            "savings_percent": None,
            "competitors": [],
            "message": "Nu s-au putut estima prețurile competitorilor.",
        }

    competitor_avg = round(sum(competitor_prices) / len(competitor_prices), 2)
    competitor_min = round(min(competitor_prices), 2)
    competitor_max = round(max(competitor_prices), 2)

    # --- Economisire ---
    if competitor_avg > 0:
        savings_percent = round((1.0 - our_price / competitor_avg) * 100.0, 1)
    else:
        savings_percent = 0.0

    # --- Poziția noastră pe piață ---
    cheaper_than = sum(1 for p in competitor_prices if our_price < p)
    position = f"Mai ieftin decât {cheaper_than} din {len(competitor_prices)} competitori"

    return {
        "our_price": our_price,
        "market_price": market_price,
        "invoice_percent": invoice_percent,
        "currency": "EUR",
        "competitor_avg": competitor_avg,
        "competitor_range": {
            "min": competitor_min,
            "max": competitor_max,
        },
        "savings_percent": savings_percent,
        "position": position,
        "competitors": competitor_details,
        "data_source": data.get("source", "necunoscută"),
        "data_last_updated": data.get("last_updated", "necunoscută"),
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_market_data() -> dict[str, Any]:
    """Încarcă datele de piață din fișierul JSON sau folosește valorile implicite."""
    # Verifică și locația din settings (market_rates_file)
    for file_path in [_MARKET_DATA_FILE, settings.market_rates_file]:
        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if "competitors" in data:
                    return data
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning("Eroare la citirea %s: %s", file_path, exc)

    logger.info(
        "Fișierul de date piață nu a fost găsit. Se folosesc date implicite."
    )
    return DEFAULT_COMPETITOR_DATA


def _estimate_competitor_price(
    competitor: dict,
    market_price: float,
    word_count: int | None,
    page_count: int | None,
) -> float | None:
    """
    Estimează prețul unui competitor pe baza tarifelor sale.

    Folosește word_count sau page_count dacă sunt disponibile,
    altfel estimează proporțional cu prețul de piață.
    """
    # Dacă avem word_count și competitor are tarif per cuvânt
    if word_count and word_count > 0:
        rate = competitor.get("rate_per_word_eur")
        if rate:
            price = word_count * rate
            min_order = competitor.get("min_order_eur", 0)
            return round(max(price, min_order), 2)

    # Dacă avem page_count și competitor are tarif per pagină
    if page_count and page_count > 0:
        rate = competitor.get("rate_per_page_eur")
        if rate:
            price = page_count * rate
            min_order = competitor.get("min_order_eur", 0)
            return round(max(price, min_order), 2)

    # Fallback: estimare pe baza prețului de piață
    # (presupunem că competitorul ar factura ~prețul de piață)
    return round(market_price, 2)
