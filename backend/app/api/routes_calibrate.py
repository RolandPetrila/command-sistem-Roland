"""
Rute pentru calibrare și recalibrare.

POST /api/calibrate           — declanșează recalibrarea (cu backup + comparație + protecții)
POST /api/calibrate/revert    — restaurează calibrarea anterioară din backup
GET  /api/calibration-status  — returnează datele curente de calibrare + metrici
"""

import json
import logging
import shutil
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel

from app.config import settings
from app.core.activity_log import log_activity

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["calibration"])

BACKUP_FILE = settings.calibration_file.parent / "calibration_backup.json"

# Ponderile și parametrii impliciți (fără calibrare)
DEFAULTS = {
    "base_rate_per_page": 25.0,
    "base_rate_per_word": 0.08,
    "weights": {"base_rate": 0.3, "word_rate": 0.4, "similarity": 0.3},
    "volume_discount_factor": 0.05,
}

# Limite de siguranță
SAFETY_MAX_MAPE = 30.0        # MAPE maxim acceptabil (%)
SAFETY_MIN_WEIGHT = 0.10      # Pondere minimă per metodă
SAFETY_MAX_FILE_ERROR = 50.0  # Eroare maximă per fișier (%)


@router.post("/calibrate")
async def trigger_calibration():
    """
    Declanșează procesul de recalibrare cu protecții.

    1. Backup calibrare curentă
    2. Calculează metrici cu setările VECHI (before)
    3. Rulează optimizarea
    4. Calculează metrici cu setările NOI (after)
    5. Verifică limite de siguranță
    6. Salvează (sau respinge) + returnează comparație
    """
    reference_dir = settings.reference_dir
    output_path = settings.calibration_file

    if not reference_dir.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                f"Directorul de referință nu a fost găsit: {reference_dir}. "
                "Asigurați-vă că fișierele de referință sunt disponibile."
            ),
        )

    # --- 1. Backup ---
    old_calibration = _load_current_calibration()
    if output_path.exists():
        shutil.copy2(output_path, BACKUP_FILE)
        logger.info("Backup calibrare salvat: %s", BACKUP_FILE)

    try:
        from app.core.calibration import run_calibration

        # Rulează calibrarea FĂRĂ salvare — safety check decide dacă se salvează
        result = run_calibration(
            reference_dir=str(reference_dir),
            output_path=None,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except ImportError as exc:
        logger.warning("Calibrare avansată indisponibilă: %s", exc)
        result = await _simple_calibration(reference_dir, output_path)
    except Exception as exc:
        logger.exception("Eroare la calibrare")
        raise HTTPException(status_code=500, detail=f"Eroare internă la calibrare: {exc}")

    # --- Extrage metrici noi ---
    new_cal = result.get("calibration", {})
    new_accuracy = result.get("accuracy", {})
    new_mape = new_accuracy.get("mape_percent", 100)
    new_weights = new_cal.get("weights", {})

    # --- Metrici vechi ---
    old_mape = None
    old_weights = DEFAULTS["weights"]
    if old_calibration:
        old_acc = old_calibration.get("accuracy", {})
        old_mape = old_acc.get("mape_percent")
        old_weights = old_calibration.get("weights", DEFAULTS["weights"])

    # --- Verificări siguranță ---
    warnings = []
    is_safe = True

    # Check 1: MAPE prea mare
    if new_mape > SAFETY_MAX_MAPE:
        warnings.append(
            f"Eroarea medie (MAPE) este {new_mape:.1f}% — peste limita de {SAFETY_MAX_MAPE}%"
        )

    # Check 2: Ponderi prea mici
    for method, weight in new_weights.items():
        if weight < SAFETY_MIN_WEIGHT:
            warnings.append(
                f"Ponderea '{method}' este doar {weight:.1%} — sub minimul de {SAFETY_MIN_WEIGHT:.0%}"
            )
            is_safe = False

    # Check 3: MAPE mai rău decât înainte
    if old_mape is not None and new_mape > old_mape + 5.0:
        warnings.append(
            f"Acuratețea s-a deteriorat: {old_mape:.1f}% → {new_mape:.1f}% (+{new_mape - old_mape:.1f}%)"
        )

    # Check 4: Fișiere cu eroare > 50%
    per_file = new_accuracy.get("per_file_errors", [])
    bad_files = [f for f in per_file if f.get("percentage_error", 0) > SAFETY_MAX_FILE_ERROR]
    if bad_files:
        names = ", ".join(f["filename"] for f in bad_files[:3])
        warnings.append(
            f"{len(bad_files)} fișiere cu eroare >{SAFETY_MAX_FILE_ERROR}%: {names}"
        )

    # Dacă e sigur → salvează calibrarea nouă
    if is_safe:
        calibration_to_save = result.get("calibration", {})
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(calibration_to_save, f, indent=2, ensure_ascii=False)
        logger.info("Calibrare nouă salvată cu succes.")
    else:
        # NU salvăm — restaurăm backup-ul sau defaults
        if BACKUP_FILE.exists():
            shutil.copy2(BACKUP_FILE, output_path)
            warnings.append("Calibrare RESPINSĂ automat — s-a restaurat backup-ul anterior.")
        else:
            # Scrie {} pentru a reveni la defaults
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("{}")
            warnings.append("Calibrare RESPINSĂ automat — se folosesc valorile implicite.")

    # --- Construiește comparație ---
    comparison = {
        "before": {
            "weights": old_weights,
            "mape": old_mape,
            "source": "calibrare anterioară" if old_calibration else "valori implicite",
        },
        "after": {
            "weights": new_weights,
            "mape": new_mape,
            "within_10": new_accuracy.get("within_10_percent", 0),
            "within_20": new_accuracy.get("within_20_percent", 0),
            "total_files": new_accuracy.get("total_files", 0),
        },
        "applied": is_safe,
        "warnings": warnings,
    }

    await log_activity(
        action="calibrate",
        status="success" if is_safe else "rejected",
        summary=f"MAPE: {new_mape}% | Ponderi: {new_weights} | {'Aplicat' if is_safe else 'RESPINS'}",
        details={
            "applied": is_safe,
            "mape": new_mape,
            "weights": new_weights,
            "warnings": warnings,
            "within_10": new_accuracy.get("within_10_percent", 0),
            "within_20": new_accuracy.get("within_20_percent", 0),
            "total_files": new_accuracy.get("total_files", 0),
        },
    )

    return {
        "status": "success" if is_safe else "rejected",
        "message": (
            "Calibrare aplicată cu succes." if is_safe
            else "Calibrare respinsă — nu a trecut verificările de siguranță."
        ),
        "result": result,
        "comparison": comparison,
        "has_backup": BACKUP_FILE.exists(),
    }


@router.post("/calibrate/revert")
async def revert_calibration():
    """Restaurează calibrarea anterioară din backup."""
    cal_file = settings.calibration_file

    if not BACKUP_FILE.exists():
        # Nu există backup → ștergem calibrarea curentă (revert la defaults)
        if cal_file.exists():
            cal_file.unlink()
        return {
            "status": "reverted_to_defaults",
            "message": "Nu există backup. Calibrarea a fost ștearsă — se folosesc valorile implicite.",
        }

    shutil.copy2(BACKUP_FILE, cal_file)
    BACKUP_FILE.unlink()
    logger.info("Calibrare restaurată din backup.")

    await log_activity(action="calibrate_revert", summary="Calibrare restaurată din backup")

    return {
        "status": "reverted",
        "message": "Calibrarea anterioară a fost restaurată cu succes.",
    }


@router.post("/calibrate/reset")
async def reset_calibration():
    """Resetează complet calibrarea la valorile implicite."""
    cal_file = settings.calibration_file

    # Backup curent înainte de ștergere
    if cal_file.exists():
        shutil.copy2(cal_file, BACKUP_FILE)
        cal_file.unlink()

    await log_activity(action="calibrate_reset", summary="Calibrare resetată la valori implicite")

    return {
        "status": "reset",
        "message": "Calibrarea a fost resetată la valorile implicite. Backup creat.",
        "has_backup": BACKUP_FILE.exists(),
    }


class WeightsRequest(BaseModel):
    base_rate: float
    word_rate: float
    similarity: float


@router.post("/calibrate/weights")
async def adjust_weights(weights: WeightsRequest):
    """
    F8: Ajustare manuala ponderi calibrare.
    Accepta: {"base_rate": 0.3, "word_rate": 0.4, "similarity": 0.3}
    Suma ponderilor trebuie sa fie 1.0 (toleranta ±0.01).
    """
    w = {"base_rate": weights.base_rate, "word_rate": weights.word_rate, "similarity": weights.similarity}

    total = sum(w.values())
    if abs(total - 1.0) > 0.01:
        raise HTTPException(400, f"Suma ponderilor trebuie sa fie 1.0 (actual: {total:.3f})")

    for k, v in w.items():
        if v < SAFETY_MIN_WEIGHT:
            raise HTTPException(400, f"Ponderea '{k}' ({v}) sub minimul de {SAFETY_MIN_WEIGHT}")

    cal_file = settings.calibration_file

    # Backup current
    if cal_file.exists():
        shutil.copy2(cal_file, BACKUP_FILE)

    # Load or create calibration data
    import datetime as dt_mod
    data = _load_current_calibration() or {}
    data["weights"] = {k: round(v, 3) for k, v in w.items()}
    data["calibrated_at"] = dt_mod.datetime.now().isoformat()

    with open(cal_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    await log_activity(
        action="calibrate_weights",
        summary=f"Ponderi ajustate manual: {data['weights']}",
        details=data["weights"],
    )

    return {
        "status": "saved",
        "message": "Ponderile au fost actualizate cu succes.",
        "weights": data["weights"],
        "has_backup": BACKUP_FILE.exists(),
    }


@router.get("/calibration-status")
async def get_calibration_status():
    """
    Returnează starea curentă a calibrării.

    Include: coeficienți, greutăți, metrici de acuratețe, data ultimei calibrări,
    și dacă există backup pentru revert.
    """
    cal_file = settings.calibration_file

    has_backup = BACKUP_FILE.exists()

    if not cal_file.exists() or cal_file.stat().st_size < 3:
        return {
            "status": "not_calibrated",
            "is_calibrated": False,
            "message": "Nu a fost efectuată nicio calibrare. Se folosesc valorile implicite.",
            "calibration": None,
            "accuracy": None,
            "has_backup": has_backup,
            "defaults": DEFAULTS,
        }

    try:
        with open(cal_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Eroare la citirea fișierului de calibrare: {exc}",
        )

    # Verifică dacă e un dict gol (resetat)
    if not data:
        return {
            "status": "not_calibrated",
            "is_calibrated": False,
            "message": "Calibrarea a fost resetată. Se folosesc valorile implicite.",
            "calibration": None,
            "accuracy": None,
            "has_backup": has_backup,
            "defaults": DEFAULTS,
        }

    weights = data.get("weights") or data.get("calibration", {}).get("weights")
    accuracy = data.get("accuracy") or data.get("calibration", {}).get("accuracy")

    # Calculează acuratețe medie din MAPE
    avg_accuracy = None
    if accuracy and accuracy.get("mape_percent") is not None:
        avg_accuracy = round((100.0 - accuracy["mape_percent"]) / 100.0, 3)

    return {
        "status": "calibrated",
        "is_calibrated": True,
        "message": "Calibrare disponibilă.",
        "last_calibrated": data.get("calibrated_at"),
        "reference_count": accuracy.get("total_files") if accuracy else None,
        "avg_accuracy": avg_accuracy,
        "has_backup": has_backup,
        "calibration": {
            "weights": weights,
            "base_rate_per_page": data.get("base_rate_per_page"),
            "base_rate_per_word": data.get("base_rate_per_word"),
            "calibrated_at": data.get("calibrated_at"),
        },
        "accuracy": accuracy,
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_current_calibration() -> dict[str, Any] | None:
    """Încarcă calibrarea curentă (dacă există)."""
    cal_file = settings.calibration_file
    if cal_file.exists() and cal_file.stat().st_size > 2:
        try:
            with open(cal_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data:
                return data
        except (json.JSONDecodeError, OSError):
            pass
    return None


async def _simple_calibration(
    reference_dir: Path, output_path: Path,
) -> dict[str, Any]:
    """
    Calibrare simplificată fără scipy — calculează media tarifelor din referințe.
    Folosită ca fallback dacă dependențele avansate nu sunt disponibile.
    """
    import re
    from app.core.analyzer import extract_features

    supported_ext = {".pdf", ".docx"}
    files = [
        f for f in reference_dir.iterdir()
        if f.is_file() and f.suffix.lower() in supported_ext
    ]

    # Încarcă prețuri din prices.json
    prices_file = reference_dir / "prices.json"
    known_prices: dict[str, float] = {}
    if prices_file.exists():
        try:
            with open(prices_file, "r", encoding="utf-8") as f:
                known_prices = json.load(f)
        except (json.JSONDecodeError, OSError):
            pass

    results = []
    errors = []
    for file in files:
        try:
            features = extract_features(str(file))
            price = known_prices.get(file.name)
            if price is None:
                match = re.search(r"(\d+(?:[.,]\d+)?)\s*EUR", file.name, re.IGNORECASE)
                if match:
                    price = float(match.group(1).replace(",", "."))
            if price:
                results.append({
                    "filename": file.name,
                    "word_count": features.get("word_count", 0),
                    "page_count": features.get("page_count", 0),
                    "price": price,
                })
        except Exception as e:
            errors.append(f"{file.name}: {e}")

    # Calcul medie tarife
    word_rates = [r["price"] / r["word_count"]
                  for r in results if r["word_count"] > 0]
    page_rates = [r["price"] / r["page_count"]
                  for r in results if r["page_count"] > 0]

    import time
    calibration_data = {
        "status": "success",
        "method": "simple_average",
        "weights": dict(settings.default_weights),
        "rates": {},
        "reference_prices": results,
        "metrics": {
            "files_scanned": len(files),
            "files_with_price": len(results),
            "avg_price_per_word": round(sum(word_rates) / len(word_rates), 4) if word_rates else None,
            "avg_price_per_page": round(sum(page_rates) / len(page_rates), 2) if page_rates else None,
            "calibrated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "errors": errors[:5],
        },
    }

    # Salvare
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(calibration_data, f, ensure_ascii=False, indent=2)
    except OSError:
        pass

    return calibration_data
