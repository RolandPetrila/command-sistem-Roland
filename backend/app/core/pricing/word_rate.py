"""
Metoda 2 de estimare preț: Tarif per cuvânt cu factor de complexitate.

Formula: preț = cuvinte × tarif_per_cuvânt × factor_complexitate

Factorul de complexitate reflectă conținutul tehnic (tabele, diagrame, imagini)
care necesită efort suplimentar de traducere.
"""

from __future__ import annotations

from typing import Any


def calculate_word_rate_price(
    features: dict[str, Any],
    base_rate_per_word: float = 0.08,
) -> dict[str, Any]:
    """
    Calculează prețul bazat pe tarif per cuvânt.

    Args:
        features: Dicționar cu caracteristici document (din analyzer).
        base_rate_per_word: Tarif de bază per cuvânt (RON). Default: 0.08.

    Returns:
        Dicționar cu prețul estimat și detaliile calculului.
    """
    word_count = features.get("word_count", 0)
    page_count = max(features.get("page_count", 1), 1)
    table_count = features.get("table_count", 0)
    image_count = features.get("image_count", 0)
    has_complex_tables = features.get("has_complex_tables", False)
    has_diagrams = features.get("has_diagrams", False)
    chart_count = features.get("chart_count", 0)
    is_scanned = features.get("is_scanned", False)
    layout_complexity = features.get("layout_complexity", 1)

    # --- Factor complexitate ---
    complexity_factor = _compute_complexity_factor(
        page_count=page_count,
        table_count=table_count,
        image_count=image_count,
        has_complex_tables=has_complex_tables,
        has_diagrams=has_diagrams,
        chart_count=chart_count,
        is_scanned=is_scanned,
        layout_complexity=layout_complexity,
    )

    # --- Preț final ---
    price = word_count * base_rate_per_word * complexity_factor
    price = round(price, 2)

    return {
        "method": "word_rate",
        "method_name": "Tarif per cuvânt",
        "price": price,
        "details": {
            "word_count": word_count,
            "base_rate_per_word": base_rate_per_word,
            "complexity_factor": round(complexity_factor, 3),
            "effective_rate_per_word": round(
                base_rate_per_word * complexity_factor, 4
            ),
        },
    }


def _compute_complexity_factor(
    page_count: int,
    table_count: int,
    image_count: int,
    has_complex_tables: bool,
    has_diagrams: bool,
    chart_count: int,
    is_scanned: bool,
    layout_complexity: int,
) -> float:
    """
    Calculează factorul de complexitate pentru tariful per cuvânt.

    Factorul de bază este 1.0 (text simplu).
    Se adaugă incremente pentru fiecare element de complexitate.
    Interval final: 1.0 - 2.0.
    """
    factor = 1.0

    # Tabele (text din tabele e mai dificil de tradus — formatare)
    tables_per_page = table_count / page_count if page_count > 0 else 0
    if tables_per_page > 0.3:
        factor += 0.10
    if has_complex_tables:
        factor += 0.10

    # Imagini cu text (necesită efort suplimentar de extragere/formatare)
    images_per_page = image_count / page_count if page_count > 0 else 0
    if images_per_page > 0.5:
        factor += 0.10

    # Diagrame și grafice tehnice
    if has_diagrams:
        factor += 0.10
    if chart_count > 3:
        factor += 0.05

    # Document scanat (OCR introduce erori, necesită verificare manuală)
    if is_scanned:
        factor += 0.20

    # Layout complex (coloane, orientare mixtă)
    if layout_complexity >= 4:
        factor += 0.15
    elif layout_complexity >= 3:
        factor += 0.10

    # Plafonare la 2.0
    return min(factor, 2.0)
