# HANDOVER — Restructurare Roland & Integrare Modul Bilingv

> Document creat la 2026-05-21 din sesiunea de finalizare a sistemului de generare bilingv DE/RO.
> Citește acest document la deschiderea sesiunii de restructurare Roland.

## Context

Există un sistem funcțional de generare HTML print-ready bilingv (DE/RO, extensibil multi-limbă) care a produs 3 documente reale și este complet documentat ca **blueprint generic**. Vrem să integrăm acest sistem ca modul nou în Roland Command Center.

**Decizie aprobată de user**: restructurăm Roland PRIMA (conform blueprint dedicat), apoi adăugăm modulul bilingv. Asta evită amplificarea dezordinii și permite slot clar de integrare.

## Plan execuție (2 etape mari)

### ETAPA 1 — Restructurare Roland (sesiunea aceasta sau imediat următoare)

**Sursă blueprint**: `c:\Proiecte\Blueprints\Roland_99\Blueprints_Restructurare_Nativ.md` (50 KB, 16 variants A-T, etape E0-E7.5)

**Plus**: `c:\Proiecte\Blueprints\Roland_99\SYMBIOTE_transfer_functionalitati.md` (12 KB) — pattern pentru transferul modulelor între proiecte (relevant pentru ETAPA 2)

**Pași recomandați**:

1. **Citește blueprint integral** Native Workspace Pattern (12 principii P1-P12)
2. **Detectează variant Roland** (probabil B/D/G — full-stack Python FastAPI + React Vite + SQLite + AI providers)
3. **Creează `.meta/profile.yaml`** cu variant + composition pentru sub-features
4. **Aplică etape E0-E7.5** din blueprint:
   - E0: audit stadiu actual
   - E1: separare cod LIVE vs narrativ vs status structurat vs zona de lucru
   - E2: creare structură root curat (max 3 fișiere)
   - E3: migrare fișiere conform variant
   - E4: hooks auto-sync (PostToolUse pentru regenerare status)
   - E5: JSON schemas în `.meta/schemas/` pentru validare YAML
   - E6: RUNBOOK.md pentru bus factor minim 2
   - E7: Root Sweeper hook pentru `/checkpoint`
   - E7.5: validare finală + commit
5. **Validare cu hooks existente** din `.claude/hooks/` (post-edit-check.sh, pre-compact.sh, session-start.sh)

### ETAPA 2 — Integrare modul `bilingual_doc` (sesiune ulterioară)

**Sursă blueprint sistem**: `~/.claude/skills/bilingual-doc-rendering/` (9 documente)

**Resurse disponibile**:

- `SKILL.md` — entrypoint + when-to-use
- `01_workflow_general.md` — pipeline 5 pași
- `02_architecture_modules.md` — 8 module backend + 4 frontend + DB schema completă (migration `0NN_bilingual_doc.sql`)
- `03_glossary_framework_generic.md` — glosar generic (orice pereche limbi, orice domeniu)
- `04_review_system_3state.md` — algoritm NEW/KEEP/FREEZE
- `05_html_templates_multilang.md` — Jinja2 templates + CSS print A4
- `06_audit_validation_rules.md` — V1-V8 validări automate
- `07_extending_new_lang_domain.md` — cum adaugi limbă/domeniu/format nou
- `08_lessons_pitfalls.md` — 15 lecții din implementarea reală

**Resurse pentru implementare**:

- **Backend arhivat (zip 255 KB)**: `~/.claude/context-snapshots/Traduceri-Bilingv-Sistem-2026-05-21/backend_archive.zip` — conține 5 generatoare Python + 13 module spec + register + audit-uri
- **Snapshot detalii decizii**: `~/.claude/context-snapshots/Traduceri-Bilingv-Sistem-2026-05-21/snapshot.md`
- **Cele 3 documente livrate (exemplar)**: `c:\Users\ALIENWARE\Desktop\Roly\4. Artificial Inteligence\1.0_Traduceri\1.0_Traduceri_in_Lucru\NOU\Finale\`

**Pași integrare**:

1. **Refactor** generatorul Python monolitic (247KB) în 8 module mici (vezi `02_architecture_modules.md`)
2. **Migrație SQL** `0NN_bilingual_doc.sql` (3 tabele: bilingual_documents, glossary_entries, review_decisions)
3. **Backend FastAPI routes**: upload PDF, list documents, get document, glossary CRUD, review decisions
4. **Frontend React**: BilingualDocUpload + Preview + Audit + History (vezi component breakdown)
5. **Integrare cu Roland Faza 9 Translator** (5 providers existenți: DeepL → Azure → Google → Gemini → OpenAI)
6. **Integrare cu Roland Glossary per client** (Faza 9 deja are infrastructure)
7. **Adăugare în module_discovery** Roland (plug-and-play)
8. **Migrare seed-uri** din spec_modules/30-32 ca preset glossary DE→RO

## Cerințe utilizator pentru ETAPA 2

1. **Multi-limbă activă**: DE, RO, EN, IT, HU, SK (extensibil oricând)
2. **Glosar generic**: NU legat de 3 fișiere DE→RO existente — trebuie să funcționeze pentru EN, SK, sau orice combinație
3. **Selectabil din UI**: limbile target alese explicit per document
4. **Calitate**: aceeași calitate ca exemplarele livrate (validare V1-V8 automată)
5. **Backward compat**: nu strica nimic din Roland existent

## Output ETAPA 2 dorit

User va putea în Roland UI:

- Upload PDF nou (orice limbă source)
- Selectează limbi target (default RO, dar multi-select)
- Selectează domeniu (medical, legal, water_tech, financial, IT, sau "general")
- Apasă "Generate"
- Vede preview HTML cu toolbar switch limbi
- Vede dashboard audit (V1-V8 metrici)
- Descarcă HTML + PDF + audit YAML
- Vede istoric documente generate
- Editează glossary (per termen, per client, per domain)

## Decizii arhitecturale luate

- **Pattern HTML single-file**: tot CSS+JS embedded — portabil
- **`data-lang` switching**: spans toate prezente, CSS ascunde/arată — NU duplicare DOM
- **Print-ready A4 mix orientation**: portrait + landscape auto-detect pe tabele
- **REVIEW 3-state** (NEW/KEEP/FREEZE): marker progresiv
- **Glosar (source_lang, target_lang, term, state, domain_tags[])**: schemă generică

## Decizii la cleanup aplicate (pentru consistență cu noile documente generate)

User a cerut explicit eliminare:

- ❌ Disclaimer footer "Inoffizielle / Traducere neoficială"
- ❌ URL sursă în footer
- ❌ Note "(PDF: N pagini)" în numerotare
- ❌ Notice "MVP" sau "Sicherheitshinweis" pe pagina 1
- ❌ Pagini Schlussseiten (meta-document — Quellen, Validierungsstatus, Hinweise utilizare)
- ✅ Format final: doar `Pagina X / N` în footer

**Regulă derivată implementată în skill global**: niciodată meta-document automat fără solicitare explicită.

## Locații cheie

| Resursă                     | Path                                                                                                         |
| --------------------------- | ------------------------------------------------------------------------------------------------------------ |
| Blueprint restructurare     | `c:\Proiecte\Blueprints\Roland_99\Blueprints_Restructurare_Nativ.md`                                         |
| Symbiote transfer           | `c:\Proiecte\Blueprints\Roland_99\SYMBIOTE_transfer_functionalitati.md`                                      |
| Skill global bilingv        | `~/.claude/skills/bilingual-doc-rendering/`                                                                  |
| Snapshot sesiune anterioară | `~/.claude/context-snapshots/Traduceri-Bilingv-Sistem-2026-05-21/`                                           |
| Backend zip                 | `~/.claude/context-snapshots/Traduceri-Bilingv-Sistem-2026-05-21/backend_archive.zip`                        |
| Exemplare livrate           | `c:\Users\ALIENWARE\Desktop\Roly\4. Artificial Inteligence\1.0_Traduceri\1.0_Traduceri_in_Lucru\NOU\Finale\` |

## Pași imediați la deschidere sesiune nouă în Roland

1. Citește acest fișier (`HANDOVER_RESTRUCTURARE_2026-05-21.md`)
2. Rulează `/onboard` sau `/status` pentru context Roland general
3. Întreabă user-ul: "Pornim restructurarea Roland conform blueprint (ETAPA 1) sau direct cu integrare modul bilingv (ETAPA 2)?"
4. **Recomandare**: ETAPA 1 prima (restructurare), ETAPA 2 după validarea structurii noi.

## După finalizarea ambelor etape

Acest fișier `HANDOVER_RESTRUCTURARE_2026-05-21.md` se poate șterge sau muta în `archive/` per blueprint Native Workspace (principiul P7 — Arhiva over delete).
