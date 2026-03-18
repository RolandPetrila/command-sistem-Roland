"""
Combinare ansamblu (ensemble) a celor 3 metode de estimare preț.

Prețul final = (w1 × tarif_per_pagină + w2 × tarif_per_cuvânt + w3 × similaritate_KNN) × dtp_factor

Ponderile sunt configurabile și se pot calibra automat pe baza fișierelor de referință.
Factorul DTP se aplică automat pe baza raportului imagini/tabele per pagină.
"""

from __future__ import annotations

from typing import Any

from app.config import settings
from app.core.pricing.base_rate import calculate_base_rate_price
from app.core.pricing.word_rate import calculate_word_rate_price
from app.core.pricing.similarity import calculate_similarity_price


def _compute_dtp_factor(features: dict[str, Any]) -> dict[str, Any]:
    """
    Calculează factorul DTP (Desktop Publishing) pe baza complexității layout-ului.

    Analizează raportul imagini/tabele per pagină și alte indicatoare de layout
    pentru a determina automat dacă documentul necesită efort suplimentar de
    reconstituire layout (DTP).

    Niveluri DTP:
    - none:   Document text simplu, fără layout complex → factor 1.00
    - light:  Câteva imagini/tabele simple → factor 1.10 (+10%)
    - medium: Layout moderat complex (diagrame, tabele multiple) → factor 1.20 (+20%)
    - heavy:  Layout foarte complex (multe imagini/diagrame tehnice) → factor 1.30 (+30%)

    Returns:
        Dicționar cu: factor, level, label, reason
    """
    page_count = max(features.get("page_count", 1), 1)
    image_count = features.get("image_count", 0)
    table_count = features.get("table_count", 0)
    chart_count = features.get("chart_count", 0)
    has_complex_tables = features.get("has_complex_tables", False)
    has_diagrams = features.get("has_diagrams", False)
    layout_complexity = features.get("layout_complexity", 1)
    text_density = features.get("text_density", 1.0)

    images_per_page = image_count / page_count
    tables_per_page = table_count / page_count
    charts_per_page = chart_count / page_count

    reasons = []

    # --- HEAVY DTP (1.30) ---
    if (images_per_page > 5.0
        or (tables_per_page > 1.0 and has_complex_tables)
        or (has_diagrams and layout_complexity >= 4 and images_per_page > 2.0)):
        factor = 1.30
        level = "heavy"
        label = "DTP Intensiv"
        if images_per_page > 5.0:
            reasons.append(f"{images_per_page:.1f} imagini/pagină")
        if tables_per_page > 1.0:
            reasons.append(f"{tables_per_page:.1f} tabele/pagină, tabele complexe")
        if has_diagrams and layout_complexity >= 4:
            reasons.append("diagrame tehnice + layout complex")

    # --- MEDIUM DTP (1.20) ---
    elif (images_per_page > 2.0
          or (tables_per_page > 0.5 and (has_complex_tables or chart_count > 0))
          or layout_complexity >= 4
          or (has_diagrams and images_per_page > 1.0)):
        factor = 1.20
        level = "medium"
        label = "DTP Moderat"
        if images_per_page > 2.0:
            reasons.append(f"{images_per_page:.1f} imagini/pagină")
        if tables_per_page > 0.5:
            reasons.append(f"{tables_per_page:.1f} tabele/pagină")
        if layout_complexity >= 4:
            reasons.append(f"complexitate layout {layout_complexity}/5")
        if has_diagrams:
            reasons.append("diagrame detectate")

    # --- LIGHT DTP (1.10) ---
    elif (images_per_page > 0.5
          or tables_per_page > 0.2
          or chart_count > 0
          or layout_complexity >= 3):
        factor = 1.10
        level = "light"
        label = "DTP Ușor"
        if images_per_page > 0.5:
            reasons.append(f"{images_per_page:.1f} imagini/pagină")
        if tables_per_page > 0.2:
            reasons.append(f"{tables_per_page:.1f} tabele/pagină")
        if layout_complexity >= 3:
            reasons.append(f"complexitate layout {layout_complexity}/5")

    # --- NO DTP (1.00) ---
    else:
        factor = 1.00
        level = "none"
        label = "Fără DTP"
        reasons.append("document text simplu")

    # Bonus suplimentar: text_density scăzută = mai mult layout, mai puțin text
    if text_density < 0.4 and level != "none":
        factor = min(factor + 0.05, 1.35)
        reasons.append(f"densitate text scăzută ({text_density})")

    return {
        "factor": round(factor, 2),
        "level": level,
        "label": label,
        "reason": "; ".join(reasons),
        "images_per_page": round(images_per_page, 1),
        "tables_per_page": round(tables_per_page, 1),
    }


def calculate_ensemble_price(
    features: dict[str, Any],
    reference_data: list[dict[str, Any]],
    weights: dict[str, float] | None = None,
    calibration: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Calculează prețul final prin combinarea celor 3 metode + factor DTP automat.

    Args:
        features: Caracteristicile documentului.
        reference_data: Fișiere de referință pentru metoda KNN.
        weights: Ponderi per metodă. Default: {"base_rate": 0.3, "word_rate": 0.4, "similarity": 0.3}.
        calibration: Parametri calibrați (rate, multiplieri). Dacă None, se folosesc valorile implicite.

    Returns:
        Dicționar cu prețul final, prețul fiecărei metode, DTP info, și detalii.
    """
    if weights is None:
        weights = dict(settings.default_weights)

    # Extrage parametri din calibrare (dacă există)
    base_rate_per_page = 25.0
    base_rate_per_word = 0.08
    volume_discount_factor = 0.05
    complexity_multipliers = None
    knn_k = 3

    if calibration:
        base_rate_per_page = calibration.get("base_rate_per_page", base_rate_per_page)
        base_rate_per_word = calibration.get("base_rate_per_word", base_rate_per_word)
        volume_discount_factor = calibration.get(
            "volume_discount_factor", volume_discount_factor
        )
        complexity_multipliers = calibration.get("complexity_multipliers", None)
        knn_k = calibration.get("knn_k", knn_k)

    # --- Metoda 1: Tarif per pagină ---
    result_base = calculate_base_rate_price(
        features=features,
        base_rate_per_page=base_rate_per_page,
        volume_discount_factor=volume_discount_factor,
        complexity_multipliers=complexity_multipliers,
    )

    # --- Metoda 2: Tarif per cuvânt ---
    result_word = calculate_word_rate_price(
        features=features,
        base_rate_per_word=base_rate_per_word,
    )

    # --- Metoda 3: Similaritate KNN ---
    result_similarity = calculate_similarity_price(
        features=features,
        reference_data=reference_data,
        k=knn_k,
    )

    # --- Combinare ansamblu ---
    price_base = result_base["price"]
    price_word = result_word["price"]
    price_similarity = result_similarity["price"]

    w1 = weights.get("base_rate", 0.3)
    w2 = weights.get("word_rate", 0.4)
    w3 = weights.get("similarity", 0.3)

    # Normalizare ponderi (în caz că nu sunt exact 1.0)
    total_w = w1 + w2 + w3
    if total_w > 0:
        w1 /= total_w
        w2 /= total_w
        w3 /= total_w

    # Dacă similaritatea nu a returnat preț valid, redistribuim ponderile
    if price_similarity == 0.0 and result_similarity["details"].get("error"):
        # Redistribuim ponderea similarității între celelalte 2 metode
        w_sum = w1 + w2
        if w_sum > 0:
            w1 = w1 / w_sum
            w2 = w2 / w_sum
        else:
            w1 = 0.5
            w2 = 0.5
        w3 = 0.0

    base_price = w1 * price_base + w2 * price_word + w3 * price_similarity

    # Fallback: dacă toate metodele au returnat 0, folosim media din datele de referință
    if base_price == 0.0 and reference_data:
        ref_prices = [r.get("price", 0) for r in reference_data if r.get("price", 0) > 0]
        if ref_prices:
            base_price = sum(ref_prices) / len(ref_prices)

    # --- Factor DTP (automat) ---
    dtp_info = _compute_dtp_factor(features)
    dtp_factor = dtp_info["factor"]

    # Prețul final include factorul DTP
    final_price = round(base_price * dtp_factor, 2)
    base_price = round(base_price, 2)

    return {
        "market_price": final_price,
        "base_price_before_dtp": base_price,
        "dtp": dtp_info,
        "weights_used": {
            "base_rate": round(w1, 3),
            "word_rate": round(w2, 3),
            "similarity": round(w3, 3),
        },
        "methods": [result_base, result_word, result_similarity],
        "method_prices": {
            "base_rate": price_base,
            "word_rate": price_word,
            "similarity": price_similarity,
        },
    }
