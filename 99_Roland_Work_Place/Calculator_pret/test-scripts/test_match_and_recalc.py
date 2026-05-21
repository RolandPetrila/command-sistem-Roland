"""
1. Identifica care referinte corespund celor 4 fisiere din Calculator_pret
2. Elimina-le din referinte
3. Recalibraz modelul pe referintele ramase
4. Calculeaza pretul pt cele 4 fisiere (acum cu adevarat necunoscute)
"""
import sys
import json
import math
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from app.core.analyzer import extract_features

import numpy as np

# ── Load reference cache ──
CACHE = Path(__file__).parent.parent / "Fisiere_Reper_Tarif" / "Pret_Intreg_100la100" / "_reference_cache.json"
with open(CACHE, encoding="utf-8") as f:
    REF_DATA = json.load(f)

# ── Cele 4 fisiere de test ──
TEST_DIR = Path(r"c:\Proiecte\NOU_Calculator_Pret_Traduceri\99_Roland_Work_Place\Calculator_pret")
TEST_FILES = list(TEST_DIR.glob("*.pdf"))

print("=" * 100)
print("PASUL 1: Identificare corespondente referinta ↔ fisiere test")
print("=" * 100)

matches = {}  # test_filename → ref_filename

for tf in sorted(TEST_FILES):
    print(f"\n  Analiz: {tf.name}...")
    feat = extract_features(str(tf))

    # Cauta match exact in referinte (page_count + word_count)
    for ref in REF_DATA:
        rf = ref["features"]
        if (rf["page_count"] == feat["page_count"] and
            rf["word_count"] == feat["word_count"]):
            matches[tf.name] = ref["filename"]
            print(f"    → MATCH: {ref['filename']} ({ref['price']} RON)")
            print(f"      pg={feat['page_count']}, cuv={feat['word_count']}, "
                  f"wpp={feat['words_per_page']}, img={feat['image_count']}")
            break
    else:
        # No exact match — find closest
        closest = min(REF_DATA, key=lambda r: abs(r["features"]["page_count"] - feat["page_count"]) +
                       abs(r["features"]["word_count"] - feat["word_count"]) / 1000)
        print(f"    → NU am gasit match exact!")
        print(f"      Test:  pg={feat['page_count']}, cuv={feat['word_count']}, wpp={feat['words_per_page']:.1f}")
        print(f"      Close: {closest['filename']} pg={closest['features']['page_count']}, "
              f"cuv={closest['features']['word_count']}")
        matches[tf.name] = closest["filename"] + " (CLOSEST)"

print(f"\n  REZUMAT CORESPONDENTE:")
for test_fn, ref_fn in matches.items():
    ref_price = next((r["price"] for r in REF_DATA if r["filename"] == ref_fn), "?")
    print(f"    {test_fn:45s} → {ref_fn} ({ref_price} RON)")

# ── Elimina referintele matched ──
matched_ref_names = {v for v in matches.values() if "(CLOSEST)" not in v}
print(f"\n  Elimin din referinte: {matched_ref_names}")

REF_REDUCED = [r for r in REF_DATA if r["filename"] not in matched_ref_names]
print(f"  Referinte ramase: {len(REF_REDUCED)}/{len(REF_DATA)}")

# ═══════════════════════════════════════════════════════════════════
# PASUL 2: Recalibrare model pe referintele ramase
# ═══════════════════════════════════════════════════════════════════

print(f"\n{'=' * 100}")
print(f"PASUL 2: Grid search pe {len(REF_REDUCED)} referinte (fara cele 4 eliminate)")
print("=" * 100)

best_mape = 999
best_p = {}

for base in np.arange(55, 70, 0.5):
    for s2 in np.arange(0, 8, 0.5):
        for cb in np.arange(0, 10, 0.5):
            errs = []
            for r in REF_REDUCED:
                f = r["features"]
                pc = f["page_count"]
                wpp_norm = f["words_per_page"] / 200 - 1
                cpp = f.get("chart_count", 0) / pc
                rate = base - s2 * wpp_norm + cb * cpp
                rate = max(rate, 30)
                pred = pc * rate
                err = abs(pred - r["price"]) / r["price"] * 100
                errs.append(err)
            mape = np.mean(errs)
            if mape < best_mape:
                best_mape = mape
                best_p = {"base": base, "s2": s2, "cb": cb}

print(f"  BEST: MAPE={best_mape:.2f}% pe {len(REF_REDUCED)} fisiere")
print(f"  Parametri: base={best_p['base']:.1f}, s2(wpp)={best_p['s2']:.1f}, cb(charts)={best_p['cb']:.1f}")
print(f"  Formula: rate/pg = {best_p['base']:.1f} - {best_p['s2']:.1f}×(wpp/200-1) + {best_p['cb']:.1f}×(charts/pg)")

# ── Detalii per fisier ramas ──
def calc_model(features, params):
    pc = features["page_count"]
    wpp_norm = features["words_per_page"] / 200 - 1
    cpp = features.get("chart_count", 0) / pc
    rate = params["base"] - params["s2"] * wpp_norm + params["cb"] * cpp
    rate = max(rate, 30)
    return round(pc * rate, 2), round(rate, 2)

print(f"\n  {'File':>12s}  {'Actual':>7s}  {'Pred':>8s}  {'Err%':>6s}  {'Rate/pg':>7s}  {'Pg':>3s}  {'WPP':>5s}  {'Dens':>5s}")
print(f"  {'─' * 75}")

total_errs = []
for r in sorted(REF_REDUCED, key=lambda x: x["price"]):
    f = r["features"]
    pred, rate = calc_model(f, best_p)
    err = abs(pred - r["price"]) / r["price"] * 100
    total_errs.append(err)
    mk = " ←" if err > 15 else ""
    print(f"  {r['filename']:>12s}  {r['price']:>7.0f}  {pred:>8.1f}  {err:>5.1f}%  {rate:>6.1f}/pg  "
          f"{f['page_count']:>3d}  {f['words_per_page']:>5.1f}  {f['text_density']:>5.2f}{mk}")

w5 = sum(1 for e in total_errs if e <= 5)
w10 = sum(1 for e in total_errs if e <= 10)
w15 = sum(1 for e in total_errs if e <= 15)
w20 = sum(1 for e in total_errs if e <= 20)
print(f"\n  MAPE: {np.mean(total_errs):.1f}%  |  ≤5%: {w5}/{len(REF_REDUCED)}  |  "
      f"≤10%: {w10}/{len(REF_REDUCED)}  |  ≤15%: {w15}/{len(REF_REDUCED)}  |  ≤20%: {w20}/{len(REF_REDUCED)}")

# ═══════════════════════════════════════════════════════════════════
# PASUL 3: Calcul pret pt cele 4 fisiere NOI (necunoscute)
# ═══════════════════════════════════════════════════════════════════

print(f"\n{'=' * 100}")
print("PASUL 3: PRET ESTIMAT pt cele 4 fisiere (model recalibrat, fara ele in referinte)")
print("=" * 100)

for tf in sorted(TEST_FILES):
    feat = extract_features(str(tf))
    pred, rate = calc_model(feat, best_p)

    ref_fn = matches.get(tf.name, "?")
    ref_price = next((r["price"] for r in REF_DATA if r["filename"] == ref_fn), None)

    td = feat["text_density"]
    if td < 0.40: tip = "DTP COMPLEX"
    elif td < 0.75: tip = "MIXT"
    else: tip = "TEXT DENS"

    wpp_norm = feat["words_per_page"] / 200 - 1
    cpp = feat.get("chart_count", 0) / feat["page_count"]

    print(f"\n  {'━' * 95}")
    print(f"  {tf.name}")
    print(f"  {'━' * 95}")
    print(f"  {feat['page_count']} pg | {feat['word_count']} cuv | {feat['words_per_page']:.0f} cuv/pg | "
          f"{feat['image_count']} img | {feat.get('chart_count',0)} charts | dens={feat['text_density']}")
    print(f"  Tip: {tip}")
    print()
    print(f"  Calcul: {best_p['base']:.1f} {-best_p['s2']*wpp_norm:+.1f}(wpp) {best_p['cb']*cpp:+.1f}(charts) = {rate} RON/pg")
    print(f"  ┌──────────────────────────────────────────────────┐")
    print(f"  │  PRET PIATA:     {feat['page_count']:>3d} pg × {rate:>5.1f} = {pred:>9.2f} RON   │")
    print(f"  │  FACTURA (75%):  {feat['page_count']:>3d} pg × {rate*0.75:>5.1f} = {pred*0.75:>9.2f} RON   │")
    if ref_price:
        err = abs(pred - ref_price) / ref_price * 100
        print(f"  │  PRET REAL:                        {ref_price:>9.0f} RON   │")
        print(f"  │  EROARE:                             {err:>6.1f}%      │")
    print(f"  └──────────────────────────────────────────────────┘")

print(f"\n{'=' * 100}")
print("COMPLET")
print("=" * 100)
