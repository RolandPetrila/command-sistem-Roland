# ROADMAP IMBUNATATIRI — Deep Research 2026-03-20

## SAPTAMANA 1 — Quick Wins (ROI > 7, Efort MIC)

| # | Actiune | Efort | Impact | Risc |
|---|---------|-------|--------|------|
| 1 | Git commit curent (41 fisiere necommitted) | 5 min | HIGH | LOW |
| 2 | Verifica SQL whitelist in `reports/router.py:399` — `column`/`table` nu trebuie sa vina din user input | 30 min | HIGH | LOW |
| 3 | Fix catch blocks goale in 5 componente (CalibrationPanel, ActivityLog, ExchangeRateCard, FileBrowser, Header) | 30 min | MEDIUM | LOW |
| 4 | Adauga "Respond ONLY in {target_lang}" la prompt-ul AI translate | 5 min | MEDIUM | LOW |
| 5 | Sterge/curata fisierele legacy test (`test_analyzer_correlation.py`, `test_ensemble_26.py`) | 5 min | LOW | LOW |

**Dependente**: Niciuna — toate independente

## SAPTAMANA 2 — Securitate & Stabilitate

| # | Actiune | Efort | Impact | Risc |
|---|---------|-------|--------|------|
| 6 | Adauga `slowapi` rate limiting (60 req/min global, 10/min pe AI/translate) | 1h | HIGH | LOW |
| 7 | Adauga 5 teste pytest minimal (health, translate, ai_generate, invoice CRUD, itp) | 4h | CRITICAL | LOW |
| 8 | Configureaza GitHub branch protection pe `main` | 15 min | MEDIUM | LOW |

**Dependente**: #1 completat (commit inainte de orice)

## SAPTAMANA 3-4 — Calitate & Arhitectura

| # | Actiune | Efort | Impact | Risc |
|---|---------|-------|--------|------|
| 9 | Sparge `invoice/router.py` (1751 linii) in 3-4 sub-routere | 2h | MEDIUM | MEDIUM |
| 10 | Sparge `ai/router_extensions.py` (1052 linii) in sub-routere | 1.5h | MEDIUM | MEDIUM |
| 11 | Adauga traducere tabele DOCX in translator (doc.tables iteration) | 2h | MEDIUM | LOW |
| 12 | Evalueaza Gemini 2.5 Flash-Lite ca provider AI secundar | 1h | MEDIUM | LOW |

**Dependente**: #7 completat (teste inainte de refactorizari)

## VIITOR (nice to have, ROI < 3)

| # | Actiune | Efort | Impact | Nota |
|---|---------|-------|--------|------|
| 13 | Evalueaza PaddleOCR ca inlocuitor Tesseract+EasyOCR | 4h | LOW | Doar daca OCR actual e insuficient |
| 14 | Optimizeaza recharts bundle (402KB) | 2h | LOW | Gzip reduce la 110KB — nu merita acum |
| 15 | Adauga keyboard shortcuts info pe Android (tooltip/help) | 1h | LOW | Niche |
