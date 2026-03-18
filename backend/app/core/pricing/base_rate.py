"""
Metoda 1 de estimare preț: Tarif per pagină cu discount logaritmic de volum.

Formula: preț = pagini × tarif_bază × multiplicator_complexitate × (1 - discount_volum)

Discountul de volum folosește o funcție logaritmică pentru a oferi reduceri
progresive la documente mari, fără a coborî sub un prag minim.
"""

from __future__ import annotations

import math
from typing import Any


def calculate_base_rate_price(
    features: dict[str, Any],
    base_rate_per_page: float = 25.0,
    volume_discount_factor: float = 0.05,
    complexity_multipliers: dict[str, float] | None = None,
) -> dict[str, Any]:
    """
    Calculează prețul bazat pe tarif per pagină.

    Args:
        features: Dicționar cu caracteristici document (din analyzer).
        base_rate_per_page: Tarif de bază per pagină (RON). Default: 25.
        volume_discount_factor: Factor pentru discountul logaritmic. Default: 0.05.
        complexity_multipliers: Multiplicatori per nivel complexitate.

    Returns:
        Dicționar cu prețul estimat și detaliile calculului.
    """
    if complexity_multipliers is None:
        complexity_multipliers = {
            "simple": 1.0,
            "moderate": 1.3,
            "complex": 1.6,
        }

    page_count = features.get("page_count", 1)
    layout_complexity = features.get("layout_complexity", 1)
    table_count = features.get("table_count", 0)
    image_count = features.get("image_count", 0)
    has_complex_tables = features.get("has_complex_tables", False)
    has_diagrams = features.get("has_diagrams", False)

    # --- Multiplicator complexitate ---
    complexity_mult = _compute_complexity_multiplier(
        layout_complexity=layout_complexity,
        table_count=table_count,
        image_count=image_count,
        has_complex_tables=has_complex_tables,
        has_diagrams=has_diagrams,
        page_count=page_count,
        multipliers=complexity_multipliers,
    )

    # --- Discount de volum (logaritmic) ---
    # Discount crește logaritmic cu nr de pagini, plafonat la 30%
    if page_count > 1:
        raw_discount = volume_discount_factor * math.log(page_count)
        volume_discount = min(raw_discount, 0.30)
    else:
        volume_discount = 0.0

    # --- Preț final ---
    price = page_count * base_rate_per_page * complexity_mult * (1 - volume_discount)
    price = round(price, 2)

    return {
        "method": "base_rate",
        "method_name": "Tarif per pagină",
        "price": price,
        "details": {
            "page_count": page_count,
            "base_rate_per_page": base_rate_per_page,
            "complexity_multiplier": round(complexity_mult, 3),
            "complexity_level": _get_complexity_label(complexity_mult, complexity_multipliers),
            "volume_discount": round(volume_discount, 4),
            "volume_discount_percent": round(volume_discount * 100, 1),
        },
    }


def _compute_complexity_multiplier(
    layout_complexity: int,
    table_count: int,
    image_count: int,
    has_complex_tables: bool,
    has_diagrams: bool,
    page_count: int,
    multipliers: dict[str, float],
) -> float:
    """
    Calculează multiplicatorul de complexitate pe baza caracteristicilor.

    Scor complexitate:
    - layout_complexity 1-2: simplu
    - layout_complexity 3: moderat
    - layout_complexity 4-5: complex
    - Bonus pentru tabele/imagini multe relativ la nr pagini
    """
    # Scor de bază din layout_complexity
    if layout_complexity <= 2:
        base_mult = multipliers.get("simple", 1.0)
    elif layout_complexity == 3:
        base_mult = multipliers.get("moderate", 1.3)
    else:
        base_mult = multipliers.get("complex", 1.6)

    # Ajustări adiționale (mici) pentru conținut special
    adjustment = 0.0

    # Tabele complexe adaugă dificultate
    if has_complex_tables:
        adjustment += 0.1

    # Multe imagini/diagrame relativ la pagini
    if page_count > 0 and image_count / page_count > 1.0:
        adjustment += 0.1

    # Diagrame tehnice
    if has_diagrams:
        adjustment += 0.05

    # Multe tabele relativ la pagini
    if page_count > 0 and table_count / page_count > 0.5:
        adjustment += 0.05

    return base_mult + adjustment


def _get_complexity_label(
    mult: float, multipliers: dict[str, float]
) -> str:
    """Returnează eticheta de complexitate cea mai apropiată."""
    simple = multipliers.get("simple", 1.0)
    moderate = multipliers.get("moderate", 1.3)
    complex_ = multipliers.get("complex", 1.6)

    if mult <= (simple + moderate) / 2:
        return "simplu"
    elif mult <= (moderate + complex_) / 2:
        return "moderat"
    else:
        return "complex"
