"""
PLAN 1.2 + 1.3: Test analyzer on 26 reference files + correlation analysis.
"""

import sys
import re
from pathlib import Path
from scipy.stats import pearsonr
import numpy as np

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.analyzer import extract_features

REF_DIR = Path(__file__).parent.parent / "Fisiere_Reper_Tarif" / "Pret_Intreg_100la100"

def get_price_from_filename(fname: str) -> float:
    """Extract price (RON) from filename like '120.pdf' -> 120.0"""
    stem = Path(fname).stem
    match = re.match(r"^(\d+)", stem)
    if match:
        return float(match.group(1))
    return 0.0

def main():
    pdf_files = sorted(REF_DIR.glob("*.pdf"), key=lambda p: get_price_from_filename(p.name))

    if not pdf_files:
        print("EROARE: Nu am gasit fisiere PDF in", REF_DIR)
        return

    print(f"Fisiere gasite: {len(pdf_files)}")
    print("=" * 120)

    # Collect data
    rows = []
    errors = []

    for pdf in pdf_files:
        price = get_price_from_filename(pdf.name)
        try:
            feat = extract_features(pdf)
            rows.append({
                "filename": pdf.name,
                "price": price,
                "pages": feat.get("page_count", 0),
                "words": feat.get("word_count", 0),
                "words_per_page": feat.get("words_per_page", 0),
                "images": feat.get("image_count", 0),
                "tables": feat.get("table_count", 0),
                "has_complex_tables": feat.get("has_complex_tables", False),
                "charts": feat.get("chart_count", 0),
                "has_diagrams": feat.get("has_diagrams", False),
                "layout_complexity": feat.get("layout_complexity", 1),
                "is_scanned": feat.get("is_scanned", False),
                "text_density": feat.get("text_density", 0),
            })
        except Exception as e:
            errors.append((pdf.name, str(e)))
            print(f"EROARE la {pdf.name}: {e}")

    if errors:
        print(f"\n{'!'*60}")
        print(f"ERORI: {len(errors)} fisiere nu au putut fi analizate")
        for fname, err in errors:
            print(f"  - {fname}: {err}")
        print(f"{'!'*60}\n")

    # ── Summary Table ──
    print(f"\n{'─'*120}")
    header = f"{'Fisier':<16} {'Pret RON':>10} {'Pagini':>8} {'Cuvinte':>10} {'Cuv/Pag':>10} {'Imagini':>8} {'Tabele':>8} {'Grafice':>8} {'Complex':>8} {'Densitate':>10} {'Scanat':>7}"
    print(header)
    print(f"{'─'*120}")

    for r in rows:
        print(
            f"{r['filename']:<16} {r['price']:>10.0f} {r['pages']:>8} {r['words']:>10} "
            f"{r['words_per_page']:>10.1f} {r['images']:>8} {r['tables']:>8} {r['charts']:>8} "
            f"{r['layout_complexity']:>8} {r['text_density']:>10.2f} {'DA' if r['is_scanned'] else 'NU':>7}"
        )

    print(f"{'─'*120}")

    # ── Statistics ──
    prices = np.array([r["price"] for r in rows])
    print(f"\nSTATISTICI PRETURI: min={prices.min():.0f}, max={prices.max():.0f}, "
          f"mean={prices.mean():.0f}, median={np.median(prices):.0f}, std={prices.std():.0f}")

    # ── Correlation Analysis ──
    print(f"\n{'='*80}")
    print("ANALIZA CORELATIE (Pearson) — fiecare feature vs. pret real")
    print(f"{'='*80}")

    features_to_test = [
        ("pages", "page_count"),
        ("words", "word_count"),
        ("words_per_page", "words_per_page"),
        ("images", "image_count"),
        ("tables", "table_count"),
        ("charts", "chart_count"),
        ("layout_complexity", "layout_complexity"),
        ("text_density", "text_density"),
    ]

    correlations = []
    for label, key in features_to_test:
        values = np.array([r[label] for r in rows])
        if np.std(values) == 0:
            print(f"  {label:<22} — varianta ZERO, skip")
            continue
        corr, pvalue = pearsonr(values, prices)
        correlations.append((label, corr, pvalue))

    # Sort by absolute correlation descending
    correlations.sort(key=lambda x: abs(x[1]), reverse=True)

    print(f"\n{'Feature':<22} {'Pearson r':>12} {'p-value':>12} {'Interpretare':<30}")
    print(f"{'─'*80}")
    for label, corr, pval in correlations:
        if abs(corr) >= 0.7:
            interp = "PUTERNICA"
        elif abs(corr) >= 0.4:
            interp = "MODERATA"
        elif abs(corr) >= 0.2:
            interp = "SLABA"
        else:
            interp = "NEGLIJABILA"

        sig = "***" if pval < 0.001 else "**" if pval < 0.01 else "*" if pval < 0.05 else "ns"
        print(f"  {label:<20} {corr:>12.4f} {pval:>12.6f} {interp:<20} {sig}")

    print(f"{'─'*80}")
    print("Semnificatie: *** p<0.001  ** p<0.01  * p<0.05  ns = nesemnificativ")

    # ── Derived features ──
    print(f"\n{'='*80}")
    print("FEATURES DERIVATE — corelatie cu pretul")
    print(f"{'='*80}")

    # Total content score = words + images*50 + tables*30
    derived = []

    # words * complexity
    vals = np.array([r["words"] * r["layout_complexity"] for r in rows])
    if np.std(vals) > 0:
        c, p = pearsonr(vals, prices)
        derived.append(("words * complexity", c, p))

    # pages * complexity
    vals = np.array([r["pages"] * r["layout_complexity"] for r in rows])
    if np.std(vals) > 0:
        c, p = pearsonr(vals, prices)
        derived.append(("pages * complexity", c, p))

    # content_score = words + images*100 + tables*50
    vals = np.array([r["words"] + r["images"]*100 + r["tables"]*50 for r in rows])
    if np.std(vals) > 0:
        c, p = pearsonr(vals, prices)
        derived.append(("content_score (w+i*100+t*50)", c, p))

    # price per page
    ppg = np.array([r["price"]/r["pages"] if r["pages"]>0 else 0 for r in rows])
    print(f"\nPRET/PAGINA: min={ppg.min():.1f}, max={ppg.max():.1f}, mean={ppg.mean():.1f}, median={np.median(ppg):.1f}")

    # price per word
    ppw = np.array([r["price"]/r["words"] if r["words"]>0 else 0 for r in rows])
    print(f"PRET/CUVANT: min={ppw.min():.4f}, max={ppw.max():.4f}, mean={ppw.mean():.4f}, median={np.median(ppw):.4f}")

    derived.sort(key=lambda x: abs(x[1]), reverse=True)
    print(f"\n{'Feature derivata':<35} {'Pearson r':>12} {'p-value':>12}")
    print(f"{'─'*65}")
    for label, corr, pval in derived:
        sig = "***" if pval < 0.001 else "**" if pval < 0.01 else "*" if pval < 0.05 else "ns"
        print(f"  {label:<33} {corr:>12.4f} {pval:>12.6f} {sig}")

    # ── Best predictor summary ──
    print(f"\n{'='*80}")
    print("CONCLUZIE — Cei mai buni predictori pentru pret:")
    print(f"{'='*80}")

    all_corr = correlations + derived
    all_corr.sort(key=lambda x: abs(x[1]), reverse=True)
    for i, (label, corr, pval) in enumerate(all_corr[:5], 1):
        print(f"  {i}. {label:<35} r={corr:.4f}  p={pval:.6f}")

    print(f"\nAnaliza completa. {len(rows)} fisiere procesate cu succes, {len(errors)} erori.")

if __name__ == "__main__":
    main()
