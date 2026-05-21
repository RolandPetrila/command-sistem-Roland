"""
Test fisiere noi — extrage features si calculeaza pret cu modelul nou.
"""
import sys
import json
import math
from pathlib import Path

# Adaug backend-ul in path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.analyzer import extract_features

FILES = [
    r"c:\Proiecte\NOU_Calculator_Pret_Traduceri\99_Roland_Work_Place\Calculator_pret\Catalogo_2025_RO_R_2.pdf",
    r"c:\Proiecte\NOU_Calculator_Pret_Traduceri\99_Roland_Work_Place\Calculator_pret\Manual Mixer EN ro.pdf",
]

def calc_pret_nou(f):
    """Model nou: rate/pg = 59 - 3×(wpp/200 - 1) + 4×(charts/pg)"""
    pc = f["page_count"]
    wpp = f["words_per_page"]
    cpp = f.get("chart_count", 0) / pc
    wpp_norm = wpp / 200 - 1

    rate = 59 - 3 * wpp_norm + 4 * cpp
    rate = max(rate, 30)

    return round(pc * rate, 2), round(rate, 2), wpp_norm, cpp

print("=" * 100)
print("TEST FISIERE NOI — Model: rate/pg = 59 - 3×(wpp/200-1) + 4×(charts/pg)")
print("=" * 100)

for filepath in FILES:
    p = Path(filepath)
    print(f"\n{'━' * 100}")
    print(f"  FISIER: {p.name}")
    print(f"  Cale: {filepath}")
    print(f"{'━' * 100}")

    if not p.exists():
        print(f"  ❌ FISIERUL NU EXISTA!")
        continue

    size_mb = p.stat().st_size / (1024 * 1024)
    print(f"  Marime: {size_mb:.1f} MB")

    print(f"\n  Extragere caracteristici...")
    try:
        features = extract_features(str(p))
    except Exception as e:
        print(f"  ❌ EROARE: {e}")
        continue

    print(f"\n  CARACTERISTICI EXTRASE:")
    print(f"    Pagini:              {features['page_count']}")
    print(f"    Cuvinte total:       {features['word_count']}")
    print(f"    Cuvinte/pagina:      {features['words_per_page']}")
    print(f"    Imagini:             {features['image_count']}")
    print(f"    Tabele:              {features['table_count']}")
    print(f"    Tabele complexe:     {features['has_complex_tables']}")
    print(f"    Charts (img mari):   {features.get('chart_count', 0)}")
    print(f"    Diagrame:            {features.get('has_diagrams', False)}")
    print(f"    Layout complexity:   {features['layout_complexity']}/5")
    print(f"    Scanat (OCR):        {features['is_scanned']}")
    print(f"    Densitate text:      {features['text_density']}")

    pret, rate, wpp_norm, cpp = calc_pret_nou(features)

    # Tipologie
    td = features["text_density"]
    if td < 0.40:
        tip = "DTP COMPLEX (mult layout, putin text)"
    elif td < 0.75:
        tip = "MIXT (text + imagini)"
    else:
        tip = "TEXT DENS (layout simplu)"

    print(f"\n  TIPOLOGIE: {tip}")

    print(f"\n  CALCUL PRET:")
    print(f"    59.0 RON/pg  (baza)")
    wpp_adj = -3 * wpp_norm
    print(f"    {wpp_adj:+.1f} RON/pg  (ajustare cuvinte/pg: {features['words_per_page']:.0f} wpp → {'text dens' if wpp_norm > 0 else 'putin text'})")
    chart_adj = 4 * cpp
    print(f"    {chart_adj:+.1f} RON/pg  (charts: {features.get('chart_count', 0)} diagrame mari)")
    print(f"    {'─' * 30}")
    print(f"    = {rate} RON/pagina")
    print(f"\n  ┌─────────────────────────────────────────────┐")
    print(f"  │  PRET PIATA:    {features['page_count']:>3d} pg × {rate} = {pret:>8.2f} RON  │")
    print(f"  │  FACTURA (75%): {features['page_count']:>3d} pg × {rate*0.75:.1f} = {pret*0.75:>8.2f} RON  │")
    print(f"  └─────────────────────────────────────────────┘")

    # Comparatie cu fisiere similare din referinta
    print(f"\n  COMPARATIE cu fisiere similare din referinta:")
    CACHE = Path(__file__).parent.parent / "Fisiere_Reper_Tarif" / "Pret_Intreg_100la100" / "_reference_cache.json"
    with open(CACHE, encoding="utf-8") as cf:
        ref_data = json.load(cf)

    # Gaseste 3 cele mai similare (dupa page_count)
    sorted_refs = sorted(ref_data, key=lambda r: abs(r["features"]["page_count"] - features["page_count"]))
    print(f"    {'Referinta':>12s}  {'Pagini':>6s}  {'Pret real':>9s}  {'Rate/pg':>7s}  {'WPP':>5s}")
    for ref in sorted_refs[:3]:
        rf = ref["features"]
        rrate = ref["price"] / rf["page_count"]
        print(f"    {ref['filename']:>12s}  {rf['page_count']:>6d}  {ref['price']:>9.0f}  {rrate:>6.1f}  {rf['words_per_page']:>5.1f}")

print(f"\n{'=' * 100}")
print("TEST COMPLET")
print(f"{'=' * 100}")
