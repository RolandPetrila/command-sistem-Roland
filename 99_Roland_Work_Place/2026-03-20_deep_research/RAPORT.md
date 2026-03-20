# DEEP RESEARCH COMPLET — Roland Command Center

Data: 2026-03-20 22:15 | Mod: COMPLET
Stack: FastAPI + React 18 + Vite + SQLite | Surse web: 6 | Agenti: 6 | Timp: ~18 min

---

## SCOR GENERAL

| Aspect | Scor | Vizual |
|--------|------|--------|
| Securitate | 8/10 | ████████░░ |
| Calitate Cod | 7/10 | ███████░░░ |
| Arhitectura | 9/10 | █████████░ |
| Testare | 1/10 | █░░░░░░░░░ |
| Performanta | 9/10 | █████████░ |
| Documentatie | 10/10 | ██████████ |
| Dependente | 8/10 | ████████░░ |
| Deploy Ready | 9/10 | █████████░ |

**TOTAL: 61/80 — BUN (testarea trage scorul in jos masiv)**

---

## METRICI PROIECT

| Metric | Valoare |
|--------|---------|
| Fisiere Python | 65 |
| Fisiere JSX/JS | 65 |
| Linii Python | 17,792 |
| Linii JS/JSX | 11,737 |
| **Total LOC** | **~29,500** |
| Module backend | 13 (auto-discovered) |
| Pagini frontend | 25 (24 lazy-loaded) |
| Tabele DB | 53 |
| Migratii SQL | 14 |
| Reguli .claude | 8 |
| Bundle total | 1.1 MB |
| Indexuri DB | 10+ |

---

## GASIRI CRITICE (actiune imediata)

### [CRITICAL] [ROI: 10] Zero teste automatizate
- **Problema**: Exista doar 2 fisiere de test legacy (`test_analyzer_correlation.py`, `test_ensemble_26.py`). Niciun test pentru 13 module backend, 25 pagini frontend.
- **Root cause**: Proiectul a crescut rapid prin faze succesive fara a include teste
- **Impact**: Orice modificare poate sparge functionalitate fara sa stii. Regula 08 (post-change validation) compenseaza partial, dar manual.
- **Fix recomandat**: Adauga pytest + httpx.AsyncClient teste pentru minimum 5 endpoint-uri critice (health, translate, ai/chat, invoice, itp). ~4h efort.
- **Efort**: MARE | **Risc implementare**: LOW

### [CRITICAL] [ROI: 9] Fisiere router supradimensionate
- **Problema**: 5 routere depasesc 800 linii:
  - `invoice/router.py` — **1,751 linii** (cel mai mare fisier din proiect)
  - `ai/router_extensions.py` — **1,052 linii**
  - `reports/router.py` — **1,035 linii**
  - `integrations/router.py` — **966 linii**
  - `translator/router.py` — **910 linii**
- **Root cause**: Fiecare modul are un singur router.py cu toate endpoint-urile
- **Impact**: Greu de navigat, modificari riscante, merge conflicts potential
- **Fix recomandat**: Sparge in sub-routere pe domeniu (ex: `invoice/router_clients.py`, `invoice/router_reports.py`, `invoice/router_templates.py`). Fara schimbare de comportament.
- **Efort**: MEDIU per modul | **Risc**: LOW (restructurare interna)

---

## GASIRI IMPORTANTE (recomandate)

### [HIGH] [ROI: 8] SQL cu f-strings — risc potential injectie
- **Fisiere afectate**:
  - `routes_history.py:72` — `f"SELECT COUNT(*) as total FROM history {where_sql}"`
  - `automations/router.py:264` — `f"UPDATE scheduled_tasks SET {', '.join(updates)} WHERE id = ?"`
  - `invoice/router.py:257` — `f"UPDATE clients SET {set_clause}..."`
  - `reports/router.py:399` — `f"SELECT {column} FROM {table}"`
- **Risc**: Daca `where_sql`, `set_clause`, `column`, `table` vin din user input fara sanitizare, e SQL injection
- **Nota**: Majoritatea par sa foloseasca parametri `?` pentru valori, dar numele de coloane/tabele din `reports/router.py:399` sunt risc real
- **Fix**: Verifica ca `column` si `table` sunt whitelisted (nu din user input direct)
- **Efort**: MIC | **Risc**: LOW

### [HIGH] [ROI: 7.5] Niciun rate limiting pe API
- **Problema**: Nu exista rate limiting pe niciun endpoint. Un client malitios (sau bot) poate face flood.
- **Impact pe Tailscale**: Redus (acces doar prin VPN), dar daca vreun device e compromis, tot API-ul e expus
- **Fix**: Adauga `slowapi` (pip install slowapi) cu 60 req/min global, 10 req/min pe translate/ai
- **Efort**: MIC (~1h) | **Risc**: LOW
- **Nota**: Fiind single-user pe Tailscale, prioritatea e mai mica decat la un API public

### [HIGH] [ROI: 7] 41 fisiere necommitted
- **Problema**: 41 fisiere modificate, 3,062 insertii, 689 stergeri — tot de la Faza 22-24 + fix-uri curente
- **Impact**: Risc de pierdere munca daca se intampla ceva cu masina
- **Fix**: `git add [specific files] && git commit -m "Faza 22-24: BAT hardening + diagnostics + error handling"`
- **Efort**: MIC (5 min) | **Risc**: LOW

### [MEDIUM] [ROI: 6] Catch blocks inca goale in componente
- **Fisiere**: `CalibrationPanel.jsx`, `ActivityLog.jsx`, `ExchangeRateCard.jsx`, `FileBrowser.jsx`, `Header.jsx`
- **Nota**: Paginile principale au fost fixate in Faza 23, dar cateva componente au ramas cu `catch { }` gol
- **Impact**: Erori silentioase in componente secundare
- **Efort**: MIC (~30 min)

### [MEDIUM] [ROI: 5.5] Un singur branch Git
- **Problema**: Doar `master`, niciun `main` remote, nicio strategie de branching
- **Impact**: Nicio protectie impotriva push-urilor gresite
- **Fix**: Configureaza `main` ca branch protejat pe GitHub, lucreaza pe feature branches
- **Efort**: MIC

---

## IMBUNATATIRI SUGERATE (optional, ROI descrescator)

### [MEDIUM] [ROI: 5] PaddleOCR ca alternativa la Tesseract+EasyOCR
- PaddleOCR-VL-1.5 (2026) atinge 94.5% acuratete, suporta 109 limbi inclusiv romana si slovaca
- Avantaj: layout detection superior (tabele, formule), un singur model in loc de doua
- **Efort**: MEDIU | **Free**: DA (open source)
- **Recomandare**: [ALTERNATIVA INTERESANTA] — evalueaza cand OCR-ul actual nu e suficient

### [MEDIUM] [ROI: 4.5] Gemini 2.5 Flash-Lite ca provider AI volume
- 15 RPM, 1,000 requests/zi, 250K tokens/min — Mai generos decat Flash standard
- **Recomandare**: [UPGRADE RECOMANDAT] — adauga ca provider secundar dupa Gemini Flash

### [LOW] [ROI: 3] DOCX table translation in Translator
- Actualmente doar paragrafele sunt traduse, tabelele sunt ignorate
- python-docx poate itera `doc.tables` → `table.rows` → `cell.text`
- **Efort**: MEDIU (~2h)

### [LOW] [ROI: 2.5] Bundle optimization — recharts e 402KB
- `vendor-charts` e cel mai mare chunk (402KB / 110KB gzipped)
- Alternativa: `lightweight-charts` sau lazy-load chart-urile doar pe DashboardPage
- **Impact real**: Minim — gzip reduce la 110KB, si e deja code-split
- **Recomandare**: [NU MERITA SCHIMBAREA] acum

---

## DEPENDENCY MAP

```
app/main.py
  ├── app/module_discovery.py → scaneaza modules/*/
  ├── app/core/activity_log.py ← folosit de TOATE modulele
  ├── app/db/database.py ← folosit de TOATE modulele
  ├── app/api/ (7 routere calculator legacy)
  └── modules/ (13 auto-discovered)

modules/ai/
  ├── router.py (chat, providers, health)
  ├── router_extensions.py (10 AI features)
  ├── providers.py (Gemini, Cerebras, Groq, Mistral, SambaNova)
  └── token_tracker.py

modules/translator/ ──imports──> modules/ai/providers (ai_generate)
modules/invoice/    ──imports──> modules/ai/providers (ai_generate)

(Nicio dependenta circulara detectata)
```

---

## CROSS-PLATFORM (Windows vs Android/Tailscale)

| Config | Windows PC | Android via Tailscale | Potential problema |
|--------|-----------|----------------------|-------------------|
| URL-uri | `window.location.origin` | `window.location.origin` | OK — dinamic |
| WebSocket | `ws://` | `wss://` (TLS) | OK — detectie protocol |
| File upload | OK | Poate fi lent pe retea | Timeout 120s setat |
| PWA | Doar HTTPS | OK cu Tailscale cert | OK |
| OCR local | Tesseract installed | N/A (server-side) | OK |
| Keyboard shortcuts | Ctrl+K, Ctrl+/ | N/A pe touch | Posibil confusing |

---

## SECURITATE — DETALII

| Check | Status | Detalii |
|-------|--------|---------|
| CORS | OK | Origini specifice + Tailscale dinamic |
| .gitignore | OK | .env, *.db, certs/, node_modules/, dist/ |
| CSP Headers | OK | Implementat in middleware |
| Path traversal | OK | filemanager: `resolve()` + `relative_to()` check |
| SQL Injection | ATENTIE | f-strings in 4 routere — verifica whitelist |
| Rate Limiting | LIPSESTE | Niciun rate limit pe niciun endpoint |
| Secrets in cod | OK | Niciun API key hardcodat |
| HTTPS | OK | TLS via Tailscale certs |
| Bare except | OK | 0 `except:` bare in Python |
| Auth | N/A | Single-user, Tailscale ca securitate |

---

## FRAGILE CODE HOTSPOTS

| Fisier | Modificari (30 commits) | Cauza | Recomandare |
|--------|------------------------|-------|-------------|
| CLAUDE.md | 6 | Auto-update dupa fiecare faza | Normal — tracking file |
| App.jsx | 5 | Fiecare pagina noua = route nou | Normal — entry point |
| manifest.js | 4 | Fiecare pagina noua = nav entry | Normal |
| Sidebar.jsx | 3 | Ajustari UI iterative | Monitor |
| main.py | 3 | Middleware adaugat in faze | Atentie — cel mai critic fisier |

---

## DEAD CODE — IDENTIFICAT

| Tip | Locatie | Detalii |
|-----|---------|---------|
| console.log | `client.js:191` | WebSocket debug — acceptabil dar ideal de sters in prod |
| `catch { /* ignore */ }` | `client.js:40` | In interceptor — e intentionat (backend report fallback) |
| Legacy test files | `backend/test_*.py` (2) | Teste vechi care probabil nu mai ruleaza |

---

## AI PROMPT AUDIT

| Locatie | Scop | Observatie |
|---------|------|-----------|
| `translator/router.py:223` | Traducere via AI | Prompt simplu "Traduce din X in Y" — functional dar fara few-shot |
| `ai/router_extensions.py` | 10 AI features | Prompt-uri cu format JSON strict — bine structurate |
| `translator/router.py:833` | Quality check | Prompt cu criteriu evaluare + format JSON — bun |
| `invoice/router.py` | OCR+AI pe facturi | Prompt cu template cerut — functional |

**Sugestie**: Adauga "Respond ONLY in [target_lang]" la prompt-ul de traducere AI — uneori modelele raspund in limba gresita.

---

## CE AM OMIS / CE POATE FI INCORECT

1. **Nu am rulat `npm audit` sau `pip audit`** — nu am verificat vulnerabilitati in dependente
2. **Nu am testat efectiv pe Android** — analiza cross-platform e teoretica
3. **Scorurile sunt estimari** — nu exista benchmark obiectiv
4. **Agentii de explorare au dat timeout** pe unele task-uri — cateva date sunt din scan-ul direct
5. **Nu am analizat edge-tts, pdfplumber, scikit-learn** in detaliu — pot avea probleme specifice
