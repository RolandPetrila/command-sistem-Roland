# TODO — Plan Implementare Roland Command Center
Data: 2026-03-21 | Generat dupa: Deep Research + Sabloane + Cerinta_Roland + EVALUARE

---

## FAZA A — ✅ DONE: Actualizare Provideri AI (2026-03-21)
**Prioritate:** CRITICA | **Efort:** ~2h | **Risc:** LOW
**Status:** ✅ IMPLEMENTAT COMPLET — Faza 25A

| # | Actiune | Status |
|---|---------|--------|
| A1 | ✅ Update model Gemini | `gemini-2.0-flash` → `gemini-2.5-flash` in providers.py + translator/providers.py |
| A2 | ✅ Adauga CerebrasProvider | Model: `qwen-3-235b-a22b-instruct-2507`, testat OK |
| A3 | ✅ Adauga MistralProvider | Model: `mistral-small-latest`, testat OK |
| A4 | ✅ Creeaza `.env` backend | Toate cheile API configurate, gitignored |
| A5 | ✅ Update chain order | Gemini → Cerebras → Groq → Mistral → OpenAI (legacy) |
| A6 | ✅ Test toti providerii | Toate 4 raspund corect cu prompt real |

---

## FAZA D — ✅ DONE: Securitate Quick Wins (2026-03-21)
**Prioritate:** MARE | **Efort:** ~1.5h | **Risc:** LOW
**Status:** ✅ IMPLEMENTAT COMPLET — Faza 25B

| # | Actiune | Status |
|---|---------|--------|
| D1 | ✅ SQL whitelist | Verificat: FALS POZITIV — lista hardcodata, nu user input |
| D2 | ✅ Fix catch blocks | SystemConfig.jsx + InvoicePercent.jsx — console.error adaugat |
| D3 | ✅ AI translate prompt | "Raspunde EXCLUSIV in {target_lang}" in Gemini + OpenAI providers |
| D4 | ✅ Rate limiting | Middleware in main.py: 60 req/min global, 10 req/min AI + translate |

---

## FAZA C — ✅ DONE: Fix-uri din Cerinta_Roland.md (2026-03-21)
**Prioritate:** MARE | **Efort:** ~3h | **Risc:** MEDIUM
**Status:** ✅ IMPLEMENTAT COMPLET — Faza 25C

| # | Actiune | Status |
|---|---------|--------|
| C1 | ✅ Fix interceptor axios | Catch ECONNABORTED + ERR_NETWORK + no response → toast + log |
| C2 | ✅ Batch traducere PDF | 10 paragrafe/batch cu separator ---PARA---, ~10x mai putine apeluri API |
| C3 | ✅ Traducere tabele DOCX | doc.tables → row → cell.text, structura tabelului pastrata |
| C4 | ✅ Timeout adaptiv | File upload/translate: 300s (era 120s), default: 60s |

**Limitari cunoscute (neschimbate):**
- PDF pierde layout-ul (text brut → DOCX). Reconstituirea layout-ului PDF nu se implementeaza.
- DOCX headers/footers/footnotes nu se traduc (limitare python-docx).

---

## FAZA B — ✅ DONE: Speed Test Internet (2026-03-21)
**Prioritate:** MEDIE | **Efort:** ~2h | **Risc:** LOW
**Status:** ✅ IMPLEMENTAT COMPLET — Faza 25D

| # | Actiune | Status |
|---|---------|--------|
| B1 | ✅ Backend endpoint | GET /api/network/speed-payload — 500KB, no-store cache |
| B2 | ✅ Frontend component | NetworkSpeedIndicator.jsx — Navigator.connection + fallback download |
| B3 | ✅ Integrare Header | Indicator: Mbps + ms, verde/galben/rosu, click remeasure |
| B4 | ✅ Auto-refresh 60s | setInterval 60s, fara flood backend |

---

## FAZA E — ✅ DONE: Fundament Testare (2026-03-21)
**Prioritate:** MEDIE | **Efort:** ~4h | **Risc:** LOW
**Status:** ✅ IMPLEMENTAT COMPLET — Faza 25E — 18/18 teste PASSED

| # | Actiune | Status |
|---|---------|--------|
| E1 | ✅ Install pytest | pytest + httpx + pytest-asyncio instalate |
| E2 | ✅ Structura tests/ | conftest.py cu AsyncClient ASGI, fixture `client` |
| E3 | ✅ Test health (5 teste) | health OK, response time, modules list, diagnostics, speed payload |
| E4 | ✅ Test translate (4 teste) | EN→RO OK, empty rejected, detect language, providers list |
| E5 | ✅ Test AI (4 teste) | providers, config, sessions list, session CRUD |
| E6 | ✅ Test invoice (2 teste) | client CRUD complet (create→read→update→delete), clients list |
| E7 | ✅ Test ITP (3 teste) | inspection create+read, list, stats overview |

**Rulare:** `cd backend && python -m pytest tests/ -v`

---

## FAZA F — NEIMPLEMENTAT: Top 10 Features P1 din EVALUARE
**Prioritate:** MICA (next sessions) | **Efort:** ~40-60h total | **Risc:** MEDIUM
**Motivatie:** 28 sugestii P1 din evaluarea completa a 145 features posibile.
**Status:** PLANIFICAT — sesiuni viitoare

| # | Feature | Modul | Efort | Din EVALUARE |
|---|---------|-------|-------|-------------|
| F1 | Voice Input (Web Speech API) | AI Chat | 2h | S2.5 |
| F2 | Prompt Templates cu variabile | AI Chat | 4h | S2.2 |
| F3 | Serii Facturi Configurabile | Invoice | 3h | S4.1 |
| F4 | Status Plata + Scadente | Invoice | 4h | S4.3 |
| F5 | Calendar ITP Programari | ITP | 6h | S5.4 |
| F6 | Notificari Unificate (bell icon) | Automations | 6h | S10.1 |
| F7 | Preview Documente in Browser | File Manager | 5h | S8.1 |
| F8 | Calibrare MAPE Interactiva UI | Calculator | 4h | S1.1 |
| F9 | Note Oferta PDF (CIP Inspection) | Calculator | 3h | S1.6 |
| F10 | Glosar per Client | Translator | 2h | S3.1 |

**Dependente:** Fazele A-E completate.

---

## SUMAR EXECUTIE

| Faza | Efort | Prioritate | Status |
|------|-------|-----------|--------|
| ✅ A — Provideri AI | ~2h | CRITICA | DONE (2026-03-21) |
| ✅ D — Securitate | ~1.5h | MARE | DONE (2026-03-21) |
| ✅ C — Fix Cerinta Roland | ~3h | MARE | DONE (2026-03-21) |
| ✅ B — Speed Test | ~2h | MEDIE | DONE (2026-03-21) |
| ✅ E — Testare | ~4h | MEDIE | DONE (2026-03-21) |
| F — Features P1 | ~40h | MICA | PLANIFICAT |

**Sesiune curenta: 5/5 faze complete (A+D+C+B+E)**
**Ordine executata: A → D → C → B → E**

---

## RESURSE NECESARE

### Chei API (configurate in `backend/.env`):
- ✅ GEMINI, GROQ, CEREBRAS, MISTRAL — AI providers
- ✅ DEEPL, AZURE_TRANSLATE — Translation providers

### Librarii instalate:
- ✅ `slowapi` — rate limiting (Faza D)
- `pytest`, `httpx`, `pytest-asyncio` — testare (Faza E, neinstalate)

### Modele AI active (martie 2026):
| Provider | Model | Free tier |
|----------|-------|-----------|
| ✅ Gemini | gemini-2.5-flash | 10 RPM, 250 req/zi |
| ✅ Cerebras | qwen-3-235b-a22b-instruct-2507 | 30 RPM, 1M tok/zi |
| ✅ Groq | llama-3.3-70b-versatile | 30 RPM |
| ✅ Mistral | mistral-small-latest | 2 RPM, 1B tok/luna |
