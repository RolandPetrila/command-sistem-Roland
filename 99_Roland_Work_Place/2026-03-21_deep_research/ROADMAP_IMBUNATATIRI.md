# Roadmap Imbunatatiri — Roland Command Center

Data: 2026-03-21 | Bazat pe Deep Research v2.0

---

## PRIORITATE 1 — Quick Wins (Saptamana 1)

### QW1. Lazy import TOATE librariile grele [CRITICAL, 45 min]

**Problema:** Backend import time 24s din cauza a 5 librarii importate la module level.

**Fisiere de modificat (8 locatii):**

1. `backend/app/core/pricing/similarity.py:17` — sklearn (~2-3s):
```python
# Muta in corpul calculate_similarity_price():
def calculate_similarity_price(...):
    from sklearn.preprocessing import StandardScaler
    ...
```

2. `backend/app/core/calibration.py:23` — scipy (~1-2s):
```python
# Muta in corpul run_calibration():
def run_calibration(...):
    from scipy.optimize import minimize
    ...
```

3. `backend/modules/ai/router.py:33-34` — PyMuPDF + python-docx (~3-4s):
```python
# Muta in _extract_text():
def _extract_text(file_path):
    if file_path.endswith('.pdf'):
        import fitz
        ...
    elif file_path.endswith('.docx'):
        from docx import Document as DocxDocument
        ...
```

4. `backend/modules/translator/router.py:8-9` — PyMuPDF + python-docx (~2-3s, DUPLICAT!):
```python
# Acelasi pattern ca la ai/router.py
```

5. `backend/app/core/analyzer.py:15` — pdfplumber (~2-3s):
```python
# Muta in extract_features():
def extract_features(file_path):
    import pdfplumber
    ...
```

**Verificare:** `python -c "import time; t=time.time(); from app.main import app; print(f'{time.time()-t:.2f}s')"` — target < 5s

---

### QW2. Adauga PRAGMA-uri performanta in get_db() [HIGH, 15 min]

**Fisier:** `backend/app/db/database.py:121-129`

```python
# DUPA busy_timeout, adauga:
await db.execute("PRAGMA journal_mode = WAL")
await db.execute("PRAGMA synchronous = NORMAL")
await db.execute("PRAGMA cache_size = -64000")  # 64MB
await db.execute("PRAGMA temp_store = MEMORY")
await db.execute("PRAGMA mmap_size = 268435456")  # 256MB
```

**Verificare:** Deschide SQLite DB, verifica `PRAGMA journal_mode` returneaza "wal"

---

### QW3. Lazy load DashboardPage [MEDIUM, 5 min]

**Fisier:** `frontend/src/App.jsx:6-7`

```jsx
// INAINTE:
import DashboardPage from './pages/DashboardPage';

// DUPA:
const DashboardPage = lazy(() => import('./pages/DashboardPage'));
```

**Verificare:** `npx vite build` — DashboardPage apare ca chunk separat

---

### QW4. Few-shot examples in AI prompts [MEDIUM, 30 min]

**Fisiere:**

1. `invoice/router.py:891` — adauga dupa "Raspunde DOAR cu JSON valid":
```
Exemplu output valid:
{"supplier_name": "SC Exemplu SRL", "invoice_number": "F-001", "amount": 1500.00, "currency": "RON"}
```

2. `translator/router.py:876` — adauga dupa "Raspunde DOAR cu un JSON valid":
```
Exemplu output valid:
{"score": 7, "issues": ["Termenul 'deadline' nu a fost tradus"], "suggestions": ["Foloseste 'termen limita' in loc de 'deadline'"]}
```

---

### QW5. Fix SQL injection date interpolation [HIGH, 5 min]

**Fisier:** `backend/modules/reports/router.py:333`

```python
# INAINTE:
f"WHERE timestamp >= date('now', '-{days} days')"

# DUPA:
"WHERE timestamp >= datetime('now', ?)", (f"-{int(days)} days",)
```

---

### QW6. Extrage _extract_text() in modul partajat [MEDIUM, 20 min]

**Problema:** Functie identica in ai/router.py:48-91 SI ai/router_extensions.py:48-70.

**Actiune:**
1. Creeaza `backend/app/core/text_utils.py` cu `_extract_text()` si `_truncate_text()`
2. Importa din ambele routere AI
3. Elimina ~30 linii duplicate

---

### QW7. Adauga max_length pe translator text [MEDIUM, 5 min]

**Fisier:** `backend/modules/translator/router.py` — TranslateTextRequest

```python
class TranslateTextRequest(BaseModel):
    text: str = Field(..., max_length=100000)  # adauga max_length
    ...
```

---

### QW8. Adauga indexuri DB lipsa [MEDIUM, 15 min]

**Fisier nou:** `backend/migrations/016_performance_indexes.sql`

```sql
CREATE INDEX IF NOT EXISTS idx_ai_config_key ON ai_config(key);
CREATE INDEX IF NOT EXISTS idx_chat_messages_session_ts ON chat_messages(session_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_glossary_domain_term ON glossary_terms(domain, term);
INSERT INTO schema_version (version, name) VALUES (16, 'performance_indexes');
```

---

## PRIORITATE 2 — Securitate & Stabilitate (Saptamana 2)

### S1. Constante explicite pentru SQL dinamic [HIGH, 1h]
- Inlocuieste f-string table/column cu dict lookup
- Depinde de: nimic

### S2. Teste pentru module netestate [HIGH, 4h]
- translator, filemanager, reports (minimum)
- Depinde de: QW1 (pornire mai rapida)

### S3. MIME validation pe file upload [MEDIUM, 30 min]
- Depinde de: nimic

### S4. Inlocuieste operatii I/O blocante cu async [MEDIUM, 2-3h]
- Foloseste `aiofiles` sau `loop.run_in_executor()` pentru open(), write_bytes(), fitz.open()
- 15+ locatii in app/api/ si app/core/
- Depinde de: nimic

---

## PRIORITATE 3 — Refactorizare (Saptamana 3-4)

### A1-A3. Sparge routerele mari
- A1: invoice/router.py (2050 linii) → 4-5 sub-routere
- A2: ai/router_extensions.py (1052 linii) → 2-3 sub-routere
- A3: reports/router.py (1035 linii) → 3 sub-routere
- **OBLIGATORIU:** Depinde de S2 (teste existente inainte de refactorizare)

---

## IMPACT ESTIMAT

Dupa implementare completa:
- Backend start: 24s → **3-5s** (QW1 — toate librariile lazy)
- DB query speed: +30-50% (QW2 pragmas + QW8 indexuri)
- SQL injection fix: risk eliminat (QW5)
- Cod duplicat: -30 linii (QW6)
- Bundle initial: -50KB gzip (QW3)
- AI accuracy: +10-15% (QW4 few-shot)
- Async safety: event loop nu mai blocheaza pe PDF-uri mari (S4)
- Test coverage: 38% → 70% (S2)
- Maintainability: significativ mai bun (A1-A3)

**Timp total Quick Wins (QW1-QW8): ~2.5h**
**Scor proiectat dupa QW+S: 63/80 → 72-75/80**
