#!/usr/bin/env python3
"""
Script verificare progres implementare — Calculator Preț Traduceri.
Verifică existența fișierelor, importuri, și funcționalitate de bază.
"""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent

# Fișiere obligatorii per fază
REQUIRED_FILES = {
    "FAZA 0 — Setup": [
        "backend/requirements.txt",
        "frontend/package.json",
        "CLAUDE.md",
        "PLAN_EXECUTIE.md",
        "update_tracking.py",
    ],
    "FAZA 1 — Analyzer": [
        "backend/app/core/analyzer.py",
    ],
    "FAZA 2 — Pricing": [
        "backend/app/core/pricing/base_rate.py",
        "backend/app/core/pricing/word_rate.py",
        "backend/app/core/pricing/similarity.py",
        "backend/app/core/pricing/ensemble.py",
        "backend/app/core/calibration.py",
        "backend/calibrate.py",
        "backend/data/calibration.json",
    ],
    "FAZA 3 — Validare": [
        "backend/app/core/validation.py",
        "backend/app/core/self_learning.py",
        "backend/data/market_rates.json",
    ],
    "FAZA 4 — API": [
        "backend/app/main.py",
        "backend/app/db/database.py",
        "backend/app/db/models.py",
        "backend/app/api/routes_upload.py",
        "backend/app/api/routes_price.py",
        "backend/app/api/routes_history.py",
        "backend/app/api/routes_calibrate.py",
        "backend/app/api/routes_files.py",
        "backend/app/api/routes_settings.py",
        "backend/app/api/routes_competitors.py",
    ],
    "FAZA 5 — Frontend": [
        "frontend/index.html",
        "frontend/vite.config.js",
        "frontend/tailwind.config.js",
        "frontend/src/main.jsx",
        "frontend/src/App.jsx",
        "frontend/src/api/client.js",
        "frontend/src/components/Layout/Sidebar.jsx",
        "frontend/src/components/Upload/DropZone.jsx",
        "frontend/src/components/Price/PriceCard.jsx",
        "frontend/src/components/History/HistoryTable.jsx",
        "frontend/src/components/Calibration/CalibrationPanel.jsx",
        "frontend/src/components/FileBrowser/FileBrowser.jsx",
        "frontend/src/components/Settings/InvoicePercent.jsx",
        "frontend/src/components/Dashboard/StatsCards.jsx",
        "frontend/src/pages/DashboardPage.jsx",
        "frontend/src/pages/UploadPage.jsx",
        "frontend/src/pages/HistoryPage.jsx",
        "frontend/src/pages/CalibrationPage.jsx",
        "frontend/src/pages/FileBrowserPage.jsx",
        "frontend/src/pages/SettingsPage.jsx",
    ],
}


def check_files():
    """Verifică existența fișierelor obligatorii."""
    total = 0
    found = 0
    results = {}

    for phase, files in REQUIRED_FILES.items():
        phase_found = 0
        phase_total = len(files)
        missing = []

        for f in files:
            total += 1
            filepath = PROJECT_ROOT / f
            if filepath.exists() and filepath.stat().st_size > 0:
                found += 1
                phase_found += 1
            else:
                missing.append(f)

        results[phase] = {
            "found": phase_found,
            "total": phase_total,
            "missing": missing,
        }

    return total, found, results


def check_reference_files():
    """Verifică fișierele reper."""
    ref_dir = PROJECT_ROOT / "Fisiere_Reper_Tarif" / "Pret_Intreg_100la100"
    if not ref_dir.exists():
        return 0, []

    pdfs = list(ref_dir.glob("*.pdf"))
    prices = []
    for pdf in pdfs:
        try:
            price = float(pdf.stem)
            prices.append(price)
        except ValueError:
            pass

    return len(pdfs), sorted(prices)


def main():
    print("=" * 60)
    print("  VERIFICARE PROGRES — Calculator Preț Traduceri")
    print("=" * 60)
    print()

    total, found, results = check_files()

    for phase, data in results.items():
        status = "✅" if data["found"] == data["total"] else "⚠️"
        print(f"{status} {phase}: {data['found']}/{data['total']} fișiere")
        if data["missing"]:
            for m in data["missing"]:
                print(f"   ❌ Lipsă: {m}")

    print()
    print(f"TOTAL: {found}/{total} fișiere ({found/total*100:.0f}%)")

    # Fișiere reper
    print()
    ref_count, prices = check_reference_files()
    print(f"📁 Fișiere reper: {ref_count} PDF-uri")
    if prices:
        print(f"   Range: {min(prices):.0f} - {max(prices):.0f} RON")
        print(f"   Medie: {sum(prices)/len(prices):.0f} RON")

    # Verificare dependențe
    print()
    print("📦 Dependențe:")
    req_file = PROJECT_ROOT / "backend" / "requirements.txt"
    if req_file.exists():
        deps = [l.strip().split("==")[0] for l in req_file.read_text().splitlines() if l.strip() and not l.startswith("#")]
        print(f"   Python: {len(deps)} pachete în requirements.txt")

    pkg_file = PROJECT_ROOT / "frontend" / "package.json"
    if pkg_file.exists():
        print(f"   Node: package.json prezent")

    # Status general
    print()
    pct = found / total * 100
    if pct == 100:
        print("🟢 TOATE fișierele sunt create. Gata pentru testare!")
    elif pct >= 80:
        print("🟡 Majoritatea fișierelor create. Câteva lipsesc.")
    else:
        print("🔴 Implementare incompletă.")

    return 0 if pct == 100 else 1


if __name__ == "__main__":
    sys.exit(main())
