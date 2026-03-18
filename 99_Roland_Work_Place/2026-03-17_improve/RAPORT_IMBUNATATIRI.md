# RAPORT IMBUNATATIRI — Calculator Pret Traduceri

**Data analizei**: 2026-03-17
**Stack**: FastAPI (Python 3.13) + React 18 + Vite + Tailwind + SQLite
**Faza proiect**: 5 COMPLETE, Faza 6 (E2E) TODO
**Fisiere analizate**: 46 (17 backend, 29 frontend)
**Sugestii gasite**: 38 total
**Scor consistenta documentatie**: 8/10

---

## CUPRINS

1. [SECURITATE (4 sugestii)](#-securitate)
2. [CORECTITUDINE (4 sugestii)](#-corectitudine)
3. [ARHITECTURA (3 sugestii)](#-arhitectura)
4. [CALITATE COD (5 sugestii)](#-calitate-cod)
5. [TESTARE (2 sugestii)](#-testare)
6. [DOCUMENTATIE (2 sugestii)](#-documentatie)
7. [PERFORMANTA (3 sugestii)](#-performanta)
8. [DEVELOPER EXPERIENCE (2 sugestii)](#-developer-experience)
9. [MODERNIZARE (3 sugestii)](#-modernizare)
10. [HYGIENE GIT (5 verificari)](#hygiene-git)
11. [TOP 3 ACTIUNI RECOMANDATE](#top-3-actiuni-recomandate)
12. [CONSISTENTA CU DOCUMENTATIA](#consistenta-cu-documentatia)

---

## 🔴 SECURITATE

### SEC-01 — XSS in FilePreview.jsx
- **Prioritate**: HIGH
- **Relevanta**: RELEVANT ACUM | RECOMANDAT
- **Locatie**: `frontend/src/components/FileBrowser/FilePreview.jsx:19,61`
- **Efort**: MIC (<1h)
- **Problema**: Continutul fisierelor se renderizeaza fara sanitizare in `<pre>{content}</pre>`. Un PDF/DOCX malitios cu continut HTML ar putea executa cod JavaScript in browser.
- **Cod afectat**:
  ```jsx
  // Linia 19 — continut nesanitizat
  setContent(typeof data === 'string' ? data : data.content || JSON.stringify(data, null, 2));
  // Linia 61 — renderizat direct
  <pre>{content}</pre>
  ```
- **Fix propus**:
  1. Instaleaza DOMPurify: `npm install dompurify`
  2. Sanitizeaza inainte de renderizare:
  ```jsx
  import DOMPurify from 'dompurify';
  // ...
  const safeContent = DOMPurify.sanitize(content, { ALLOWED_TAGS: [] });
  <pre>{safeContent}</pre>
  ```
  Alternativ, asigura-te ca `<pre>` nu interpreteaza HTML (React face escape by default pentru text, dar nu si pentru `dangerouslySetInnerHTML`). Verifica sa nu existe `dangerouslySetInnerHTML` nicaieri in componenta.
- **Impact neremediat**: Un fisier uploadat cu continut HTML malitios poate executa cod in sesiunea utilizatorului.

---

### SEC-02 — Path Traversal in routes_files.py
- **Prioritate**: HIGH
- **Relevanta**: RELEVANT ACUM | RECOMANDAT
- **Locatie**: `backend/app/api/routes_files.py:47-52`
- **Efort**: MIC (<1h)
- **Problema**: Protectia `.relative_to()` e fragila pe Windows — symlinks si junction points pot bypassa verificarea.
- **Cod afectat**:
  ```python
  target = (base / path).resolve()
  try:
      target.relative_to(base)  # Daca trece, path-ul e "sigur"
  except ValueError:
      raise HTTPException(403, ...)
  ```
- **Fix propus**:
  ```python
  target = (base / path).resolve()
  # Verificare suplimentara: blocheaza symlinks
  if target.is_symlink():
      raise HTTPException(403, "Acces interzis: symlink detectat")
  try:
      target.relative_to(base.resolve())
  except ValueError:
      raise HTTPException(403, "Acces interzis: cale in afara directorului permis")
  ```
- **Impact neremediat**: Un atacator ar putea naviga in afara directorului permis si citi fisiere de pe disc.

---

### SEC-03 — Upload fara validare magic bytes
- **Prioritate**: MEDIUM
- **Relevanta**: RELEVANT ACUM
- **Locatie**: `backend/app/api/routes_upload.py:50-51`
- **Efort**: MIC (<1h)
- **Problema**: Content-type header e ignorat (linia 50-51: `pass`), doar extensia fisierului e verificata. Un fisier malitios cu extensie `.pdf` trece fara probleme.
- **Cod afectat**:
  ```python
  if file.content_type and file.content_type not in ALLOWED_CONTENT_TYPES:
      pass  # unele browsere...
  ```
- **Fix propus**:
  ```python
  # Citeste primii bytes si verifica semnatura
  content = await file.read()
  await file.seek(0)  # resetare pozitie

  MAGIC_BYTES = {
      ".pdf": b"%PDF",
      ".docx": b"PK",  # DOCX = ZIP archive
  }
  expected_magic = MAGIC_BYTES.get(ext)
  if expected_magic and not content[:len(expected_magic)].startswith(expected_magic):
      raise HTTPException(400, f"Fisier invalid: semnatura nu corespunde extensiei {ext}")
  ```
- **Impact neremediat**: Fisiere malitioase cu extensie falsa pot fi uploadate si procesate.

---

### SEC-04 — WebSocket pe ws:// nu wss://
- **Prioritate**: LOW
- **Relevanta**: RELEVANT VIITOR
- **Locatie**: `frontend/src/api/client.js:101`
- **Efort**: MIC (<1h)
- **Problema**: WebSocket-ul foloseste `ws://` (necriptat). Aplicatia e localhost-only (conform CLAUDE.md), deci riscul e minim acum.
- **Fix propus** (la deploy extern):
  ```javascript
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const ws = new WebSocket(`${protocol}//localhost:8000/ws/progress/${taskId}`);
  ```
- **Impact neremediat**: La deploy extern, comunicatia WebSocket ar fi in clar (man-in-the-middle).

---

## 🔴 CORECTITUDINE

### COR-01 — Logica weight redistribution in ensemble.py
- **Prioritate**: HIGH
- **Relevanta**: RELEVANT ACUM | RECOMANDAT
- **Locatie**: `backend/app/core/pricing/ensemble.py:96-106`
- **Efort**: MIC (<1h)
- **Problema**: Cand metoda similarity esueaza, ponderile se redistribuie. Dar daca w1+w2=0 (teoretic posibil), fallback-ul la 0.5/0.5 nu verifica ca metodele base_rate si word_rate au returnat preturi reale (non-zero).
- **Cod afectat**:
  ```python
  if price_similarity == 0.0 and result_similarity["details"].get("error"):
      w_sum = w1 + w2
      if w_sum > 0:
          w1 = w1 / w_sum
          w2 = w2 / w_sum
      else:
          w1 = 0.5
          w2 = 0.5
      w3 = 0.0
  ```
- **Fix propus**:
  ```python
  if price_similarity == 0.0 and result_similarity["details"].get("error"):
      # Daca nicio metoda nu a returnat pret valid, fallback la pret mediu referinte
      if price_base == 0.0 and price_word == 0.0:
          fallback = _calculate_fallback_price(features, reference_data)
          return {"market_price": fallback, "confidence": 30.0, ...}
      w_sum = w1 + w2
      w1 = w1 / w_sum if w_sum > 0 else 0.5
      w2 = w2 / w_sum if w_sum > 0 else 0.5
      w3 = 0.0
  ```
- **Impact neremediat**: Calcul de pret eronat (0 RON sau valori distorsionate) cand mai multe metode esueaza simultan.

---

### COR-02 — SelfLearnButton raporteaza succes pe eroare
- **Prioritate**: MEDIUM
- **Relevanta**: RELEVANT ACUM
- **Locatie**: `frontend/src/components/Price/SelfLearnButton.jsx:13-16`
- **Efort**: MIC (<1h)
- **Problema**: Blocul `catch` seteaza `status='success'` — utilizatorul crede ca validarea a functionat cand backend-ul a esuat de fapt.
- **Cod afectat**:
  ```jsx
  catch {
    // Even if endpoint doesn't exist yet, show success for UX
    setStatus('success');
  }
  ```
- **Fix propus**:
  ```jsx
  catch (err) {
    console.error('Eroare la validare pret:', err);
    setStatus('error');
    // Optional: afiseaza mesaj utilizator
  }
  ```
- **Impact neremediat**: Utilizatorul crede ca pretul a fost invatat de sistem, dar de fapt nu — datele de self-learning raman incomplete.

---

### COR-03 — WebSocket memory leak la upload multiplu
- **Prioritate**: MEDIUM
- **Relevanta**: RELEVANT ACUM
- **Locatie**: `frontend/src/pages/UploadPage.jsx:104`
- **Efort**: MIC (<1h)
- **Problema**: WebSocket-ul e fortat inchis dupa 30s timeout dar event listeners nu se curata. La upload-uri multiple, obiectele WebSocket orfane raman in memorie.
- **Cod afectat**:
  ```javascript
  setTimeout(() => { try { ws.close(); } catch {} }, 30000);
  ```
- **Fix propus**:
  ```jsx
  useEffect(() => {
    let ws = null;
    const cleanup = () => {
      if (ws) {
        ws.onopen = null;
        ws.onmessage = null;
        ws.onerror = null;
        ws.onclose = null;
        try { ws.close(); } catch {}
        ws = null;
      }
    };
    // ... logica WebSocket ...
    return cleanup;  // React curata la unmount
  }, [taskId]);
  ```
- **Impact neremediat**: Consum crescut de memorie in browser dupa upload-uri repetate.

---

### COR-04 — Silent error handling la delete din HistoryPage
- **Prioritate**: MEDIUM
- **Relevanta**: RELEVANT ACUM
- **Locatie**: `frontend/src/pages/HistoryPage.jsx:35-41`
- **Efort**: MIC (<1h)
- **Problema**: Cand delete-ul esueaza, eroarea e silentioasa — item-ul dispare din UI (setState deja executat) dar ramane in DB.
- **Cod afectat**:
  ```javascript
  const handleDelete = async (id) => {
    try {
      await deleteHistoryEntry(id);
      setEntries((prev) => prev.filter((e) => e.id !== id));
    } catch {
      // Silently handle
    }
  };
  ```
- **Fix propus**:
  ```javascript
  const handleDelete = async (id) => {
    try {
      await deleteHistoryEntry(id);
      setEntries((prev) => prev.filter((e) => e.id !== id));
    } catch (err) {
      console.error('Eroare la stergere:', err);
      alert('Nu s-a putut sterge intrarea. Incearca din nou.');
      // NU modifica state-ul local — item-ul ramane vizibil
    }
  };
  ```
- **Impact neremediat**: Utilizatorul vede item-ul disparut dar la refresh reapare — experienta confuza.

---

## 🟠 ARHITECTURA

### ARH-01 — Circular import intre routes_price si main
- **Prioritate**: MEDIUM
- **Relevanta**: RELEVANT VIITOR
- **Locatie**: `backend/app/api/routes_price.py:91`, `backend/app/core/self_learning.py:165`
- **Efort**: MEDIU (1-4h)
- **Problema**: `from app.main import ws_manager` in routes_price.py e un circular import deferred. Similar in self_learning.py cu `load_reference_data`. Functioneaza acum dar e fragil — orice reorganizare de import-uri poate sparge aplicatia.
- **Fix propus**:
  1. Creaza `backend/app/core/ws.py` cu clasa `ConnectionManager` si instanta `ws_manager`
  2. Creaza `backend/app/core/references.py` cu functia `load_reference_data`
  3. Import-urile devin directe, fara cicluri
- **Impact neremediat**: Cod fragil, greu de refactorizat pe viitor.

---

### ARH-02 — Fara versionare calibration.json
- **Prioritate**: MEDIUM
- **Relevanta**: RELEVANT ACUM
- **Locatie**: `backend/app/core/calibration.py:232`, `backend/data/calibration.json`
- **Efort**: MEDIU (1-4h)
- **Problema**: `calibration.json` se suprascrie la fiecare recalibrare fara backup. O calibrare gresita inseamna pierderea parametrilor anteriori fara posibilitate de rollback.
- **Fix propus**:
  ```python
  import shutil
  from datetime import datetime

  def _backup_calibration():
      cal_file = settings.calibration_file
      if cal_file.exists():
          backup_dir = settings.data_dir / "calibration_history"
          backup_dir.mkdir(exist_ok=True)
          timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
          shutil.copy2(cal_file, backup_dir / f"calibration_{timestamp}.json")
          # Pastreaza doar ultimele 10 versiuni
          backups = sorted(backup_dir.glob("calibration_*.json"))
          for old in backups[:-10]:
              old.unlink()
  ```
- **Impact neremediat**: Calibrare gresita → preturi eronate → fara rollback rapid.

---

### ARH-03 — API client nestandardizat
- **Prioritate**: LOW
- **Relevanta**: RELEVANT VIITOR
- **Locatie**: `frontend/src/api/client.js:26-128`
- **Efort**: MEDIU (1-4h)
- **Problema**: Fiecare endpoint are error handling diferit — unele silentioase, altele throw, altele cu fallback. Inconsistent si greu de depanat.
- **Fix propus**: Creaza un request wrapper centralizat:
  ```javascript
  async function apiCall(method, url, data, options = {}) {
    try {
      const response = await api[method](url, data);
      return response.data;
    } catch (error) {
      const message = error.response?.data?.detail || error.message;
      if (!options.silent) {
        console.error(`[API ${method.toUpperCase()}] ${url}:`, message);
      }
      throw new ApiError(message, error.response?.status);
    }
  }
  ```
- **Impact neremediat**: Debugging dificil cand erorile sunt tratate diferit in fiecare componenta.

---

## 🟠 CALITATE COD

### CAL-01 — Hardcoded API URL in client.js
- **Prioritate**: MEDIUM
- **Relevanta**: RELEVANT ACUM
- **Locatie**: `frontend/src/api/client.js:3`
- **Efort**: MIC (<1h)
- **Problema**: `const API_BASE_URL = 'http://localhost:8000'` — orice schimbare de port/host necesita modificare manuala in cod.
- **Fix propus**:
  ```javascript
  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
  ```
  Si optional in `.env.development`:
  ```
  VITE_API_URL=http://localhost:8000
  ```
- **Impact neremediat**: Nu poate fi configurat fara modificare cod sursa.

---

### CAL-02 — Default weights hardcoded in ensemble.py
- **Prioritate**: MEDIUM
- **Relevanta**: RELEVANT ACUM
- **Locatie**: `backend/app/core/pricing/ensemble.py:37-41`
- **Efort**: MIC (<1h)
- **Problema**: `config.py` defineste `default_weights = {"base_rate": 0.3, "word_rate": 0.4, "similarity": 0.3}`, dar `ensemble.py` are aceleasi valori hardcoded separat. Risc de dezacord la modificare.
- **Cod afectat**:
  ```python
  if weights is None:
      weights = {
          "base_rate": 0.3,
          "word_rate": 0.4,
          "similarity": 0.3,
      }
  ```
- **Fix propus**:
  ```python
  from app.config import settings

  if weights is None:
      weights = settings.default_weights
  ```
- **Impact neremediat**: Modificarea ponderilor in config.py nu are efect daca nu se modifica si ensemble.py.

---

### CAL-03 — Magic numbers in fisiere multiple
- **Prioritate**: LOW
- **Relevanta**: RELEVANT VIITOR
- **Locatie**:
  - `backend/app/core/analyzer.py:162` — `avg_words_per_page < 10` (threshold scanned)
  - `backend/app/core/analyzer.py:167` — `2000.0` (text density normalization)
  - `backend/app/core/pricing/word_rate.py:104` — `chart_count > 3` (chart complexity)
  - `backend/app/core/validation.py:128` — `0.50` (deviation threshold)
- **Efort**: MIC (<1h)
- **Fix propus**: Defineste constante la nivel de modul:
  ```python
  # analyzer.py
  MIN_WORDS_PER_PAGE_FOR_DIGITAL = 10
  TYPICAL_CHARS_PER_PAGE_A4 = 2000

  # word_rate.py
  CHART_COMPLEXITY_THRESHOLD = 3

  # validation.py
  MAX_PRICE_DEVIATION_RATIO = 0.50
  ```
- **Impact neremediat**: Valori dispersate greu de gasit si modificat.

---

### CAL-04 — Cod duplicat: slider styling si formatDate
- **Prioritate**: LOW
- **Relevanta**: RELEVANT VIITOR
- **Locatie**:
  - Slider: `frontend/src/components/Price/PriceCard.jsx:67-72` vs `frontend/src/components/Settings/InvoicePercent.jsx:64-68`
  - formatDate: `frontend/src/components/History/HistoryTable.jsx:5-8` vs `frontend/src/components/Dashboard/RecentActivity.jsx:6-19`
- **Efort**: MIC (<1h)
- **Fix propus**:
  1. Creaza `frontend/src/utils/formatters.js` cu `formatDate()`
  2. Creaza `frontend/src/components/shared/Slider.jsx` pentru styling comun
- **Impact neremediat**: Bug-fix intr-o locatie nu se propaga in cealalta.

---

### CAL-05 — UploadPage.jsx prea mare (240 linii, 3 responsabilitati)
- **Prioritate**: LOW
- **Relevanta**: RELEVANT VIITOR
- **Locatie**: `frontend/src/pages/UploadPage.jsx`
- **Efort**: MEDIU (1-4h)
- **Problema**: Contine upload form + results display + progress display — 3 responsabilitati distincte intr-o singura componenta.
- **Fix propus**: Extrage in 3 componente:
  - `UploadForm.jsx` — dropzone + file list
  - `ProgressDisplay.jsx` — WebSocket progress
  - `ResultsDisplay.jsx` — pret calculat + actiuni
- **Impact neremediat**: Greu de testat si modificat independent.

---

## 🟡 TESTARE

### TEST-01 — Zero teste unitare sau de integrare
- **Prioritate**: HIGH
- **Relevanta**: RELEVANT ACUM | RECOMANDAT
- **Locatie**: Intregul proiect — nu exista folder `tests/` sau fisiere `*.test.*`
- **Efort**: MARE (>4h)
- **Problema**: 46 fisiere de cod, 0 fisiere de test. Faza 6 (E2E) din PLAN_EXECUTIE.md nu poate fi completata corect fara teste.
- **Fix propus**: Creaza structura de teste:
  ```
  backend/tests/
  ├── conftest.py          # fixtures pytest
  ├── test_analyzer.py     # parsare PDF/DOCX cu fisiere reper
  ├── test_pricing.py      # calcule pret cu input-uri cunoscute
  ├── test_ensemble.py     # weight redistribution, fallback
  ├── test_validation.py   # 3 niveluri validare
  ├── test_routes.py       # HTTP endpoints (TestClient)
  └── test_security.py     # path traversal, SQL injection
  ```
  Prioritate teste:
  1. `test_pricing.py` — core business, impact maxim
  2. `test_analyzer.py` — 26 fisiere reper disponibile
  3. `test_routes.py` — endpoint-uri API
- **Impact neremediat**: Fara teste, bug-urile sunt descoperite doar la utilizare manuala — Faza 6 incompletabila corect.

---

### TEST-02 — Fara Error Boundaries in React
- **Prioritate**: MEDIUM
- **Relevanta**: RELEVANT ACUM
- **Locatie**: `frontend/src/App.jsx`
- **Efort**: MIC (<1h)
- **Problema**: O eroare intr-un singur component (ex: un JSON malformat in chart) crashuieste intreaga aplicatie React — ecran alb.
- **Fix propus**:
  ```jsx
  // frontend/src/components/shared/ErrorBoundary.jsx
  import { Component } from 'react';

  class ErrorBoundary extends Component {
    state = { hasError: false, error: null };

    static getDerivedStateFromError(error) {
      return { hasError: true, error };
    }

    render() {
      if (this.state.hasError) {
        return (
          <div className="p-8 text-red-400">
            <h2>Eroare neasteptata</h2>
            <p>{this.state.error?.message}</p>
            <button onClick={() => this.setState({ hasError: false })}>
              Reincearca
            </button>
          </div>
        );
      }
      return this.props.children;
    }
  }
  ```
  Apoi in App.jsx, wrap fiecare pagina cu `<ErrorBoundary>`.
- **Impact neremediat**: Un bug intr-o singura componenta face toata aplicatia inutilizabila.

---

## 🟡 DOCUMENTATIE

### DOC-01 — Fara .gitignore
- **Prioritate**: MEDIUM
- **Relevanta**: RELEVANT ACUM
- **Locatie**: Radacina proiectului — fisierul lipseste complet
- **Efort**: MIC (<1h)
- **Problema**: Proiectul NU are .gitignore. La initializare git, risc de commit accidental: `node_modules/` (200MB+), `__pycache__/`, `*.db`, `uploads/`, `.env`.
- **Fix propus**: Creaza `.gitignore` cu:
  ```gitignore
  # Python
  __pycache__/
  *.py[cod]
  *.pyo
  .pytest_cache/
  *.egg-info/

  # Node
  node_modules/
  dist/
  build/
  .vite/

  # Database
  *.db
  *.db-journal

  # Uploads (fisiere utilizator)
  backend/uploads/

  # Environment
  .env
  .env.local
  .env.*.local

  # IDE
  .vscode/
  .idea/
  *.swp
  *.swo

  # OS
  Thumbs.db
  .DS_Store
  ```
- **Impact neremediat**: Commit accidental de fisiere mari sau sensibile.

---

### DOC-02 — README.md lipseste
- **Prioritate**: LOW
- **Relevanta**: RELEVANT VIITOR
- **Locatie**: Radacina proiectului
- **Efort**: MIC (<1h)
- **Problema**: CLAUDE.md exista (pentru AI), dar README.md (pentru oameni) lipseste. Daca altcineva deschide proiectul, nu stie cum sa-l porneasca.
- **Fix propus**: Genereaza README.md pe baza CLAUDE.md, adaptat pentru cititor uman.
- **Impact neremediat**: Onboarding dificil pentru orice persoana noua.

---

## 🟢 PERFORMANTA

### PERF-01 — Sorting fara memoizare in HistoryTable
- **Prioritate**: LOW
- **Relevanta**: RELEVANT VIITOR
- **Locatie**: `frontend/src/components/History/HistoryTable.jsx:24-36`
- **Efort**: MIC (<1h)
- **Problema**: Array nou sortat creat la fiecare render, chiar daca datele nu s-au schimbat.
- **Fix propus**:
  ```jsx
  const sorted = useMemo(() =>
    [...(entries || [])].sort((a, b) => { ... }),
    [entries, sortKey, sortDir]
  );
  ```
- **Impact neremediat**: Performance hit minor, vizibil doar cu sute de intrari.

---

### PERF-02 — Calcul inline la fiecare render in AccuracyChart
- **Prioritate**: LOW
- **Relevanta**: RELEVANT VIITOR
- **Locatie**: `frontend/src/components/Calibration/AccuracyChart.jsx:88-109`
- **Efort**: MIC (<1h)
- **Problema**: Statisticile (mean, median, max error) se recalculeaza la fiecare render prin IIFE inline.
- **Fix propus**: Muta calculul in `useMemo`:
  ```jsx
  const stats = useMemo(() => {
    const errors = data.map(d => d.error);
    return {
      mean: errors.reduce((a, b) => a + b, 0) / errors.length,
      max: Math.max(...errors),
      // ...
    };
  }, [data]);
  ```
- **Impact neremediat**: Calcul inutil repetat la fiecare re-render.

---

### PERF-03 — StandardScaler refitted per request in similarity.py
- **Prioritate**: LOW
- **Relevanta**: RELEVANT VIITOR
- **Locatie**: `backend/app/core/pricing/similarity.py:108-111`
- **Efort**: MEDIU (1-4h)
- **Problema**: La fiecare calcul de pret, `StandardScaler` se re-fit pe toate referintele. La 100+ referinte, devine lent.
- **Fix propus**: Cache scaler la nivel de modul, re-fit doar la calibrare:
  ```python
  _cached_scaler = None
  _cached_ref_vectors = None

  def _get_scaler(ref_vectors):
      global _cached_scaler, _cached_ref_vectors
      if _cached_ref_vectors is not ref_vectors:
          _cached_scaler = StandardScaler().fit(ref_vectors)
          _cached_ref_vectors = ref_vectors
      return _cached_scaler
  ```
- **Impact neremediat**: Incetinire progresiva pe masura ce cresc referintele.

---

## 🟢 DEVELOPER EXPERIENCE

### DX-01 — Fara linting config
- **Prioritate**: LOW
- **Relevanta**: RELEVANT VIITOR
- **Locatie**: Radacina proiectului — lipsa `.eslintrc`, `.flake8`, `ruff.toml`
- **Efort**: MIC (<1h)
- **Problema**: Nicio configurare de linting. Stilul de cod depinde de disciplina individuala.
- **Fix propus**:
  - Backend: `ruff.toml` (modern, rapid, inlocuieste flake8+isort+black)
  - Frontend: `.eslintrc.cjs` cu config React
- **Impact neremediat**: Inconsistenta de stil, potential bugs detectabile static.

---

### DX-02 — Fara .editorconfig
- **Prioritate**: LOW
- **Relevanta**: RELEVANT VIITOR
- **Locatie**: Radacina proiectului
- **Efort**: MIC (<1h)
- **Problema**: Indentation/encoding nestandarizat intre editoare diferite.
- **Fix propus**:
  ```ini
  # .editorconfig
  root = true

  [*]
  indent_style = space
  indent_size = 4
  end_of_line = lf
  charset = utf-8
  trim_trailing_whitespace = true
  insert_final_newline = true

  [*.{js,jsx,json,css}]
  indent_size = 2
  ```
- **Impact neremediat**: Tab-uri vs spatii mixate, encoding diferit pe masini diferite.

---

## 🔵 MODERNIZARE

### MOD-01 — Vite 5.4 → Vite 6.x
- **Prioritate**: LOW
- **Relevanta**: OVERKILL
- **Locatie**: `frontend/package.json`
- **Efort**: MIC (<1h)
- **Problema**: Vite 5.4 functioneaza bine. Vite 6 exista dar nu aduce beneficii concrete pentru acest proiect.
- **Concluzie**: Nu meriti efortul acum. Upgrade la urmatorul proiect major.

---

### MOD-02 — Tailwind 3.4 → Tailwind 4.x
- **Prioritate**: LOW
- **Relevanta**: OVERKILL
- **Locatie**: `frontend/package.json`
- **Efort**: MEDIU (1-4h)
- **Problema**: Tailwind 4 are schimbari majore de configurare (CSS-first config). Nu aduce beneficii imediate.
- **Concluzie**: Nu meriti efortul acum. Proiectul functioneaza bine cu v3.4.

---

### MOD-03 — PropTypes sau migrare TypeScript
- **Prioritate**: LOW
- **Relevanta**: RELEVANT VIITOR
- **Locatie**: Toate cele 30 componente React
- **Efort**: MARE (>4h)
- **Problema**: Zero type safety in frontend. 30 componente fara PropTypes sau TypeScript. Erori de tip detectate doar la runtime.
- **Fix propus**: Pas intermediar — adauga PropTypes (nu TypeScript complet):
  ```jsx
  import PropTypes from 'prop-types';

  PriceCard.propTypes = {
    data: PropTypes.shape({
      market_price: PropTypes.number.isRequired,
      invoice_price: PropTypes.number.isRequired,
    }).isRequired,
    onPercentChange: PropTypes.func,
  };
  ```
- **Impact neremediat**: Bug-uri de tip descoperite doar la runtime, nu la development.

---

## HYGIENE GIT

| # | Verificare | Status | Detalii |
|---|-----------|--------|---------|
| 1 | .gitignore exista | ✗ LIPSESTE | Risc major — vezi DOC-01 |
| 2 | Fisiere sensibile (.env, .key, .pem) | ✓ Curat | Niciun fisier sensibil gasit |
| 3 | Fisiere mari tracked (>1MB) | ⚠️ Atentie | 19 PDF-uri reper in `Fisiere_Reper_Tarif/` (1MB+) — candidati git-lfs |
| 4 | Git repo initializat | ✗ NU | Proiectul nu e inca un repo git |
| 5 | node_modules protejat | ⚠️ Risc | Fara .gitignore, `git add .` ar include 200MB+ |

---

## TOP 3 ACTIUNI RECOMANDATE

### 1. [RECOMANDAT] Securitate: XSS + Path Traversal + Magic Bytes
**Fisiere**: `FilePreview.jsx:19`, `routes_files.py:47`, `routes_upload.py:50`
**De ce e prioritar**: Vulnerabilitati de securitate active — chiar daca aplicatia e localhost-only, principiul defense-in-depth cere remediere inainte de orice test E2E.
**Efort total**: ~2h pentru toate 3.

### 2. [RECOMANDAT] Infrastructura: .gitignore + initializare git
**Fisiere**: `.gitignore` (de creat), radacina proiect
**De ce e prioritar**: Proiectul nu are .gitignore si nici repo git. Orice pas spre Faza 6 ar trebui versionat. Fara .gitignore, primul `git add .` include node_modules (200MB+), database, uploads.
**Efort total**: ~15 minute.

### 3. [RECOMANDAT] Core business: Fix ensemble weights + teste pricing
**Fisiere**: `ensemble.py:96-106`, `backend/tests/test_pricing.py` (de creat)
**De ce e prioritar**: Logica de calcul pret e nucleul aplicatiei. Bug-ul de weight redistribution poate genera preturi eronate. Testele unitare sunt necesare inainte de Faza 6.6 (test pe 26 fisiere reper — target: >90% acuratete).
**Efort total**: ~4h (1h fix + 3h teste de baza).

---

## CONSISTENTA CU DOCUMENTATIA

**Scor: 8/10**

### Conventii RESPECTATE (8):
- ✓ Text UI in romana
- ✓ Cod si identificatori tehnici in engleza
- ✓ Moneda RON, fara TVA
- ✓ Doar EN ↔ RO
- ✓ Single user, no auth
- ✓ Localhost only
- ✓ Structura 6 pagini conform PLAN_EXECUTIE.md
- ✓ Relative paths in config.py (`Path(__file__).resolve()`)

### Conventii PARTIAL nerespectate (2):
- ⚠️ `ensemble.py` NU foloseste `settings.default_weights` din config — duplicare hardcoded
- ⚠️ Faza 6 nedemarata — teste E2E lipsesc complet (blocant pentru criteriul de succes: >90% acuratete)

---

## LEGENDA

| Simbol | Semnificatie |
|--------|-------------|
| [RECOMANDAT] | Top prioritate — impact mare, efort justificat |
| [RELEVANT ACUM] | Necesita actiune in faza curenta |
| [RELEVANT VIITOR] | Util dar nu urgent — planifica pentru faze urmatoare |
| [OVERKILL] | Depaseste nevoile reale actuale |
| HIGH | Impact major sau risc de securitate |
| MEDIUM | Impact functional, workaround posibil |
| LOW | Imbunatatire calitativa, non-urgent |

---

*Raport generat automat de /improve — 2026-03-17*
*Proiect: NOU_Calculator_Pret_Traduceri | Faza: 5 COMPLETE*
