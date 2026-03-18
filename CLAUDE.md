# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Roland - Command Center** — Panou personal multifuncțional: calculator preț traduceri (modul existent), traducător integrat, facturare, tool-uri rapide, AI pe documente, integrări externe (Gmail, Drive, Calendar, GitHub), automatizări — totul într-un singur loc, accesibil de pe PC și Android prin Tailscale.

**Firmă:** CIP Inspection SRL (CUI 43978110) — ITP auto + traduceri tehnice.
**Utilizator:** Doar Roland — permanent single-user, fără auth multi-user.
**Buget:** Exclusiv resurse FREE — nu se adaugă abonamente noi.

## Location

**Primary working directory**: `C:\Proiecte\NOU_Calculator_Pret_Traduceri`
**Original source (Google Drive backup)**: `G:\My Drive\Roly\4. Artificial Inteligence\1.0_Traduceri\NOU_Calculator_Pret_Traduceri`

Always work from `C:\Proiecte\...` — Google Drive is too slow for venv, node_modules, and file watchers.

## Project Status

### Modul Calculator Traduceri (Faze 0-8) — COMPLETE
- 46 fișiere cod, backend + frontend verificate, teste E2E trecute (2026-03-17)
- Calibrare MAPE 32%, weights: base_rate=0.50, word_rate=0.35, similarity=0.15
- Dashboard vizual cu Activity Log, DTP automat, calcul multi-fișier
- Research competitori (12 site-uri, date reale)

**Ramas opțional (calculator):**
- [ ] Îmbunătățire acuratețe calibrare (MAPE 32% → sub 25%)
- [ ] Afișare ponderi metode în UI
- [ ] Fix comparație competitori endpoint

### Audit Arhitectural (2026-03-18) — COMPLET
16 observații (4 critice), toate rezolvate în plan. Detalii: `99_Roland_Work_Place/Documentare_Extindere_Proiect.md` secțiunea 10.

### Wave 0 — Fundație (2026-03-18) — IN PROGRESS
- [x] `git init` + `.gitignore` complet
- [x] Fix URL-uri hardcoded (`client.js` → URL dinamic, WebSocket protocol dinamic)
- [x] Sistem migrare DB (`migrations/` + `schema_version` + `run_migrations()`)
- [x] Module auto-discovery backend (`module_discovery.py` + `modules/calculator/`)
- [x] Frontend manifest (`modules/manifest.js` + sidebar dinamic cu categorii colapsibile)
- [x] Activity log → SQLite (migrare completă, async, JSON înlocuit)
- [x] `busy_timeout = 5000` adăugat (concurrency fix)
- [ ] Notificări infrastructură (toast + WebSocket) — amânat, se adaugă când e nevoie

**Roadmap complet:** `99_Roland_Work_Place/0.0_PLAN_EXTINDERE_COMPLET.md` (Fazele 8-18, ~40-55 sesiuni)
**Documentare:** `99_Roland_Work_Place/Documentare_Extindere_Proiect.md`
**Selector HTML:** `99_Roland_Work_Place/0.0_PLAN_EXTINDERE_COMPLET.html`

## How to Run

### Quick start (double-click)
```
C:\Proiecte\NOU_Calculator_Pret_Traduceri\START_Calculator.bat
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
# Swagger API docs: http://localhost:8000/docs
# Health check: http://localhost:8000/api/health
```

### Calibration (one-time, before first use)
```bash
cd C:\Proiecte\NOU_Calculator_Pret_Traduceri\backend
set PYTHONIOENCODING=utf-8
python calibrate.py --verbose
```

### Dependencies
- **Python 3.13** — packages installed globally (no venv): fastapi, uvicorn, PyMuPDF, pdfplumber, python-docx, scikit-learn, scipy, aiosqlite, pydantic-settings
- **Node.js v20** — packages in frontend/node_modules: react, vite, tailwindcss, recharts, axios, lucide-react, react-dropzone
- **Important**: use `python -m pip` (not bare `pip`) and `python -m uvicorn` (not bare `uvicorn`) on this machine

## Architecture

- **Backend**: FastAPI (Python 3.13) + SQLite (aiosqlite) + WebSocket progress
- **Module system**: `backend/modules/[modul]/` auto-discovered, `modules/calculator/` = modul fondator
- **Frontend**: React 18 + Vite + Tailwind CSS + Recharts
- **Navigation**: `frontend/src/modules/manifest.js` → sidebar dinamic cu categorii colapsibile
- **DB**: SQLite unic cu sistem migrare SQL (`migrations/` + `schema_version`)
- **PDF/DOCX**: PyMuPDF + pdfplumber + pytesseract + python-docx
- **Pricing**: Ensemble of 3 methods (base_rate, word_rate, KNN similarity)
- **AI Providers** (planificat Faza 15): Gemini Flash/Pro (principal) + OpenAI/Groq/Azure free (fallback)

## Key Files

### Backend (backend/)
- `app/main.py` — FastAPI entry point, CORS, WebSocket, module auto-discovery
- `app/module_discovery.py` — Scanează `modules/` pentru routere
- `app/config.py` — Settings (pydantic-settings, relative paths via `Path(__file__)`)
- `app/core/analyzer.py` — PDF/DOCX feature extraction
- `app/core/pricing/` — 3 pricing methods + ensemble combiner
- `app/core/calibration.py` — Auto-calibration with scipy.optimize
- `app/core/validation.py` — 3-level validation
- `app/core/self_learning.py` — User-validated prices → recalibration
- `app/core/activity_log.py` — Activity logging (async, SQLite-backed)
- `app/api/routes_*.py` — API endpoints (registered via `modules/calculator/`)
- `app/db/database.py` — SQLite + migration runner (`run_migrations()`)
- `migrations/` — SQL numerotate (001_initial, 002_activity_log)
- `modules/calculator/__init__.py` — MODULE_INFO cu 7 routere
- `calibrate.py` — CLI calibration script

### Frontend (frontend/src/)
- `App.jsx` — Main layout + routing (6 pages), pageTitles din manifest
- `modules/manifest.js` — Sursa unică navigare (categorii + routes + icons)
- `pages/` — DashboardPage, UploadPage, HistoryPage, CalibrationPage, FileBrowserPage, SettingsPage
- `components/Layout/Sidebar.jsx` — Dinamic din manifest, categorii colapsibile
- `components/` — Upload, Price, History, Calibration, FileBrowser, Settings, Dashboard
- `api/client.js` — Axios + WebSocket helpers (URL-uri dinamice, fără hardcoded)

### Reference Data
- `Fisiere_Reper_Tarif/Pret_Intreg_100la100/` — 26 reference PDFs (120-10820 RON, mean ~1750 RON)

### Documentation & Planning
- `99_Roland_Work_Place/0.0_PLAN_EXTINDERE_COMPLET.md` — Plan complet Fazele 8-18
- `99_Roland_Work_Place/0.0_PLAN_EXTINDERE_COMPLET.html` — Selector vizual interactiv
- `99_Roland_Work_Place/Documentare_Extindere_Proiect.md` — Documentare decizii + audit
- `99_Roland_Work_Place/Cerinta_Roland.md` — Cerințe originale utilizator

## Implementation Summary (for new AI sessions)

| Phase | Status | What |
|-------|--------|------|
| 0 — Setup | DONE | Project structure, requirements, package.json, PLAN_EXECUTIE.md |
| 1 — Analyzer | DONE | PDF/DOCX feature extraction (pages, words, images, tables, complexity, OCR) |
| 2 — Pricing | DONE | 3 methods (base_rate/page, word_rate/word, KNN similarity) + ensemble + calibration |
| 3 — Validation | DONE | 3-level validation + self-learning + market rates |
| 4 — Backend API | DONE | FastAPI with 7 routers + SQLite + WebSocket progress |
| 5 — Frontend | DONE | React + Tailwind, 6 pages, all components |
| 6 — E2E Tests | DONE | Integration testing, all endpoints verified, Playwright automation |
| 7 — Enhancements | DONE | DTP auto, calibration protections, multi-file calc, activity logging, competitor research |
| 8 — Dashboard+Cal | DONE | Activity Log dashboard, calibration run, multi-file E2E test, auto-update rules |
| Audit + Planning | DONE | Architectural audit (16 obs.), Wave planning, PLAN_EXTINDERE + Documentare (2026-03-18) |
| Wave 0 — Fundație | DONE | Git init, module auto-discovery, DB migrations, URL fix, activity log→SQLite, dynamic sidebar (2026-03-18) |
| Wave 1 — Deploy | NEXT | Tailscale + HTTPS/TLS, PWA, API Key Vault, backup script, auto-start |

## Conventions

- All user-facing text in **Romanian**
- Code and technical identifiers in **English**
- Currency: RON, no VAT (non-VAT-payer)
- Languages: only EN ↔ RO (traduceri)
- Domain: technical/industrial translations + ITP auto
- Single user, no auth/roles — Tailscale mesh VPN for security
- Access: localhost (curent) → Tailscale multi-device (planificat Wave 1)
- AI providers: **exclusiv gratuit** — Gemini Flash/Pro (principal), OpenAI free / Groq free / Azure free (fallback)
- Documentation and work files only in `99_Roland_Work_Place/`
- Modular architecture: `backend/modules/` + `frontend/src/modules/manifest.js` (implementat Wave 0)
- New modules: add folder in `backend/modules/[name]/` with `MODULE_INFO` + entry in `manifest.js`

## Auto-Update Rules

### Regula 1 — PLAN_EXECUTIE.md (existentă)
**Trigger:** Finalul fiecărei sesiuni de lucru sau completarea unui task semnificativ.
1. Marchează cu `[x]` orice item implementat în sesiunea curentă
2. Adaugă itemuri noi pentru funcționalități implementate dar nelistate
3. Adaugă o nouă Fază dacă implementările nu se încadrează în fazele existente
4. Mută itemurile finalizate din "Ramas opțional" în faza corespunzătoare
5. Actualizează și secțiunea "Project Status" din CLAUDE.md cu faza curentă

**Format item nou:** `- [x] X.Y Descriere scurtă — detalii tehnice (YYYY-MM-DD)`
**Nu necesită confirmare** — se execută automat.

### Regula 2 — Regenerare HTML (existentă)
**Trigger:** Orice modificare a `99_Roland_Work_Place/0.0_PLAN_EXTINDERE_COMPLET.md`.
1. Actualizează `0.0_PLAN_EXTINDERE_COMPLET.html` — array-ul PHASES din JavaScript
2. Păstrează structura HTML existentă (selector interactiv cu checkboxes, dark theme)
3. **Nu necesită confirmare** — se execută automat
4. Fișierul `.md` se modifică DOAR la cererea explicită a utilizatorului (NU automat)

### Regula 3 — Git Safety (nouă)
**Trigger:** Înainte de orice refactorizare majoră (mutare fișiere, restructurare module, schema DB).
1. Verifică existența unui commit recent sau fișiere necomise
2. Dacă există modificări necomise → propune `git add + commit` ÎNAINTE de refactorizare
3. La finalul refactorizării → propune commit cu descriere clară
**Nu blochează** — doar avertizează și propune.

### Regula 4 — URL Hardcoded Check (nouă)
**Trigger:** Orice modificare a `frontend/src/api/client.js`.
1. Verifică că fișierul NU conține `localhost` hardcoded (excepție: comentarii)
2. URL-urile trebuie să folosească `window.location.origin` sau să fie relative
3. WebSocket: protocol dinamic (`ws:`/`wss:` bazat pe `location.protocol`)
4. Dacă găsește URL hardcoded → avertizare IMEDIATĂ
**Origine:** Audit CRITICAL-2.

### Regula 5 — DB Migration Check (nouă)
**Trigger:** Orice modificare pe fișiere din `app/db/` sau `backend/modules/*/models.py`.
1. Verifică dacă modificarea adaugă/modifică tabele sau coloane
2. Dacă da → verifică existența unui fișier SQL corespunzător în `migrations/`
3. Dacă lipsește → avertizează și propune crearea fișierului SQL
**Origine:** Audit CRITICAL-4. Se activează DUPĂ implementarea Wave 0.

### Regula 6 — Cross-Phase Dependency Check (nouă)
**Trigger:** La implementarea oricărui feature din PLAN_EXTINDERE.
1. Consultă secțiunea DEPENDINȚE CROSS-FAZĂ din `0.0_PLAN_EXTINDERE_COMPLET.md`
2. Verifică dacă feature-ul are dependințe neimplementate
3. Dacă da → avertizează și listează dependințele lipsă
**Nu blochează** — doar informează.

### Regula 7 — Wave/Phase Status Sync (nouă)
**Trigger:** La completarea unui Wave sau a unei Faze întregi.
1. Actualizează secțiunea "Project Status" din acest CLAUDE.md
2. Actualizează Implementation Summary cu noul status
3. Marchează Wave/Faza ca DONE cu data
**Se combină cu Regula 1** — executat la sfârșitul sesiunii.

### Regula 8 — Pre-Implementation Briefing (nouă)
**Trigger:** Înainte de a începe implementarea oricărui Wave sau Fază.
**Obligatoriu** — NU se începe cod fără parcurgerea acestui proces.

1. **Sugerează** cele mai logice Wave/Faze de implementat (ordonate după: dependențe rezolvate → efort mic → valoare mare)
2. **Prezintă** Wave-ul/Faza recomandată cu:
   - Ce conține (listă items cu descriere scurtă + exemplu concret de utilizare)
   - Efort estimat per item
   - Dependențe (ce trebuie să existe deja)
   - Ce se schimbă vizibil pentru utilizator după implementare
3. **Așteaptă confirmare explicită** de la utilizator înainte de a scrie cod
4. Dacă utilizatorul vrea modificări (adaugă/scoate items, schimbă ordinea) → ajustează și re-prezintă

**Format prezentare:**
```
## Wave/Faza X — [Nume] ([N] items, ~[T] ore)

| # | Feature | Ce face (exemplu) | Efort |
|---|---------|-------------------|-------|
| 1 | Nume    | "Apeși Ctrl+K, scrii 'set', ajungi instant la Setări" | 1-2h |

Dependențe: [lista sau "niciuna"]
Rezultat vizibil: [ce vede utilizatorul diferit după implementare]
```

**Origine:** Cerere explicită utilizator (2026-03-18).

## Known Issues / Notes

- Windows console (cp1252) cannot print Romanian characters (ț, ă, etc.) — always set `PYTHONIOENCODING=utf-8`
- Use `python -m pip` and `python -m uvicorn` instead of bare commands
- Google Drive path is backup only — never run venv/node_modules from there
- config.py uses relative paths (`Path(__file__).resolve()`) — works from any location
- Windows: uvicorn child workers zombie la restart — trebuie kill toate procesele python.exe
- ⚠️ **CRITICAL-1:** PWA necesită HTTPS — Tailscale dă IP 100.x.y.z, nu localhost → service worker refuză fără TLS cert
- ~~CRITICAL-2:~~ REZOLVAT — client.js folosește URL-uri dinamice (Wave 0)
- ~~MISSING-16:~~ REZOLVAT — Git repo inițializat (Wave 0)
