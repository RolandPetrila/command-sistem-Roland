"""
Auto-calibrare coeficienți pe baza fișierelor de referință.

Procesul:
1. Încarcă cele 26 PDF-uri de referință, extrage caracteristici, preia prețurile cunoscute.
2. Folosește scipy.optimize.minimize pentru a găsi parametrii optimi:
   - base_rate_per_page, base_rate_per_word
   - ponderile ansamblului
3. Validare leave-one-out cross-validation.
4. Salvează rezultatele în data/calibration.json.
5. Raportează metrici de acuratețe (MAE, MAPE, erori per fișier).
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from scipy.optimize import minimize

from app.core.analyzer import extract_features, get_feature_vector
from app.core.pricing.base_rate import calculate_base_rate_price
from app.core.pricing.word_rate import calculate_word_rate_price
from app.core.pricing.similarity import (
    calculate_similarity_price,
    load_reference_data,
)

logger = logging.getLogger(__name__)


def load_reference_files(
    reference_dir: str | Path,
) -> list[dict[str, Any]]:
    """
    Încarcă fișierele de referință: extrage caracteristici + preț din nume.

    Returns:
        Listă de dicționare cu filename, price, features, vector.
    """
    return load_reference_data(reference_dir)


def _ensemble_price_from_params(
    features: dict[str, Any],
    reference_data: list[dict[str, Any]],
    params: np.ndarray,
) -> float:
    """
    Calculează prețul ansamblu cu parametrii dați.

    params[0] = base_rate_per_page
    params[1] = base_rate_per_word
    params[2] = weight_base_rate
    params[3] = weight_word_rate
    params[4] = volume_discount_factor
    """
    base_rate_per_page = params[0]
    base_rate_per_word = params[1]
    w_base = params[2]
    w_word = params[3]
    volume_discount_factor = params[4]
    # w_similarity = 1 - w_base - w_word (pentru a suma la 1)
    w_sim = max(0.0, 1.0 - w_base - w_word)

    r_base = calculate_base_rate_price(
        features, base_rate_per_page=base_rate_per_page,
        volume_discount_factor=volume_discount_factor,
    )
    r_word = calculate_word_rate_price(
        features, base_rate_per_word=base_rate_per_word,
    )
    r_sim = calculate_similarity_price(features, reference_data, k=3)

    price = (
        w_base * r_base["price"]
        + w_word * r_word["price"]
        + w_sim * r_sim["price"]
    )
    return price


def _objective_function(
    params: np.ndarray,
    ref_data: list[dict[str, Any]],
) -> float:
    """
    Funcția obiectiv: minimizează suma erorilor pătratice relative (MSPE)
    cu leave-one-out cross-validation.
    """
    total_error = 0.0
    n = len(ref_data)

    for i in range(n):
        # Leave-one-out: excludem fișierul i din referințe
        loo_data = ref_data[:i] + ref_data[i + 1:]
        target = ref_data[i]

        predicted = _ensemble_price_from_params(
            features=target["features"],
            reference_data=loo_data,
            params=params,
        )
        actual = target["price"]

        # Eroare procentuală pătratică
        if actual > 0:
            relative_error = (predicted - actual) / actual
            total_error += relative_error ** 2

    return total_error / n


def run_calibration(
    reference_dir: str | Path,
    output_path: str | Path | None = None,
) -> dict[str, Any]:
    """
    Rulează procesul complet de calibrare.

    Args:
        reference_dir: Directorul cu PDF-urile de referință.
        output_path: Calea unde se salvează calibration.json.

    Returns:
        Dicționar cu parametrii calibrați și metricile de acuratețe.
    """
    logger.info("Începere calibrare din: %s", reference_dir)

    # 1. Încarcă fișierele de referință
    ref_data = load_reference_files(reference_dir)
    if len(ref_data) < 5:
        raise ValueError(
            f"Prea puține fișiere de referință ({len(ref_data)}). "
            f"Sunt necesare minimum 5 pentru calibrare."
        )

    logger.info("Fișiere de referință încărcate: %d", len(ref_data))

    # 2. Parametrii inițiali
    # [base_rate_per_page, base_rate_per_word, w_base, w_word, volume_discount_factor]
    x0 = np.array([25.0, 0.08, 0.30, 0.40, 0.05])

    # Limite — fiecare pondere minim 15% pentru stabilitate
    bounds = [
        (5.0, 100.0),    # base_rate_per_page
        (0.01, 0.30),    # base_rate_per_word
        (0.15, 0.50),    # w_base  (min 15%)
        (0.15, 0.50),    # w_word  (min 15%)
        (0.0, 0.15),     # volume_discount_factor
    ]

    # Constrângere: w_base + w_word <= 0.85 (w_similarity >= 15%)
    constraints = [
        {"type": "ineq", "fun": lambda p: 0.85 - p[2] - p[3]},
    ]

    # 3. Optimizare
    logger.info("Rulare optimizare...")
    result = minimize(
        _objective_function,
        x0,
        args=(ref_data,),
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options={"maxiter": 500, "ftol": 1e-8},
    )

    optimal_params = result.x
    logger.info("Optimizare finalizată. Succes: %s", result.success)

    # 4. Extrage parametrii optimi + clamping forțat pentru siguranță
    MIN_WEIGHT = 0.15
    w_base_raw = float(optimal_params[2])
    w_word_raw = float(optimal_params[3])
    w_sim_raw = max(0.0, 1.0 - w_base_raw - w_word_raw)

    # Hard clamp: fiecare pondere minim 15%
    w_base = max(MIN_WEIGHT, min(0.50, w_base_raw))
    w_word = max(MIN_WEIGHT, min(0.50, w_word_raw))
    w_sim = max(MIN_WEIGHT, 1.0 - w_base - w_word)

    # Re-normalizare dacă suma != 1.0
    total_w = w_base + w_word + w_sim
    w_base /= total_w
    w_word /= total_w
    w_sim /= total_w

    calibrated = {
        "base_rate_per_page": round(float(optimal_params[0]), 4),
        "base_rate_per_word": round(float(optimal_params[1]), 6),
        "weights": {
            "base_rate": round(w_base, 4),
            "word_rate": round(w_word, 4),
            "similarity": round(w_sim, 4),
        },
        "volume_discount_factor": round(float(optimal_params[4]), 6),
        "complexity_multipliers": {"simple": 1.0, "moderate": 1.3, "complex": 1.6},
    }

    # 5. Calculare metrici de acuratețe (leave-one-out)
    errors: list[dict[str, Any]] = []
    absolute_errors: list[float] = []
    percentage_errors: list[float] = []

    for i, item in enumerate(ref_data):
        loo_data = ref_data[:i] + ref_data[i + 1:]
        predicted = _ensemble_price_from_params(
            features=item["features"],
            reference_data=loo_data,
            params=optimal_params,
        )
        actual = item["price"]
        abs_error = abs(predicted - actual)
        pct_error = (abs_error / actual * 100) if actual > 0 else 0

        absolute_errors.append(abs_error)
        percentage_errors.append(pct_error)
        errors.append({
            "filename": item["filename"],
            "actual_price": actual,
            "predicted_price": round(predicted, 2),
            "absolute_error": round(abs_error, 2),
            "percentage_error": round(pct_error, 1),
        })

    mae = float(np.mean(absolute_errors))
    mape = float(np.mean(percentage_errors))
    max_error = float(np.max(percentage_errors))
    median_error = float(np.median(percentage_errors))

    accuracy_metrics = {
        "mae_ron": round(mae, 2),
        "mape_percent": round(mape, 1),
        "max_error_percent": round(max_error, 1),
        "median_error_percent": round(median_error, 1),
        "within_10_percent": sum(1 for e in percentage_errors if e <= 10),
        "within_20_percent": sum(1 for e in percentage_errors if e <= 20),
        "total_files": len(ref_data),
        "per_file_errors": errors,
    }

    calibrated["calibrated_at"] = datetime.now(timezone.utc).isoformat()
    calibrated["accuracy"] = {
        "mae_ron": accuracy_metrics["mae_ron"],
        "mape_percent": accuracy_metrics["mape_percent"],
        "max_error_percent": accuracy_metrics["max_error_percent"],
        "median_error_percent": accuracy_metrics["median_error_percent"],
        "within_10_percent": accuracy_metrics["within_10_percent"],
        "within_20_percent": accuracy_metrics["within_20_percent"],
        "total_files": accuracy_metrics["total_files"],
        "per_file_errors": accuracy_metrics["per_file_errors"],
    }

    # 6. Salvare rezultate
    if output_path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(calibrated, f, indent=2, ensure_ascii=False)
        logger.info("Calibrare salvată în: %s", out)

    return {
        "calibration": calibrated,
        "accuracy": accuracy_metrics,
        "optimization_success": result.success,
        "optimization_message": result.message,
    }
