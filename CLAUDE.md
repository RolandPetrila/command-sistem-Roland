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
| Wave 2 Quick Tools | PARTIAL | Command Palette, QR, Notepad done; Calc, PwdGen, Barcode pending (2026-03-18) |
| Wave 1 Deploy | DONE | Tailscale HTTPS, PWA, Vault, Backup, Auto-start (2026-03-18) |
| Faza 12 Convertor | DONE | 10 conversii, Android-safe, COM fix (2026-03-18) |
| Faza 14 File Manager | PARTIAL | Browse, CRUD, upload, download, duplicates done; fulltext, tags deferred (2026-03-18) |
| Restructurare reguli | DONE | 12 reguli → 5 fișiere .claude/rules/, hooks, commands, agent (2026-03-19) |

**Opțional ramas (calculator):** Calibrare MAPE sub 25%, ponderi metode în UI, fix competitori endpoint.
**Roadmap complet:** `99_Roland_Work_Place/0.0_PLAN_EXTINDERE_COMPLET.md`
**Documentare:** `99_Roland_Work_Place/Documentare_Extindere_Proiect.md`

## How to Run

### Quick start (double-click)
```
START_Calculator.bat          # dev mode
START_Production.bat          # production with TLS autodetect
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
- **AI Providers** (planned): Gemini Flash/Pro + OpenAI/Groq/Azure free (fallback)

## Key Files

**Backend:** `app/main.py` (entry), `app/module_discovery.py`, `app/config.py`, `app/core/` (analyzer, pricing, calibration, validation, activity_log), `app/db/database.py`, `modules/` (calculator, converter, filemanager, vault)

**Frontend:** `App.jsx` (routing), `modules/manifest.js` (navigation), `api/client.js` (API + WebSocket), `pages/` (10 pages), `components/Layout/` (Sidebar, Header)

**Reference:** `Fisiere_Reper_Tarif/` (26 PDFs, 120-10820 RON)

## Rules & Automation

Detailed rules in `.claude/rules/` (auto-loaded every message):
- `01-progress-tracking.md` — Update plan, HTML, CLAUDE.md, PROJECT_STATUS after each implementation
- `02-pre-implementation.md` — Dependency check + briefing + confirmation before any wave/phase
- `03-validation-and-testing.md` — Test all features + GHID_TESTARE.md + user confirmation before next phase
- `04-code-safety.md` — Git safety, URL hardcoded check, DB migration check
- `05-rule-governance.md` — Protocol for modifying rules + priority: local > global

**Commands:** `/update-status`, `/pre-wave`, `/test-guide`, `/rule-change`
**Agent:** `rule-guardian` — analyzes rule changes read-only

## Conventions

- All user-facing text in **Romanian**, code in **English**
- Currency: RON, no VAT. Languages: EN ↔ RO only
- Single user, no auth — Tailscale mesh VPN for security
- AI providers: exclusively free tier
- Work files: `99_Roland_Work_Place/`
- New modules: folder in `backend/modules/[name]/` + entry in `manifest.js`
- Git: add specific files, NEVER `git add -A`

## Known Issues

- Windows cp1252: always set `PYTHONIOENCODING=utf-8`
- Use `python -m pip` / `python -m uvicorn` (not bare commands)
- uvicorn zombie workers on restart — kill all python.exe
- PWA needs HTTPS — Tailscale gives 100.x.y.z, requires TLS cert
