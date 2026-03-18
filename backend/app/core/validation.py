"""
Validare pe 3 niveluri a prețului estimat.

1. Statistică — prețul cade în intervalul rezonabil (min/max referințe ± 2 std dev)
2. Similaritate — comparare cu cele mai similare fișiere de referință
3. Consistență — cele 3 metode din ansamblu sunt de acord (±30%)

Returnează un scor de încredere (0-100%) și lista de avertismente.
"""

from __future__ import annotations

from typing import Any

import numpy as np


def validate_price(
    ensemble_result: dict[str, Any],
    reference_data: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Validare completă pe 3 niveluri a prețului estimat.

    Args:
        ensemble_result: Rezultatul din calculate_ensemble_price().
        reference_data: Fișierele de referință (cu prețuri cunoscute).

    Returns:
        Dicționar cu:
            confidence: scor 0-100
            warnings: listă de avertismente
            validation_details: detalii per nivel
    """
    warnings: list[str] = []
    confidence_penalties: list[float] = []
    details: dict[str, Any] = {}

    market_price = ensemble_result["market_price"]
    method_prices = ensemble_result["method_prices"]

    # ==================================================================
    # NIVEL 1: Validare statistică
    # ==================================================================
    stat_result = _validate_statistical(market_price, reference_data)
    details["statistical"] = stat_result
    if not stat_result["passed"]:
        warnings.extend(stat_result["warnings"])
        confidence_penalties.append(stat_result["penalty"])

    # ==================================================================
    # NIVEL 2: Validare similaritate
    # ==================================================================
    sim_result = _validate_similarity(ensemble_result, reference_data)
    details["similarity"] = sim_result
    if not sim_result["passed"]:
        warnings.extend(sim_result["warnings"])
        confidence_penalties.append(sim_result["penalty"])

    # ==================================================================
    # NIVEL 3: Validare consistență
    # ==================================================================
    cons_result = _validate_consistency(method_prices, market_price)
    details["consistency"] = cons_result
    if not cons_result["passed"]:
        warnings.extend(cons_result["warnings"])
        confidence_penalties.append(cons_result["penalty"])

    # ==================================================================
    # Scor final de încredere
    # ==================================================================
    base_confidence = 100.0
    total_penalty = sum(confidence_penalties)
    confidence = max(0.0, min(100.0, base_confidence - total_penalty))

    return {
        "confidence": round(confidence, 1),
        "warnings": warnings,
        "validation_details": details,
        "passed_all": len(warnings) == 0,
    }


def _validate_statistical(
    price: float,
    reference_data: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Nivel 1: Verifică dacă prețul cade în intervalul rezonabil.

    Intervalul = [min_ref - 2*std, max_ref + 2*std].
    """
    if not reference_data:
        return {
            "passed": True,
            "penalty": 0.0,
            "warnings": [],
            "range_min": 0,
            "range_max": 0,
            "note": "Nu există referințe pentru validare statistică.",
        }

    ref_prices = np.array([r["price"] for r in reference_data])
    mean_price = float(np.mean(ref_prices))
    std_price = float(np.std(ref_prices))
    min_price = float(np.min(ref_prices))
    max_price = float(np.max(ref_prices))

    # Interval rezonabil
    range_min = max(0, min_price - 2 * std_price)
    range_max = max_price + 2 * std_price

    warnings: list[str] = []
    penalty = 0.0

    if price < range_min:
        penalty = 25.0
        warnings.append(
            f"Prețul estimat ({price:.0f} RON) este sub intervalul "
            f"statistic minim ({range_min:.0f} RON)."
        )
    elif price > range_max:
        penalty = 25.0
        warnings.append(
            f"Prețul estimat ({price:.0f} RON) depășește intervalul "
            f"statistic maxim ({range_max:.0f} RON)."
        )
    elif price < min_price * 0.5 or price > max_price * 1.5:
        penalty = 15.0
        warnings.append(
            f"Prețul estimat ({price:.0f} RON) este în afara intervalului "
            f"tipic al referințelor ({min_price:.0f} - {max_price:.0f} RON)."
        )

    return {
        "passed": len(warnings) == 0,
        "penalty": penalty,
        "warnings": warnings,
        "range_min": round(range_min, 2),
        "range_max": round(range_max, 2),
        "mean_price": round(mean_price, 2),
        "std_price": round(std_price, 2),
        "ref_min": round(min_price, 2),
        "ref_max": round(max_price, 2),
    }


def _validate_similarity(
    ensemble_result: dict[str, Any],
    reference_data: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Nivel 2: Compară prețul cu cele mai similare fișiere de referință.

    Dacă prețul diferă cu > 50% față de media vecinilor KNN, penalizează.
    """
    # Extragem informațiile KNN din metoda similarity
    similarity_method = None
    for m in ensemble_result.get("methods", []):
        if m.get("method") == "similarity":
            similarity_method = m
            break

    if not similarity_method or not similarity_method["details"].get("neighbors"):
        return {
            "passed": True,
            "penalty": 0.0,
            "warnings": [],
            "note": "Nu sunt disponibile date de similaritate.",
        }

    neighbors = similarity_method["details"]["neighbors"]
    neighbor_prices = [n["price"] for n in neighbors]
    avg_neighbor_price = (
        sum(neighbor_prices) / len(neighbor_prices) if neighbor_prices else 0
    )

    market_price = ensemble_result["market_price"]
    warnings: list[str] = []
    penalty = 0.0

    if avg_neighbor_price > 0:
        deviation = abs(market_price - avg_neighbor_price) / avg_neighbor_price
        if deviation > 0.50:
            penalty = 20.0
            warnings.append(
                f"Prețul estimat ({market_price:.0f} RON) diferă cu "
                f"{deviation * 100:.0f}% față de media vecinilor KNN "
                f"({avg_neighbor_price:.0f} RON)."
            )
        elif deviation > 0.30:
            penalty = 10.0
            warnings.append(
                f"Prețul estimat ({market_price:.0f} RON) diferă cu "
                f"{deviation * 100:.0f}% față de media vecinilor KNN "
                f"({avg_neighbor_price:.0f} RON). Verificare recomandată."
            )

    return {
        "passed": len(warnings) == 0,
        "penalty": penalty,
        "warnings": warnings,
        "avg_neighbor_price": round(avg_neighbor_price, 2),
        "neighbors": neighbors,
    }


def _validate_consistency(
    method_prices: dict[str, float],
    final_price: float,
) -> dict[str, Any]:
    """
    Nivel 3: Verifică dacă cele 3 metode sunt de acord (±30%).

    Dacă oricare metodă diferă cu > 30% față de media celorlalte, penalizează.
    """
    prices = {k: v for k, v in method_prices.items() if v > 0}
    warnings: list[str] = []
    penalty = 0.0

    if len(prices) < 2:
        return {
            "passed": True,
            "penalty": 0.0,
            "warnings": [],
            "note": "Prea puține metode active pentru validare consistență.",
        }

    price_values = list(prices.values())
    mean_price = sum(price_values) / len(price_values)

    method_names = {
        "base_rate": "Tarif per pagină",
        "word_rate": "Tarif per cuvânt",
        "similarity": "Similaritate KNN",
    }

    deviations: dict[str, float] = {}
    for method, price in prices.items():
        if mean_price > 0:
            dev = abs(price - mean_price) / mean_price
            deviations[method] = dev
            if dev > 0.50:
                penalty = max(penalty, 20.0)
                name = method_names.get(method, method)
                warnings.append(
                    f"Metoda '{name}' estimează {price:.0f} RON, "
                    f"diferență de {dev * 100:.0f}% față de media "
                    f"({mean_price:.0f} RON). Acord scăzut între metode."
                )
            elif dev > 0.30:
                penalty = max(penalty, 10.0)
                name = method_names.get(method, method)
                warnings.append(
                    f"Metoda '{name}' estimează {price:.0f} RON, "
                    f"diferență de {dev * 100:.0f}% față de media "
                    f"({mean_price:.0f} RON). Verificare recomandată."
                )

    return {
        "passed": len(warnings) == 0,
        "penalty": penalty,
        "warnings": warnings,
        "method_deviations": {
            k: round(v * 100, 1) for k, v in deviations.items()
        },
        "mean_of_methods": round(mean_price, 2),
    }
