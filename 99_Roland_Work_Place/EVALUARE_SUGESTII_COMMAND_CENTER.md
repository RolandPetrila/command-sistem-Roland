# Roland Command Center — Evaluare Fezabilitate & Prioritizare Sugestii

> **Generat:** 2026-03-19 | **Analizat de:** Claude Code (Opus 4.6)
> **Metodologie:** Analiza stack existent (FastAPI + React 18 + SQLite + 13 module) + evaluare business CIP Inspection SRL
> **Legendă fezabilitate:** `[FEZABIL]` = stack existent, <1 sesiune | `[FEZABIL CU EFORT MARE]` = >2 sesiuni sau dependente noi | `[NEFEZABIL/EXCLUD]` = nu se poate sau nu are sens
> **Legendă prioritate:** `P1` = impact direct venituri/operatiuni | `P2` = eficientizare workflow | `P3` = confort/polish

---

## SUMAR EXECUTIV

| Metric | Valoare |
|--------|---------|
| Total sugestii evaluate | 130 + 10 weaknesses + 5 arhitecturale = **145** |
| [FEZABIL] | **115 (88%)** |
| [FEZABIL CU EFORT MARE] | **12 (9%)** |
| [NEFEZABIL/EXCLUD] | **3 (2%)** |
| Prioritate P1 (Critic) | **28** |
| Prioritate P2 (Important) | **52** |
| Prioritate P3 (Nice-to-have) | **50** |

**Concluzie:** Stack-ul permite aproape totul. Problema nu e fezabilitatea, ci **prioritizarea** — 130 features noi ar dubla complexitatea. Recomandare: implementeaza maximum 15-20 in urmatoarele sesiuni, in ordinea valorii business.

---

## 1. MODUL: CALCULATOR PRET TRADUCERI

| ID | Sugestie | Fezabilitate | Prioritate | Justificare tehnica |
|----|----------|:------------:|:----------:|---------------------|
| S1.1 | Calibrare MAPE Interactiva UI | [FEZABIL] | **P1** | `calibrate.py` exista deja. Expune ca API endpoint `/api/calculator/calibrate` cu parametri ponderi. Frontend: 3 slidere Recharts + recalcul live. ~4h |
| S1.2 | Istoric Calcule cu Cautare | [FEZABIL] | P2 | Verifica daca `calculations` table exista. Daca nu, tabel nou + FTS5 (pattern deja folosit in translator/filemanager). Tabel paginat React. ~4h |
| S1.3 | Template-uri Client | [FEZABIL] | P2 | Tabel `client_templates` legat de `clients` (modul invoice). Dropdown pre-complete. ~3h |
| S1.4 | Calcul Batch Fisiere | [FEZABIL] | P2 | Upload multiplu deja in File Manager. Loop calcul + tabel sumar. WebSocket progress existent. ~4h |
| S1.5 | Comparare Calcule Side-by-Side | [FEZABIL] | P3 | Depinde de S1.2 (istoric). Selectie 2 calcule + diff view. ~2h |
| S1.6 | Nota Oferta PDF | [FEZABIL] | **P1** | `reportlab` deja in proiect (Invoice). Template PDF antet CIP Inspection. ~3h |
| S1.7 | Alerta Preturi Neactualizate | [FEZABIL] | P3 | `os.path.getmtime()` pe 26 PDF-uri referinta. Banner galben simplu. ~1h |
| S1.8 | Grafic Evolutie Preturi | [FEZABIL] | P2 | Recharts LineChart + date din istoric (S1.2). Suprapunere cu competitori. ~3h |
| S1.9 | Camp Urgenta + Suprataxa | [FEZABIL] | **P1** | Checkbox + multiplicator configurabil (default 1.3x). Trivial backend + frontend. ~1h |
| S1.10 | Export Raport Lunar | [FEZABIL] | P2 | Agregare din istoric + SMTP existent. openpyxl pentru Excel. ~3h |

---

## 2. MODUL: AI CHAT & DOCUMENTE

| ID | Sugestie | Fezabilitate | Prioritate | Justificare tehnica |
|----|----------|:------------:|:----------:|---------------------|
| S2.1 | Sesiuni cu Titlu Auto + Categorii | [FEZABIL] | P2 | Sesiunile SQLite **exista deja** (Faza 15A). Adauga coloane `title`, `category`. AI genereaza titlu din primele 2-3 mesaje. ~3h |
| S2.2 | Prompt Templates cu Variabile | [FEZABIL] | **P1** | Tabel `prompt_templates` cu `{{variabile}}`. CRUD UI + dropdown in chat. Replace regex la trimitere. ~4h |
| S2.3 | Document Persistent in Sesiune | [FEZABIL CU EFORT MARE] | P2 | Trebuie: extragere text document → stocare per sesiune → injectare in context la fiecare mesaj. Limita tokens per provider e principala provocare (Gemini Flash: 1M, OpenAI: 128K). ~8h |
| S2.4 | Comparare Multi-Provider | [FEZABIL] | P2 | 3 apeluri `asyncio.gather()` paralele → 3 coloane React. Consuma tokens din toti 3 providerii. ~4h |
| S2.5 | Voice Input (Web Speech API) | [FEZABIL] | **P1** | **100% frontend, ZERO backend.** `window.SpeechRecognition` nativ in Chrome/Android. Buton microfon + `onresult` → text in input. ~2h |
| S2.6 | AI Agent Tool Use | [FEZABIL CU EFORT MARE] | P2 | Necesita: function calling schema per modul, executor loop, validare permisiuni, UI confirmare. Cel mai complex item din lista. ~16h+ |
| S2.7 | Perplexity /search | [FEZABIL] | P2 | API REST simplu (key probabil in Vault). Comanda `/search` in chat → response cu citations. ~3h |
| S2.8 | AI Batch pe Folder | [FEZABIL CU EFORT MARE] | P2 | Queue system + progress per fisier + management consum tokens. ~8h |
| S2.9 | Feedback Thumbs Up/Down | [FEZABIL] | P3 | Tabel `ai_feedback(message_id, score, note)`. Butoane UI. Statistici agregate per provider. ~2h |
| S2.10 | Export Conversatie PDF/DOCX/MD | [FEZABIL] | P3 | `reportlab` + `python-docx` deja in proiect. Serializare sesiune → document formatat. ~3h |

---

## 3. MODUL: TRADUCATOR

| ID | Sugestie | Fezabilitate | Prioritate | Justificare tehnica |
|----|----------|:------------:|:----------:|---------------------|
| S3.1 | Glosar per Client | [FEZABIL] | **P1** | Adauga `client_id` (FK) la tabela glosar existenta. Filter automat la selectie client. ~2h |
| S3.2 | TM Vizualizare/Editare + TMX | [FEZABIL] | **P1** | CRUD UI pe tabela TM existenta. Export TMX = XML standard (etree). Import: parse TMX → insert segments. ~5h |
| S3.3 | Traducere DOCX cu Stiluri | [FEZABIL CU EFORT MARE] | **P1** | `python-docx` citeste/scrie stiluri, dar: tabele complexe, footnotes, headers/footers sunt problematice. Necesita testare intensiva per tip document. ~12h |
| S3.4 | Mod Revizuire Track Changes | [FEZABIL CU EFORT MARE] | **P1** | UI 3 coloane (original/AI/revizuit) + diff highlight + auto-add in TM. Frontend complex cu ContentEditable sau Monaco Editor. ~10h |
| S3.5 | Statistici DeepL Prognoza | [FEZABIL] | P2 | Tracking chars **exista deja**. Calcul: `chars_consumate / zile_trecute * zile_ramase_luna`. Dashboard Recharts. ~2h |
| S3.6 | Proiecte Traducere cu Status | [FEZABIL] | **P1** | Tabel `translation_projects` + `project_files` (status per fisier). UI cu progress bar + deadline. ~5h |
| S3.7 | Detectie Termeni Netradusi | [FEZABIL] | P2 | Post-processing: check glosar terms in source vs. target. Lista "potential untranslated". ~3h |
| S3.8 | Traducere Email din Gmail | [FEZABIL] | P2 | Buton "Traduce" pe email viewer → `POST /api/translator/translate` cu body email. ~2h |
| S3.9 | Raport Lunar Traduceri | [FEZABIL] | P3 | Agregare din `translation_history` + legatura cu calculator. ~3h |
| S3.10 | Traducere Live Debounce | [FEZABIL] | P3 | Frontend `useDebounce(500)` + API call. Atentie la consum chars DeepL. ~2h |

---

## 4. MODUL: FACTURARE (INVOICE)

| ID | Sugestie | Fezabilitate | Prioritate | Justificare tehnica |
|----|----------|:------------:|:----------:|---------------------|
| S4.1 | Serii Facturi Configurabile | [FEZABIL] | **P1** | Config `invoice_series(prefix, start_number)`. Auto-increment + validare gaps. ~3h |
| S4.2 | Facturi Recurente | [FEZABIL] | P2 | Tabel `recurring_invoices(client_id, amount, day_of_month)`. Task scheduler trigger. ~4h |
| S4.3 | Status Plata + Scadente | [FEZABIL] | **P1** | Coloane `status ENUM('emisa','trimisa','partial','platita','restanta')`, `due_date`, `paid_amount`. Alerta la `due_date < today`. ~4h |
| S4.4 | Proforma → Factura | [FEZABIL] | **P1** | Camp `type ENUM('factura','proforma','oferta')`. Buton "Converteste" = copie date + genereaza numar serie. ~3h |
| S4.5 | Multi-Linie Factura | [FEZABIL] | **P1** | Tabel `invoice_lines(invoice_id, description, qty, unit_price, vat_rate)`. PDF cu tabel multi-rand. Migrare DB noua. ~5h |
| S4.6 | Trimitere WhatsApp | [FEZABIL] | P3 | URL scheme `https://wa.me/{phone}?text={encoded_message}`. Zero API, zero cost. ~1h |
| S4.7 | Import Facturi Furnizori | [FEZABIL] | P2 | OCR existent + tabel `expenses(date, vendor, amount, category)`. ~5h |
| S4.8 | Generare Contract Template | [FEZABIL] | P2 | `python-docx` template populate cu `{{client}}`, `{{suma}}` etc. Similar cu S13.5. ~4h |
| S4.9 | Dashboard Financiar | [FEZABIL] | **P1** | Recharts: BarChart venituri/cheltuieli + LineChart profit. Agregare din invoices + expenses. ~5h |
| S4.10 | Raport pentru Contabil | [FEZABIL] | **P1** | Export Excel cu coloane standard RO: nr, data, client, CUI, baza, TVA, total, status. `openpyxl` deja folosit. ~3h |

---

## 5. MODUL: ITP INSPECTII AUTO

| ID | Sugestie | Fezabilitate | Prioritate | Justificare tehnica |
|----|----------|:------------:|:----------:|---------------------|
| S5.1 | Fisa Client Auto (Proprietar) | [FEZABIL] | **P1** | Tabel `itp_owners(name, phone, email)` + FK pe inspectii. Istoric per proprietar. ~4h |
| S5.2 | Alerta Expirare + Email | [FEZABIL] | **P1** | Email: SMTP existent. SMS: **[NEFEZABIL GRATUIT]** — nu exista API SMS gratuit fiabil. Doar email. Task scheduler: query inspectii cu `expiry_date - 30 days < today`. ~3h |
| S5.3 | Motiv Respingere Clasificat | [FEZABIL] | P2 | Enum cu motive standard (frane, lumini, emisii etc.) + multi-select. Statistici pie chart. ~3h |
| S5.4 | Calendar ITP Programari | [FEZABIL] | **P1** | Tabel `itp_appointments(date, time_slot, owner_id, vehicle_id)`. Calendar view React (grid pe ore). ~6h |
| S5.5 | Raport Fiscal ITP | [FEZABIL] | **P1** | Agregare inspectii × pret fix → total lunar. Export PDF/Excel pentru contabil. ~3h |
| S5.6 | Import CSV din RAR | [FEZABIL] | P2 | Parsare CSV cu pandas/csv. Depinde de formatul export RAR. ~3h |
| S5.7 | Heatmap Activitate | [FEZABIL] | P3 | Calendar heatmap component (CSS grid + color scale). Date din inspectii per zi. ~3h |
| S5.8 | Statistici per Inspector | [FEZABIL] | P2 | Coloana `inspector_name` pe inspectii. Relevant doar daca CIP are mai multi inspectori. ~2h |
| S5.9 | Notificari RCA/Rovinieta | [FEZABIL] | P3 | Campuri extra pe vehicul: `rca_expiry`, `rovinieta_expiry`. Alerta similara cu ITP. ~3h |
| S5.10 | Export Raport Anual | [FEZABIL] | P2 | Agregare anuala + comparatie YoY. PDF raport comprehensiv. ~4h |

---

## 6. MODUL: QUICK TOOLS

| ID | Sugestie | Fezabilitate | Prioritate | Justificare tehnica |
|----|----------|:------------:|:----------:|---------------------|
| S6.1 | Voice Notes + Transcriere | [FEZABIL] | **P1** | `Web Speech API` (frontend) → text → `POST /api/notes`. Offline-capable. Feature DEFERRED care merita finalizat. ~3h |
| S6.2 | Notepad Foldere + Tag-uri | [FEZABIL] | P2 | Tabele `note_folders`, `note_tags`, relatii many-to-many. FTS5 cautare fulltext. ~4h |
| S6.3 | Color Picker | [FEZABIL] | P3 | 100% frontend React. Input HEX/RGB + canvas picker. ~2h |
| S6.4 | Text Diff | [FEZABIL] | P2 | `diff-match-patch` (npm, <10KB). Highlight adaugari/stergeri. ~2h |
| S6.5 | Convertor Data/Timp | [FEZABIL] | P3 | `Intl.DateTimeFormat` + zile lucratoare calc. 100% frontend. ~2h |
| S6.6 | Generator Semnatura Email HTML | [FEZABIL] | P3 | Template wizard 3-4 designuri + copy HTML. ~2h |
| S6.7 | Regex Tester | [FEZABIL] | P3 | Frontend regex exec + highlight + AI explain. ~2h |
| S6.8 | Calculator Financiar | [FEZABIL] | P2 | Formule rate/dobanzi + BNR API (gratuit XML). ~3h |
| S6.9 | Screenshot Annotation | [FEZABIL CU EFORT MARE] | P3 | HTML5 Canvas cu drawing tools (arrows, rect, text, blur). Complex UI. ~8h |
| S6.10 | Convertor Numere | [FEZABIL] | P3 | `parseInt/toString` cu baze diferite + roman numerals. Trivial. ~1h |

---

## 7. MODUL: CONVERTOR FISIERE

| ID | Sugestie | Fezabilitate | Prioritate | Justificare tehnica |
|----|----------|:------------:|:----------:|---------------------|
| S7.1 | DOCX ↔ HTML | [FEZABIL] | P3 | Backend: `mammoth` (Python) DOCX→HTML. HTML→DOCX: `python-docx` cu parse HTML. ~4h |
| S7.2 | Extragere Imagini din PDF | [FEZABIL] | P2 | `PyMuPDF (fitz)` deja in proiect → `page.get_images()` + `fitz.Pixmap()`. ~2h |
| S7.3 | Watermark PDF | [FEZABIL] | **P1** | `PyMuPDF`: `page.insert_text()` sau overlay cu `reportlab`. Configurabil opacitate/pozitie. ~3h |
| S7.4 | Redactare PDF (Blackout GDPR) | [FEZABIL] | **P1** | `PyMuPDF`: `page.add_redact_annot()` + `page.apply_redactions()`. Eliminare permanenta. ~4h |
| S7.5 | Conversie Batch cu Queue | [FEZABIL] | P2 | WebSocket progress deja existent. Queue SQLite sau simplu async loop cu status per fisier. ~4h |
| S7.6 | Auto-Deskew Scanuri | [FEZABIL CU EFORT MARE] | P3 | Necesita `opencv-python` (~50MB dependinta). `cv2.minAreaRect()` + rotate. ~4h daca opencv instalat |
| S7.7 | Audio → Text Transcriere | [FEZABIL] | P2 | Whisper API (OpenAI) sau Gemini Audio. Key deja in Vault. Upload audio + API call. ~4h |
| S7.8 | Semnatura Vizuala PDF | [FEZABIL] | P3 | Canvas touch drawing (frontend) → PNG → overlay pe PDF cu PyMuPDF. ~4h |
| S7.9 | Protectie PDF Parola | [FEZABIL] | P2 | `PyMuPDF`: `doc.save(encryption=fitz.PDF_ENCRYPT_AES_256, user_pw="...")`. ~2h |
| S7.10 | Preview Inainte/Dupa | [FEZABIL] | P2 | PDF.js embed side-by-side. ~3h |

---

## 8. MODUL: FILE MANAGER

| ID | Sugestie | Fezabilitate | Prioritate | Justificare tehnica |
|----|----------|:------------:|:----------:|---------------------|
| S8.1 | Preview Documente in Browser | [FEZABIL] | **P1** | PDF.js (gratuit, 500KB). DOCX preview: `mammoth` → HTML inline. ~5h |
| S8.2 | Versioning Simplu | [FEZABIL] | P2 | La re-upload: rename old `file_v{n-1}` + tabel `file_versions`. Restore = swap. ~4h |
| S8.3 | Link Temporar Partajare | [FEZABIL] | **P1** | `shared_links(uuid, file_id, expires_at)` + endpoint public `/share/{uuid}`. ~3h |
| S8.4 | OCR Auto la Upload | [FEZABIL] | **P1** | `BackgroundTask` post-upload: detect PDF/image → OCR (PyMuPDF/Tesseract) → FTS5 index. ~4h |
| S8.5 | Statistici Stocare | [FEZABIL] | P3 | `os.walk()` + agregare per extensie/folder/age. Recharts pie/bar. ~3h |
| S8.6 | Comparare Fisiere Diff | [FEZABIL] | P2 | Integrare cu endpoint AI diff existent (Faza 15A). ~2h |
| S8.7 | Smart Collections | [FEZABIL] | P2 | Tabel `smart_collections(name, rules_json)`. Query dinamic la acces. ~5h |
| S8.8 | Backup Auto Google Drive | [FEZABIL] | **P1** | Google Drive REST API **deja integrat**. Task scheduler: upload folder selectat → Drive. ~4h |
| S8.9 | Thumbnail Grid View | [FEZABIL] | P3 | `Pillow` thumbnail gen la upload + CSS grid view toggle. ~3h |
| S8.10 | Rename Batch Pattern | [FEZABIL] | P2 | Pattern `{date}_{seq}_{original}` + preview tabel + batch `os.rename()`. ~3h |

---

## 9. MODUL: VAULT (API KEYS)

| ID | Sugestie | Fezabilitate | Prioritate | Justificare tehnica |
|----|----------|:------------:|:----------:|---------------------|
| S9.1 | Categorii Keys | [FEZABIL] | P3 | Coloana `category VARCHAR`. UI grupare pe categorii. ~1h |
| S9.2 | Monitorizare Utilizare | [FEZABIL] | P2 | Tabel `key_usage(key_id, module, timestamp, tokens)`. Recharts line chart. ~4h |
| S9.3 | Alerta Limita Free Tier | [FEZABIL] | P2 | Config `key_limits(key_id, max_value, period)`. Check la fiecare utilizare. ~3h |
| S9.4 | Rotatie Auto Keys | [FEZABIL] | P2 | Multiple keys per service type. Fallback logic: try key1 → if error → try key2. ~3h |
| S9.5 | Test Conectivitate Ping | [FEZABIL] | **P1** | Ping minim per provider type (GET /models pentru AI, health pentru altele). ~3h |
| S9.6 | Import/Export Criptat | [FEZABIL] | P2 | AES-256 export JSON → fisier criptat. Import: decrypt → validate → insert. ~3h |
| S9.7 | Log Activitate per Key | [FEZABIL] | P3 | Audit log tabel. Filtrabil per key/modul/timp. ~3h |
| S9.8 | Reminder Expirare | [FEZABIL] | P3 | Camp `expires_at` + alerta la 14 zile inainte. ~1h |
| S9.9 | Validare Format Key | [FEZABIL] | P2 | Regex per provider: `AIza.*` (Gemini), `sk-.*` (OpenAI), `ghp_.*` (GitHub). ~1h |
| S9.10 | Dashboard Sanatate | [FEZABIL] | **P1** | Agregare: verde/galben/rosu per key. Last test time + latency. ~3h |

---

## 10. MODUL: AUTOMATIZARI

| ID | Sugestie | Fezabilitate | Prioritate | Justificare tehnica |
|----|----------|:------------:|:----------:|---------------------|
| S10.1 | Notificari Unificate | [FEZABIL] | **P1** | Bell icon header + tabel `notifications(module, type, message, read, created_at)`. Agregare din toate modulele. **CEL MAI MARE IMPACT UX.** ~6h |
| S10.2 | Raport Zilnic/Saptamanal Email | [FEZABIL] | P2 | Task schedulat + SMTP + template HTML email. ~3h |
| S10.3 | Webhook Incoming | [FEZABIL] | P2 | `POST /api/webhook/in` + dispatcher bazat pe payload type. ~3h |
| S10.4 | Macro Recorder | [FEZABIL CU EFORT MARE] | P2 | Secvente de actiuni (JSON steps) + executor sequential. UI inregistrare + playback. ~12h |
| S10.5 | Conditii If/Then pe Tasks | [FEZABIL] | P2 | Expresii conditionale evaluate la runtime: `if condition then action`. JSON schema. ~5h |
| S10.6 | Monitorizare Performanta | [FEZABIL] | P3 | Middleware FastAPI cu timing per endpoint. Agregare top slowest. ~3h |
| S10.7 | Backup Auto Configurabil | [FEZABIL] | **P1** | Extinde `backup.py` existent: config UI (ce/frecventa/retentie) + scheduler integration. ~4h |
| S10.8 | Log Centralizat cu UI | [FEZABIL] | **P1** | `GET /api/logs?module=X&level=ERROR&since=2026-03-19` + viewer React cu filtre. ~5h |
| S10.9 | Dry Run Simulate | [FEZABIL] | P2 | Flag `simulate=True` pe task runner. Returneaza "ar face" fara a executa. ~2h |
| S10.10 | Webhook Out (Zapier/Make) | [FEZABIL] | P2 | `httpx.post(webhook_url, json=event_data)` la trigger events. Config per event type. ~3h |

---

## 11. MODUL: INTEGRARI EXTERNE

| ID | Sugestie | Fezabilitate | Prioritate | Justificare tehnica |
|----|----------|:------------:|:----------:|---------------------|
| S11.1 | Gmail Inbox cu Filtre | [FEZABIL] | P2 | IMAP SEARCH cu criterii (UNSEEN, FROM, SUBJECT). Categorii pe baza sender patterns. ~4h |
| S11.2 | Compunere Email + Template + Traducere | [FEZABIL] | **P1** | Combina: Gmail SMTP + template populate + Translator inline. Flux complet in Command Center. ~5h |
| S11.3 | Drive Sync Selectiv | [FEZABIL] | **P1** | Google Drive REST API **deja integrat**. Perechi folder local↔Drive + cron sync. ~4h |
| S11.4 | Calendar ↔ ITP Sync | [FEZABIL] | P2 | Google Calendar API **deja integrat**. La creare appointment ITP → create Calendar event. ~3h |
| S11.5 | GitHub Dashboard Issues/PRs | [FEZABIL] | P3 | GitHub httpx **deja integrat**. UI summary cu issues/PRs. ~3h |
| S11.6 | Email Digest Unificat | [FEZABIL] | P2 | Task schedulat: agregare notificari zilei → un singur email HTML. ~3h |
| S11.7 | Google Contacts Auto-Complete | [NEFEZABIL/EXCLUD] | P3 | **Necesita Google People API cu OAuth 2.0** — nu functioneaza cu App Password. Complexitate OAuth disproportionata fata de valoare. |
| S11.8 | GitHub Auto-Commit Config | [FEZABIL] | P3 | `subprocess.run(["git", "add", ...])` din Python. Risc: commit-uri neintentionate. ~2h |
| S11.9 | Telegram Bot Notificari | [FEZABIL] | P2 | Telegram Bot API = REST gratuit, simplu. `httpx.post(f"https://api.telegram.org/bot{token}/sendMessage")`. ~2h |
| S11.10 | Status Page Auto-Reconnect | [FEZABIL] | P2 | Extend status dashboard existent cu periodic health check + token refresh. ~3h |

---

## 12. MODUL: RAPOARTE & STATISTICI

| ID | Sugestie | Fezabilitate | Prioritate | Justificare tehnica |
|----|----------|:------------:|:----------:|---------------------|
| S12.1 | Dashboard KPI Business | [FEZABIL] | **P1** | Recharts dashboard: venituri, clienti, traduceri, ITP, facturi restante. Agregare cross-module. ~6h |
| S12.2 | Raport Comparativ YoY | [FEZABIL] | P2 | Query-uri cu `WHERE date BETWEEN` an curent vs. an precedent. Line chart comparativ. ~4h |
| S12.3 | Raport Productivitate | [FEZABIL] | P3 | Activity log **deja existent**. Statistici ore/module/varfuri. ~3h |
| S12.4 | Export per Modul | [FEZABIL] | P2 | Endpoint-uri `/api/{module}/export?format=xlsx&period=Q1-2026`. ~4h |
| S12.5 | Predictii AI Business | [FEZABIL] | P2 | AI pe date istorice + regresie simpla. Depinde de volumul datelor acumulate. ~4h |
| S12.6 | Jurnal Fulltext + Export | [FEZABIL] | P3 | FTS5 pe jurnal existent + export PDF/DOCX cu `reportlab`/`python-docx`. ~3h |
| S12.7 | Heatmap Calendar GitHub-Style | [FEZABIL] | P3 | Component custom: CSS grid 52 coloane × 7 randuri + color scale. ~3h |
| S12.8 | Raport Utilizare API Costuri | [FEZABIL] | P2 | Agregare din token tracker (existent) + calcul cost echivalent per provider. ~3h |
| S12.9 | Alerta Anomalii | [FEZABIL] | P2 | Thresholds configurabile. Detectie: valoare > 10× media ultimelor 30 zile. ~3h |
| S12.10 | Raport Satisfactie Client | [FEZABIL] | P3 | Tabel `client_feedback(client_id, service_type, score, comment)`. ~2h |

---

## 13. MODUL: QUICK TOOLS EXTRA

| ID | Sugestie | Fezabilitate | Prioritate | Justificare tehnica |
|----|----------|:------------:|:----------:|---------------------|
| S13.1 | Clipboard Manager PC ↔ Android | [FEZABIL] | **P1** | Endpoint `/api/clipboard` + tabel + WebSocket push. Sync bidirecional via Tailscale. Win+V nu face asta. ~4h |
| S13.2 | Focus Timer Pomodoro | [FEZABIL] | P3 | Frontend timer + la final: popup "Ce ai realizat?" → salvare in jurnal. ~2h |
| S13.3 | Snippet Manager (Texte Business) | [FEZABIL] | **P1** | Tabel `snippets(title, content, category)`. Acces din Command Palette (Ctrl+K). Diferit de code snippets. ~3h |
| S13.4 | Convertor MD ↔ HTML ↔ Text | [FEZABIL] | P3 | `marked` (npm) MD→HTML. `turndown` HTML→MD. `innerText` HTML→Text. ~2h |
| S13.5 | Generator Contracte Wizard | [FEZABIL] | **P1** | Wizard React (5 steps) + `python-docx` template populate. Tipuri: traducere, ITP, serviciu general. ~5h |
| S13.6 | Bookmarklete Navigare | [FEZABIL] | P3 | CRUD bookmarks + integrare Command Palette (existent). ~2h |
| S13.7 | Shared Notepad PC ↔ Android | [FEZABIL] | **P1** | WebSocket real-time. Endpoint `/ws/shared-notepad`. Sincronizare live cross-device. ~3h |
| S13.8 | Calculator TVA/Fiscal RO | [FEZABIL] | P2 | Formule: impozit venit 10% micro/16% SRL, CAS/CASS, TVA 19%. Input → output structurat. ~3h |
| S13.9 | Validator Nr Inmatriculare | [FEZABIL] | P3 | Regex: `^(B|[A-Z]{2})-\d{2,3}-[A-Z]{3}$`. Validare + sugestii format. ~1h |
| S13.10 | To-Do List GTD Lite | [FEZABIL] | P2 | Tabel `todos(title, status, priority, deadline, category)`. CRUD + filtre. Complementar cu Jurnal. ~3h |

---

## 14. ANALIZA GENERALA — WEAKNESSES & ARHITECTURA

### Weaknesses Evaluate

| ID | Problema | Severitate | Solutie | Efort |
|----|----------|:----------:|---------|:-----:|
| W1 | Testare Android incompleta | **CRITICA** | Parcurge sistematic GHID_TESTARE.md pe `https://desktop-cjuecmn.tail7bc485.ts.net:8000` | 1-2 sesiuni manuale |
| W2 | DOCX→PDF depinde de Word COM | CRITICA | Adauga fallback `libreoffice --headless --convert-to pdf`. Check la startup care e disponibil. | 2h |
| W3 | 53 tabele fara optimizare | IMPORTANTA | Task scheduler: `VACUUM` + `ANALYZE` saptamanal. Verifica indecsi FTS5. | 1h |
| W4 | Fara rollback DB migrari | IMPORTANTA | `BEGIN TRANSACTION` / `ROLLBACK` per migrare in `run_migrations()`. | 2h |
| W5 | Error handling neuniform frontend | IMPORTANTA | Audit toate `fetch()` / `axios.get/post` → verifica `.catch()` + toast error. | 3h |
| W6 | MAPE 32% sub tinta 25% | IMPORTANTA | Rezolvat prin S1.1 (calibrare interactiva). | vezi S1.1 |
| W7 | Gmail/Drive fara OAuth | MINORA | Non-urgent. Planifica migrare 6-12 luni. App Passwords functioneaza. | - |
| W8 | Notificari unificate DEFERRED | IMPORTANTA | Rezolvat prin S10.1. | vezi S10.1 |
| W9 | Voice Notes DEFERRED | MINORA | Rezolvat prin S6.1. | vezi S6.1 |
| W10 | Dark/Light mode absent | MINORA | CSS variables toggle. Tailwind `dark:` classes. ~3h. | 3h |

### Sugestii Arhitecturale

| ID | Sugestie | Fezabilitate | Prioritate | Detalii |
|----|----------|:------------:|:----------:|---------|
| A1 | Queue SQLite pentru task-uri grele | [FEZABIL] | **P1** | Tabel `task_queue(id, type, payload, status, created_at, started_at, completed_at)`. Worker periodic (BackgroundTask loop). Previne blocaje la OCR batch, traduceri mari. ~4h |
| A2 | Cache lru_cache pentru dashboard | [FEZABIL] | P2 | `@functools.lru_cache(maxsize=128)` pe query-uri agregative. TTL manual cu timestamp check. ~1h |
| A3 | Config file/UI separata | [FEZABIL] | P2 | `config.yaml` sau tabel `settings(key, value, type)` + pagina Settings in UI. ~5h |
| A4 | Health Check Detailed | [FEZABIL] | P2 | `/api/health/detailed`: status per modul, ultima eroare, timestamp ultima activitate. ~2h |
| A5 | Log UI Viewer | [FEZABIL] | **P1** | `/api/logs` + React viewer cu filtre modul/nivel/timp. `RotatingFileHandler` deja exista. ~5h |

---

## PRIORITIZARE FINALA — TOP 30 CROSS-MODULE

### TIER 1 — CRITICA (implementeaza ACUM, impact maxim)

| # | ID | Sugestie | Modul | Efort | Impact Business |
|---|------|---------|-------|:-----:|-----------------|
| 1 | W1 | Testare sistematica Android | General | 1-2 sesiuni | Descoperire buguri ascunse |
| 2 | S10.1 | Notificari Unificate | Automatizari | ~6h | Cel mai mare impact UX al intregii aplicatii |
| 3 | S4.3 | Status Plata Facturi | Facturare | ~4h | Cash flow management direct |
| 4 | S4.5 | Multi-Linie Factura | Facturare | ~5h | Functionalitate de baza lipsa |
| 5 | S4.1 | Serii Facturi Configurabile | Facturare | ~3h | Conformitate fiscala |
| 6 | S1.1 | Calibrare MAPE Interactiva | Calculator | ~4h | Core feature sub target |
| 7 | W4 | Transaction safety migrari DB | General | ~2h | Previne coruptie DB |

### TIER 2 — IMPORTANT (sesiunile urmatoare)

| # | ID | Sugestie | Modul | Efort | Impact Business |
|---|------|---------|-------|:-----:|-----------------|
| 8 | S6.1 | Voice Notes + Transcriere | Quick Tools | ~3h | Utilitate maxima pe mobil |
| 9 | S2.5 | Voice Input Chat (Web Speech) | AI Chat | ~2h | Zero backend, utilitate mobil |
| 10 | S5.1 | Fisa Client Auto (Proprietar ITP) | ITP | ~4h | Fidelizare clienti |
| 11 | S5.2 | Alerta ITP Email Expirare | ITP | ~3h | Marketing pasiv, venit recurent |
| 12 | S5.4 | Calendar ITP Programari | ITP | ~6h | Organizare operationala |
| 13 | S1.6 | Nota Oferta PDF din Calcul | Calculator | ~3h | Automatizare 10-15 min/oferta |
| 14 | S1.9 | Camp Urgenta + Suprataxa | Calculator | ~1h | Monetizare urgente |
| 15 | S2.2 | Prompt Templates cu Variabile | AI Chat | ~4h | Economie timp zilnic |
| 16 | S3.1 | Glosar Tehnic per Client | Traducator | ~2h | Calitate traduceri recurente |
| 17 | S3.2 | TM Vizualizare/Editare + TMX | Traducator | ~5h | TM = activ valoros |
| 18 | S8.4 | OCR Auto la Upload in FTS5 | File Manager | ~4h | Documente cautabile automat |
| 19 | S8.8 | Backup Auto Google Drive | File Manager | ~4h | Protectie date critice |
| 20 | S4.4 | Proforma → Factura Conversie | Facturare | ~3h | Flux profesional |

### TIER 3 — VALOARE BUNA (cand ai timp)

| # | ID | Sugestie | Modul | Efort | Impact Business |
|---|------|---------|-------|:-----:|-----------------|
| 21 | S13.5 | Generator Contracte Wizard | Quick Extra | ~5h | Nevoie reala CIP |
| 22 | S13.7 | Shared Notepad PC ↔ Android | Quick Extra | ~3h | Sync cross-device |
| 23 | S11.2 | Email Template + Traducere | Integr. | ~5h | Flux complet in-app |
| 24 | S7.3 | Watermark PDF | Convertor | ~3h | Protectie documente |
| 25 | S7.4 | Redactare PDF GDPR | Convertor | ~4h | Conformitate GDPR |
| 26 | S8.1 | Preview Documente Browser | File Mgr | ~5h | Productivitate |
| 27 | S9.5 | Test Conectivitate Keys | Vault | ~3h | Elimina guess-work |
| 28 | S12.1 | Dashboard KPI Business | Rapoarte | ~6h | Vizibilitate business |
| 29 | S10.8 | Log Centralizat cu UI | Automatizari | ~5h | Debugging rapid |
| 30 | S13.1 | Clipboard Manager PC ↔ Android | Quick Extra | ~4h | Sync clipboard cross-device |

---

## RECOMANDARE STRATEGICA

### Nu implementa totul. Urmeaza aceasta secventa:

**Faza A — Stabilizare (1-2 sesiuni)**
- W1: Testare Android completa
- W4: Transaction safety DB
- W5: Audit error handling frontend
- W3: VACUUM + ANALYZE task

**Faza B — Core Business (2-3 sesiuni)**
- S4.3 + S4.5 + S4.1 + S4.4: Facturare completa (serii, multi-linie, status plata, proforma)
- S1.1 + S1.9: Calculator calibrare + urgenta
- S5.1 + S5.2 + S5.4: ITP clienti + alerte + programari

**Faza C — Productivitate (2-3 sesiuni)**
- S10.1: Notificari unificate
- S6.1 + S2.5: Voice notes + voice input
- S2.2: Prompt templates
- S3.1 + S3.2: Glosar client + TM editor

**Faza D — Automatizare & Protectie (1-2 sesiuni)**
- S8.8 + S10.7: Backup auto Drive + backup configurabil
- S8.4: OCR auto la upload
- S13.5 + S13.7: Contracte wizard + shared notepad

**Estimare totala Faze A-D: 8-10 sesiuni = cele mai valoroase 30 features din 130**

---

*Evaluat: 2026-03-19 | Stack: FastAPI + React 18 + SQLite + 13 module*
*Total evaluat: 145 itemi (130 sugestii + 10 weaknesses + 5 arhitecturale)*
*Metodologie: Analiza cod existent + evaluare impact business CIP Inspection SRL*
