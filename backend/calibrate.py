"""
Script CLI pentru calibrarea coeficienților pe baza fișierelor de referință.

Utilizare:
    python calibrate.py
    python calibrate.py --reference-dir "cale/catre/referinte"
    python calibrate.py --output "cale/catre/calibration.json"

Procesul:
1. Încarcă PDF-urile de referință (cu prețuri în numele fișierului).
2. Extrage caracteristici din fiecare fișier.
3. Optimizează parametrii folosind scipy.optimize.minimize.
4. Validare leave-one-out cross-validation.
5. Salvează rezultatele în calibration.json.
6. Afișează raport detaliat cu metrici de acuratețe.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

# Adaugă directorul backend în sys.path pentru importuri
_BACKEND_DIR = Path(__file__).resolve().parent
if str(_BACKEND_DIR.parent) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR.parent))

from app.config import settings
from app.core.calibration import run_calibration

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("calibrate")


def main() -> None:
    """Punct de intrare principal pentru scriptul de calibrare."""
    parser = argparse.ArgumentParser(
        description="Calibrare coeficienți Calculator Preț Traduceri",
    )
    parser.add_argument(
        "--reference-dir",
        type=str,
        default=None,
        help=(
            "Directorul cu PDF-urile de referință. "
            "Implicit: Fisiere_Reper_Tarif/Pret_Intreg_100la100/"
        ),
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Calea către fișierul calibration.json de ieșire.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Afișează detalii suplimentare.",
    )

    args = parser.parse_args()

    # Determină căile
    reference_dir = Path(args.reference_dir) if args.reference_dir else settings.reference_dir
    output_path = Path(args.output) if args.output else settings.calibration_file

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Verificare director referințe
    if not reference_dir.exists():
        logger.error("Directorul de referință nu există: %s", reference_dir)
        sys.exit(1)

    pdf_count = len(list(reference_dir.glob("*.pdf")))
    if pdf_count == 0:
        logger.error("Nu s-au găsit fișiere PDF în: %s", reference_dir)
        sys.exit(1)

    # Header
    print("=" * 70)
    print("  CALIBRARE CALCULATOR PREȚ TRADUCERI")
    print("=" * 70)
    print(f"  Director referințe : {reference_dir}")
    print(f"  Fișiere PDF găsite : {pdf_count}")
    print(f"  Fișier ieșire      : {output_path}")
    print("=" * 70)
    print()

    # Rulare calibrare
    try:
        result = run_calibration(
            reference_dir=reference_dir,
            output_path=output_path,
        )
    except ValueError as exc:
        logger.error("Eroare calibrare: %s", exc)
        sys.exit(1)
    except Exception as exc:
        logger.error("Eroare neașteptată: %s", exc, exc_info=True)
        sys.exit(1)

    # Afișare rezultate
    cal = result["calibration"]
    acc = result["accuracy"]

    print()
    print("=" * 70)
    print("  PARAMETRI CALIBRAȚI")
    print("=" * 70)
    print(f"  Tarif per pagină   : {cal['base_rate_per_page']:.4f} RON")
    print(f"  Tarif per cuvânt   : {cal['base_rate_per_word']:.6f} RON")
    print(f"  Discount volum     : {cal['volume_discount_factor']:.6f}")
    print()
    print("  Ponderi ansamblu:")
    for method, weight in cal["weights"].items():
        print(f"    {method:20s} : {weight:.4f}")
    print()
    print("  Multiplicatori complexitate:")
    for level, mult in cal["complexity_multipliers"].items():
        print(f"    {level:20s} : {mult:.2f}")

    print()
    print("=" * 70)
    print("  METRICI DE ACURATEȚE (Leave-One-Out Cross-Validation)")
    print("=" * 70)
    print(f"  MAE (eroare absolută medie)     : {acc['mae_ron']:.2f} RON")
    print(f"  MAPE (eroare procentuală medie) : {acc['mape_percent']:.1f}%")
    print(f"  Eroare maximă                   : {acc['max_error_percent']:.1f}%")
    print(f"  Eroare mediană                  : {acc['median_error_percent']:.1f}%")
    print(f"  Fișiere cu eroare ≤10%          : {acc['within_10_percent']}/{acc['total_files']}")
    print(f"  Fișiere cu eroare ≤20%          : {acc['within_20_percent']}/{acc['total_files']}")

    print()
    print("=" * 70)
    print("  ERORI PER FIȘIER")
    print("=" * 70)
    print(f"  {'Fișier':<20s} {'Preț real':>10s} {'Estimat':>10s} {'Eroare':>10s} {'%':>8s}")
    print("  " + "-" * 60)

    per_file = sorted(acc["per_file_errors"], key=lambda x: x["percentage_error"], reverse=True)
    for item in per_file:
        marker = " ⚠" if item["percentage_error"] > 20 else ""
        print(
            f"  {item['filename']:<20s} "
            f"{item['actual_price']:>10.0f} "
            f"{item['predicted_price']:>10.0f} "
            f"{item['absolute_error']:>10.0f} "
            f"{item['percentage_error']:>7.1f}%{marker}"
        )

    print()
    print("=" * 70)
    print(f"  Optimizare reușită : {'DA' if result['optimization_success'] else 'NU'}")
    print(f"  Mesaj optimizer    : {result['optimization_message']}")
    print(f"  Rezultat salvat în : {output_path}")
    print("=" * 70)

    # Evaluare finală
    if acc["mape_percent"] <= 15:
        print("\n  ✅ Calibrare EXCELENTĂ — eroare medie sub 15%.")
    elif acc["mape_percent"] <= 25:
        print("\n  ⚠️  Calibrare BUNĂ — eroare medie sub 25%. Se recomandă mai multe referințe.")
    else:
        print("\n  ❌ Calibrare SLABĂ — eroare medie peste 25%. Sunt necesare ajustări.")


if __name__ == "__main__":
    main()
