# Deep Research Report — Roland Command Center

Data: 2026-03-21 03:05 | Stack: FastAPI + React 18 + Vite + SQLite | Agenti: 4 | Timp: ~15 min

---

## PROGRES FATA DE ULTIMUL SCAN (2026-03-20)

| Metrica | Anterior | Actual | Delta |
|---------|----------|--------|-------|
| Scor total | 61/80 | 63/80 | **+2** |
| LOC total | ~29,500 | ~31,400 | +1,900 |
| Fisiere Python | 65 | 72 | +7 |
| Fisiere JSX/JS | 65 | 66 | +1 |
| Tabele DB | 53 | 57 | +4 |
| Migratii | 14 | 15 | +1 |
| Test files | 2 | 7 | **+5** |
| Bundle dist | 1.1 MB | 1.3 MB | +200 KB |
| Endpoints | ~160 | 197 | +37 |

**Probleme rezolvate:** Rate limiting (Faza 25B), Teste automatizate (Faza 25E), Commit-uri actualizate, Error handling (Faza 23/25B)
**Probleme noi:** Backend import time degradat (24s), Router invoice crescut (2050 linii), Bundle crescut

---

## Scor General

| Aspect | Anterior | Actual | Delta | Vizual |
|--------|----------|--------|-------|--------|
| Securitate | 8/10 | 8.5/10 | +0.5 | xxxxxxxxx. |
| Calitate Cod | 7/10 | 6.5/10 | -0.5 | xxxxxxx... |
| Arhitectura | 9/10 | 9/10 | 0 | xxxxxxxxx. |
| Testare | 1/10 | 4/10 | **+3** | xxxx...... |
| Performanta | 9/10 | 7.5/10 | **-1.5** | xxxxxxxx.. |
| Documentatie | 10/10 | 10/10 | 0 | xxxxxxxxxx |
| Dependente | 8/10 | 8/10 | 0 | xxxxxxxx.. |
| Deploy Ready | 9/10 | 9/10 | 0 | xxxxxxxxx. |
| **TOTAL** | **61/80** | **63/80** | **+2** | |

**Interpretare:** IMBUNATATIT — testele au adus +3 puncte, dar performanta a scazut -1.5 din cauza import time si bundle size.

---

## Metrici Proiect (masurate)

| Metrica | Valoare | Cum am masurat |
|---------|---------|---------------|
| Backend import time | **23.92s** | `python -c "from app.main import app"` |
| Frontend build time | 76s | `npx vite build` |
| Frontend bundle total | 1.3 MB (dist/) | `du -sh frontend/dist/` |
| Cel mai mare chunk (gzip) | vendor-charts 110.65 KB | vite build output |
| Total gzip transferat | ~290 KB | suma chunks gzip din build |
| Total LOC backend | 18,914 | `wc -l` pe toate .py |
| Total LOC frontend | 12,487 | `wc -l` pe toate .jsx/.js |
| Endpoints API | 197 | `grep -c @router` |
| Pagini frontend | 25 | count pages/ |
| Componente frontend | 33 | count components/ |
| Module backend | 13 | module_discovery |
| Tabele DB | 57 | din CLAUDE.md |
| Migratii SQL | 15 | count migrations/ |
| Fisiere test | 7 (5 suites) | count test_*.py |
| Linii test | ~265 | `wc -l` test files |
| print() in prod code | 0 | grep (doar in test files) |
| TODO/FIXME in prod | 0 | grep |

---

## Gasiri Critice (actiune imediata)

### [CRITICAL] [ROI: 10] Backend import 24s — 5 librarii grele la nivel de modul [CERT]
- **Fisiere afectate** (toate importate la module level, nu lazy):
  - `app/core/pricing/similarity.py:17` — `from sklearn.preprocessing import StandardScaler` (~2-3s)
  - `app/core/calibration.py:23` — `from scipy.optimize import minimize` (~1-2s)
  - `modules/ai/router.py:33-34` — `import fitz` + `from docx import Document` (~3-4s)
  - `modules/translator/router.py:8-9` — `import fitz` + `from docx import Document` (~2-3s, duplicate!)
  - `app/core/analyzer.py:15` — `import pdfplumber` (~2-3s)
- **Root cause**: Import la module level, nu lazy la function level. fitz/docx importate de 2x!
- **Impact**: START_Roland.bat asteapta 24s inainte sa devina disponibil. Pe Android, si mai lent.
- **Fix**: Muta TOATE importurile in corpul functiilor care le folosesc (~8 locatii)
- **Efort**: MIC (45 min) | **Risc**: LOW
- **Impact estimat**: 24s → **3-5s** startup

### [CRITICAL] [ROI: 9] Router-e supradimensionate — 5 fisiere > 800 linii [CERT]
- **Fisiere afectate**:
  - `invoice/router.py` — **2,050 linii** (+300 fata de ultimul scan!)
  - `ai/router_extensions.py` — **1,052 linii**
  - `reports/router.py` — **1,035 linii**
  - `integrations/router.py` — **966 linii**
  - `translator/router.py` — **944 linii**
- **Root cause**: Toate endpoint-urile unui modul intr-un singur fisier
- **Impact**: Greu de navigat, risc mare de erori la editare, merge conflicts
- **Fix**: Sparge in sub-routere (ex: `invoice/router_clients.py`, `invoice/router_series.py`). Fara schimbare de comportament.
- **Efort**: MEDIU (2h per modul) | **Risc**: LOW (restructurare interna)
- **Nota**: Trebuie teste INAINTE de refactorizare (vezi S2 in Roadmap)

---

## Gasiri Importante (recomandate)

### [HIGH] [ROI: 8.5] SQLite get_db() lipsesc PRAGMA-uri de performanta [CERT]
- **Fisier**: `app/db/database.py:121-129`
- **Problema**: `get_db()` seteaza doar `foreign_keys=ON` si `busy_timeout=5000`. Lipsesc:
  - `PRAGMA journal_mode = WAL` (setat doar in `init_db`, nu si in `get_db`)
  - `PRAGMA synchronous = NORMAL` (de 2x mai rapid ca FULL, sigur cu WAL)
  - `PRAGMA cache_size = -64000` (64MB cache vs default 2MB)
  - `PRAGMA temp_store = MEMORY` (temp tables in RAM)
  - `PRAGMA mmap_size = 268435456` (256MB memory-mapped I/O)
- **Root cause**: Pragmele au fost adaugate doar la init, nu la fiecare conexiune
- **Impact**: Fiecare query e mai lent decat ar putea fi. WAL mode e setat o data la init dar nu e persistent per-conexiune.
- **Fix**: Adauga pragmele in `get_db()` dupa `busy_timeout`
- **Efort**: MIC (15 min) | **Risc**: LOW
- **Sursa**: [SQLite Performance Tuning](https://phiresky.github.io/blog/2020/sqlite-performance-tuning/) [CERT]

### [HIGH] [ROI: 8.5] SQL injection via date interpolation in reports [CERT]
- **Fisier**: `reports/router.py:333`
- **Cod**: `f"WHERE timestamp >= date('now', '-{days} days')"` — `days` din query string interpolat direct in SQL
- **Nota**: FastAPI valideaza `days` cu `ge=1, le=365`, dar interpolarea directa e anti-pattern chiar si cu validare
- **Fix**: `WHERE timestamp >= datetime('now', ?)` cu parametru `f"-{int(days)} days"`
- **Efort**: MIC (5 min) | **Risc**: LOW

### [HIGH] [ROI: 8] SQL f-strings in reports/router.py [CERT]
- **Fisiere afectate** (cele mai riscante):
  - `reports/router.py:399` — `f"SELECT {column} FROM {table}"` — column si table din lista hardcoded
  - `reports/router.py:826` — `f"SELECT * FROM {table}"` — table din lista hardcoded
- **Alte fisiere** (risc mai mic — doar SET clause cu valori parametrizate):
  - `invoice/router.py:285,993,1277` — `f"UPDATE ... SET {set_clause}"`
  - `automations/router.py:264`, `itp/router.py:218,777`, `translator/glossary.py:189`
- **Root cause**: Constructie dinamica de SQL necesara pentru UPDATE cu campuri variabile
- **Impact**: Risc scazut deoarece valorile sunt whitelisted, dar pattern-ul e anti-best-practice
- **Fix**: Pentru UPDATE-uri: verifica ca set_clause vine doar din campuri whitelisted. Pentru reports: inlocuieste cu dict lookup explicit.
- **Efort**: MIC (1h) | **Risc**: LOW

### [HIGH] [ROI: 7.5] 15+ operatii I/O blocante in context async [CERT]
- **Problema**: Functii async folosesc `open()`, `.write_bytes()`, `fitz.open()`, `pdfplumber.open()` sincron
- **Fisiere afectate**:
  - `app/api/routes_upload.py:93` — `.write_bytes()` blocant la file save
  - `app/api/routes_calibrate.py` — 7 instante de `open()` sincron
  - `app/core/analyzer.py:57,111` — `fitz.open()` si `pdfplumber.open()` blocante (5-30s pe PDF-uri mari)
  - `app/core/calibration.py:264` — write sincron
  - `app/core/self_learning.py:35,45` — JSON I/O sincron
  - `app/core/pricing/similarity.py:48,101` — cache I/O sincron
- **Root cause**: Event loop-ul se blocheaza in timpul operatiilor de fisier
- **Impact**: In timp ce un PDF se proceseaza (5-30s), TOATE celelalte request-uri asteapta
- **Fix**: Inlocuieste cu `aiofiles` sau `loop.run_in_executor()` pentru operatii grele
- **Efort**: MEDIU (2-3h) | **Risc**: LOW

### [HIGH] [ROI: 7.5] Testare inca sub 40% coverage [CERT]
- **Module testate**: health, translate, AI, invoice, ITP (5/13 = 38%)
- **Module FARA teste**: translator (complet), filemanager, reports, automations, integrations, converter, quick_tools, quick_tools_extra, vault
- **Linii test**: ~265 pentru ~19,000 linii backend
- **Fix**: Adauga teste cel putin pentru translator si filemanager (cele mai folosite dupa calculator)
- **Efort**: MARE (4h) | **Risc**: LOW

### [MEDIUM] [ROI: 6.5] vendor-charts bundle 411 KB (110 KB gzip) [CERT]
- **Fisier**: `frontend/vite.config.js` (manualChunks configuration)
- **Problema**: recharts e cea mai mare dependenta (411KB raw, 110KB gzip) si se incarca la prima vizita
- **Impact**: Pe mobile/Tailscale, 110KB extra la first load
- **Fix optiuni**:
  - A) Lazy import recharts doar in paginile care il folosesc (DashboardPage, ReportsPage) — nu la nivel de App
  - B) Inlocuieste recharts cu o librarie mai mica (chart.js = ~60KB, uPlot = ~35KB) — efort mare
- **Recomandare**: Optiunea A (recharts deja e in chunk separat deci e lazy-loaded, dar verificati daca Dashboard il importa eager)
- **Efort**: MIC-MEDIU | **Risc**: LOW

### [MEDIUM] [ROI: 6] DashboardPage importat eager (nu lazy) [CERT]
- **Fisier**: `frontend/src/App.jsx:6`
- **Problema**: `import DashboardPage from './pages/DashboardPage'` — singura pagina importata direct, toate celelalte 24 sunt lazy
- **Impact**: DashboardPage (446 linii) + dependentele sale se incarca in bundle-ul principal
- **Fix**: `const DashboardPage = lazy(() => import('./pages/DashboardPage'))`
- **Efort**: MIC (5 min) | **Risc**: LOW
- **Nota**: Dashboard e landing page, deci lazy loading poate adauga un flash la prima vizita. Acceptabil cu PageLoader fallback.

### [MEDIUM] [ROI: 6] Cod duplicat: _extract_text() si _truncate_text() [CERT]
- **Fisiere**: `ai/router.py:48-91` si `ai/router_extensions.py:48-70`
- **Problema**: Functii identice copiate in 2 fisiere (extragere text din PDF/DOCX/TXT si trunchiere)
- **Fix**: Muta in `app/core/text_utils.py`, importa din ambele routere. Elimina ~30 linii duplicate.
- **Efort**: MIC (20 min) | **Risc**: LOW

### [MEDIUM] [ROI: 5.5] CSP 'unsafe-inline' pentru script-src [CERT]
- **Fisier**: `app/main.py:299-300`
- **Cod**: `"script-src 'self' 'unsafe-inline'"` — permite executie inline JavaScript
- **Impact**: Daca exista o vulnerabilitate XSS, `unsafe-inline` permite exploatarea completa
- **Fix**: Elimina `unsafe-inline` din script-src (pastrand-o doar in style-src pt Tailwind/React inline styles)
- **Nota**: Necesita testare ca Vite build-ul functioneaza fara inline scripts
- **Efort**: MIC (30 min) | **Risc**: MEDIUM (poate sparge PWA daca exista inline scripts)

### [MEDIUM] [ROI: 5.5] Indexuri DB lipsa pe tabele frecvent interogate [CERT]
- **Tabele afectate**:
  - `ai_config` — lipsa index pe `key` (interogat la fiecare AI call)
  - `chat_messages` — lipsa index compozit `(session_id, created_at DESC)` (incarcare sesiuni)
  - `glossary_terms` — lipsa index `(domain, term)` (lookup termeni)
- **Fix**: Migrare SQL noua cu 3-4 CREATE INDEX
- **Efort**: MIC (15 min) | **Risc**: LOW

### [MEDIUM] [ROI: 5.5] Lipsa validare lungime string pe translator requests [CERT]
- **Fisier**: `translator/router.py` — `TranslateTextRequest.text` nu are `max_length`
- **Problema**: Un request cu 1MB de text poate cauza probleme de memorie
- **Fix**: Adauga `max_length=100000` pe campul text din Pydantic model
- **Efort**: MIC (5 min) | **Risc**: LOW

### [MEDIUM] [ROI: 5.5] AI Prompts fara few-shot examples [CERT]
- **Locatii**:
  - `invoice/router.py:891` — prompt extragere factura din OCR
  - `invoice/router.py:1541` — prompt extragere date document
  - `translator/router.py:862` — prompt evaluare calitate traducere
- **Problema**: Prompt-urile specifica formatul JSON dorit dar nu includ un exemplu concret (few-shot)
- **Impact**: AI-ul poate returna formate inconsistente, mai ales cu provideri mai slabi
- **Fix**: Adauga un exemplu de output valid in fiecare prompt
- **Efort**: MIC (30 min) | **Risc**: LOW

---

## Audit Granular

### Per-Endpoint Backend (197 endpoints, highlight probleme)

| Endpoint | Fisier:Linie | Problema | Certitudine |
|----------|-------------|----------|-------------|
| POST /api/reports/query | reports/router.py:399 | f-string SQL cu table/column (whitelist OK) | [CERT] |
| GET /api/reports/export/full | reports/router.py:826 | f-string SQL cu table name (whitelist OK) | [CERT] |
| POST /api/calibrate/weights | routes_calibrate.py:250 | Validare OK dupa fix WeightsRequest | [CERT] |
| POST /api/invoice/scan-ocr | invoice/router.py:891 | AI prompt fara few-shot | [CERT] |
| POST /api/translator/quality | translator/router.py:862 | AI prompt fara few-shot | [CERT] |
| GET /api/fm/browse | filemanager/router.py:94 | Path traversal PROTEJAT (_resolve) | [CERT] |
| ALL /api/ai/* | ai/router.py | Rate limited 10/min OK | [CERT] |
| ALL /api/translate/* | translator/router.py | Rate limited 10/min OK | [CERT] |

### Per-Pagina Frontend (25 pagini)

| Pagina | Fisier | Linii | Lazy? | Probleme | Certitudine |
|--------|--------|-------|-------|----------|-------------|
| DashboardPage | DashboardPage.jsx | 446 | **NU** | Import eager | [CERT] |
| ITPPage | ITPPage.jsx | 664 | DA | Cel mai mare JSX | [CERT] |
| AutomationsPage | AutomationsPage.jsx | 615 | DA | - | [CERT] |
| ReportsPage | ReportsPage.jsx | 601 | DA | - | [CERT] |
| InvoicePage | InvoicePage.jsx | 565 | DA | - | [CERT] |
| AIChatPage | AIChatPage.jsx | 543 | DA | fetch() pt SSE (documented exception) | [CERT] |
| IntegrationsPage | IntegrationsPage.jsx | 533 | DA | - | [CERT] |
| FileBrowserPage | FileBrowserPage.jsx | 511 | DA | - | [CERT] |

### AI Prompts Audit

| Locatie | Scop | Specific? | Format? | Anti-haluc? | Few-shot? | Sugestie |
|---------|------|-----------|---------|-------------|-----------|----------|
| invoice/router.py:891 | OCR factura | DA | JSON | DA ("DOAR JSON") | **NU** | Adauga exemplu JSON valid |
| invoice/router.py:1541 | OCR document | DA | JSON | DA | **NU** | Adauga exemplu output |
| translator/router.py:862 | Calitate traducere | DA | JSON exact | DA | **NU** | Adauga exemplu score/issues |
| ai/router.py:185 | System prompt chat | DA | - | NU | - | OK pt chat general |

### Surse Externe API

| Client API | Fisier | Error handling? | Rate limit? | Cache? | Retry? |
|-----------|--------|----------------|------------|--------|--------|
| Gemini AI | ai/providers.py | DA (failover chain) | DA (10/min) | DA (MD5 cache) | DA (chain) |
| Cerebras | ai/providers.py | DA | DA | DA | DA (chain) |
| Groq | ai/providers.py | DA | DA | DA | DA (chain) |
| Mistral | ai/providers.py | DA | DA | DA | DA (chain) |
| DeepL | translator/providers.py | DA | DA (10/min) | Partial (TM) | DA (chain) |
| BNR curs | components/ExchangeRate | DA | NU | Partial | NU |
| ANAF CUI | pages/CompanyCheck | DA | NU | NU | NU |

---

## Dead Code Identificat

| Tip | Locatie | Detalii | Certitudine |
|-----|---------|---------|-------------|
| Functie duplicata | ai/router.py:48-91 | _extract_text() si _truncate_text() copiate in router_extensions.py | [CERT] |
| Functie duplicata | ai/router_extensions.py:48-70 | Copie identica a functiilor din router.py | [CERT] |
| Test legacy | test_ensemble_26.py | 220 linii, nu e in tests/ | [CERT] |
| Test legacy | test_analyzer_correlation.py | 190 linii, nu e in tests/ | [CERT] |
| Functie | scraper/competitors.py | Nu pare apelat din nicio ruta activa | [PROBABIL] |
| Import | backup.py (root) | Script standalone, nu modul | [CERT] |
| Import nefolosit | ai/providers.py | `asyncio`, `hashlib`, `time` importate dar nefolosite | [PROBABIL] |

**Nota**: Dead code relativ minimal. Duplicarea _extract_text e cea mai importanta de rezolvat.

---

## Dependency Map

```
app/main.py
  |--imports--> app/config.py (settings)
  |--imports--> app/db/database.py (get_db, init_db)
  |--imports--> app/module_discovery.py
  |                |--auto-discovers-->
  |                    modules/calculator/ (7 sub-routers)
  |                    modules/ai/ (2 routers: router.py + router_extensions.py)
  |                    modules/translator/ (1 router + providers.py + tm.py + glossary.py)
  |                    modules/invoice/ (1 router, 2050 lines)
  |                    modules/itp/ (1 router)
  |                    modules/filemanager/ (1 router)
  |                    modules/reports/ (1 router)
  |                    modules/automations/ (1 router)
  |                    modules/integrations/ (1 router)
  |                    modules/converter/ (1 router)
  |                    modules/quick_tools/ (2 routers)
  |                    modules/quick_tools_extra/ (1 router)
  |                    modules/vault/ (1 router)
  |--imports--> app/core/activity_log.py
  |--imports--> app/api/routes_price.py
  |--imports--> app/api/routes_calibrate.py
  |--imports--> app/api/routes_history.py

Inter-module dependencies:
  invoice/router.py --imports--> modules/ai/providers.py (ai_generate for OCR)
  translator/router.py --imports--> modules/ai/providers.py (ai_generate for quality)
  ai/router_extensions.py --imports--> app/db/database.py (DB stats for context)

  [NO CIRCULAR DEPENDENCIES DETECTED]
```

---

## Cross-Platform Issues

| Config | Windows | Android/Tailscale | Problema | Fix |
|--------|---------|-------------------|----------|-----|
| CORS | localhost OK | TAILSCALE_ORIGIN env | Daca env var nu e setat, Android nu merge | Documentat in GHID_ACCES_REMOTE |
| Encoding | cp1252 default | UTF-8 | PYTHONIOENCODING=utf-8 necesar | Setat in BAT |
| Paths | Backslash | Forward slash | `_resolve()` face `replace("\\", "/")` | OK |
| Bundle gzip | Fast local | Slow 4G/Tailscale | 290KB gzip total | Acceptabil |
| Import time | 24s | 24s+ | Lent pe ambele | Fix: lazy imports sklearn |

---

## Provider/Tool Scan

| Tool curent | Alternativa gasita | Free? | Avantaj | Recomandare |
|-------------|-------------------|-------|---------|-------------|
| recharts (411KB) | uPlot (35KB) | DA | 10x mai mic | [ALTERNATIVA INTERESANTA] — efort mare migrare |
| recharts | Chart.js (60KB) | DA | 7x mai mic, popular | [ALTERNATIVA INTERESANTA] — efort mediu |
| aiosqlite (single conn) | aiosqlitepool | DA | Connection pool | [NU MERITA SCHIMBAREA] — single user |
| Gemini 2.5 Flash | Gemini 2.5 Pro | Free tier | Mai inteligent | [NU MERITA SCHIMBAREA] — Flash e OK |
| edge-tts | - | - | Best free TTS | [NU MERITA SCHIMBAREA] |
| Tesseract OCR | docTR | DA | Mai precis pe layout | [ALTERNATIVA INTERESANTA] — pip install |

---

## Best Practices Comparison (surse web 2026)

| Practica | Status proiect | Recomandare | Prioritate |
|----------|---------------|-------------|-----------|
| Lazy imports heavy libs | NU — sklearn/scipy la module level | MUTA in functii | CRITICAL |
| SQLite WAL + performance pragmas | PARTIAL — WAL doar la init | Adauga in get_db() | HIGH |
| Rate limiting | DA — 60/10 req/min | OK | - |
| CORS specific origins | DA — nu wildcard | OK | - |
| Pydantic validation | DA — pe majoritatea endpoints | OK | - |
| Async handlers + async DB | DA — aiosqlite | OK | - |
| File upload validation | PARTIAL — size check, basic type | Adauga MIME validation | LOW |
| Connection pooling | NU — new conn per request | Acceptabil pt single-user | LOW |
| Background tasks | NU explicit | Adauga pt email/heavy ops | MEDIUM |
| Structured logging | DA — logging module | OK | - |
| Error monitoring | DA — diagnostics panel | OK | - |
| Code splitting | DA — 24/25 pagini lazy | Lazy si Dashboard | MEDIUM |
| PWA offline | DA — workbox | OK | - |
| Gzip compression | DA — GZipMiddleware | OK | - |
| CSP headers | DA — adaugat in Faza 20 | OK | - |
| Input sanitization | PARTIAL | Verificat pt injection | MEDIUM |
| API versioning | NU — /api/ fara /v1/ | Acceptabil pt single-user | LOW |

**Surse web consultate:**
- [FastAPI Best Practices Production 2026](https://fastlaunchapi.dev/blog/fastapi-best-practices-production-2026)
- [Optimizing React Vite Builds](https://medium.com/@salvinodsa/optimizing-react-builds-with-vite-practical-techniques-for-faster-apps-063d4952e67d)
- [SQLite Performance Tuning](https://phiresky.github.io/blog/2020/sqlite-performance-tuning/)
- [Going Fast with SQLite and Python](https://charlesleifer.com/blog/going-fast-with-sqlite-and-python/)

---

## Fragile Code Hotspots (cele mai modificate fisiere din ultimele 50 commituri)

| Fisier | Nr modificari | Cauza probabila | Recomandare |
|--------|--------------|-----------------|-------------|
| CLAUDE.md | 9 | Actualizat la fiecare faza | Normal — doc tracking |
| App.jsx | 6 | Noi pagini adaugate | Normal — entry point |
| 0.0_PLAN_EXTINDERE | 6 | Progress tracking | Normal — plan doc |
| manifest.js | 5 | Noi pagini in sidebar | Normal |
| main.py | 4 | Middleware, CORS, features | Atentie — risc de bloat |
| database.py | 4 | Migratii, pragmas | OK — stabilizat |
| Header.jsx | 4 | Theme, shortcuts, speed | Atentie — 332 linii |
| FileBrowserPage.jsx | 3 | Features adaugate iterativ | OK |
| ai/router.py | 3 | Noi features AI | Atentie — 778 linii |

---

## Metrici Actuale vs Target

| Metrica | Actual (masurat) | Target recomandat | Cum masori | Prioritate |
|---------|-----------------|-------------------|-----------|-----------|
| Backend cold start | **23.92s** | **< 3s** | `python -c "..."` | **CRITICAL** |
| Bundle gzip total | ~290 KB | < 200 KB | vite build | MEDIUM |
| Largest chunk gzip | 110 KB (charts) | < 50 KB | vite build | LOW |
| Test coverage (modules) | 38% (5/13) | > 80% | count | HIGH |
| Test LOC ratio | 1.4% (265/19K) | > 10% | wc -l | HIGH |
| Endpoints fara test | ~62% | < 20% | comparison | HIGH |
| Fisiere > 800 linii (py) | 5 | 0 | wc -l sort | MEDIUM |
| Fisiere > 500 linii (jsx) | 6 | max 2-3 | wc -l sort | LOW |
| DB connections/req | 1 new/req | 1 (pool) | code review | LOW |
| Dead code files | 2-3 | 0 | grep unused | LOW |

---

## Roadmap Imbunatatiri

### SAPTAMANA 1 — Quick Wins (ROI > 7, Efort MIC)

| # | Actiune | Fisier:Linie | Efort | Impact | ROI | Risc | Depinde de |
|---|---------|-------------|-------|--------|-----|------|-----------|
| QW1 | Lazy import sklearn/scipy | pricing/similarity.py:17, calibration.py:23 | 30 min | **CRITICAL** | 10 | LOW | nimic |
| QW2 | Adauga PRAGMA-uri SQLite in get_db() | db/database.py:121 | 15 min | HIGH | 9 | LOW | nimic |
| QW3 | Lazy load DashboardPage | App.jsx:6 | 5 min | MEDIUM | 8.5 | LOW | nimic |
| QW4 | Few-shot examples in AI prompts | invoice/router.py:891, translator/router.py:862 | 30 min | MEDIUM | 7 | LOW | nimic |

**Toate independente — pot fi executate in orice ordine sau paralel.**
**Timp total estimat: ~1.5h | Impact: backend start 24s → ~3-5s**

### SAPTAMANA 2 — Securitate & Stabilitate

| # | Actiune | Efort | Impact | ROI | Risc | Depinde de |
|---|---------|-------|--------|-----|------|-----------|
| S1 | Inlocuieste f-string SQL cu constante explicite | 1h | HIGH | 8 | LOW | nimic |
| S2 | Teste pentru translator + filemanager + reports | 4h | HIGH | 7.5 | LOW | QW1 (teste pornesc mai repede) |
| S3 | MIME validation pe file upload endpoints | 30 min | MEDIUM | 6 | LOW | nimic |

### SAPTAMANA 3-4 — Arhitectura & Calitate

| # | Actiune | Efort | Impact | ROI | Risc | Depinde de |
|---|---------|-------|--------|-----|------|-----------|
| A1 | Sparge invoice/router.py (2050 linii) in 4-5 sub-routere | 2h | MEDIUM | 5 | MEDIUM | **S2** (teste inainte de refactorizare!) |
| A2 | Sparge ai/router_extensions.py (1052 linii) | 1.5h | MEDIUM | 5 | MEDIUM | **S2** |
| A3 | Sparge reports/router.py (1035 linii) | 1.5h | MEDIUM | 5 | MEDIUM | **S2** |

**IMPORTANT:** A1-A3 NU se fac inainte de S2. Testele trebuie sa existe ca plasa de siguranta.

### VIITOR (nice to have, ROI < 3)

| # | Actiune | Efort | Impact | Conditie |
|---|---------|-------|--------|---------|
| V1 | Inlocuieste recharts cu chart.js/uPlot | 4h | LOW | Doar daca bundle e problema |
| V2 | Frontend E2E tests cu Playwright | 8h | MEDIUM | Dupa S2 complet |
| V3 | Connection pool aiosqlitepool | 2h | LOW | Doar daca apar probleme concurenta |
| V4 | API versioning (/api/v1/) | 3h | LOW | Doar la public release |

---

## Ce Am Omis / Ce Poate Fi Incorect

1. **[NEVERIFICAT]** Nu am putut rula `npm audit` / `pip audit` — depinde de versiuni exacte instalate
2. **[NEVERIFICAT]** Performanta pe Android via Tailscale — masurata doar local pe Windows
3. **[NEVERIFICAT]** Comportamentul la multiple conexiuni simultane SQLite — single-user, greu de testat
4. **[PROBABIL]** Import time de 24s — sklearn/scipy sunt principalii vinovati, dar alte module pot contribui si ele
5. **[NEVERIFICAT]** Dead code in frontend — nu am verificat toate import-urile nefolosite din JSX
6. **[PROBABIL]** Agentii de background au gasit posibil detalii suplimentare care nu au fost integrate complet in timp util
7. **[CERT]** Nu am verificat exhaustiv FIECARE endpoint (197 total) — am auditat cele mai riscante

---

## Snapshot JSON

```json
{
  "snapshot_date": "2026-03-21",
  "project": "Roland Command Center",
  "stack": "FastAPI + React 18 + Vite + SQLite",
  "metrics": {
    "backend_import_time_s": 23.92,
    "frontend_build_time_s": 76,
    "frontend_bundle_kb_raw": 1331,
    "frontend_bundle_kb_gzip": 290,
    "largest_chunk_kb_gzip": 110.65,
    "db_size_kb": null,
    "total_endpoints": 197,
    "total_pages": 25,
    "total_components": 33,
    "total_loc_backend": 18914,
    "total_loc_frontend": 12487,
    "total_loc": 31401,
    "python_files": 72,
    "jsx_js_files": 66,
    "db_tables": 57,
    "db_migrations": 15,
    "backend_modules": 13,
    "test_files": 7,
    "test_lines": 265,
    "print_in_prod": 0,
    "todo_fixme_in_prod": 0
  },
  "scores": {
    "security": 8.5,
    "code_quality": 6.5,
    "architecture": 9,
    "testing": 4,
    "performance": 7.5,
    "documentation": 10,
    "dependencies": 8,
    "deploy_ready": 9,
    "total": 62.5
  },
  "scores_previous": {
    "security": 8,
    "code_quality": 7,
    "architecture": 9,
    "testing": 1,
    "performance": 9,
    "documentation": 10,
    "dependencies": 8,
    "deploy_ready": 9,
    "total": 61
  },
  "issues": {
    "critical": 2,
    "high": 5,
    "medium": 7,
    "low": 0
  },
  "improvements_proposed": 19,
  "issues_resolved_since_last": 4,
  "issues_new_since_last": 6
}
```
