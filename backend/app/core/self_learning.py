"""
Modul de auto-învățare: salvează prețuri validate de utilizator
și recalibrează coeficienții.

Flux:
1. Utilizatorul validează/corectează un preț estimat.
2. Caracteristicile fișierului + prețul confirmat se adaugă la setul de referință.
3. Se declanșează recalibrarea automată.
4. Se păstrează un istoric al învățării.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.config import settings
from app.core.analyzer import get_feature_vector

logger = logging.getLogger(__name__)

# Fișierul unde se stochează referințele învățate
LEARNED_REFERENCES_FILE = settings.data_dir / "learned_references.json"
LEARNING_HISTORY_FILE = settings.data_dir / "learning_history.json"


def _load_json(path: Path) -> Any:
    """Încarcă un fișier JSON. Returnează [] dacă nu există."""
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Nu pot citi %s: %s", path, exc)
        return []


def _save_json(path: Path, data: Any) -> None:
    """Salvează date în fișier JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def add_validated_price(
    filename: str,
    features: dict[str, Any],
    confirmed_price: float,
    original_estimate: float | None = None,
    notes: str = "",
) -> dict[str, Any]:
    """
    Salvează un preț validat de utilizator în setul de referință.

    Args:
        filename: Numele fișierului original.
        features: Caracteristicile extrase din document.
        confirmed_price: Prețul confirmat de utilizator (RON).
        original_estimate: Prețul estimat inițial de sistem (opțional).
        notes: Note suplimentare de la utilizator.

    Returns:
        Dicționar cu statusul operației.
    """
    # Încarcă referințe existente
    references = _load_json(LEARNED_REFERENCES_FILE)

    # Creează noua referință
    new_ref = {
        "filename": filename,
        "price": confirmed_price,
        "features": features,
        "vector": get_feature_vector(features),
        "original_estimate": original_estimate,
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "notes": notes,
        "source": "user_validation",
    }

    # Verifică dacă fișierul există deja în referințe
    existing_idx = None
    for i, ref in enumerate(references):
        if ref.get("filename") == filename:
            existing_idx = i
            break

    if existing_idx is not None:
        # Actualizează referința existentă
        references[existing_idx] = new_ref
        action = "actualizat"
    else:
        # Adaugă referință nouă
        references.append(new_ref)
        action = "adăugat"

    _save_json(LEARNED_REFERENCES_FILE, references)

    # Salvează în istoricul de învățare
    _add_to_history(
        filename=filename,
        confirmed_price=confirmed_price,
        original_estimate=original_estimate,
        action=action,
    )

    logger.info(
        "Referință %s: %s — %.2f RON (estimare inițială: %s RON)",
        action,
        filename,
        confirmed_price,
        original_estimate,
    )

    return {
        "status": "success",
        "action": action,
        "filename": filename,
        "confirmed_price": confirmed_price,
        "total_learned_references": len(references),
    }


def _add_to_history(
    filename: str,
    confirmed_price: float,
    original_estimate: float | None,
    action: str,
) -> None:
    """Adaugă o intrare în istoricul de învățare."""
    history = _load_json(LEARNING_HISTORY_FILE)

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "filename": filename,
        "confirmed_price": confirmed_price,
        "original_estimate": original_estimate,
        "action": action,
    }

    if original_estimate and original_estimate > 0:
        entry["error_percent"] = round(
            abs(original_estimate - confirmed_price) / confirmed_price * 100, 1
        )

    history.append(entry)
    _save_json(LEARNING_HISTORY_FILE, history)


def get_all_references(
    include_learned: bool = True,
) -> list[dict[str, Any]]:
    """
    Returnează toate referințele disponibile (originale + învățate).

    Args:
        include_learned: Dacă True, include și referințele validate de utilizator.

    Returns:
        Lista completă de referințe.
    """
    from app.core.pricing.similarity import load_reference_data

    # Referințe originale din Fisiere_Reper_Tarif
    original_refs = load_reference_data(settings.reference_dir)

    if not include_learned:
        return original_refs

    # Referințe învățate
    learned = _load_json(LEARNED_REFERENCES_FILE)

    # Combinare (referințele învățate pot suprascrie pe cele originale)
    all_refs = {r["filename"]: r for r in original_refs}
    for ref in learned:
        all_refs[ref["filename"]] = ref

    return list(all_refs.values())


def get_learning_history() -> list[dict[str, Any]]:
    """Returnează istoricul complet de învățare."""
    return _load_json(LEARNING_HISTORY_FILE)


def get_learning_stats() -> dict[str, Any]:
    """Returnează statistici despre procesul de învățare."""
    history = _load_json(LEARNING_HISTORY_FILE)
    learned = _load_json(LEARNED_REFERENCES_FILE)

    errors = [
        e["error_percent"]
        for e in history
        if "error_percent" in e
    ]

    stats = {
        "total_validations": len(history),
        "total_learned_references": len(learned),
        "last_validation": history[-1]["timestamp"] if history else None,
    }

    if errors:
        stats["avg_error_percent"] = round(sum(errors) / len(errors), 1)
        stats["min_error_percent"] = round(min(errors), 1)
        stats["max_error_percent"] = round(max(errors), 1)
        stats["improving"] = (
            len(errors) >= 5
            and sum(errors[-5:]) / 5 < sum(errors[:5]) / min(5, len(errors))
        )

    return stats


async def trigger_recalibration() -> dict[str, Any]:
    """
    Declanșează recalibrarea cu toate referințele (originale + învățate).

    Aceasta este o operație costisitoare — se rulează async.
    """
    from app.core.calibration import run_calibration

    all_refs = get_all_references(include_learned=True)
    if len(all_refs) < 5:
        return {
            "status": "skipped",
            "reason": f"Prea puține referințe ({len(all_refs)}). Minimum necesar: 5.",
        }

    result = run_calibration(
        reference_dir=settings.reference_dir,
        output_path=settings.calibration_file,
    )

    logger.info(
        "Recalibrare completă. MAPE: %.1f%%",
        result["accuracy"]["mape_percent"],
    )

    return {
        "status": "success",
        "accuracy": result["accuracy"],
        "calibration": result["calibration"],
    }
