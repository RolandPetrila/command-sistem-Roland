Plan: Restructurare completă reguli + documentație — Roland Command Center

 Context

 Utilizatorul dorește reorganizarea completă a sistemului de reguli și documentație al proiectului folosind TOATE mecanismele disponibile  
 în Claude Code: .claude/rules/, .claude/commands/, .claude/agents/, hooks, nested CLAUDE.md, memory. Scopul principal: orice sesiune nouă 
  Claude Code să aibă instant contextul complet al proiectului, fără re-citire manuală.

 Cerințe din 99_Roland_Work_Place/Restructurare_Regulamente.md (6 puncte principale):
 1. Regulă testare per fază → .claude/rules/
 2. Prezentare toate regulile + opinie
 3. Analiză fișiere + propunere reorganizare
 4. Auto-update documente la fiecare execuție
 5. Agent/regulă guvernanță reguli cu log
 6. Status live proiect pentru orice sesiune/terminal

 Corecții din z_Cerere2_Restructurare_Regulamente.md (6 probleme + 1 regulă nouă):
 - P1: R-CLEAN/R-WORK din global NU se aplică aici → regulă prioritate
 - P2: R-SYNC NU se aplică (nu e proiect regulament multi-AI)
 - P3: R-SNAPSHOT NU se aplică (tracking prin PLAN_EXTINDERE, nu PENDING_IMPLEMENTARI)
 - P4: PLAN_EXECUTIE.md RĂMÂNE în rădăcină (NU se arhivează)
 - P5: git add pe fișiere specifice, NICIODATĂ git add -A
 - P6: Pre-implementation briefing din proiect ÎNLOCUIEȘTE R-BRIEF + R-MODE din global
 - REGULĂ NOUĂ: Prioritate reguli locale > globale la conflict

 ---
 Pas 1 — Git commit înainte de restructurare (Regula 3 — Git Safety)

 Commit tot ce e necomis (fișiere specifice, NU -A):
 cd C:/Proiecte/NOU_Calculator_Pret_Traduceri
 git add CLAUDE.md 99_Roland_Work_Place/ backend/modules/filemanager/ frontend/src/pages/FileBrowserPage.jsx
 git commit -m "Pre-restructurare: Faza 14 implementată + Regula 12 + GHID_TESTARE"

 ---
 Pas 2 — Creare directoare noi

 .claude/rules/          # reguli auto-citite la fiecare mesaj
 .claude/commands/       # comenzi slash custom
 .claude/agents/         # agenți cu prompt dedicat
 .claude/hooks/          # scripturi bash pentru hooks
 99_Roland_Work_Place/archive/   # fișiere deprecated

 ---
 Pas 3 — Consolidare 12 reguli → 5 fișiere în .claude/rules/

 Mapare reguli vechi → noi:

 ┌──────────────────────────────┬────────────────────────────────────────────────────────────────────┬──────────────┐
 │          Fișier nou          │                              Conține                               │ Reguli vechi │
 ├──────────────────────────────┼────────────────────────────────────────────────────────────────────┼──────────────┤
 │ 01-progress-tracking.md      │ Update plan, regen HTML, update CLAUDE.md status, test markers     │ R1+R2+R7+R10 │
 ├──────────────────────────────┼────────────────────────────────────────────────────────────────────┼──────────────┤
 │ 02-pre-implementation.md     │ Dependency check, briefing sumar, prezentare detaliată, confirmare │ R6+R8+R11    │
 ├──────────────────────────────┼────────────────────────────────────────────────────────────────────┼──────────────┤
 │ 03-validation-and-testing.md │ Validare wave, creare/update GHID_TESTARE.md                       │ R9+R12       │
 ├──────────────────────────────┼────────────────────────────────────────────────────────────────────┼──────────────┤
 │ 04-code-safety.md            │ Git safety, URL hardcoded check, DB migration check                │ R3+R4+R5     │
 ├──────────────────────────────┼────────────────────────────────────────────────────────────────────┼──────────────┤
 │ 05-rule-governance.md        │ Protocol modificare reguli, conflict check, logging                │ NOU          │
 └──────────────────────────────┴────────────────────────────────────────────────────────────────────┴──────────────┘

 De ce merge consolidarea:

 - R1+R2+R7+R10 se declanșează toate "după implementare" → un checklist
 - R8+R11+R6 se declanșează toate "înainte de implementare" → o poartă
 - R9+R12 ambele post-fază → un workflow
 - R3+R4+R5 sunt toate verificări de cod → un fișier
 - Nimic nu se pierde, doar se grupează logic

 Conținut fiecare fișier:

 01-progress-tracking.md — Trigger: După FIECARE implementare. Checklist:
 1. Marchează ✅/🔄/⏸️  în 0.0_PLAN_EXTINDERE_COMPLET.md cu data și status testare
 2. Regenerează 0.0_PLAN_EXTINDERE_COMPLET.html (array PHASES)
 3. Actualizează Project Status din CLAUDE.md
 4. Actualizează .claude/PROJECT_STATUS.md (snapshot)
 5. Automat, fără confirmare

 02-pre-implementation.md — Trigger: ÎNAINTE de orice Wave/Fază. OBLIGATORIU:
 1. Verifică dependințe cross-fază din plan
 2. Sugerează faze logice (dependințe rezolvate → efort mic → valoare mare)
 3. Prezintă tabel sumar: Feature | Exemplu concret | Efort
 4. Pentru FIECARE funcție: stare curentă → stare viitoare → exemplu → tehnologie
 5. Recomandare ce să prioritizeze, ce se poate amâna
 6. AȘTEAPTĂ confirmare explicită

 03-validation-and-testing.md — Trigger: La finalizarea oricărei faze. OBLIGATORIU:
 1. Testează toate funcționalitățile implementate
 2. Creează/actualizează 99_Roland_Work_Place/GHID_TESTARE.md:
   - Pași test Web (PC) + Test Telefon (Android)
   - Rezultat așteptat + Status
 3. Fix imediat dacă ceva nu funcționează
 4. NU se trece la faza următoare fără confirmare utilizator
 5. Marchează statusul testării: ✅ Android OK | ✅ Local OK | 🧪  Netestat

 04-code-safety.md — Trigger: La modificarea codului:
 1. Git Safety (înainte de refactorizare majoră): verifică modificări necomise → propune commit
 2. URL Check (la editarea client.js): NU hardcoded localhost, folosește window.location.origin
 3. DB Migration Check (la editarea app/db/ sau modules/*/models.py): verifică fișier SQL în migrations/

 05-rule-governance.md — Trigger: Când utilizatorul cere modificare/adăugare/ștergere regulă:
 1. Citește TOATE regulile existente din .claude/rules/
 2. Analizează cererea: consistență logică, conflicte cu reguli existente
 3. Adaptează formularea regulii pentru claritate
 4. Prezintă BEFORE/AFTER
 5. DUPĂ confirmare: aplică și loghează în 99_Roland_Work_Place/CHANGELOG_RULES.md
 6. Format log: ### [YYYY-MM-DD] — [fișier] — [ADD/MODIFY/DELETE] + Before/After/Reason

 Include secțiune PRIORITATE REGULI:
 - Regulile din .claude/rules/ și CLAUDE.md per-proiect au PRIORITATE față de ~/.claude/CLAUDE.md global la conflict direct
 - Regulile globale specifice folderului 00_Regulament_Claude_Code NU se aplică aici:
   - R-CLEAN — nu se aplică (structura proiectului e definită în CLAUDE.md local)
   - R-WORK — nu se aplică (convențiile locale: 99_Roland_Work_Place/ fără subfoldere datate)
   - R-SYNC — nu se aplică (proiectul nu are echivalent Gemini/Codex)
   - R-SNAPSHOT — nu se aplică (tracking prin PLAN_EXTINDERE + .claude/rules/, nu PENDING_IMPLEMENTARI.md)
 - R-BRIEF și R-MODE din global → ÎNLOCUITE de 02-pre-implementation.md pentru task-uri din acest proiect. Un singur briefing, nu 3        
 suprapuse.

 ---
 Pas 4 — Creare 4 comenzi slash în .claude/commands/

 ┌────────────────┬──────────────────┬──────────────────────────────────────────────────────────────────────┐
 │    Comandă     │      Fișier      │                               Ce face                                │
 ├────────────────┼──────────────────┼──────────────────────────────────────────────────────────────────────┤
 │ /update-status │ update-status.md │ Actualizează plan .md, HTML, CLAUDE.md status, PROJECT_STATUS.md     │
 ├────────────────┼──────────────────┼──────────────────────────────────────────────────────────────────────┤
 │ /pre-wave      │ pre-wave.md      │ Pre-implementation briefing complet (dependency + summary + details) │
 ├────────────────┼──────────────────┼──────────────────────────────────────────────────────────────────────┤
 │ /test-guide    │ test-guide.md    │ Creează/actualizează GHID_TESTARE.md cu pași Web + Android           │
 ├────────────────┼──────────────────┼──────────────────────────────────────────────────────────────────────┤
 │ /rule-change   │ rule-change.md   │ Procesează cerere modificare regulă prin protocol guvernanță         │
 └────────────────┴──────────────────┴──────────────────────────────────────────────────────────────────────┘

 ---
 Pas 5 — Creare agent în .claude/agents/

 rule-guardian.md — Agent read-only care:
 - Citește toate regulile din .claude/rules/
 - Analizează cererea de modificare
 - Verifică conflicte
 - Prezintă regula adaptată
 - Loghează modificarea

 Tools restricționate: Read, Grep, Glob (nu poate modifica fișiere singur).

 ---
 Pas 6 — Creare hook scripts în .claude/hooks/

 session-start.sh — La deschiderea sesiunii:
 - Citește și afișează .claude/PROJECT_STATUS.md (snapshot compact)
 - Read-only, idempotent

 session-stop.sh — La închiderea sesiunii:
 - Afișează reminder: "Dacă ai implementat ceva, rulează /update-status"
 - Read-only, idempotent

 post-edit-check.sh — După fiecare Edit/Write:
 - Verifică URL hardcoded în client.js
 - Verifică schema DB change fără migrare
 - Read-only, doar afișează warnings

 pre-compact.sh — Înainte de compactarea contextului:
 - Regenerează .claude/PROJECT_STATUS.md cu status curent din CLAUDE.md
 - Singurul hook care scrie (necesar pentru a supraviețui compactării)

 ---
 Pas 7 — Actualizare settings.local.json

 Merge hooks cu permisiunile existente:
 {
   "permissions": { ... (păstrate exact) },
   "hooks": {
     "SessionStart": [{ "hooks": [{ "type": "command", "command": "bash .claude/hooks/session-start.sh", "timeout": 5 }] }],
     "Stop": [{ "hooks": [{ "type": "command", "command": "bash .claude/hooks/session-stop.sh", "timeout": 5 }] }],
     "PostToolUse": [{ "hooks": [{ "type": "command", "command": "bash .claude/hooks/post-edit-check.sh", "timeout": 5 }], "matcher":      
 "Edit|Write" }],
     "PreCompact": [{ "hooks": [{ "type": "command", "command": "bash .claude/hooks/pre-compact.sh", "timeout": 5 }] }]
   }
 }

 ---
 Pas 8 — Slim CLAUDE.md (354 → ~150 linii)

 Ce RĂMÂNE:
 - Project Overview (12 linii)
 - Location (5 linii)
 - Project Status — comprimat la tabel compact, 1 linie per fază (~20 linii)
 - How to Run (34 linii)
 - Architecture (10 linii)
 - Key Files — comprimat (~15 linii)
 - Conventions (13 linii)
 - Pointer secțiune: "Reguli detaliate: .claude/rules/ | Comenzi: /update-status, /pre-wave, /test-guide, /rule-change" (5 linii)
 - Known Issues — comprimat, eliminate cele rezolvate (5 linii)

 Ce se ELIMINĂ din CLAUDE.md:
 - Toate cele 12 reguli detaliate (142 linii) → mută în .claude/rules/
 - Implementation Summary table (20 linii) → redundant cu Project Status
 - Checkbox-uri detaliate per wave (30 linii) → comprimate la 1 linie/fază

 ---
 Pas 9 — Creare nested CLAUDE.md

 backend/CLAUDE.md (~45 linii):
 - Cum adaugi un modul backend: MODULE_INFO template, structura modules/[name]/
 - Convenții DB: migrări, aiosqlite, busy_timeout
 - Activity log pattern: log_activity(action=..., summary=..., details=...)
 - Python: PYTHONIOENCODING=utf-8, python -m pip/uvicorn

 frontend/CLAUDE.md (~45 linii):
 - Cum adaugi o pagină: component, Route în App.jsx, entry în manifest.js
 - manifest.js: NAV_SECTIONS categorii
 - Stiluri: Tailwind, lucide-react icons
 - API: URL-uri dinamice, nu hardcoded localhost

 ---
 Pas 10 — Arhivare fișiere deprecated

 Mută în 99_Roland_Work_Place/archive/:
 - 99_Roland_Work_Place/1.0_PLAN_EXTINDERE.md — superseded de 0.0
 - 99_Roland_Work_Place/2.0_PLAN_EXTINDERE_PROPUNERI.md — propuneri incorporate
 - 99_Roland_Work_Place/2.1_PLAN_EXTINDERE_PROPUNERI.md — propuneri incorporate
 - 99_Roland_Work_Place/2.2_PLAN_EXTINDERE_PROPUNERI.md — propuneri incorporate
 - 99_Roland_Work_Place/MAX_EFFORT.md — instrucțiune one-time
 - 99_Roland_Work_Place/Restructurare_Regulamente.md — cerința curentă, executată
 - 99_Roland_Work_Place/z_Cerere2_Restructurare_Regulamente.md — correcții cerință, executate

 NU se arhivează: PLAN_EXECUTIE.md — rămâne în rădăcină (referit în CLAUDE.md, memory, conversații anterioare)

 Mută în 99_Roland_Work_Place/:
 - Competitori.md (din rădăcină) — date referință, nu cod
 - dashboard-screenshot.png (din rădăcină) — screenshot, nu cod

 Opțional de șters:
 - 2026-03-17-020627-implement... (73KB session transcript) — nu e documentație

 ---
 Pas 11 — Creare fișiere noi

 - .claude/PROJECT_STATUS.md — snapshot compact (~30 linii) generat automat
 - 99_Roland_Work_Place/CHANGELOG_RULES.md — log modificări reguli
 - 99_Roland_Work_Place/ANALIZA_FISIERE.md — analiza cerută de utilizator (cerința 3)

 ---
 Pas 12 — Update memory

 - feedback_auto_update_plan.md — actualizez referința de la PLAN_EXECUTIE.md la 0.0_PLAN_EXTINDERE_COMPLET.md

 ---
 Pas 13 — Creare ANALIZA_FISIERE.md (cerința 3)

 Fișier cu analiza completă a tuturor fișierelor din proiect:
 - Ce fișiere sunt utile, redundante, confuze
 - Propunere reorganizare
 - Status final după restructurare

 ---
 Verificare end-to-end

 1. Hook SessionStart: Deschid terminal nou → vezi instant PROJECT_STATUS.md
 2. Reguli auto-load: .claude/rules/*.md citite automat → nu mai e nevoie să fie în CLAUDE.md
 3. Comenzi: /pre-wave funcționează, /update-status actualizează tot
 4. Agent: /rule-change "adaugă regulă X" → analizează, prezintă, logheaz
 5. Nested CLAUDE.md: Editez fișier backend → vede backend/CLAUDE.md automat
 6. CLAUDE.md: Sub 200 linii, conține doar esențialul
 7. Arhivare: Fișierele vechi sunt în archive/, nu cauzează confuzie

 ---
 Structura finală fișiere

 .claude/
 ├── settings.local.json        # MODIFICAT: +hooks
 ├── PROJECT_STATUS.md          # NOU: snapshot auto-generat
 ├── rules/
 │   ├── 01-progress-tracking.md    # R1+R2+R7+R10
 │   ├── 02-pre-implementation.md   # R6+R8+R11
 │   ├── 03-validation-and-testing.md # R9+R12
 │   ├── 04-code-safety.md         # R3+R4+R5
 │   └── 05-rule-governance.md     # NOU
 ├── commands/
 │   ├── update-status.md
 │   ├── pre-wave.md
 │   ├── test-guide.md
 │   └── rule-change.md
 ├── agents/
 │   └── rule-guardian.md
 └── hooks/
     ├── session-start.sh
     ├── session-stop.sh
     ├── post-edit-check.sh
     └── pre-compact.sh

 CLAUDE.md                      # MODIFICAT: ~150 linii (de la 354)
 backend/CLAUDE.md              # NOU: pattern-uri backend
 frontend/CLAUDE.md             # NOU: pattern-uri frontend

 PLAN_EXECUTIE.md                   # PĂSTRAT în rădăcină (P4)

 99_Roland_Work_Place/
 ├── 0.0_PLAN_EXTINDERE_COMPLET.md    # PĂSTRAT
 ├── 0.0_PLAN_EXTINDERE_COMPLET.html  # PĂSTRAT
 ├── Documentare_Extindere_Proiect.md # PĂSTRAT
 ├── GHID_TESTARE.md                  # PĂSTRAT
 ├── Cerinta_Roland.md                # PĂSTRAT
 ├── Competitori.md                   # MUTAT din rădăcină
 ├── dashboard-screenshot.png         # MUTAT din rădăcină
 ├── CHANGELOG_RULES.md               # NOU
 ├── ANALIZA_FISIERE.md               # NOU
 └── archive/                         # NOU
     ├── 1.0_PLAN_EXTINDERE.md
     ├── 2.0_PLAN_EXTINDERE_PROPUNERI.md
     ├── 2.1_PLAN_EXTINDERE_PROPUNERI.md
     ├── 2.2_PLAN_EXTINDERE_PROPUNERI.md
     ├── MAX_EFFORT.md
     ├── Restructurare_Regulamente.md
     └── z_Cerere2_Restructurare_Regulamente.md

 Fișiere totale: 20 create/modificate | 9 arhivate | 0 șterse