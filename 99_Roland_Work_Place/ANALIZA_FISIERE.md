# Analiza Completă Fișiere — Roland Command Center

**Data analiză:** 2026-03-19
**Total fișiere (fără node_modules, .git):** ~228

---

## Structură pe directoare

| Director | Fișiere | Rol |
|----------|---------|-----|
| `/` (rădăcină) | 9 | Config, startup scripts, CLAUDE.md |
| `backend/` | 42 Python | FastAPI, modules, core logic |
| `frontend/src/` | 39 JS/JSX | React pages, components, API |
| `99_Roland_Work_Place/` | 14 active + 9 archive | Documentație, planuri, ghiduri |
| `.claude/` | 14 | Rules, commands, hooks, agent |
| `Fisiere_Reper_Tarif/` | 26 PDF + 1 JSON | Referințe prețuri calibrare |
| `backend/data/` | 7 JSON + 1 DB | Date, calibrare, backups |
| `backend/migrations/` | 4 SQL | Schema DB |

---

## Fișiere din rădăcină — Status

| Fișier | Rol | Status |
|--------|-----|--------|
| `CLAUDE.md` | Ghid principal proiect | ✅ Activ, ~150 linii (restructurat) |
| `PLAN_EXECUTIE.md` | Plan execuție original | ✅ Activ, referit în memory |
| `START_Calculator.bat` | Start dev mode | ✅ Activ |
| `START_Production.bat` | Start producție TLS | ✅ Activ |
| `setup_autostart.bat` | Task Scheduler | ✅ Activ |
| `_start_backend.bat` | Start doar backend | ⚠️ Redundant — START_Calculator.bat face totul |
| `_start_frontend.bat` | Start doar frontend | ⚠️ Redundant — dar util debug |
| `update_tracking.py` | Script tracking | ⚠️ De verificat dacă e folosit |
| `2026-03-17-...plan.txt` | Transcript sesiune (73KB) | ❌ Neesențial — de arhivat/șters |

---

## Backend — Structură modulară

**Module active (4 + 1 core):**
1. `modules/calculator/` — Modul fondator, 7 routere
2. `modules/converter/` — 10 tipuri conversie
3. `modules/filemanager/` — Browse, CRUD, upload, download, duplicates
4. `modules/quick_tools/` — Notepad cu auto-save
5. `modules/vault/` — API Key Vault (Fernet + PBKDF2)

**Core:** `app/core/` — analyzer, pricing (3 metode + ensemble), calibration, validation, self_learning, activity_log

**DB:** 4 migrări SQL, schema_version tracked, busy_timeout=5000

**Fișiere potențial redundante:**
- `data/activity_log.json` — Legacy (înlocuit de SQLite în Wave 0)
- `test_analyzer_correlation.py`, `test_ensemble_26.py` — Teste one-time, pot fi arhivate

---

## Frontend — 10 pagini, componente modulare

**Pages:** Dashboard, Upload, History, Calibration, FileBrowser, Settings, Converter, QRGenerator, Notepad, Vault

**Componente organizate pe feature:** Layout (3), Upload (3), Price (6), History (2), Calibration (2), FileBrowser (2), Dashboard (3), Settings (2), shared (2)

**Critice:** `api/client.js` (URL-uri dinamice — Wave 0 fix), `modules/manifest.js` (sursa unică navigare)

---

## 99_Roland_Work_Place/ — Documentație

**Active (esențiale):**
- `0.0_PLAN_EXTINDERE_COMPLET.md` — Master plan (31KB)
- `0.0_PLAN_EXTINDERE_COMPLET.html` — Selector vizual interactiv
- `Documentare_Extindere_Proiect.md` — Audit + decizii arhitecturale
- `GHID_TESTARE.md` — Ghid testare per funcție
- `Cerinta_Roland.md` — Cerințe originale
- `CHANGELOG_RULES.md` — Log modificări reguli
- `Competitori.md` — Research competitori
- `dashboard-screenshot.png` — Screenshot referință

**Arhivate (9 fișiere în archive/):**
- Planuri vechi: 1.0, 2.0, 2.1, 2.2_PLAN_EXTINDERE
- MAX_EFFORT.md, cerințe restructurare (executate)

---

## .claude/ — Sistem reguli

| Tip | Fișiere | Încărcare |
|-----|---------|-----------|
| Rules | 5 fișiere | Auto la fiecare mesaj |
| Commands | 4 comenzi slash | La cerere: /update-status, /pre-wave, /test-guide, /rule-change |
| Agent | 1 (rule-guardian) | Read-only, analiză reguli |
| Hooks | 4 scripturi bash | Auto la evenimente (session start/stop, post-edit, pre-compact) |
| Config | settings.local.json | Permisiuni + hooks config |
| Status | PROJECT_STATUS.md | Snapshot auto-generat |

---

## Propuneri de acțiune

### De arhivat/șters (opțional):
1. `2026-03-17-...plan.txt` (73KB transcript) — nu e documentație
2. `_start_backend.bat` + `_start_frontend.bat` — redundante (START_Calculator le înlocuiește)
3. `backend/data/activity_log.json` — legacy, SQLite e sursa de adevăr
4. `backend/test_*.py` — teste one-time, pot merge în archive/

### Status final post-restructurare:
- ✅ Rădăcina curată: CLAUDE.md, PLAN_EXECUTIE, 4 bat-uri, .gitignore
- ✅ Reguli externalizate: 12 reguli inline → 5 fișiere .claude/rules/
- ✅ Comenzi slash: 4 comenzi custom
- ✅ Hooks: 4 scripturi auto-trigger
- ✅ Nested CLAUDE.md: backend/ + frontend/
- ✅ Arhivă: 10 fișiere deprecated → archive/
- ✅ Documentație centralizată în 99_Roland_Work_Place/
