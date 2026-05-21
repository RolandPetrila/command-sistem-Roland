# CLAUDE.md

Regulament pentru Claude Code (claude.ai/code) când lucrează în acest repository.

## Project Overview

**Roland - Command Center** — Panou personal multifuncțional: calculator preț traduceri, traducător integrat, facturare, ITP, AI pe documente, integrări externe, automatizări. Accesibil de pe PC și Android prin Tailscale + Cloudflare Tunnel.

**Firmă:** CIP Inspection SRL (CUI 43978110)
**Utilizator:** Doar Roland — permanent single-user, fără auth multi-user
**Buget:** Exclusiv resurse FREE — nu se adaugă abonamente noi

## Location

**Working dir:** `C:\Proiecte\NOU_Calculator_Pret_Traduceri`
**Google Drive backup:** `G:\My Drive\Roly\4. Artificial Inteligence\1.0_Traduceri\NOU_Calculator_Pret_Traduceri`

Lucrează DOAR din `C:\Proiecte\...` — Google Drive e prea lent pentru venv, node_modules, file watchers.

## Status & Plan

- **Status structurat** (machine-readable): `.meta/status.yaml`
- **Plan curent + roadmap:** `docs/plan.md`
- **Istoric complet faze 0-33:** `99_Roland_Work_Place/0.0_PLAN_EXTINDERE_COMPLET.md`
- **Decizii arhitecturale:** `.meta/decisions.yaml`
- **Resume punct curent:** `docs/resume.md`
- **TODO actiuni manuale:** `docs/todo.md`

## How to Run

Quick start (vezi `RUNBOOK.md` pentru detalii operatiuni):

```
python start.py             # dev cu HMR + Cloudflare tunnel public (DEFAULT)
python start.py dev         # dev cu HMR, fara tunnel
python start.py prod        # production (build + FastAPI serveste dist/)
python start.py stop        # opreste backend + vite + tunnel
```

URLs: local `http://127.0.0.1:8000` | dev `http://localhost:5173` | tunnel `https://*.trycloudflare.com`

## Architecture

- **Backend:** FastAPI (Python 3.13) + SQLite (aiosqlite) + WebSocket progress
- **Frontend:** React 18 + Vite + Tailwind CSS + PWA auto-update
- **Module system:** `backend/modules/[name]/` auto-discovered (vezi `backend/CLAUDE.md`)
- **Navigation:** `frontend/src/modules/manifest.js` → sidebar dinamic (vezi `frontend/CLAUDE.md`)
- **DB:** SQLite + migration system (`backend/migrations/` + `schema_version`)
- **Pricing:** Ensemble 3 methods (base_rate, word_rate, KNN similarity)
- **Deploy:** Tailscale local + Cloudflare Tunnel public + Task Scheduler auto-start

**Module backend (14):** ai, automations, calculator (modul fondator — bundleaza routes\_\*.py), converter, filemanager, integrations, invoice (cu efactura UBL 2.1), itp, quick_tools, quick_tools_extra, reports, timetracking, translator, vault.

**Cifre live** (regenerate via `python .claude/scripts/sync-meta.py`):
14 module backend, 26 pagini frontend, 355 routes, 25 migrations, 86 teste backend (pytest) + 14 frontend (vitest).

## API Providers (free tier only)

| Tip           | Chain                                                                                              |
| ------------- | -------------------------------------------------------------------------------------------------- |
| AI            | Gemini 2.5 Flash → Cerebras Qwen3-235B (primar `claude-prep`) → Groq Llama 3.3 70B → Mistral Small |
| Translation   | DeepL → Azure F0 → Google Cloud → MyMemory → LibreTranslate                                        |
| TTS           | edge-tts (Microsoft Neural) → Web Speech API browser                                               |
| OCR           | Tesseract + EasyOCR local → OCR.space cloud                                                        |
| Notifications | Web Push VAPID → Telegram Bot → ntfy.sh → Email Gmail SMTP                                         |
| Business APIs | BNR XML (free), ANAF Verificare CUI (free)                                                         |

Vezi `.claude/rules/06-free-tier-enforcement.md` pentru reguli complete.

## Key Files

**Backend:** `app/main.py` (entry), `app/module_discovery.py`, `app/config.py`, `app/core/` (analyzer, pricing, calibration, validation, activity_log), `app/db/database.py`, `modules/` (14 module auto-discovered)

**Frontend:** `App.jsx` (routing, lazy loading), `modules/manifest.js` (navigation), `api/client.js` (API + WebSocket dinamic), `pages/` (26 pagini), `hooks/` (useDebounce, useTheme, useHotkeys, useNotifications), `components/Layout/` (Sidebar, Header), `components/shared/` (CommandPalette, GlobalToast, FloatingTimer)

**Reference data:** `Fisiere_Reper_Tarif/` (26 PDFs calibrare, 120-10820 RON)

**API Keys central:** `C:\Users\ALIENWARE\.api-keys\` (catalog + Windows env vars) — vezi `~/.claude/CLAUDE.md` pentru reguli sistem central.

## Conventions

- Toate user-facing strings in **Romana**, cod + log messages + var names in **English**
- Currency: RON, no VAT. Languages: EN ↔ RO only
- Single user, NO multi-user auth (Tailscale mesh VPN pentru security)
- AI/API providers: exclusively free tier (vezi rule 06)
- USER_WORKSPACE: `99_Roland_Work_Place/` (notite personale, audit-uri, capturi)
- AI work: `.workspace/` (drafts, investigations, audit-outputs)
- New module: folder in `backend/modules/[name]/` + entry in `manifest.js`
- **Git: NEVER `git add -A`** — add specific files by name (rule 04)
- Windows: always `set PYTHONIOENCODING=utf-8` + `python -m pip` / `python -m uvicorn`

## Native Workspace Structure (post-restructurare Faza 34)

```
[root]                       max 5 fisiere
├── README.md                Overview public (max 100 linii)
├── RUNBOOK.md               Operatiuni urgenta (1 pagina)
├── CLAUDE.md                Acest fisier (slim <200 linii)
├── start.py                 Launcher Python unic
└── launch_roland.vbs        Shim auto-start invisible

.meta/                       Single Source of Truth structurat
├── profile.yaml             Composition A+R + scale single-user
├── status.yaml              Stare live (regenerata via sync-meta.py)
├── decisions.yaml           13 decizii arhitecturale
└── sitemap.yaml             Tree depth 3 (regenerat via indexer.py)

docs/                        Narrative arhitectural
├── plan.md                  Plan curent + roadmap (<500 linii)
├── resume.md, todo.md, README.md
├── handovers/               Documente transfer
└── audit-externe/           Audit-uri Gemini/ChatGPT

.workspace/                  Zona AI work (drafts, investigations)
.archive/                    Documente deprecated (P7 — arhiva over delete)
99_Roland_Work_Place/        USER_WORKSPACE personala (neschimbat)
.claude/                     Sistem Claude Code (rules + hooks + scripts + memory)
backend/, frontend/, assets/, scripts/, cloudflared/, Fisiere_Reper_Tarif/, logs/
```

## Rules & Automation

Reguli proiect (auto-loaded fiecare message): `.claude/rules/`

| Rule                      | Trigger                                                                 |
| ------------------------- | ----------------------------------------------------------------------- |
| 01 progress-tracking      | After EVERY implementation (update docs/plan + 0.0_PLAN + .meta/status) |
| 02 pre-implementation     | BEFORE any Wave/Phase (dependency check + briefing + confirmation)      |
| 03 validation-and-testing | At Wave/Phase completion (test + GHID_TESTARE + user confirm)           |
| 04 code-safety            | Git safety + URL hardcoded check + DB migration check                   |
| 05 rule-governance        | Protocol modificare reguli + priority local > global                    |
| 06 free-tier-enforcement  | Zero cost + approved provider chains                                    |
| 07 error-handling         | NO silent catch + global toast + diagnostics                            |
| 08 post-change-validation | Verify full system startup dupa orice cod modification                  |

**Comenzi:** `/update-status`, `/pre-wave`, `/test-guide`, `/rule-change`
**Agent:** `rule-guardian` (read-only)
**Scripts:** `.claude/scripts/sync-meta.py`, `indexer.py`, `root-sweeper.py` (auto-sync `.meta/`)

## Known Issues

- Windows cp1252: always `set PYTHONIOENCODING=utf-8`
- Use `python -m pip` / `python -m uvicorn` (NU bare commands)
- uvicorn zombie workers on restart — `python start.py stop` rezolva
- PWA needs HTTPS — Tailscale `.ts.net` host + tailscale cert sau Cloudflare Tunnel
- PowerShell 5.1 UTF-8 fara BOM — scripturi `.claude/scripts/` sunt in Python (NU PS)
