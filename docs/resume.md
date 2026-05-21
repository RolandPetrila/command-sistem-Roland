# RESUME — Roland Command Center · Punct curent

> **Pentru reluare în terminal nou:** rulează `/onboard` sau cere "citește docs/resume.md si continua".

## 📍 Stare la 2026-05-22

| Item                | Valoare                                                                        |
| ------------------- | ------------------------------------------------------------------------------ |
| Branch              | `master`                                                                       |
| Ultimul commit      | `c0d3d40` Merge Restructurare Native Workspace v2.1 (ETAPA 1)                  |
| Push origin master  | ✅ DONE (31921b7..c0d3d40)                                                     |
| Faza activă         | **ETAPA 2 — Modul `bilingual_doc`** (PLAN APROBAT, gata de start Faza 2.1)     |
| ETAPA 1 status      | ✅ COMPLETA (8 commit-uri restructurare merged)                                |
| URL public live     | quick tunnel — verifica `python start.py` pentru URL curent                    |
| Auto-start la login | ✅ Task Scheduler `RolandCC_AutoStart`                                         |
| Watchdog erori      | ✅ În `start.py` (cap 5 restart/proces)                                        |
| Rate limit LAN      | ✅ Dezactivat (single-user)                                                    |
| Hooks auto-sync     | ⚠️ Wired in script-uri, AWAITING user manual register in `settings.local.json` |

## ✅ ETAPA 1 — Restructurare Native Workspace (DONE 2026-05-22)

8 commit-uri pe branch `restructurare-native-ws` merged in master (`c0d3d40`):

- E0: 8 commit-uri Faza 34 logice + branch
- E1: Cleanup radacina (15→7 fisiere)
- E2: `.meta/` minimal (4 YAML: profile + status + decisions + sitemap)
- E3: `docs/plan.md` curent + update rules 01/02/03
- E4: `.workspace/` (drafts + investigations + audit-outputs)
- E5: 3 scripturi Python (`sync-meta.py`, `indexer.py`, `root-sweeper.py`)
- E6: `RUNBOOK.md` + `CLAUDE.md` slim 146 linii + `README.md` 67 linii
- E7: Hooks wired (`post-edit-check.sh` + `session-stop.sh`)
- E7.5: Validare Rule 08 PASS + final commit + merge + push

## 🎯 URMATORUL PAS — ETAPA 2 Faza 2.1

**Continui cu**: `Faza 2.1 — Backend Core bilingual_doc`

**Scope Faza 2.1 (~4-5h)**:

1. **Migration `026_bilingual_doc.sql`** — 3 tabele:
   - `bilingual_documents (id, filename, source_lang, target_langs[], domain, status, created_at, audit_yaml)`
   - `glossary_entries (id, source_lang, target_lang, source_term, target_term, state, domain_tags[], confidence, notes, seed_flag, created_at)`
   - `review_decisions (id, document_id, term_id, decision, decided_by, decided_at)`

2. **5 module backend** in `backend/modules/bilingual_doc/`:
   - `pdf_extractor.py` — PyMuPDF per-pagina text + blocks + tabele
   - `structure_parser.py` — regex §N, (N), tabele, anexe
   - `glossary_engine.py` — FREEZE/KEEP/NEW priority lookup + domain_tags
   - `translator_chain.py` — wrapper peste Faza 9 (5 providers) + cache TM
   - `orchestrator.py` — Pipeline 5 pasi coordinator

3. **API routes** in `router.py`:
   - `POST /api/bilingual/upload` (multipart PDF + target_langs + domain)
   - `GET /api/bilingual/documents` (list paginated)
   - `GET /api/bilingual/documents/{id}` (detalii + status)

4. **MODULE_INFO** in `__init__.py` (plug-and-play auto-discovery)

**Validare Faza 2.1**: `curl POST` PDF → JSON cu pagini extrase + glossary lookups + traduceri partial. Headless, NU UI inca.

## 🚀 Plan complet ETAPA 2 (5 sub-faze, ~14-19h total)

| Faza | Continut                                                                               | Efort |
| ---- | -------------------------------------------------------------------------------------- | ----- |
| 2.1  | Backend Core (migration + 5 module + API routes)                                       | 4-5h  |
| 2.2  | Rendering + Audit (Jinja2 templates + V1-V8 validari)                                  | 3-4h  |
| 2.3  | Frontend UI (BilingualDocPage + 4 componente)                                          | 3-4h  |
| 2.4  | Glossary CRUD + Review System (UI editor + seed DE→RO)                                 | 2-3h  |
| 2.5  | Testing + Polish (E2E pe 3 ref docs + GHID_TESTARE + responsive mobile + merge + push) | 2-3h  |

## 📚 Resurse pregatite pentru ETAPA 2

| Resursa               | Path                                                                                                         |
| --------------------- | ------------------------------------------------------------------------------------------------------------ |
| Skill global (9 docs) | `~/.claude/skills/bilingual-doc-rendering/`                                                                  |
| Backend zip (255 KB)  | `~/.claude/context-snapshots/Traduceri-Bilingv-Sistem-2026-05-21/backend_archive.zip`                        |
| Snapshot decizii      | `~/.claude/context-snapshots/Traduceri-Bilingv-Sistem-2026-05-21/snapshot.md`                                |
| 3 exemplare livrate   | `c:\Users\ALIENWARE\Desktop\Roly\4. Artificial Inteligence\1.0_Traduceri\1.0_Traduceri_in_Lucru\NOU\Finale\` |
| Handover detaliat     | `docs/handovers/2026-05-21_restructurare.md`                                                                 |

## 🔑 Decizii arhitecturale ETAPA 2 confirmate

1. **Scriu nou modular** conform `02_architecture_modules.md` din skill global (NU refolosesc zip monolitic 247KB)
2. **5 sub-faze secventiale** cu commit + validare Rule 08 per faza
3. **Multi-limba activ**: DE, RO, EN, IT, HU, SK (extensibil)
4. **Glosar generic** (NU hardcoded pereche limbi/domeniu) — seed DE→RO doar ca punct plecare cu `seed_flag=true`
5. **Pattern HTML single-file** cu `data-lang` switching (CSS hide/show — NU duplicare DOM)
6. **Print A4 mix orientation** portrait + landscape auto-detect (>5 col SAU col >20 char)
7. **REVIEW 3-state** progresiv: NEW → KEEP (1 doc) → FREEZE (2+ docs cu confirmare user)
8. **V1-V8 audit blocker** (toate trebuie PASS pentru release HTML)
9. **NU meta-document automat** (Schlussseiten/Quellen/Validierungsstatus — only la solicitare explicita)
10. **Footer minim**: doar `Pagina X / N` (NU disclaimer, NU URL, NU "(PDF: N pagini)")

## 📋 PENTRU TERMINAL NOU

```bash
# Pas 1 — Deschide Claude Code in
cd C:\Proiecte\NOU_Calculator_Pret_Traduceri

# Pas 2 — Cere context
"/onboard"   # va citi acest fisier + CLAUDE.md + .meta/status.yaml + git log

# Pas 3 — Pornire ETAPA 2 Faza 2.1
"continui ETAPA 2 din punctul curent — pornim Faza 2.1 backend core bilingual_doc"
```

## ⚠️ Context critic — NU repeta greseli

- **NU re-crea .bat** — folosesc DOAR `python start.py`
- **NU edita `.claude/settings.local.json`** — self-mod classifier blocheaza. User editeaza manual
- **NU porni backend fara `--reload`** — duce la regresie stale code
- **NU pune Gemini ca primar pentru `claude-prep`** — 250 RPD se atinge rapid. Cerebras Qwen3-235B e regula
- **NU readuce rate limit pe LAN** — single-user
- **NU `git add -A`** — adauga fisiere specifice (rule 04)
- **NU comit token-uri/chei in plaintext** — sistem central API keys deja
- **NU re-folosi cod monolitic zip** pentru bilingual_doc — scriu nou conform skill
- **NU edita PowerShell scripturi cu UTF-8 fara BOM** — folosesc Python pentru `.claude/scripts/`

## 🔧 Task-uri active (TaskList state)

| #   | Status  | Subject                                                                           |
| --- | ------- | --------------------------------------------------------------------------------- |
| 11  | pending | DECIZIE ULTERIOARA — MERGE CalculatorPage + CalculatorAdvancedPage (post-ETAPA 2) |
| 13  | pending | Faza 2.1 — Backend Core bilingual_doc                                             |
| 14  | pending | Faza 2.2 — Rendering + Audit                                                      |
| 15  | pending | Faza 2.3 — Frontend UI                                                            |
| 16  | pending | Faza 2.4 — Glossary CRUD + Review System                                          |
| 17  | pending | Faza 2.5 — Testing + Polish                                                       |

(Task-urile 1-10 + 12 deja completed pentru ETAPA 1 + follow-up CLAUDE.md fix.)

---

**Generat de:** `/checkpoint` la 2026-05-22 dupa aprobare plan ETAPA 2
