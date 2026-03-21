# TODO — Plan Implementare Roland Command Center

Data: 2026-03-21 | Sursa: Deep Research v1 (63/80) + v2 (58.5/80) consolidat
Scor actual estimat: ~74/80 | Toate fazele DONE

---

## Istoric — Faze Completate (2026-03-21)

| Faza | Descriere | Status |
|------|-----------|--------|
| Faza 25A (ex-A) | Provideri AI: Gemini 2.5-flash, +Cerebras, +Mistral, .env | DONE |
| Faza 25B (ex-D) | Securitate: SQL whitelist OK, catch blocks, rate limiting | DONE |
| Faza 25C (ex-C) | Fix cerinte: interceptor, batch PDF, DOCX tables, timeout 300s | DONE |
| Faza 25D (ex-B) | Speed test: Mbps + latency in header, auto-refresh 60s | DONE |
| Faza 25E (ex-E) | Testare fundament: pytest + 18 teste, toate PASSED | DONE |
| Faza F | Cross-module: voice input, prompt templates, serii facturi, etc. | DONE |
| **Faza 26A** | Security & Upgrades: PyMuPDF CVE fix, cryptography, httpx, pytest | **DONE** |
| **Faza 26B** | Performance: Lazy imports (5x cold start), BNR/ANAF/calibration cache, SQLite PRAGMA | **DONE** |
| **Faza 26C** | Code Quality: N+1 fix, SQL parameterized, shared file_utils, lang validation, asyncio.Lock | **DONE** |
| **Faza 26D** | AI Prompts: anti-hallucination, confidence scores, few-shot, null for uncertain | **DONE** |
| **Faza 26E** | Testing: 68 teste (50 noi), toate PASSED, 8 module acoperite | **DONE** |
| **Faza 26F** | Refactorizare: 3 fisiere mari (4137 LOC) -> 11 fisiere sub 500 LOC | **DONE** |
| **Faza 26G** | Hardening: CORS restrict, DB indexes (8 noi), blocking I/O -> async (5 cazuri) | **DONE** |

---

## Detalii Implementare Faze 26A-26G

### Faza 26A — Security & Upgrades (DONE)
- PyMuPDF >=1.26.7 (CVE-2026-3029 fix)
- cryptography >=44.0.0, certifi >=2024.12.14
- httpx >=0.25.0, pytest >=8.0.0, pytest-asyncio >=0.23.0

### Faza 26B — Performance (DONE)
- Lazy imports: fitz, pdfplumber, docx, scipy, sklearn (33s -> 6.33s cold start)
- In-memory caches: BNR (1h TTL), ANAF CUI (24h TTL), calibration (mtime-based)
- SQLite PRAGMA: cache_size=-8000 (8MB), temp_store=MEMORY

### Faza 26C — Code Quality (DONE)
- N+1 query fix: LEFT JOIN + ROW_NUMBER() in automations
- SQL parameterization: `'-' || ? || ' days'` pattern
- Shared file_utils.py (deduplicated from 3 files)
- Language validation whitelist in translator
- asyncio.Lock on prompt cache
- Translator text max_length=50000

### Faza 26D — AI Prompts (DONE)
- Anti-hallucination instructions on all AI prompts
- Confidence scoring (0-100) in extraction prompts
- Null for uncertain fields
- Few-shot examples in invoice/classify/extract prompts

### Faza 26E — Testing (DONE)
- 50 new tests across 8 modules (68 total, all PASSED)
- Modules: converter, filemanager, reports, vault, automations, quick_tools, translator, ai_docs
- Rate limiter test bypass for ASGI test client

### Faza 26F — Refactorizare (DONE)
- invoice/router.py (2050 LOC) -> crud.py + ai_extraction.py + pdf_generation.py + reports.py
- ai/router_extensions.py (1052 LOC) -> document_ops.py + tools.py
- reports/router.py (1035 LOC) -> system_reports.py + journal.py + timeline.py
- DashboardPage lazy import + useCallback optimization

### Faza 26G — Hardening & Polish (DONE)
- CORS: restrict methods to GET/POST/PUT/DELETE/OPTIONS
- DB indexes: 8 new (chat_messages.session_id, task_runs.task_id, uptime_history.monitor_id, etc.)
- Blocking I/O -> asyncio.to_thread(): 5 call sites (file_utils, document_ops, invoice, routes_price, self_learning)
- CSP nonce: SKIPPED (Vite SPA generates inline scripts, Tailwind needs inline styles — low ROI for single-user behind VPN)

---

## Viitor (Nice-to-Have, ROI scazut)

| # | Actiune | Impact | Efort | Conditie |
|---|---------|--------|-------|----------|
| V1 | Recharts 2 -> 3 upgrade (bundle reduction) | MEDIUM | 2-3h | Cand recharts 3 e stabil |
| V2 | Vitest frontend tests setup + primele teste | MEDIUM | 4h+ | Dupa backend tests complete |
| V3 | React 18 -> 19 upgrade | LOW | 8h+ | Dupa V1, ecosystem ready |

---

## Surse

- `99_Roland_Work_Place/2026-03-21_deep_research/RAPORT.md` (scor 63/80, v1)
- `99_Roland_Work_Place/2026-03-21_deep_research_v2/RAPORT.md` (scor 58.5/80, v2)
- `99_Roland_Work_Place/2026-03-21_deep_research_v2/ROADMAP_IMBUNATATIRI.md`
