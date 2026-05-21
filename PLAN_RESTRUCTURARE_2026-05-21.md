# PLAN RESTRUCTURARE Native Workspace — Roland Command Center

> **Generat:** 2026-05-21 · **Sursa blueprint:** `c:\Proiecte\Blueprints\Roland_99\Blueprints_Restructurare_Nativ.md` (v2.1)
> **Aplicare:** SELECTIVA — filtrat prin P13 (Scale lens, single-user) + P14 (Tool overhead awareness)
> **Branch executie:** `restructurare-native-ws` (creat dupa E0)

---

## 1. Scop si tinta

**De ce:** Roland are 33 faze acumulate, root cu ~15 fisiere (target P4: 2-3), 27 fisiere necommited (~4400 modificari), fisier monolit `0.0_PLAN_EXTINDERE_COMPLET.md` referit din rules. Inainte de a adauga modul nou `bilingual_doc` (ETAPA 2), curatam si organizam structural.

**Tinta dupa restructurare:**

- Maximum 3 fisiere la radacina (README + RUNBOOK + CLAUDE.md slim)
- `.meta/` cu profile+status+decisions+sitemap (4 YAML-uri)
- `docs/` cu narrative (plan + handover + archive)
- `.workspace/` pentru zona AI (drafts/investigations/audit-outputs)
- `.archive/` pentru documente deprecated
- `99_Roland_Work_Place/` ramane USER_WORKSPACE (zona personala)
- 3 scripturi PowerShell auto-sync
- Hooks wired

**Variant detectat:** Composition **A + R** (Frontend React/Vite + Backend FastAPI pure).

---

## 2. Decizii arhitecturale luate

| Decizie                                                                                  | Motiv                                                                           |
| ---------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| Aplica blueprint SELECTIV (skip JSON schemas, verify-deps, status-board, ingest-sources) | P13/P14 — single-user nu necesita bus factor 2 si overhead schemas              |
| `99_Roland_Work_Place/` ramane in loc, NU mutat in `.workspace/`                         | Conform blueprint pattern (P6) — e USER_WORKSPACE, distinct de `.workspace/` AI |
| 3 scripturi PowerShell, NU 8                                                             | Doar cele cu beneficiu real: sync-meta + indexer + root-sweeper                 |
| Branch dedicat `restructurare-native-ws`                                                 | Izolare in caz de regresie                                                      |
| Commit Faza 34 PRIMA, in 9 commit-uri logice                                             | Pastrare istoric per feature                                                    |

**Modules verdict (post-audit):**

- KEEP toate cele 14 module active (calculator, ai, automations, converter, filemanager, integrations, invoice, itp, quick_tools, quick_tools_extra, reports, timetracking NEW, translator, vault)
- FIX referinta inexistenta `calculator_pret` in CLAUDE.md (incorporat in E6)
- MERGE CalculatorPage + CalculatorAdvancedPage → **DUPA** restructurare (Task #11)

---

## 3. Reguli de siguranta

1. **R-RISK HIGH** la mutari masive: orice mutare/redenumire >5 fisiere → confirmare user
2. **NU `git add -A`** — adaugare specifica per commit
3. **NU sterg, doar mut in `.archive/`** — git history protejeaza, dar visibility e cleaner
4. **Validare Rule 08 dupa fiecare etapa cu modificari de cod sau imports**: `python -c "from app.main import app"` PASS
5. **Hook silent fail** — exit 0 chiar la eroare ca sa nu blocheze tool execution
6. **Backup pre-E1**: comit toate fisierele necommited inainte de orice mutare
7. **STOP la prima validare esuata** — fix imediat, NU continui

---

## 4. Checklist executie

### E0 — Pregatire + safety (Task #1)

- [ ] Verific `git status` — confirma stare reala
- [ ] Comit Faza 34 in 9 commit-uri logice per feature (vezi §5)
- [ ] Creez branch `restructurare-native-ws`
- [ ] Verific build local: `python -c "from app.main import app"`
- [ ] Push pe origin/master inainte de branch

### E1 — Cleanup radacina (Task #3)

- [ ] Creez `.archive/` cu README
- [ ] Mut in `.archive/`:
  - [ ] `roland_backend.log` (70KB)
  - [ ] `roland_start.log`
  - [ ] `package-lock.json` (orfan)
  - [ ] `.codex_global_staging/`
  - [ ] `.claude-outputs/`
  - [ ] `update_tracking.py` (vechi)
  - [ ] `launch_roland.vbs` (vechi)
  - [ ] `SABLOANE_SI_HINTURI_RECOMANDATE.md` (vechi)
  - [ ] `API_KEYS.md` (sensibil — mutare in `.archive/` care e gitignored)
- [ ] Creez `docs/` cu README
- [ ] Mut in `docs/`:
  - [ ] `RESUME_PUNCT_CURENT.md` → `docs/resume.md`
  - [ ] `HANDOVER_RESTRUCTURARE_2026-05-21.md` → `docs/handovers/2026-05-21_restructurare.md`
  - [ ] `PLAN_EXECUTIE.md` → `docs/plan-executie-legacy.md`
  - [ ] `TODO.md` → `docs/todo.md`
- [ ] Verific: la radacina raman doar README.md (creez nou), RUNBOOK.md (E6), CLAUDE.md (slim in E6), start.py (entry), .gitignore, .gitattributes
- [ ] Update referinte din rules si CLAUDE.md la noile paths

### E2 — `.meta/` setup minimal (Task #4)

- [ ] Creez `.meta/`
- [ ] `.meta/profile.yaml` — composition A+R + evidence detection
- [ ] `.meta/status.yaml` — initial cu Faza 33 baseline + Faza 34 ETA committed
- [ ] `.meta/decisions.yaml` — extract decizii din CLAUDE.md (provider chains, single-user, free-tier, Tailscale, etc.)
- [ ] `.meta/sitemap.yaml` — depth 3, exclude {node_modules, venv, .git, .archive, dist, **pycache**}

### E3 — Split documente narrative (Task #5)

- [ ] Backup `99_Roland_Work_Place/0.0_PLAN_EXTINDERE_COMPLET.md` in `.archive/`
- [ ] Creez `docs/plan.md` (faze curente + viitor, max 500 linii)
- [ ] Creez `docs/archive/faze_anterioare.md` (faze 0-32 detalii)
- [ ] Update referinte la noul plan in:
  - [ ] `CLAUDE.md`
  - [ ] `.claude/rules/01-progress-tracking.md`
  - [ ] `.claude/rules/02-pre-implementation.md`
  - [ ] `.claude/rules/03-validation-and-testing.md`
  - [ ] `99_Roland_Work_Place/GHID_TESTARE.md`
- [ ] Genereaza HTML din docs/plan.md (echivalent 0.0_PLAN_EXTINDERE_COMPLET.html)

### E4 — `.workspace/` setup (Task #6)

- [ ] Creez `.workspace/`
- [ ] Creez `.workspace/{drafts,investigations,audit-outputs}/` cu README per folder
- [ ] Adauga `.workspace/` in .gitignore (zona AI, nu version control)
- [ ] Documenteaza distinctia `.workspace/` (AI) vs `99_Roland_Work_Place/` (USER)

### E5 — Scripturi minime (Task #7)

- [ ] Creez `.claude/scripts/sync-meta.ps1`:
  - Reads git log, pytest, build status
  - Writes `.meta/status.yaml`
  - Silent fail
- [ ] Creez `.claude/scripts/indexer.ps1`:
  - MAX_DEPTH=3
  - EXCLUDE: node_modules, venv, .git, .archive, dist, **pycache**, .vscode, .ruff_cache
  - Writes `.meta/sitemap.yaml`
- [ ] Creez `.claude/scripts/root-sweeper.ps1`:
  - Counts root files
  - WARN if >3
  - Lists offenders
- [ ] Test fiecare script manual

### E6 — RUNBOOK + CLAUDE.md slim (Task #8)

- [ ] Creez `RUNBOOK.md` (max 1 pagina):
  - Pornire: `python start.py`
  - Oprire: `python start.py stop`
  - Restart tunnel: `python start.py tunnel`
  - Backup manual: `curl POST /api/reports/backup`
  - Recovery DB: pasi exacti
  - Telegram Chat ID config
  - Tailscale URL access
  - Contact emergency
- [ ] Trim `CLAUDE.md` de la 13KB la <200 linii:
  - Sterge Project Status urias (mut in `docs/archive/faze_anterioare.md`)
  - Sterge How to Run detaliat (referinta in RUNBOOK)
  - Pastreaza: Overview, Architecture, Conventions, Known Issues, Rules referinta
  - **Fix referinta inexistenta `calculator_pret`** (Task #12)
- [ ] Creez `README.md` la radacina (max 100 linii) — overview pentru cititor extern

### E7 — Hooks auto-sync (Task #9)

- [ ] Update `.claude/hooks/post-edit-check.sh`:
  - Apel `sync-meta.ps1` silent fail
- [ ] Update `.claude/hooks/session-stop.sh`:
  - Apel `root-sweeper.ps1` + log warning
- [ ] Test: hooks NU blocheaza Edit/Write/MultiEdit
- [ ] Test: silent fail funcționează (exit 0 chiar la eroare)

### E7.5 — Validare + commit final (Task #10)

- [ ] **Rule 08 validation:**
  - [ ] Import check: `python -c "from app.main import app; print('Import OK')"`
  - [ ] Backend start: `python -m uvicorn app.main:app --port 8000`
  - [ ] Health check: `curl http://127.0.0.1:8000/api/health`
  - [ ] Frontend build: `cd frontend && npx vite build`
- [ ] **Rule 01 — Progress tracking:**
  - [ ] Update `docs/plan.md` (Faza 34: Restructurare DONE)
  - [ ] Update `CLAUDE.md` Project Status (slim version)
  - [ ] Update `.claude/PROJECT_STATUS.md`
- [ ] **Commit final:**
  - Mesaj: `Faza 34 partea 2: Restructurare Native Workspace aplicat selectiv`
  - Files: specific cu git add per directory
- [ ] **Verificare:**
  - [ ] Maximum 3 fisiere la radacina (excl. start.py, .gitignore, .gitattributes)
  - [ ] `.meta/`, `docs/`, `.workspace/`, `.archive/` create
  - [ ] Hooks functioneaza
  - [ ] CLAUDE.md sub 200 linii

---

## 5. Strategie commit Faza 34 (E0)

9 commit-uri logice, NU `git add -A`:

| #   | Subject                                                                                                      | Files                                                                                                                                                                                                                                            |
| --- | ------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1   | `feat(launcher): start.py unic + Cloudflare tunnel + watchdog (Faza 34)`                                     | `start.py`, `cloudflared/`, `scripts/`, `launch_roland.vbs`, `package-lock.json` (orfan ramane), `99_Roland_Work_Place/CLOUDFLARE_TUNNEL_SETUP.md`                                                                                               |
| 2   | `feat(timetracking): modul nou + tabela time_entries (migration 024)`                                        | `backend/modules/timetracking/`, `backend/migrations/024_imbunatatiri_v1.sql`, `frontend/src/pages/TimeTrackingPage.jsx`, `frontend/src/components/shared/FloatingTimer.jsx`, `frontend/src/modules/manifest.js`, `frontend/src/App.jsx` (route) |
| 3   | `feat(invoice): efactura.py — XML UBL 2.1 conform ANAF`                                                      | `backend/modules/invoice/efactura.py`                                                                                                                                                                                                            |
| 4   | `feat(search): routes_search.py — endpoint cautare cross-module`                                             | `backend/app/api/routes_search.py`, `backend/app/main.py` (registration)                                                                                                                                                                         |
| 5   | `feat(db): migrations 020-025 (vault expiry, task timeout, payment terms, translation cache, doc templates)` | `backend/migrations/020_*.sql` ... `025_*.sql`                                                                                                                                                                                                   |
| 6   | `feat(notepad+ai): voice input + claude-prep action + AI tools updates`                                      | `backend/modules/quick_tools/router_notepad.py`, `backend/modules/ai/tools.py`, `frontend/src/pages/NotepadPage.jsx`, `frontend/src/pages/AIChatPage.jsx`                                                                                        |
| 7   | `feat(pwa+ui): auto-update + mobile sidebar + theme toggle + responsive`                                     | `frontend/vite.config.js`, `frontend/src/components/Layout/Header.jsx`, `frontend/src/components/shared/CommandPalette.jsx`, restul `frontend/src/pages/*.jsx` modificate (Dashboard, FileBrowser, History, ITP, Invoice, Translator, Vault)     |
| 8   | `chore(config): limita extinse + rate limit disabled LAN + log capture`                                      | `backend/app/config.py`, `backend/app/main.py`, `backend/modules/reports/__init__.py`, `backend/modules/reports/system_reports.py`, `backend/modules/translator/models.py`, `backend/pyproject.toml`, `99_Roland_Work_Place/9.Poza_Android.jpeg` |
| 9   | `docs(checkpoint): RESUME + HANDOVER + TODO + recomandari (preparare restructurare)`                         | `RESUME_PUNCT_CURENT.md`, `HANDOVER_RESTRUCTURARE_2026-05-21.md`, `TODO.md`, `99_Roland_Work_Place/RECOMANDARI_IMBUNATATIRI.md`, `99_Roland_Work_Place/Calculator_pret/` (fisiere noi calibrare)                                                 |

Untracked tests (`backend/test_fisiere_noi.py`, `backend/test_match_and_recalc.py`) — discutie: sunt teste experimentale Faza 34? Daca da, commit 8 sau separare. Verific.

---

## 6. Jurnal executie (completat pe parcurs)

| Etapa | Status  | Start | End | Note |
| ----- | ------- | ----- | --- | ---- |
| E0    | PENDING |       |     |      |
| E1    | PENDING |       |     |      |
| E2    | PENDING |       |     |      |
| E3    | PENDING |       |     |      |
| E4    | PENDING |       |     |      |
| E5    | PENDING |       |     |      |
| E6    | PENDING |       |     |      |
| E7    | PENDING |       |     |      |
| E7.5  | PENDING |       |     |      |

**Issues intalnite:** (gol initial)

**Decizii pe parcurs:** (gol initial)

---

## 7. Rollback strategy

Daca ceva esueaza critic:

1. Abandon branch `restructurare-native-ws`
2. Return la master (deja contine Faza 34 commit-uri)
3. Investigare in `.workspace/investigations/` (creata in E4) cu RCA
4. Re-planificare daca scopuri trebuie ajustate

**Punct de safe abandonment per etapa:** dupa fiecare commit din E0; dupa fiecare etapa subsequenta — cleanup partial poate ramane si fi commit-at separat.

---

## 8. Validare succes finala

Dupa E7.5, urmatoarele trebuie sa fie ADEVARATE:

- [ ] `python start.py` porneste curat backend + frontend
- [ ] `python -c "from app.main import app"` OK
- [ ] `curl http://127.0.0.1:8000/api/health` returneaza 200
- [ ] Frontend build PASS
- [ ] Hooks `.claude/hooks/post-edit-check.sh` ruleaza fara eroare
- [ ] La radacina: maximum 5-6 entry-uri (README.md, RUNBOOK.md, CLAUDE.md, start.py, .gitignore, .gitattributes — exclud foldere `.archive/`, `.claude/`, etc.)
- [ ] `.meta/profile.yaml` valid YAML
- [ ] `.meta/status.yaml` reflecta starea reala (commit + branch + tests)
- [ ] `docs/plan.md` < 500 linii
- [ ] `CLAUDE.md` < 200 linii
- [ ] `RUNBOOK.md` ≤ 1 pagina
- [ ] Niciun link rupt in restul `.md`-urilor catre fisierele mutate
