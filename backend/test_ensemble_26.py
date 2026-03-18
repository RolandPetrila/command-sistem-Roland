"""
PLAN item 2.6 — Test ensemble on 26 reference files.
Target: MAPE < 10%.

Steps:
1. Run calibration first (if not already calibrated)
2. Load calibration params
3. For each reference PDF: extract features, calculate ensemble price
4. Compare vs real price from filename
5. Print detailed table + accuracy stats
"""

import json
import sys
import os
from pathlib import Path
from statistics import mean, median

# Ensure backend is on the path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.config import settings
from app.core.analyzer import extract_features
from app.core.pricing.ensemble import calculate_ensemble_price
from app.core.pricing.similarity import load_reference_data
from app.core.calibration import run_calibration


def main():
    ref_dir = settings.reference_dir
    cal_file = settings.calibration_file

    print("=" * 80)
    print("PLAN 2.6 — TEST ENSEMBLE PE 26 FISIERE DE REFERINTA")
    print("=" * 80)
    print(f"Director referinte: {ref_dir}")
    print(f"Fisier calibrare:   {cal_file}")
    print()

    # ------------------------------------------------------------------
    # STEP 1: Run calibration if needed
    # ------------------------------------------------------------------
    cal_data = {}
    if cal_file.exists():
        with open(cal_file, "r", encoding="utf-8") as f:
            cal_data = json.load(f)

    if not cal_data.get("calibrated_at"):
        print("[INFO] Calibrare nu a fost rulata. Rulez calibrarea acum...")
        print("-" * 60)
        result = run_calibration(
            reference_dir=ref_dir,
            output_path=cal_file,
        )
        print(f"  Optimizare succes: {result['optimization_success']}")
        print(f"  Mesaj: {result['optimization_message']}")
        print(f"  MAPE calibrare (LOO): {result['accuracy']['mape_percent']:.1f}%")
        print("-" * 60)
        # Reload calibration
        with open(cal_file, "r", encoding="utf-8") as f:
            cal_data = json.load(f)
        print("[OK] Calibrare completa si salvata.\n")
    else:
        print(f"[OK] Calibrare existenta din: {cal_data['calibrated_at']}")
        if cal_data.get("accuracy"):
            print(f"     MAPE calibrare: {cal_data['accuracy']['mape_percent']}%")
        print()

    # ------------------------------------------------------------------
    # STEP 2: Load all reference data (for KNN similarity)
    # ------------------------------------------------------------------
    print("[INFO] Incarcare fisiere de referinta...")
    all_references = load_reference_data(ref_dir)
    print(f"  Gasite: {len(all_references)} fisiere\n")

    # Weights from calibration
    weights = cal_data.get("weights", {
        "base_rate": 0.3,
        "word_rate": 0.4,
        "similarity": 0.3,
    })

    # ------------------------------------------------------------------
    # STEP 3: Test each file (Leave-One-Out for KNN fairness)
    # ------------------------------------------------------------------
    print("[INFO] Testare ensemble pe fiecare fisier (Leave-One-Out)...\n")

    results = []
    pdf_files = sorted(ref_dir.glob("*.pdf"))

    for pdf_path in pdf_files:
        # Extract real price from filename
        try:
            real_price = float(pdf_path.stem)
        except ValueError:
            print(f"  [SKIP] Nu pot extrage pretul din: {pdf_path.name}")
            continue

        # Extract features
        try:
            features = extract_features(pdf_path)
        except Exception as e:
            print(f"  [ERROR] Extragere features din {pdf_path.name}: {e}")
            continue

        # Leave-One-Out: exclude current file from references
        loo_refs = [r for r in all_references if r["filename"] != pdf_path.name]

        # Calculate ensemble price
        ensemble_result = calculate_ensemble_price(
            features=features,
            reference_data=loo_refs,
            weights=weights,
            calibration=cal_data,
        )

        estimated_price = ensemble_result["market_price"]
        error_abs = abs(estimated_price - real_price)
        error_pct = (error_abs / real_price * 100) if real_price > 0 else 0

        results.append({
            "filename": pdf_path.name,
            "real_price": real_price,
            "estimated_price": estimated_price,
            "error_abs": error_abs,
            "error_pct": error_pct,
            "method_prices": ensemble_result.get("method_prices", {}),
            "weights_used": ensemble_result.get("weights_used", {}),
        })

    # ------------------------------------------------------------------
    # STEP 4: Print detailed table
    # ------------------------------------------------------------------
    print("=" * 95)
    print(f"{'Fisier':<16} {'Pret Real':>10} {'Pret Estim.':>12} {'Eroare':>10} {'Err %':>8}  {'Status'}")
    print("-" * 95)

    for r in sorted(results, key=lambda x: x["real_price"]):
        status = "OK" if r["error_pct"] <= 10 else ("WARN" if r["error_pct"] <= 20 else "FAIL")
        marker = "  " if status == "OK" else (" !" if status == "WARN" else " X")
        print(
            f"{r['filename']:<16} {r['real_price']:>10.0f} RON {r['estimated_price']:>10.2f} RON "
            f"{r['error_abs']:>8.2f} RON {r['error_pct']:>6.1f}% {marker} {status}"
        )

    print("=" * 95)

    # ------------------------------------------------------------------
    # STEP 5: Accuracy metrics
    # ------------------------------------------------------------------
    errors_pct = [r["error_pct"] for r in results]
    errors_abs = [r["error_abs"] for r in results]

    mape = mean(errors_pct) if errors_pct else 0
    median_err = median(errors_pct) if errors_pct else 0
    max_err = max(errors_pct) if errors_pct else 0
    min_err = min(errors_pct) if errors_pct else 0
    mae = mean(errors_abs) if errors_abs else 0

    within_5 = sum(1 for e in errors_pct if e <= 5)
    within_10 = sum(1 for e in errors_pct if e <= 10)
    within_15 = sum(1 for e in errors_pct if e <= 15)
    within_20 = sum(1 for e in errors_pct if e <= 20)
    total = len(results)

    print()
    print("=" * 60)
    print("METRICI DE ACURATETE")
    print("=" * 60)
    print(f"  Total fisiere testate:     {total}")
    print(f"  MAPE (Mean Abs % Error):   {mape:.1f}%")
    print(f"  Eroare mediana:            {median_err:.1f}%")
    print(f"  MAE (Mean Abs Error):      {mae:.2f} RON")
    print(f"  Eroare minima:             {min_err:.1f}%")
    print(f"  Eroare maxima:             {max_err:.1f}%")
    print()
    print(f"  In limita  5%:  {within_5:>2}/{total} ({within_5/total*100:.0f}%)")
    print(f"  In limita 10%:  {within_10:>2}/{total} ({within_10/total*100:.0f}%)")
    print(f"  In limita 15%:  {within_15:>2}/{total} ({within_15/total*100:.0f}%)")
    print(f"  In limita 20%:  {within_20:>2}/{total} ({within_20/total*100:.0f}%)")
    print()

    target_met = mape < 10
    print("=" * 60)
    if target_met:
        print(f"  TARGET ATINS: MAPE = {mape:.1f}% < 10%")
    else:
        print(f"  TARGET NEATINS: MAPE = {mape:.1f}% >= 10%")
    print("=" * 60)

    # ------------------------------------------------------------------
    # STEP 6: Calibration params used
    # ------------------------------------------------------------------
    print()
    print("Parametri calibrare utilizati:")
    print(f"  base_rate_per_page:   {cal_data.get('base_rate_per_page')}")
    print(f"  base_rate_per_word:   {cal_data.get('base_rate_per_word')}")
    print(f"  volume_discount:      {cal_data.get('volume_discount_factor')}")
    print(f"  weights:              {cal_data.get('weights')}")
    print(f"  complexity_mult:      {cal_data.get('complexity_multipliers')}")
    print()

    # Method breakdown for worst performers
    worst = sorted(results, key=lambda x: -x["error_pct"])[:5]
    print("Top 5 cele mai mari erori (detalii metode):")
    print("-" * 80)
    for r in worst:
        mp = r["method_prices"]
        wu = r["weights_used"]
        print(f"  {r['filename']:<14} Real: {r['real_price']:.0f} | Estim: {r['estimated_price']:.2f} | Err: {r['error_pct']:.1f}%")
        print(f"    base_rate={mp.get('base_rate', 0):.2f} (w={wu.get('base_rate', 0):.3f})  "
              f"word_rate={mp.get('word_rate', 0):.2f} (w={wu.get('word_rate', 0):.3f})  "
              f"similarity={mp.get('similarity', 0):.2f} (w={wu.get('similarity', 0):.3f})")
    print()

    return 0 if target_met else 1


if __name__ == "__main__":
    sys.exit(main())
