# Roadmap Imbunatatiri --- Roland Command Center

Data: 2026-03-21 | Sursa: Deep Research v2 (6 agenti) | Scor actual: 58.5/80

---

## Prioritizare Completa (sortat dupa ROI)

| # | Actiune | Fisier/Comanda | Impact | Efort | ROI | Risc | Depinde de |
|---|---------|---------------|--------|-------|-----|------|-----------|
| QW1 | Upgrade PyMuPDF >=1.26.7 | `pip install PyMuPDF>=1.26.7` | CRITICAL | 5min | 10 | LOW | - |
| QW2 | Upgrade cryptography + certifi | `pip install --upgrade cryptography certifi` | HIGH | 10min | 10 | LOW | - |
| QW3 | Lazy imports (6 fisiere) | analyzer.py, calibration.py, similarity.py, translator/router.py, ai/router.py, ai/router_extensions.py | CRITICAL | 1h | 10 | LOW | - |
| QW4 | Adauga httpx in requirements.txt | `echo "httpx>=0.25.0" >> requirements.txt` | HIGH | 5min | 10 | LOW | - |
| QW5 | Adauga caching (lru_cache) | BNR curs, ANAF CUI, calibration data, settings | HIGH | 30min | 8 | LOW | - |
| QW6 | Fix N+1 query automations | automations/router.py:~125 --- LEFT JOIN in loc de loop | HIGH | 30min | 8 | LOW | - |
| QW7 | Parametrizeaza `days` in SQL | reports/router.py:333 --- `?` in loc de f-string | MEDIUM | 10min | 7 | LOW | - |
| QW8 | Extrage _extract_text() partajat | Creeaza app/core/file_utils.py, sterge 3 duplicari | MEDIUM | 45min | 7 | LOW | - |
| QW9 | Empty catch cleanup + dead import | ~20 catch-uri goale + difflib in router_extensions.py:25 | LOW | 30min | 3 | LOW | - |
| T1 | Teste converter+fm+reports+vault | 40+ teste noi pytest (include vault critical) | HIGH | 4-5h | 7 | LOW | QW1 |
| T2 | pip audit + pytest in requirements.txt | Adauga pytest, httpx, pytest-asyncio in requirements | MEDIUM | 30min | 6 | LOW | QW1,QW2 |
| S1 | Imbunatatire AI prompts invoice | Expand system prompts: "return null for uncertain", confidence level | HIGH | 1h | 7 | LOW | - |
| S2 | Validare target_lang | translator/providers.py:219 --- `assert target_lang in ["ro","en"]` | MEDIUM | 10min | 6 | LOW | - |
| S3 | asyncio.Lock pe global state | _prompt_cache, _monitor_tasks, _bnr_cache | MEDIUM | 1h | 5 | LOW | - |
| R1 | Sparge invoice/router.py | 2050 -> 4 fisiere | MEDIUM | 2-3h | 5 | MEDIUM | T1 |
| R2 | Sparge ai/router_extensions | 1052 -> 2-3 fisiere | MEDIUM | 2h | 5 | MEDIUM | T1 |
| R3 | Sparge reports/router.py | 1035 -> 3 fisiere | MEDIUM | 2h | 5 | MEDIUM | T1 |
| R4 | Sterge componente nefolosite | ActivityLog.jsx, StatsCards.jsx, FilePreview.jsx | LOW | 10min | 4 | LOW | - |
| R5 | useMemo/useCallback DashboardPage | ActivityChart + fetchAll | LOW | 15min | 3 | LOW | - |
| V1 | Recharts 2->3 upgrade | Frontend bundle reduction | MEDIUM | 2-3h | 3 | MEDIUM | - |
| V2 | Vitest frontend tests | Setup + primele teste | MEDIUM | 4h+ | 2 | LOW | T1 |
| V3 | CORS restrict methods | main.py:147 --- ["GET","POST","PUT","DELETE","OPTIONS"] | LOW | 5min | 2 | LOW | - |
| V4 | React 18->19 | Major ecosystem upgrade | LOW | 8h+ | 1 | HIGH | V1 |

---

## Diagrama Dependinte

```
SAPTAMANA 1 --- Quick Wins (toate independente, parallelizabile):
  QW1 (PyMuPDF)      QW2 (security)      QW3 (lazy imports)
  QW4 (httpx req)     QW5 (caching)       QW6 (N+1 fix)
  QW7 (SQL param)     QW8 (_extract_text)  QW9 (cleanup)
       |                   |
       v                   v
SAPTAMANA 2 --- Securitate & Teste:
  T1 (40+ teste noi)     T2 (pip audit + req)
  S1 (AI prompts)        S2 (target_lang)
  S3 (asyncio.Lock)
       |
       v
SAPTAMANA 3-4 --- Refactorizare (DOAR dupa teste!):
  R1 (invoice 2050->4x)  R2 (ai ext 1052->3x)  R3 (reports 1035->3x)
  R4 (sterge dead comp)  R5 (useMemo dashboard)

VIITOR (nice-to-have):
  V1 (recharts 3)  V2 (vitest)  V3 (CORS)  V4 (React 19)
```

**REGULA**: Refactorizare R1-R3 DOAR dupa ce T1 adauga teste. Nu refactoriza fara safety net!

---

## Scor Estimat dupa Implementare

| Dupa ce etapa | Scor estimat | Delta | Timp cumulat |
|---------------|-------------|-------|-------------|
| Actual | 58.5/80 | - | - |
| QW1-QW4 (upgrades + httpx) | 62/80 | +3.5 | 20 min |
| QW3 (lazy imports) | 64/80 | +2 | 1h 20min |
| QW5-QW6 (caching + N+1) | 65.5/80 | +1.5 | 2h 20min |
| QW7-QW9 (cleanup) | 66/80 | +0.5 | 3h 30min |
| S1-S3 (securitate prompts) | 67.5/80 | +1.5 | 5h 40min |
| T1-T2 (teste) | 71/80 | +3.5 | 10h |
| R1-R5 (refactorizari) | 73/80 | +2 | 17h |
| **Total posibil** | **73/80** | **+14.5** | ~17h total |

---

## Rezumat Issues

| Severitate | Count | Exemple cheie |
|-----------|-------|-------------|
| CRITICAL | 2 | CVE-2026-3029 PyMuPDF, Import 33s |
| HIGH | 9 | N+1 query, httpx missing, _extract_text 3x, testing 8%, invoice 2050 LOC, AI prompts generic |
| MEDIUM | 8 | Global state no lock, target_lang injection, useMemo, recharts bundle |
| LOW | 5 | Dead import, dead components, CORS methods, catch cleanup, autoprefixer |
| **TOTAL** | **24** | |
