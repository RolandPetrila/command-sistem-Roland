"""
Metoda 3 de estimare preț: KNN pe baza similarității cu fișierele de referință.

Încarcă fișierele de referință (cu prețuri cunoscute), normalizează
caracteristicile, găsește K=3 vecini apropiați și returnează media ponderată
inversă distanței.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.preprocessing import StandardScaler

from app.core.analyzer import extract_features, get_feature_vector

logger = logging.getLogger(__name__)

# Cache global pentru referințe — se parsează o singură dată
_reference_cache: dict[str, list[dict[str, Any]]] = {}


def load_reference_data(reference_dir: str | Path) -> list[dict[str, Any]]:
    """
    Încarcă fișierele de referință și extrage caracteristicile + prețurile.
    Rezultatele sunt cache-uite — PDF-urile se parsează o singură dată.

    Fiecare fișier are numele = prețul în RON (ex: 478.pdf → 478 RON).

    Returns:
        Listă de dicționare: {"filename", "price", "features", "vector"}
    """
    ref_dir = Path(reference_dir)
    cache_key = str(ref_dir)

    # Returnează din cache dacă există
    if cache_key in _reference_cache:
        return _reference_cache[cache_key]

    # Încearcă să încarce din fișier JSON cache (pre-calculat)
    cache_file = ref_dir / "_reference_cache.json"
    if cache_file.exists():
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cached = json.load(f)
            if len(cached) > 0:
                logger.info(
                    "Încărcate %d referințe din cache: %s", len(cached), cache_file
                )
                _reference_cache[cache_key] = cached
                return cached
        except Exception as exc:
            logger.warning("Cache corupt, re-parsare: %s", exc)

    if not ref_dir.exists():
        logger.warning("Directorul de referință nu există: %s", ref_dir)
        return []

    reference_data: list[dict[str, Any]] = []

    for pdf_path in sorted(ref_dir.glob("*.pdf")):
        # Extrage prețul din numele fișierului
        try:
            price = float(pdf_path.stem)
        except ValueError:
            logger.warning(
                "Nu pot extrage prețul din numele fișierului: %s", pdf_path.name
            )
            continue

        # Extrage caracteristici
        try:
            features = extract_features(pdf_path)
            vector = get_feature_vector(features)
            reference_data.append({
                "filename": pdf_path.name,
                "price": price,
                "features": features,
                "vector": vector,
            })
            logger.info("Parsed: %s (%.0f RON)", pdf_path.name, price)
        except Exception as exc:
            logger.warning(
                "Eroare la extragerea caracteristicilor din %s: %s",
                pdf_path.name,
                exc,
            )
            continue

    logger.info(
        "Încărcate %d fișiere de referință din %s", len(reference_data), ref_dir
    )

    # Salvează cache pe disc
    if reference_data:
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(reference_data, f, ensure_ascii=False, indent=2)
            logger.info("Cache salvat: %s", cache_file)
        except Exception as exc:
            logger.warning("Nu pot salva cache: %s", exc)

    _reference_cache[cache_key] = reference_data
    return reference_data


def calculate_similarity_price(
    features: dict[str, Any],
    reference_data: list[dict[str, Any]],
    k: int = 3,
) -> dict[str, Any]:
    """
    Calculează prețul prin KNN pe baza similarității cu fișierele de referință.

    Args:
        features: Caracteristicile documentului de analizat.
        reference_data: Lista de referințe (din load_reference_data).
        k: Numărul de vecini (default: 3).

    Returns:
        Dicționar cu prețul estimat și detaliile calculului.
    """
    if not reference_data:
        return {
            "method": "similarity",
            "method_name": "Similaritate KNN",
            "price": 0.0,
            "details": {
                "error": "Nu există fișiere de referință încărcate.",
                "neighbors": [],
            },
        }

    target_vector = np.array(get_feature_vector(features)).reshape(1, -1)

    # Pregătire matrice referințe
    ref_vectors = np.array([r["vector"] for r in reference_data])
    ref_prices = np.array([r["price"] for r in reference_data])
    ref_names = [r["filename"] for r in reference_data]

    # Normalizare (StandardScaler pe referințe, apoi transform pe target)
    scaler = StandardScaler()
    ref_normalized = scaler.fit_transform(ref_vectors)
    target_normalized = scaler.transform(target_vector)

    # Calcul distanțe euclidiene
    distances = np.linalg.norm(ref_normalized - target_normalized, axis=1)

    # Selectare K cei mai apropiați vecini
    k_actual = min(k, len(reference_data))
    nearest_indices = np.argsort(distances)[:k_actual]

    # Ponderare inversă distanței
    nearest_distances = distances[nearest_indices]
    nearest_prices = ref_prices[nearest_indices]
    nearest_names = [ref_names[i] for i in nearest_indices]

    # Evitare împărțire la zero
    epsilon = 1e-10
    weights = 1.0 / (nearest_distances + epsilon)
    weights_normalized = weights / weights.sum()

    # Preț ponderat
    price = float(np.dot(weights_normalized, nearest_prices))
    price = round(price, 2)

    # Detalii vecini
    neighbors_info = []
    for i in range(k_actual):
        idx = nearest_indices[i]
        neighbors_info.append({
            "filename": nearest_names[i],
            "price": float(nearest_prices[i]),
            "distance": round(float(nearest_distances[i]), 4),
            "weight": round(float(weights_normalized[i]), 4),
        })

    return {
        "method": "similarity",
        "method_name": "Similaritate KNN",
        "price": price,
        "details": {
            "k": k_actual,
            "neighbors": neighbors_info,
            "total_references": len(reference_data),
        },
    }
