# Plan implementare — Roland Command Center

> **Document curent** — sumar stare + roadmap viitor.
> Pentru istoric complet faze 0-33 (1236 linii detalii task-uri si decizii): `../99_Roland_Work_Place/0.0_PLAN_EXTINDERE_COMPLET.md`
> Pentru status structurat machine-readable: `../.meta/status.yaml`

---

## 1. Context

**Roland - Command Center** — panou personal multifuncțional: calc preț traduceri, traducător, facturare, ITP, AI pe documente, integrări externe, automatizări. Acces PC + Android prin Tailscale/Cloudflare.

**Stack:** FastAPI Python 3.13 + React 18 + Vite + SQLite (aiosqlite) + Tailwind.
**User:** Roland (CIP Inspection SRL, CUI 43978110) — single-user permanent.
**Buget:** Free tier only (zero cost).
**Deploy:** Local (Windows 10) + Tailscale local + Cloudflare Tunnel public + auto-start Task Scheduler.

---

## 2. Stare curenta (2026-05-22)

**Ultima faza completa:** Restructurare Native Workspace v2.1 — toate etapele E0-E7.5 ✅ DONE.
**Faza urmatoare:** ETAPA 2 — Integrare modul `bilingual_doc` (planned).

**Cifre cheie:**

- 14 module backend auto-discovered, 355 routes
- 26 pagini frontend
- 25 migrations SQL
- 86 teste backend pytest + 14 teste frontend vitest
- 33 faze completate

**Branch curent:** `restructurare-native-ws`
**Master ultim commit:** `5ec3beb` (Faza 34 — docs checkpoint)

---

## 3. Roadmap activ

### ETAPA 1 — Restructurare Native Workspace ✅ COMPLETA (2026-05-22)

Aplicare blueprint `c:/Proiecte/Blueprints/Roland_99/Blueprints_Restructurare_Nativ.md` SELECTIV (filtrat prin P13 scale lens + P14 tool overhead).

| Etapa | Status  | Continut                                                                                                   |
| ----- | ------- | ---------------------------------------------------------------------------------------------------------- |
| E0    | ✅ DONE | Commit Faza 34 in 8 commit-uri logice + branch dedicat                                                     |
| E1    | ✅ DONE | Cleanup radacina: mutare la docs/, .archive/, USER_WORKSPACE                                               |
| E2    | ✅ DONE | .meta/ minimal (profile + status + decisions + sitemap)                                                    |
| E3    | ✅ DONE | docs/plan.md + update referinte rules 01/02/03                                                             |
| E4    | ✅ DONE | .workspace/ (drafts + investigations + audit-outputs + scratchpad)                                         |
| E5    | ✅ DONE | 3 scripturi Python (sync-meta + indexer + root-sweeper) — schimbat din PS la Python pentru robustete UTF-8 |
| E6    | ✅ DONE | RUNBOOK.md (101 linii) + CLAUDE.md slim (146 linii) + README.md (67 linii)                                 |
| E7    | ✅ DONE | Hooks auto-sync wired (post-edit-check + session-stop)                                                     |
| E7.5  | ✅ DONE | Validare Rule 08 PASS (import + health + frontend build) + commit final                                    |

Plan detaliat: `../PLAN_RESTRUCTURARE_2026-05-21.md` (mut in .archive/ dupa E7.5).

### ETAPA 2 — Modul bilingual_doc (PLAN APROBAT 2026-05-22, 5 sub-faze)

Integrare sistem generator HTML print-ready bilingv DE/RO (extensibil multi-limbă) ca modul nou Roland. **Decizie: scriu nou modular conform skill global (NU refolosesc zip monolitic 247KB).**

**5 sub-faze secventiale (~14-19h total):**

| Faza                           | Continut                                                                                                                                                                                                 | Efort |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----- |
| **2.1** Backend Core           | Migration 026_bilingual_doc.sql (3 tabele) + 5 module (pdf_extractor, structure_parser, glossary_engine, translator_chain wrapper Faza 9, orchestrator) + API routes (POST upload, GET list, GET detail) | 4-5h  |
| **2.2** Rendering + Audit      | html_renderer (Jinja2 + CSS print A4 portrait/landscape auto-detect) + auditor (V1-V8 blocker) + integrare orchestrator                                                                                  | 3-4h  |
| **2.3** Frontend UI            | BilingualDocPage + 4 componente (Upload, Preview iframe, Audit dashboard, History) + manifest.js entry + App.jsx route lazy-loaded                                                                       | 3-4h  |
| **2.4** Glossary CRUD + Review | API CRUD glossary + UI editor + review decisions tracking (NEW/KEEP/FREEZE promovare) + seed DE→RO (chemistry, legal, water_tech) cu seed_flag=true                                                      | 2-3h  |
| **2.5** Testing + Polish       | Test E2E pe 3 ref docs (TrinkwV 65p + BAnz B12 26p + Fomar 1p) + GHID_TESTARE update + responsive mobile + merge final + push                                                                            | 2-3h  |

**Cerinte user confirmate:** Multi-limbă activ (DE, RO, EN, IT, HU, SK extensibil), glosar generic, selectabil UI, validare V1-V8 automata, backward compat.

**Decizii arhitecturale confirmate (ETAPA 2 briefing 2026-05-22):**

1. **Scriu nou modular** conform `02_architecture_modules.md` (NU port zip monolitic)
2. **Pipeline 5 pasi**: extract → parse → translate → render → audit
3. **HTML single-file** cu `data-lang` switching (CSS hide/show, NU duplicare DOM)
4. **Print A4 mix orientation**: portrait + landscape auto-detect (>5 col SAU col >20 char)
5. **REVIEW 3-state**: NEW → KEEP (1 doc) → FREEZE (2+ docs cu confirmare user)
6. **V1-V8 audit blocker** (spans balance, tag balance, contaminari diacritice, footer numerotare)
7. **NU meta-document automat** (Schlussseiten/Quellen — only la solicitare explicita)
8. **Footer minim**: doar `Pagina X / N`
9. **Seed-uri DE→RO marcate `seed_flag=true`** — NU FREEZE automat
10. **Process page-by-page streaming** pentru PDF 100+ pagini (NU all-at-once)

**Tabele DB Faza 2.1:**

```sql
bilingual_documents (id, filename, source_lang, target_langs[], domain, status, created_at, audit_yaml)
glossary_entries (id, source_lang, target_lang, source_term, target_term, state, domain_tags[], confidence, notes, seed_flag, created_at)
review_decisions (id, document_id, term_id, decision, decided_by, decided_at)
```

**Risc-uri identificate + mitigation:**

| Risc                              | Mitigation                                          |
| --------------------------------- | --------------------------------------------------- |
| PDF scanate (no extractable text) | Fallback EasyOCR (Faza 15A) — adauga ~30 min in 2.1 |
| Encoding diacritice Windows       | `PYTHONIOENCODING=utf-8` standard                   |
| Tabele complexe → landscape       | Heuristic >5 col sau col >20 char                   |
| Glosar polluted de seed-uri       | `seed_flag=true` separate, NU FREEZE auto           |
| Memory PDF 100+ pagini            | Page-by-page streaming                              |

**Resurse:**

- Skill global (9 docs): `~/.claude/skills/bilingual-doc-rendering/`
- Backend zip referinta: `~/.claude/context-snapshots/Traduceri-Bilingv-Sistem-2026-05-21/backend_archive.zip`
- 3 docs reale referinta: `c:/Users/ALIENWARE/Desktop/Roly/4. Artificial Inteligence/1.0_Traduceri/.../NOU/Finale/`
- HANDOVER detaliat: `docs/handovers/2026-05-21_restructurare.md`

### Follow-ups (post-ETAPA 1, ordine flexibila)

| #   | Item                                              | Task                                                                                                     | Efort                  |
| --- | ------------------------------------------------- | -------------------------------------------------------------------------------------------------------- | ---------------------- |
| 1   | **MERGE CalculatorPage + CalculatorAdvancedPage** | Combinare /calc + /calculator intr-o pagina cu toggle basic/advanced (Task #11)                          | 1-2h                   |
| 2   | **Telegram Chat ID config**                       | User configureaza Chat ID real (numeric din getUpdates)                                                  | 5 min user             |
| 3   | **Telegram notificari active**                    | Cron alert ITP expiry + facturi scadente + backup status                                                 | 1-2h                   |
| 4   | **Gmail App Password**                            | User configureaza in .env GMAIL_APP_PASSWORD                                                             | 10 min user            |
| 5   | **Test Android prin Tailscale**                   | User testeaza fiecare pagina, raporteaza bug-uri responsive                                              | 30 min user            |
| 6   | **AXA F — Polish mobile/responsive**              | Fix bug-uri Android dupa testare                                                                         | 2-3h                   |
| 7   | **Import ITP inspectii CSV**                      | User pregateste CSV + import                                                                             | 1-2h user + 30 min cod |
| 8   | **Adaugare clienti reali**                        | ANAF auto-fill + manual entry                                                                            | 30-60 min user         |
| 9   | **AXA B — Calibrare pricing**                     | Reduce MAPE 32% → sub 15% prin date reale (necesita 50+ perechi document-pret)                           | 3-4h dupa date         |
| 10  | **Fix 3 teste pre-existente**                     | test_filemanager_search (MemoryError FTS5), test_translate_en_ro (DeepL), test_vault_key_get_nonexistent | 1-2h                   |
| 11  | **Diagnostics complete**                          | IndexedDB offline queue + source maps + AI report endpoint (din Roland_Diagnostics_v1 blueprint)         | 6-8h                   |
| 12  | **Circuit breaker generic**                       | Skeleton 03 — wrapper pentru AI providers + integrations                                                 | 1h                     |

Pentru detalii actiuni manuale user: `docs/todo.md`.

---

## 4. Decizii arhitecturale cheie

Vezi `.meta/decisions.yaml` pentru lista completa (13 entries). Highlight:

- **D02** — Free tier exclusively (chain providers in `.claude/rules/06-free-tier-enforcement.md`)
- **D04** — Module auto-discovery (backend/modules/[name]/ + manifest.js frontend)
- **D06** — Cerebras Qwen3-235B primar pentru claude-prep (NU Gemini — 250 RPD limit)
- **D07** — Rate limit DISABLED pentru LAN/Tailscale/Cloudflare IPs (single-user)
- **D09** — Launcher unic Python (NU .bat — sters START_Roland.bat)
- **D11** — USER_WORKSPACE = 99_Roland_Work_Place/ (NU mutat la .workspace/)
- **D12** — Aplicare blueprint Native Workspace SELECTIVA (skip JSON schemas + MCP guard + status-board)
- **D13** — API_KEYS migrat la sistem central `C:/Users/ALIENWARE/.api-keys/`

---

## 5. Reguli operationale

8 reguli proiect in `.claude/rules/`:

1. `01-progress-tracking.md` — Update plan + HTML + CLAUDE + PROJECT_STATUS dupa fiecare implementare
2. `02-pre-implementation.md` — Briefing complet + confirmation user inainte de orice Wave/Faza
3. `03-validation-and-testing.md` — Teste + GHID_TESTARE + user confirmation
4. `04-code-safety.md` — Git safety, URL hardcoded check, DB migration check
5. `05-rule-governance.md` — Protocol modificare reguli + priority local > global
6. `06-free-tier-enforcement.md` — Zero cost policy + approved provider chains
7. `07-error-handling.md` — No silent catch + global toast + diagnostics panel
8. `08-post-change-validation.md` — Rule 08 — verify full system startup dupa orice cod modification

Comenzi proiect: `/update-status`, `/pre-wave`, `/test-guide`, `/rule-change`.

---

## 6. Resurse externe

| Resursa                              | Locatie                                                 |
| ------------------------------------ | ------------------------------------------------------- |
| Istoric complet 33 faze (1236 linii) | `../99_Roland_Work_Place/0.0_PLAN_EXTINDERE_COMPLET.md` |
| Status structurat YAML               | `../.meta/status.yaml`                                  |
| Decizii arhitecturale                | `../.meta/decisions.yaml`                               |
| Sitemap proiect                      | `../.meta/sitemap.yaml`                                 |
| Catalog API gratuite                 | `../99_Roland_Work_Place/CATALOG_API_GRATUITE.md`       |
| Ghid acces remote                    | `../99_Roland_Work_Place/GHID_ACCES_REMOTE.md`          |
| Roadmap implementare                 | `../99_Roland_Work_Place/ROADMAP_IMPLEMENTARE.md`       |
| GHID testare manuala                 | `../99_Roland_Work_Place/GHID_TESTARE.md`               |
| Operatiuni urgenta                   | `../RUNBOOK.md` (planned E6)                            |
| HANDOVER restructurare               | `handovers/2026-05-21_restructurare.md`                 |
| Audit-uri externe Gemini             | `audit-externe/gemini-2026-04-09/`                      |
| Resume sesiune                       | `resume.md`                                             |
| TODO actiuni manuale                 | `todo.md`                                               |

---

## 7. Indicatori de urmarit

| Indicator            | Acum     | Target | Sursa                           |
| -------------------- | -------- | ------ | ------------------------------- |
| MAPE Pricing         | 32%      | <15%   | Calibrare cu date reale (AXA B) |
| Date reale import    | ~5%      | 80%+   | ITP + clienti + facturi reale   |
| Teste backend        | 86       | 120+   | pytest backend                  |
| Teste frontend       | 14       | 30+    | vitest frontend                 |
| API Keys functionale | 6/10     | 8+     | env vars + cod                  |
| Mobile usability     | Netestat | 90%+   | Test Android                    |
| Routes backend       | 355      | —      | live count                      |
| Modules backend      | 14       | —      | live count                      |

---

## 8. Conventii proiect

- Toate user-facing strings in **Romana**
- Cod, log messages, var names in **English**
- Currency RON, no VAT
- Languages EN ↔ RO only
- Single user, NO multi-user auth
- AI/API providers exclusively free tier
- Work files in `99_Roland_Work_Place/` (USER_WORKSPACE)
- AI work files in `.workspace/` (planned E4)
- Git: add specific files, NEVER `git add -A`
- Python: always `set PYTHONIOENCODING=utf-8` + `python -m pip`, `python -m uvicorn`
- Module discovery: folder in `backend/modules/[name]/` cu `__init__.py MODULE_INFO`
- Frontend route: entry in `frontend/src/modules/manifest.js`
