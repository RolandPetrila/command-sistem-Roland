# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Roland - Command Center** — Panou personal multifuncțional: calculator preț traduceri, traducător integrat, facturare, tool-uri rapide, AI pe documente, integrări externe, automatizări — totul într-un singur loc, accesibil de pe PC și Android prin Tailscale.

**Firmă:** CIP Inspection SRL (CUI 43978110) — ITP auto + traduceri tehnice.
**Utilizator:** Doar Roland — permanent single-user, fără auth multi-user.
**Buget:** Exclusiv resurse FREE — nu se adaugă abonamente noi.

## Location

**Primary working directory**: `C:\Proiecte\NOU_Calculator_Pret_Traduceri`
**Google Drive backup**: `G:\My Drive\Roly\4. Artificial Inteligence\1.0_Traduceri\NOU_Calculator_Pret_Traduceri`

Always work from `C:\Proiecte\...` — Google Drive is too slow for venv, node_modules, and file watchers.

## Project Status

| Phase | Status | Summary |
|-------|--------|---------|
| Faze 0-8 Calculator | DONE | 46 fișiere, MAPE 32%, dashboard, competitori (2026-03-17) |
| Audit Arhitectural | DONE | 16 obs (4 critice), toate rezolvate (2026-03-18) |
| Wave 0 Fundație | DONE | Git, migrations, module discovery, dynamic sidebar (2026-03-18) |
| Wave 2 Quick Tools | DONE | Command Palette, QR, Notepad, Calculator, PwdGen, Barcode (2026-03-19) |
| Wave 1 Deploy | DONE | Tailscale HTTPS, PWA, Vault, Backup, Auto-start (2026-03-18) |
| Faza 12 Convertor | DONE | 10 conversii, Android-safe, COM fix (2026-03-18) |
| Faza 14 File Manager | DONE | Browse, CRUD, upload, download, duplicates, fulltext FTS5, tags, favorites, auto-organize (2026-03-19) |
| Restructurare reguli | DONE | 12 reguli → 5 fișiere .claude/rules/, hooks, commands, agent (2026-03-19) |
| Faza 9 Translator | DONE | 5 providers (DeepL→Azure→Google→Gemini→OpenAI), TM, glossary, file translation, langdetect (2026-03-19) |
| Faza 15A AI Chat+Docs | DONE | Chat SSE streaming (Gemini→OpenAI→Groq), 6 doc endpoints, OCR+AI, diff, 10 API keys (2026-03-19) |
| Faza 15B AI Enhanced | DONE | 10 AI features + token indicator + provider selector (2026-03-19) |
| Faza 10 Facturare Ext | DONE | Client history, rapoarte, export CSV/Excel, templates, email, scanner OCR (2026-03-19) |
| Faza 13 Integrări | DONE | Gmail, Google Drive, Calendar, GitHub — 5 endpoint-uri per provider (2026-03-19) |
| Faza 15.8 Quality | DONE | Evaluare calitate traducere AI (scor, issues, suggestions) (2026-03-19) |
| Faza 16 Automatizări | DONE | Scheduler, Shortcuts, Uptime Monitor, API Tester, Health (2026-03-19) |
| Faza 17 Rapoarte | DONE | Disk stats, system info, timeline, journal, bookmarks, export JSON (2026-03-19) |
| Faza 18 ITP | DONE | Inspecții CRUD, import, statistici, alerte expirare, export (2026-03-19) |

| Faza 19 Unificare Docs | DONE | 3 V2 → 3 documente unificate, strategie API maximala, regula free-tier (2026-03-20) |
| Faza 20 Quick Wins | DONE | 11/15: GZip, CSP, BNR curs, ANAF CUI, cache AI, convertor numere, useDebounce (2026-03-20) |
| Faza 21 Audit Full | DONE | Audit A-G: verificare firma ANAF, BNR convertor, numere-litere, dashboard pro, dark/light theme, keyboard shortcuts, code splitting lazy load, backup ZIP, notificari browser, CompanyCheckPage (2026-03-20) |
| Faza 22 Unificare BAT | DONE | Un singur START_Roland.bat (start/stop/build), sterse 7 fisiere vechi, health check, TLS autodetect, backup local (2026-03-20) |
| Faza 23 Diagnostice | DONE | Request logger middleware, axios error interceptor, global toast, diagnostics panel, fix catch blocks, rule 07 (2026-03-20) |
| Faza 24 BAT Hardening | DONE | Aggressive process cleanup, backend log capture, 60s timeout, error display, rule 08 post-validation (2026-03-20) |
| Faza 25A Provideri AI | DONE | Gemini 2.5-flash (fix deprecated), +Cerebras qwen3-235b, +Mistral small, .env, chain 4 provideri testat OK (2026-03-21) |
| Faza 25B Security Wins | DONE | SQL whitelist OK, fix catch blocks, AI translate prompt, rate limiting 60/10 req/min (2026-03-21) |
| Faza 25C Fix Cerinta | DONE | Interceptor network errors, batch PDF (10x), DOCX tables translate, timeout 300s (2026-03-21) |
| Faza 25D Speed Test | DONE | Network speed indicator in header: Mbps + latency, auto-refresh 60s, click remeasure (2026-03-21) |
| Faza 25E Testare | DONE | pytest + 18 teste (health, translate, AI, invoice CRUD, ITP) — toate PASSED (2026-03-21) |
| Faza F Cross-Module | DONE | Voice input, prompt templates, serii facturi, scadente, programari ITP, notificari, preview docs, calibrare interactiva, oferte PDF, glosar per client (2026-03-21) |
| Faza 26A-G Deep Research | DONE | Security (CVE fix), Performance (5x cold start), Code Quality (N+1, SQL param), AI Prompts (anti-hallucination), Testing (68 tests), Refactorizare (3 fisiere mari split), Hardening (DB indexes, async I/O) (2026-03-21) |
| Faza 27 Module Ext | DONE | 78 features across 14 modules: vault security, converter limits, FM batch ops, notepad search, cron scheduler, dashboard alerts, translation cache, ITP vehicle history, invoice recurring, passphrase gen (2026-03-22) |
| Faza 28 Runda 2 QA | DONE | 39 fixes across 14 modules: 12 BUG, 6 SEC, 7 PERF, 14 QUALITY — path traversal, cascading delete, pagination, async IMAP, dashboard chart fix, factorial DOS, hash session, recurring drift (2026-03-22) |

**Roadmap implementare:** `99_Roland_Work_Place/ROADMAP_IMPLEMENTARE.md`
**Catalog API gratuite:** `99_Roland_Work_Place/CATALOG_API_GRATUITE.md`
**Ghid acces remote:** `99_Roland_Work_Place/GHID_ACCES_REMOTE.md`
**Plan extindere:** `99_Roland_Work_Place/0.0_PLAN_EXTINDERE_COMPLET.md`

## How to Run

### Quick start (double-click)
```
START_Roland.bat              # pornire sistem (production, TLS autodetect)
START_Roland.bat build        # rebuild frontend + pornire
START_Roland.bat stop         # oprire sistem
```

### Manual start
```bash
# Terminal 1 — Backend
cd C:\Proiecte\NOU_Calculator_Pret_Traduceri\backend
set PYTHONIOENCODING=utf-8
python -m uvicorn app.main:app --reload --port 8000 --host 127.0.0.1

# Terminal 2 — Frontend
cd C:\Proiecte\NOU_Calculator_Pret_Traduceri\frontend
npm run dev

# Browser: http://localhost:5173
# Swagger: http://localhost:8000/docs
# Health: http://localhost:8000/api/health
```

### Calibration (one-time)
```bash
cd backend && set PYTHONIOENCODING=utf-8 && python calibrate.py --verbose
```

### Dependencies
- **Python 3.13** (global, no venv): fastapi, uvicorn, PyMuPDF, pdfplumber, python-docx, scikit-learn, scipy, aiosqlite, pydantic-settings
- **Node.js v20**: react, vite, tailwindcss, recharts, axios, lucide-react, react-dropzone
- **Important**: use `python -m pip` and `python -m uvicorn` on this machine

## Architecture

- **Backend**: FastAPI (Python 3.13) + SQLite (aiosqlite) + WebSocket progress
- **Module system**: `backend/modules/[name]/` auto-discovered — see `backend/CLAUDE.md`
- **Frontend**: React 18 + Vite + Tailwind CSS — see `frontend/CLAUDE.md`
- **Navigation**: `frontend/src/modules/manifest.js` → sidebar dinamic
- **DB**: SQLite + migration system (`migrations/` + `schema_version`)
- **Pricing**: Ensemble 3 methods (base_rate, word_rate, KNN similarity)
- **AI Providers**: Gemini 2.5 Flash (primary) → Cerebras Qwen3-235B (volume, 1M tok/day) → Groq Llama 3.3 70B (speed) → Mistral Small (1B tok/mo) → OpenAI (legacy, free tier non-functional)
- **Translation Providers**: DeepL (quality) → Azure F0 (2M chars/mo) → Google Cloud → MyMemory → LibreTranslate local
- **TTS Providers**: edge-tts (Microsoft Neural, RO, unlimited) → Web Speech API (browser fallback)
- **OCR Providers**: Tesseract + EasyOCR local → OCR.space cloud
- **Notification Providers**: Web Push VAPID → Telegram Bot → ntfy.sh → Email digest
- **Modules** (14): calculator, ai, translator, invoice, itp, quick_tools, quick_tools_extra, converter, filemanager, vault, automations, integrations, reports, calculator_pret
- **DB Tables**: 57+, **Migrations**: 16, **Tests**: 68+ (pytest), **Endpoints**: 310+
- **Business APIs**: BNR curs valutar (XML, free), ANAF Verificare CUI (REST, free)

## Key Files

**Backend:** `app/main.py` (entry), `app/module_discovery.py`, `app/config.py`, `app/core/` (analyzer, pricing, calibration, validation, activity_log), `app/db/database.py`, `modules/` (13 modules auto-discovered)

**Frontend:** `App.jsx` (routing, lazy loading), `modules/manifest.js` (navigation), `api/client.js` (API + WebSocket), `pages/` (25 pages), `hooks/` (useDebounce, useTheme, useHotkeys, useNotifications), `components/Layout/` (Sidebar, Header with theme toggle + shortcuts), `components/Dashboard/ExchangeRateCard.jsx`

**Reference:** `Fisiere_Reper_Tarif/` (26 PDFs, 120-10820 RON)

## Rules & Automation

Detailed rules in `.claude/rules/` (auto-loaded every message):
- `01-progress-tracking.md` — Update plan, HTML, CLAUDE.md, PROJECT_STATUS after each implementation
- `02-pre-implementation.md` — Dependency check + briefing + confirmation before any wave/phase
- `03-validation-and-testing.md` — Test all features + GHID_TESTARE.md + user confirmation before next phase
- `04-code-safety.md` — Git safety, URL hardcoded check, DB migration check
- `05-rule-governance.md` — Protocol for modifying rules + priority: local > global
- `06-free-tier-enforcement.md` — Zero cost policy, approved provider chains, violation response
- `07-error-handling.md` — Mandatory error handling: no silent catch, global toast, diagnostics panel
- `08-post-change-validation.md` — Verify full system startup after ANY code changes before declaring done

**Commands:** `/update-status`, `/pre-wave`, `/test-guide`, `/rule-change`
**Agent:** `rule-guardian` — analyzes rule changes read-only

## Conventions

- All user-facing text in **Romanian**, code in **English**
- Currency: RON, no VAT. Languages: EN ↔ RO only
- Single user, no auth — Tailscale mesh VPN for security
- AI/API providers: exclusively free tier — see `.claude/rules/06-free-tier-enforcement.md` for approved chains
- Work files: `99_Roland_Work_Place/`
- New modules: folder in `backend/modules/[name]/` + entry in `manifest.js`
- Git: add specific files, NEVER `git add -A`

## Known Issues

- Windows cp1252: always set `PYTHONIOENCODING=utf-8`
- Use `python -m pip` / `python -m uvicorn` (not bare commands)
- uvicorn zombie workers on restart — kill all python.exe
- PWA needs HTTPS — Tailscale gives 100.x.y.z, requires TLS cert
