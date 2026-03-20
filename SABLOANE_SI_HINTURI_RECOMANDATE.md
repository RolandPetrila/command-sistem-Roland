# SABLOANE SI HINTURI RECOMANDATE — Roland Command Center

Data: 2026-03-20 | Baza: Deep Research (61/80) + Analiza workflow 24 faze

---

## Sectiunea 1 — Slash Commands Recomandate

### Commands existente (32 total: 25 globale + 7 proiect)
**Proiect:** `/backup-db`, `/commit-phase`, `/pre-wave`, `/rebuild`, `/rule-change`, `/test-guide`, `/update-status`
**Bine acoperite:** Ciclul faza (pre-wave → implement → test-guide → commit-phase → update-status). Rebuild si backup sunt utile.

### Command NOU #1: `/validate`

| Camp | Continut |
|------|----------|
| Nume | `/validate` |
| Problema rezolvata | Regula 08 exista dar trebuie executata manual pas cu pas. Dupa incidentul Faza 23 (trust issue), validarea e critica dar usor de uitat |
| Cand se foloseste | Dupa ORICE modificare de cod, inainte de a declara "gata" |
| Continut complet | Vezi mai jos |

```markdown
# /validate — Validare sistem completa (Rule 08)

Executa validarea completa din `.claude/rules/08-post-change-validation.md`:

1. Kill procese test: `taskkill /f /im python.exe` daca portul 8000 e ocupat
2. Verifica port 8000 liber: `netstat -aon | findstr ":8000"`
3. Import check rapid:
   ```bash
   cd C:\Proiecte\NOU_Calculator_Pret_Traduceri\backend
   set PYTHONIOENCODING=utf-8
   python -c "from app.main import app; print('Import OK')"
   ```
4. Start backend + health check:
   ```bash
   python -m uvicorn app.main:app --port 8000 --host 127.0.0.1
   curl http://127.0.0.1:8000/api/health
   ```
5. Frontend build (daca frontend modificat): `cd frontend && npx vite build`
6. Kill procesul de test, verifica port liber
7. Raporteaza:
   ```
   VALIDARE SISTEM:
   - Import check: OK/FAIL
   - Backend start: OK/FAIL
   - Health check: OK/FAIL
   - Frontend build: OK/FAIL/N/A
   - Port cleanup: OK/FAIL
   ```

Daca ORICE pas esueaza → fixeaza INAINTE de a declara gata.
```

---

### Command NOU #2: `/quick-test`

| Camp | Continut |
|------|----------|
| Nume | `/quick-test` |
| Problema rezolvata | Testing = 1/10 (cel mai slab punct din Deep Research). Cand se adauga pytest, trebuie sa existe un mod rapid de a le rula |
| Cand se foloseste | Dupa modificari backend, inainte de commit |
| Continut complet | Vezi mai jos |

```markdown
# /quick-test — Ruleaza testele backend rapid

1. Verifica daca `pytest` e instalat: `python -m pytest --version`
   - Daca NU: `python -m pip install pytest httpx pytest-asyncio`
2. Ruleaza testele:
   ```bash
   cd C:\Proiecte\NOU_Calculator_Pret_Traduceri\backend
   set PYTHONIOENCODING=utf-8
   python -m pytest tests/ -v --tb=short
   ```
3. Raporteaza: PASSED X / FAILED Y / ERRORS Z
4. Daca FAILED > 0: afiseaza care teste au picat si propune fix
5. Daca nu exista folder `tests/` sau e gol: semnaleaza ca testele trebuie create (Roadmap #7)
```

---

### Command NOU #3: `/roadmap`

| Camp | Continut |
|------|----------|
| Nume | `/roadmap` |
| Problema rezolvata | Deep Research a generat un roadmap cu 15 actiuni prioritizate, dar nu exista un mod rapid de a-l consulta si a executa din el |
| Cand se foloseste | La inceputul sesiunii cand Roland vrea sa stie "ce ar fi urmatorul pas logic" |
| Continut complet | Vezi mai jos |

```markdown
# /roadmap — Consulta si executa din roadmap-ul de imbunatatiri

1. Citeste `99_Roland_Work_Place/2026-03-20_deep_research/ROADMAP_IMBUNATATIRI.md`
2. Citeste `99_Roland_Work_Place/2026-03-20_deep_research/RAPORT.md` — scorul actual
3. Afiseaza statusul curent:
   ```
   ROADMAP STATUS (ultima analiza: YYYY-MM-DD, scor: X/80)

   SAPTAMANA 1 — Quick Wins:
   [x] / [ ] #1 Git commit
   [x] / [ ] #2 SQL whitelist check
   ...

   Recomandat ACUM: #N — [descriere] (efort: X, impact: Y)
   ```
4. Intreaba: "Vrei sa execut actiunea #N?" sau "Alege un numar din roadmap"
5. La executie, respecta regula 08 (validate dupa)
```

---

### Analiza commands care NU sunt necesare

| Command potential | De ce NU il propun |
|-------------------|-------------------|
| `/start` (pornire sistem) | START_Roland.bat face deja asta; Claude Code nu e mecanismul de pornire zilnica |
| `/security-scan` | `/deep-research focus security` acopera deja; un command dedicat ar fi redundant |
| `/fix-catch-blocks` | Actiune one-time din roadmap, nu pattern recurent |

---

## Sectiunea 2 — Fisiere de Memorie Recomandate

### Memorie existenta (6 fisiere) — BINE STRUCTURATE
- `user_profile.md` — profil complet, relevant
- `feedback_pre_implementation_briefing.md` — workflow confirmat
- `feedback_validate_between_waves.md` — workflow confirmat
- `feedback_post_change_validation.md` — incident Faza 23
- `debugging_patterns.md` — 4 patterns utile (zombies, cp1252, python -m, CORS)
- `decisions_api_providers.md` — decizii providers cu motivare

### Memorie NOUA #1: `reference_deep_research_baseline.md`

| Camp | Continut |
|------|----------|
| Nume fisier | `reference_deep_research_baseline.md` |
| Ce contine | Scorul de baza din Deep Research (61/80) + scoruri pe categorii + data scanului |
| Frecventa actualizare | La fiecare rulare `/deep-research` |
| Cine actualizeaza | AI automat |

**De ce:** Urmatorul `/deep-research` va putea compara cu baseline-ul si raporta delta. Fara aceasta memorie, progresul nu e masurabil.

### Memorie NOUA #2: `project_security_findings.md`

| Camp | Continut |
|------|----------|
| Nume fisier | `project_security_findings.md` |
| Ce contine | 3 CRITICAL + 3 HIGH security issues din Deep Research, cu status rezolvare |
| Frecventa actualizare | La fix-ul fiecarei probleme |
| Cine actualizeaza | AI automat dupa remediere |

**De ce:** Problemele de securitate (SQL injection in reports/router.py:399, rate limiting absent, AIChatPage fetch() bypass) trebuie urmarite pana la rezolvare. Memory-ul dispare din context daca nu e salvat.

### Memorie care NU trebuie adaugata

| Potential | De ce NU |
|-----------|---------|
| Architecture snapshot | Derivabil din cod — `find + wc` in 5 secunde |
| File count/LOC metrics | Se schimba la fiecare commit, stale instant |
| Git activity summary | `git log` e autoritar |

---

## Sectiunea 3 — Prompturi Rapide

Texte scurte pe care Roland le poate scrie la inceputul mesajului pentru a seta comportamentul:

### Prompt #1 — Quick fix
**Prefix:** `fix rapid:`
**Efect:** Sare peste briefing-ul complet (regula 02), executa direct cu validare la final
**Exemplu:** `fix rapid: catch block gol in CalibrationPanel.jsx`

### Prompt #2 — Doar raspuns
**Prefix:** `intrebare:`
**Efect:** Doar raspunde, nu modifica nimic, nu propune plan, nu actualizeaza fisiere
**Exemplu:** `intrebare: ce librarie folosim pentru PDF parsing?`

### Prompt #3 — Continua
**Prefix:** `continua`
**Efect:** Reia exact de unde s-a oprit sesiunea anterioara, fara intrebari
**Exemplu:** `continua` (la inceputul unei sesiuni noi)

### Prompt #4 — Testeaza tot
**Prefix:** `testeaza:`
**Efect:** Porneste backend, testeaza endpoint-urile specificate, raporteaza, opreste
**Exemplu:** `testeaza: translator, ai chat, invoice`

---

## Sectiunea 4 — Diagnostic Regulament

### CE E BINE (de pastrat)

| Observatie | Fisier |
|-----------|--------|
| Regula 08 (post-validation) e excelenta si unica in acest proiect — previne incidentul Faza 23 de a se repeta | `08-post-change-validation.md` |
| Regula 06 (free-tier) cu lista completa de provideri aprobati + checklist 5 puncte e exemplara | `06-free-tier-enforcement.md` |
| Separarea clara 8 reguli in 8 fisiere cu trigger definit per regula e clean | `.claude/rules/` |
| Workflow codificat (pre-wave → implement → test-guide → commit → update-status) e complet | Commands proiect |

### Problema #1 — Regula 07 are o violare cunoscuta neadresata

- **CE:** `AIChatPage.jsx` foloseste `fetch()` nativ in loc de `api` (axios client). Asta bypasses interceptorul de erori + toast + diagnostics panel.
- **UNDE:** `.claude/rules/07-error-handling.md` — nu mentioneaza explicit aceasta violare
- **FIX:** Adauga in regula 07, sectiunea "Known violations to fix":
  ```markdown
  ## Known Violations (to fix)
  - `AIChatPage.jsx` — uses native fetch() for SSE streaming, bypassing axios interceptor.
    Acceptable for SSE (axios doesn't support streaming), but error handling must be manual.
    Status: ACKNOWLEDGED — SSE requires fetch(), add manual error toast.
  ```
- **IMPACT:** Clarifica ca e o exceptie stiuta, nu o omisiune accidentala

### Problema #2 — Regula 04 nu defineste prag de avertizare pentru fisiere necommitted

- **CE:** 41 fisiere necommitted = risc pierdere munca. Dar regula 04 (code safety) doar spune "check for uncommitted changes" fara un prag care sa declanseze avertizare prioritara.
- **UNDE:** `.claude/rules/04-code-safety.md` — sectiunea "Git Safety"
- **FIX:** Adauga dupa punctul "Check for uncommitted changes":
  ```markdown
  - If uncommitted changes > 20 files or > 1000 lines → PRIORITY WARNING at session start:
    "ATENTIE: X fisiere necommitted. Recomandat: /commit-phase inainte de orice modificare noua."
  ```
- **IMPACT:** Previne acumularea de 41 fisiere necommitted (situatia actuala). Avertizeaza proactiv.

### Problema #3 — Regula 01 (progress tracking) si Regula 08 (validation) se suprapun partial

- **CE:** Regula 01 zice "after EVERY implementation execution" iar Regula 08 zice "after completing ANY code modifications". Ambele se aplica la acelasi moment dar cu actiuni diferite.
- **UNDE:** `01-progress-tracking.md` trigger vs `08-post-change-validation.md` trigger
- **FIX:** Nu e nevoie de modificare structurala — sunt complementare (01 = documenteaza, 08 = valideaza). Dar clarifica ordinea:
  ```
  Ordinea la finalizare: Regula 08 (validate) → Regula 01 (track progress)
  Logica: mai intai confirma ca functioneaza, apoi documenteaza.
  ```
  Adauga aceasta nota la inceputul regulii 01.
- **IMPACT:** Elimina confuzia despre care se executa prima

---

## Sectiunea 5 — Ordine de Implementare

Toate recomandarile ordonate dupa beneficiu/efort:

| # | Recomandare | Efort (min) | Beneficiu | Prioritate |
|---|-------------|-------------|-----------|------------|
| 1 | Creeaza `/validate` command | 5 | Previne incidente tip Faza 23, standardizeaza Rule 08 | CRITICA |
| 2 | Salveaza memorie `reference_deep_research_baseline.md` | 3 | Permite comparatie la urmatorul deep-research | MARE |
| 3 | Fix regula 04 — prag avertizare fisiere necommitted | 5 | Previne acumulare 41+ fisiere riscante | MARE |
| 4 | Salveaza memorie `project_security_findings.md` | 5 | Urmareste 6 vulnerabilitati pana la rezolvare | MARE |
| 5 | Clarifica ordinea Rule 08 → Rule 01 | 3 | Elimina ambiguitate executie | MEDIE |
| 6 | Adauga Known Violations in regula 07 (AIChatPage fetch) | 3 | Documenta exceptia SSE ca stiuta | MEDIE |
| 7 | Creeaza `/quick-test` command | 5 | Pregateste pentru pytest (roadmap #7) | MEDIE |
| 8 | Creeaza `/roadmap` command | 5 | Acces rapid la planul de imbunatatiri | MICA |

**Total efort estimat: ~35 minute pentru toate 8 recomandarile**

---

## Ce din Deep Research poate fi integrat CA SISTEM (nu ca feature)

Din cele 15 actiuni din ROADMAP, 3 imbunatatesc direct sistemul de lucru (nu codul aplicatiei):

| # Roadmap | Actiune | Tip imbunatatire sistem |
|-----------|---------|------------------------|
| #1 | Git commit 41 fisiere | `/commit-phase` exista deja — doar trebuie executat |
| #7 | Adauga pytest minimal | `/quick-test` command (propus mai sus) + folder `tests/` |
| #8 | GitHub branch protection | One-time setup, nu necesita command |

Celelalte 12 actiuni sunt imbunatatiri de cod/feature, nu de sistem de lucru.
