# Roland Command Center — Roadmap Implementare (Unificat)

> **Generated:** 2026-03-20
> **Conditie ABSOLUTA:** 100% GRATUIT — nicio functie nu necesita abonament, plata sau card bancar
> **Surse:** `SUGESTII_SI_ANALIZA_COMMAND_CENTER_V2.md` + `12_ZONE_IMBUNATATIRE_GRATUITE_V2.md` + 10 functii noi originale
> **Deduplicare:** Unde aceeasi functie apare in ambele surse, s-a pastrat versiunea cea mai completa ca un singur item
> **Provideri platiti eliminati:** e-Factura certSIGN, e-Signature digital, Perplexity, OpenAI (din chain-uri noi), Whisper OpenAI, SMS Romania, PaddleOCR, Coqui TTS, Piper TTS

---

## PROVIDER CHAINS (referinta globala)

| Categorie | Chain (ordinea de fallback) |
|-----------|---------------------------|
| **AI Text** | Gemini Flash --> Cerebras --> Groq --> Mistral --> SambaNova |
| **Traduceri** | DeepL Free --> Azure Translator F0 --> Google Cloud --> MyMemory --> LibreTranslate local |
| **TTS** | edge-tts --> Web Speech API browser --> Azure TTS F0 (daca contul exista) |
| **OCR** | Tesseract local + EasyOCR --> OCR.space cloud --> Azure Vision (daca contul exista) |
| **Notificari** | Web Push VAPID --> Telegram Bot --> ntfy.sh --> Email digest |
| **Embeddings** | Gemini Embeddings --> all-MiniLM-L6-v2 local |
| **Email** | Gmail SMTP (500/zi) --> Brevo (300/zi) --> Resend (100/zi) |
| **Audio STT** | Groq Whisper --> Gemini Flash Audio --> whisper.cpp local |

---

## TOP 15 QUICK WINS (sub 1-2h fiecare, valoare/efort maxim)

| # | ID | Functie | Ce obtii concret | Efort | Modul |
|---|-----|---------|-----------------|-------|-------|
| 1 | Z2.9 | GZip Middleware FastAPI | -60-80% dimensiune raspunsuri JSON, 1 linie cod | 5 min | Performanta |
| 2 | S1.9 | Camp Urgenta cu Suprataxa | Checkbox + multiplicator pret configurabil | 30 min | Calculator |
| 3 | Z1.6 | CORS policy audit productie | Verificare `allow_origins` nu contine `*` | 15 min | Securitate |
| 4 | Z2.1 | Index SQLite pe `activity_log` | Dashboard si history semnificativ mai rapide | 20 min | Performanta |
| 5 | Z3.8 | Fix zoom neintentionat input-uri | Elimina zoom enervant pe Android la focus | 15 min | Mobil |
| 6 | S6.10 | Convertor Numere baze | Input/output intre baze de numeratie, zero backend | 30 min | Quick Tools |
| 7 | S9.9 | Validare Format Key la salvare | Regex per tip serviciu la salvare in Vault | 30 min | Vault |
| 8 | S13.4 | Convertor Markdown/HTML/Text | 3 textarea-uri + `marked.js`, conversie live | 45 min | Quick Tools Extra |
| 9 | S1.7 | Alerta Preturi Neactualizate | Banner conditionat pe Dashboard daca tarife vechi | 45 min | Calculator |
| 10 | Z9.4 | Toast notifications standardizate | Consistenta vizuala pe toate modulele | 45 min | UI/UX |
| 11 | Z4.6 | Prompt caching local | -20-40% consum tokeni pentru query-uri similare | 45 min | AI Strategy |
| 12 | Z2.6 | Debounce 300ms pe search inputs | Reduce 80% din query-urile inutile la cautare | 30 min | Performanta |
| 13 | Z1.11 | CSP Headers | Previne XSS in PWA cu continut uploadat | 30 min | Securitate |
| 14 | Z2.2 | VACUUM + ANALYZE periodic | DB mai mic, query-uri mai rapide | 30 min | Performanta |
| 15 | NEW3 | BNR Curs Valutar live | Curs EUR/RON din feed BNR XML, zero auth | 1h | Dashboard |

**Total estimat:** ~7-8 ore pentru toate 15, cu impact imediat vizibil.

---

## CUPRINS MODULE

1. [Calculator Pret Traduceri](#1-calculator-pret-traduceri)
2. [AI Chat & Documente](#2-ai-chat--documente)
3. [Traducator](#3-traducator)
4. [Facturare (Invoice)](#4-facturare-invoice)
5. [ITP Inspectii Auto](#5-itp-inspectii-auto)
6. [Quick Tools](#6-quick-tools)
7. [Convertor Fisiere](#7-convertor-fisiere)
8. [File Manager](#8-file-manager)
9. [Vault (API Keys)](#9-vault-api-keys)
10. [Automatizari](#10-automatizari)
11. [Integrari Externe](#11-integrari-externe)
12. [Rapoarte & Statistici](#12-rapoarte--statistici)
13. [Quick Tools Extra](#13-quick-tools-extra)
14. [CRM (Modul NOU)](#14-crm-modul-nou)
15. [Infrastructura Cross-Module](#15-infrastructura-cross-module)
16. [Analiza Generala Proiect](#16-analiza-generala-proiect)

---

## 1. Calculator Pret Traduceri

> **Status actual:** Ensemble 3 metode (base_rate, word_rate, KNN), MAPE 32%, dashboard competitori, AI explicatie pret, 26 PDF-uri referinta.

#### S1.1 — Calibrare MAPE Interactiva in UI **[FEZABIL]**
- **Ce face:** Panou vizual cu slidere Tailwind pentru ajustarea manuala a ponderilor celor 3 metode. MAPE se recalculeaza instant pe setul de date istoric. Grafic Recharts live.
- **Exemplu concret:** Muti sliderul KNN de la 33% la 50%, graficul arata imediat ca MAPE scade de la 32% la 27%. Dai save si noile ponderi sunt active.
- **Provider gratuit:** Recharts (deja instalat) + endpoint backend cu date din `calibration_results`
- **Efort:** 2-3h
- **Dep:** Niciuna

#### S1.2 — Istoric Calcule cu Cautare si Filtre **[FEZABIL]**
- **Ce face:** Tabel paginat cu toate calculele anterioare, filtrabil dupa client, limba, tip, pret, data. Export CSV.
- **Exemplu concret:** Cauti toate calculele pentru clientul "Dacia" din ultimele 6 luni — vezi ca pretul mediu a fost 450 RON.
- **Provider gratuit:** SQLite (tabel `calculations` existent) + openpyxl (instalat)
- **Efort:** 2-3h
- **Dep:** Niciuna

#### S1.3 — Template-uri de Calcul per Client **[FEZABIL]**
- **Ce face:** Salvezi profilul unui client (limba, tip doc, reducere, termen plata). Dropdown pre-completeaza campurile.
- **Exemplu concret:** Clientul "Bosch Romania" cere mereu EN->RO tehnic, 15% discount. Selectezi din dropdown si calculul porneste cu aceste setari.
- **Provider gratuit:** SQLite tabel nou `client_templates`
- **Efort:** 2h
- **Dep:** Niciuna

#### S1.4 — Calcul Batch Mai Multe Fisiere Simultan **[FEZABIL]**
- **Ce face:** Uploadezi 5-10 fisiere, calculatorul ruleaza pe fiecare si returneaza tabel sumar + total.
- **Exemplu concret:** Client trimite pachet de 8 documente tehnice. Le incarci pe toate, primesti tabel cu pret per fisier si total lot: 3.240 RON.
- **Provider gratuit:** react-dropzone (deja instalat) + motorul de calcul existent
- **Efort:** 2-3h
- **Dep:** Niciuna

#### S1.5 — Comparare Doua Calcule Side-by-Side **[FEZABIL]**
- **Ce face:** Selectezi 2 calcule din istoric si le afisezi in paralel: features, pret, metoda dominanta, diferenta procentuala.
- **Exemplu concret:** Compari calculul pentru un manual tehnic de 50 pag din 2025 vs. unul similar din 2024.
- **Provider gratuit:** Frontend pur (React)
- **Efort:** 1-2h
- **Dep:** S1.2 (Istoric Calcule)

#### S1.6 — Nota de Oferta PDF Automata din Calcul **[FEZABIL]**
- **Ce face:** Buton "Genereaza Oferta" dupa calcul — PDF profesional cu antet CIP Inspection, detalii, pret, valabilitate 30 zile.
- **Exemplu concret:** Calculezi pretul, dai "Genereaza Oferta", primesti PDF gata de trimis pe email clientului.
- **Provider gratuit:** reportlab (deja instalat pentru facturi)
- **Efort:** 2-3h
- **Dep:** Niciuna

#### S1.7 — Alerta Preturi Neactualizate **[FEZABIL]** *QUICK WIN*
- **Ce face:** Banner conditionat pe Dashboard daca fisierele de referinta tarifara nu au fost actualizate de > X luni.
- **Exemplu concret:** La 6 luni, apare banner galben: "Tarifele de referinta pot fi depasite — ultima actualizare: 2025-09-15".
- **Provider gratuit:** Query pe `file_stats` (existent)
- **Efort:** 45 min
- **Dep:** Niciuna

#### S1.8 — Grafic Evolutie Preturi Proprii vs. Piata **[FEZABIL]**
- **Ce face:** Line chart Recharts cu evolutia pretului tau mediu per pagina in timp, suprapus cu min/max piata din Competitori.
- **Exemplu concret:** Graficul arata ca in Q4 2025 pretul tau era cu 12% sub media pietei — indiciu ca poti creste tarifele.
- **Provider gratuit:** Recharts (deja instalat) + date din `calculations` + `Competitori.md`
- **Efort:** 2-3h
- **Dep:** Niciuna

#### S1.9 — Camp "Urgenta" cu Suprataxa Automata **[FEZABIL]** *QUICK WIN*
- **Ce face:** Checkbox "Traducere urgenta (24h)" care aplica automat suprataxa configurabila (+30% default).
- **Exemplu concret:** Client suna ca are nevoie pana maine. Bifezi "Urgenta 24h", pretul devine 650 RON in loc de 500 RON.
- **Provider gratuit:** 1 coloana noua DB (`is_urgent BOOLEAN`)
- **Efort:** 30 min
- **Dep:** Niciuna

#### S1.10 — Export Raport Lunar Calculator **[FEZABIL]**
- **Ce face:** Raport automat lunar: numar calcule, valoare totala, clienti noi vs. recurenti, MAPE curent. Trimis pe email.
- **Exemplu concret:** La 1 martie: "Februarie 2026: 43 calcule, valoare totala estimata 18.500 RON, 5 clienti noi, MAPE: 29%."
- **Provider gratuit:** APScheduler (instalat) + Gmail SMTP (functional)
- **Efort:** 2h
- **Dep:** Niciuna

**Ordine recomandata:** S1.9 -> S1.7 -> S1.1 -> S1.2 -> S1.6 -> S1.3 -> S1.4 -> S1.8 -> S1.10 -> S1.5

---

## 2. AI Chat & Documente

> **Status actual:** Chat SSE streaming (Gemini->OpenAI->Groq), 6 endpoint-uri documente, OCR+AI, 10 API keys, evaluare calitate, provider selector, token indicator, context-aware.

#### S2.1 — Sesiuni Chat cu Titlu Auto si Organizare Categorii **[FEZABIL]**
- **Ce face:** Extinde sesiunile existente cu: titlu auto-generat, categorii (Traduceri/Facturare/ITP/General), pin, arhivare.
- **Exemplu concret:** Sesiunile apar grupate: "Traduceri (12 sesiuni)", pinezi "Analiza Contract Bosch 2026" pentru acces rapid.
- **Provider gratuit:** SQLite (3 coloane noi pe `chat_sessions`)
- **Efort:** 2-3h
- **Dep:** Niciuna

#### S2.2 — Prompt Templates cu Variabile Editabile **[FEZABIL]**
- **Ce face:** Librarie de prompturi predefinite cu variabile `{{document}}`, `{{client}}`, `{{suma}}`. Selectezi template, completezi, trimiti.
- **Exemplu concret:** Template "Genereaza email oferta": "Buna ziua {{client}}, va transmitem oferta pentru {{document}} in valoare de {{suma}} RON."
- **Provider gratuit:** SQLite tabel `prompt_templates`
- **Efort:** 2h
- **Dep:** Niciuna

#### S2.3 — Mod "Lucreaza pe Document" — AI cu Fisier Atasat Persistent **[FEZABIL CU EFORT MARE]**
- **Ce face:** Incarci un PDF/DOCX care ramane "activ" pe toata sesiunea. Chunk-uire + indexare TF-IDF, trimite doar chunk-urile relevante la fiecare intrebare.
- **Exemplu concret:** Incarci contract de 30 pag. Intrebi: "Care sunt clauzele de penalitate?" -> "Exista termen de exclusivitate?" fara re-upload.
- **Provider gratuit:** scikit-learn TF-IDF (deja instalat) + Gemini Flash
- **Efort:** 6-8h
- **Dep:** Niciuna

#### S2.4 — Comparare Raspunsuri Multi-Provider (Side-by-Side) **[FEZABIL]**
- **Ce face:** Trimiti acelasi prompt la 2-3 provideri simultan, raspunsurile apar in coloane cu timp si token count per provider.
- **Exemplu concret:** Trimiti aceeasi traducere la Gemini, Groq si Cerebras. Compari calitatea celor 3 variante.
- **Provider gratuit:** asyncio.gather + Gemini + Groq + Cerebras (free tier)
- **Efort:** 3-4h
- **Dep:** Niciuna

#### S2.5 — Voice Input (Speech-to-Text) via Web Speech API **[FEZABIL CU LIMITARE]**
- **Ce face:** Buton microfon in chat — vorbesti, textul apare automat. NECESITA internet pentru limba romana.
- **Exemplu concret:** Apesi microfon: "Genereaza o oferta pentru traducerea unui manual tehnic auto de 80 pagini." Textul apare scris.
- **Provider gratuit:** Web Speech API (gratuit in Chrome/Edge, necesita internet pt romana)
- **Efort:** 1-2h
- **Dep:** Niciuna
- **Nota:** Identic cu Z3.1 (Voice Input) si S6.1 — implementare unica, buton prezent in chat + cautare

#### S2.6 — AI Agent cu Acces la Module (Tool Use) **[FEZABIL CU EFORT MARE]**
- **Ce face:** AI executa actiuni in aplicatie: calculeaza pret, cauta in documente, creeaza factura — pe baza unui prompt natural.
- **Exemplu concret:** "Calculeaza pretul pentru contract_dacia.pdf si creeaza o factura cu pretul rezultat." AI executa, tu confirmi.
- **Provider gratuit:** Gemini Flash function calling (suport partial pe free tier)
- **Efort:** 30-50h (8-12 sesiuni)
- **Dep:** S2.2 (Prompt Templates — util dar nu obligatoriu)

#### S2.7 — Cautare Web cu Citatii (inlocuieste Perplexity) **[FEZABIL]**
- **Ce face:** Comanda `/search` in chat care trimite query-ul la Gemini/Cerebras cu instructiunea de a cauta si cita surse.
- **Exemplu concret:** `/search tarife traduceri tehnice auto Romania 2026` — AI returneaza informatii actuale cu surse.
- **Provider gratuit:** Gemini Flash (prompt-based search) sau Cerebras (1M tok/zi)
- **Efort:** 2h
- **Dep:** Niciuna
- **Nota:** Perplexity eliminat (no free tier). Inlocuit cu search prompt pe Gemini/Cerebras.

#### S2.8 — AI Batch Processing pe Folder **[FEZABIL CU EFORT MARE]**
- **Ce face:** Selectezi folder + prompt template — AI proceseaza toate documentele si salveaza rezultatele per fisier.
- **Exemplu concret:** Selectezi "Contracte 2025" cu 40 PDF-uri + prompt "Extrage: client, valoare, data". Primesti tabel Excel.
- **Provider gratuit:** Gemini Flash + queue SQLite + openpyxl
- **Efort:** 6-8h
- **Dep:** S2.2 (Prompt Templates)

#### S2.9 — Feedback pe Raspunsuri AI (Thumbs + Nota) **[FEZABIL]**
- **Ce face:** Butoane thumbs up/down pe fiecare raspuns AI + nota optionala. Statistici per provider.
- **Exemplu concret:** Gemini da raspuns slab. Dai thumbs down + "terminologie auto incorecta". Peste timp, statisticile arata ca Gemini e slab pe texte tehnice.
- **Provider gratuit:** SQLite tabel `ai_feedback`
- **Efort:** 1-2h
- **Dep:** Niciuna

#### S2.10 — Export Conversatie ca Document **[FEZABIL]**
- **Ce face:** Buton "Exporta conversatie" — genereaza PDF/DOCX/MD formatat cu toata sesiunea.
- **Exemplu concret:** Sesiune de 2 ore analiza contract. Exportezi ca PDF si arhivezi impreuna cu contractul.
- **Provider gratuit:** reportlab (PDF) + python-docx (DOCX) — ambele instalate
- **Efort:** 2h
- **Dep:** Niciuna

#### NEW7 — Semantic Search cu Gemini Embeddings **[FEZABIL]**
- **Ce face:** Indexeaza documentele din File Manager cu vectori Gemini Embeddings. Cautare semantica ("gaseste contracte cu clauze de penalitate") in loc de cautare text exact.
- **Exemplu concret:** Cauti "documente despre garantie echipamente" si gasesti contracte care contin "warranty terms" in engleza + "conditii de garantare" in romana.
- **Provider gratuit:** Gemini Embeddings API (free tier, 1500 req/zi) sau all-MiniLM-L6-v2 local (pip install sentence-transformers)
- **Efort:** 4-6h
- **Dep:** Niciuna

**Ordine recomandata:** S2.2 -> S2.1 -> S2.5 -> S2.9 -> S2.10 -> S2.4 -> S2.7 -> NEW7 -> S2.3 -> S2.8 -> S2.6

---

## 3. Traducator

> **Status actual:** 5 provideri (DeepL->Azure->Google->Gemini->OpenAI), TM FTS5, glosar tehnic CRUD, traducere fisiere PDF/DOCX, detectie limba, tracking chars DeepL, istoric.

#### S3.1 — Glosar Tehnic per Client **[FEZABIL]**
- **Ce face:** Glosare separate per client. La traducere, se aplica automat glosarul clientului selectat.
- **Exemplu concret:** Clientul "Continental" prefera "unitate de control" in loc de "ECU". Glosarul se activeaza automat la selectie.
- **Provider gratuit:** SQLite (coloana `client_id` pe tabel `glossary`)
- **Efort:** 2h
- **Dep:** Niciuna

#### S3.2 — Memorie de Traducere cu Vizualizare si Editare **[FEZABIL]**
- **Ce face:** Interfata vizuala pentru TM: vezi, editezi, stergi segmente, import/export TMX.
- **Exemplu concret:** TM are traducere gresita "airbag lateral" -> "perna laterala". O editezi la "airbag de parte". Toate traducerile viitoare folosesc varianta corecta.
- **Provider gratuit:** SQLite (tabel `translation_memory` existent) + xml.etree (TMX)
- **Efort:** 3-4h
- **Dep:** Niciuna

#### S3.3 — Traducere cu Pastrare Formatare Avansata DOCX **[FEZABIL CU EFORT MARE]**
- **Ce face:** La traducerea DOCX, pastreaza stiluri Word (heading-uri, bold, italic, tabele, note subsol).
- **Exemplu concret:** Manual tehnic cu Heading 1/2, tabele, note — documentul tradus are aceeasi structura vizuala.
- **Provider gratuit:** python-docx (deja instalat)
- **Efort:** 6-8h (3-4 sesiuni)
- **Dep:** Niciuna

#### S3.4 — Mod Revizuire Traducere (Track Changes) **[FEZABIL CU EFORT MARE]**
- **Ce face:** 3 coloane: original | traducere AI | revizuirea ta. Trackezi exact ce ai schimbat, adaugare automata in TM/Glosar.
- **Exemplu concret:** AI traduce "engine control unit" -> "unitate motor control". Tu corectezi la "unitate de comanda motor". Modificarea se adauga automat in TM.
- **Provider gratuit:** diff-match-patch JS (open-source)
- **Efort:** 6-8h (3-4 sesiuni)
- **Dep:** S3.2 (TM vizualizare)

#### S3.5 — Statistici Utilizare DeepL cu Prognoza **[FEZABIL]**
- **Ce face:** Dashboard consum DeepL: caractere consumate/ramase, prognoza data epuizare cota, grafic zilnic.
- **Exemplu concret:** Ai 500K chars/luna, azi e 19 martie cu 380K consumate. Sistemul: "Cota se epuizeaza pe 23 martie — treci pe Azure."
- **Provider gratuit:** scipy linregress (instalat) + Recharts
- **Efort:** 2-3h
- **Dep:** Niciuna

#### S3.6 — Proiecte de Traducere cu Status **[FEZABIL]**
- **Ce face:** Grupezi fisiere intr-un proiect, urmaresti progresul per fisier (asteptare/lucru/finalizat/livrat), deadline.
- **Exemplu concret:** Proiect "Bosch Cataloage Q1": 8 fisiere, deadline 28 martie. 5 finalizate, 2 in lucru, 1 asteptare. 3 zile ramase.
- **Provider gratuit:** SQLite tabele `translation_projects` + `project_files`
- **Efort:** 3-4h
- **Dep:** Niciuna

#### S3.7 — Detectie si Avertizare Termeni Netraduci **[FEZABIL]**
- **Ce face:** Dupa traducere, verifica daca termenii din glosar apar in original dar NU in traducere. Lista de verificare.
- **Exemplu concret:** Glosarul: "ABS" -> "sistem antibloc". AI detecteaza ca "ABS" apare de 4 ori in original dar 0 in traducere.
- **Provider gratuit:** String matching pe tabelul `glossary`
- **Efort:** 1-2h
- **Dep:** S3.1 (Glosar per client — optional)

#### S3.8 — Traducere Email Direct din Gmail **[FEZABIL]**
- **Ce face:** Buton "Traduce" pe vizualizarea email-ului, traducerea apare sub original.
- **Exemplu concret:** Email in germana de la furnizor. Dai "Traduce" -> traducerea RO apare in 3 secunde, fara copy-paste.
- **Provider gratuit:** Modulele Gmail + Translator existente
- **Efort:** 1-2h
- **Dep:** Niciuna

#### S3.9 — Raport Lunar Traduceri **[FEZABIL]**
- **Ce face:** Raport automat: caractere traduse, distributie per provider, documente procesate, limba predominanta.
- **Exemplu concret:** "Februarie 2026: 2.4M caractere (DeepL 68%, Google 22%, Gemini 10%), 34 documente, EN->RO 89%."
- **Provider gratuit:** APScheduler + Gmail SMTP
- **Efort:** 2h
- **Dep:** Niciuna

#### S3.10 — Traducere Live (Tastare in Timp Real) **[FEZABIL]**
- **Ce face:** Mod "live" cu debounce 500ms — pe masura ce tastezi, traducerea apare automat. Limitat la texte sub 500 caractere.
- **Exemplu concret:** Tastezi in romana si traducerea in engleza apare imediat alaturi.
- **Provider gratuit:** DeepL Free / Gemini Flash
- **Efort:** 1-2h
- **Dep:** Niciuna

**Ordine recomandata:** S3.1 -> S3.7 -> S3.5 -> S3.8 -> S3.2 -> S3.10 -> S3.6 -> S3.9 -> S3.3 -> S3.4

---

## 4. Facturare (Invoice)

> **Status actual:** Generator facturi PDF (reportlab), CRUD clienti, istoric comenzi, raport lunar grafice, export Excel/CSV, template documente, email smtplib, scanner facturi OCR.

#### S4.1 — Serii de Facturi Configurabile si Numerotare Automata **[FEZABIL]**
- **Ce face:** Serie configurabila (ex: "CIP-2026-") cu numerotare secventiala automata. Detectie gaps.
- **Exemplu concret:** Prima factura: CIP-2026-001. La a 15-a: CIP-2026-015. Avertizare daca seria are gap.
- **Provider gratuit:** SQLite tabel `invoice_series`
- **Efort:** 2h
- **Dep:** Niciuna

#### S4.2 — Facturi Recurente / Abonamente **[FEZABIL]**
- **Ce face:** Client marcat "recurent" cu suma fixa lunara. Generare automata sau alerta la data configurata.
- **Exemplu concret:** Client cu retainer 1.500 RON/luna. La 1 ale fiecarei luni: "Factura recurenta gata — aproba sau modifica."
- **Provider gratuit:** APScheduler + SQLite `recurring_invoices`
- **Efort:** 2-3h
- **Dep:** Niciuna

#### S4.3 — Status Plata cu Urmarire Scadente **[FEZABIL]**
- **Ce face:** Status per factura (emisa/trimisa/partial/platita/restanta). Alerta automata la X zile dupa scadenta. Dashboard total restant.
- **Exemplu concret:** Factura CIP-2026-034 scadenta 15 martie. Azi 20 martie — rosu "Restanta 5 zile — total restant: 2.400 RON". Buton "Trimite reminder email".
- **Provider gratuit:** SQLite + APScheduler
- **Efort:** 2-3h
- **Dep:** Niciuna

#### S4.4 — Proforma / Oferta cu Conversie in Factura **[FEZABIL]**
- **Ce face:** Creezi proforma. La confirmare client, un click o converteste in factura reala cu numar fiscal.
- **Exemplu concret:** Proforma 2026-P-05. Client confirma. "Converteste in factura" -> CIP-2026-038, toate datele copiate.
- **Provider gratuit:** SQLite tabel `proforma_invoices`
- **Efort:** 2-3h
- **Dep:** S4.1 (Serii facturi)

#### S4.5 — Multi-Linie pe Factura **[FEZABIL]**
- **Ce face:** O factura contine mai multe linii/servicii cu descriere, cantitate, pret unitar, TVA per linie.
- **Exemplu concret:** "Traducere manual + Revizuire + Apostilare": 3 linii separate, total 1.850 RON.
- **Provider gratuit:** SQLite tabel `invoice_lines`
- **Efort:** 3h
- **Dep:** Niciuna

#### S4.6 — Trimitere Factura WhatsApp (via Clipboard) **[FEZABIL]**
- **Ce face:** Buton "Trimite WhatsApp" — genereaza URL `wa.me/{{phone}}?text={{message}}` cu link factura.
- **Exemplu concret:** Client prefera WhatsApp. Dai "Trimite WA", se deschide web.whatsapp.com cu mesajul gata.
- **Provider gratuit:** Frontend pur (URL wa.me)
- **Efort:** 30 min
- **Dep:** Niciuna

#### S4.7 — Import Facturi Furnizori in Registru Cheltuieli **[FEZABIL]**
- **Ce face:** OCR existent scaneaza facturi primite. Registru cheltuieli separat de venituri.
- **Exemplu concret:** Factura furnizor hartie: scanezi, OCR extrage datele, intra automat in "Cheltuieli Martie 2026".
- **Provider gratuit:** OCR existent + SQLite tabel `expenses`
- **Efort:** 3-4h
- **Dep:** Niciuna

#### S4.8 — Generare Contract din Template la Factura Noua **[FEZABIL]**
- **Ce face:** La factura noua, optional genereaza contract de prestari servicii din template DOCX cu placeholders.
- **Exemplu concret:** Client nou, 3.000 RON. Bifezi "Genereaza contract" -> DOCX cu datele clientului, suma, clauze standard.
- **Provider gratuit:** python-docx (instalat)
- **Efort:** 2-3h
- **Dep:** Niciuna

#### S4.9 — Dashboard Financiar: Venituri, Cheltuieli, Profit **[FEZABIL]**
- **Ce face:** Grafice Recharts: venituri lunare, cheltuieli, profit estimat, comparatie an curent vs. anterior.
- **Exemplu concret:** Bare albastre venituri, rosii cheltuieli, linie verde profit. Q4 2025 cel mai mare profit dar Q1 2026 sub target.
- **Provider gratuit:** Recharts (instalat) + SQLite agregate
- **Efort:** 3-4h
- **Dep:** S4.7 (Import Cheltuieli — optional, fara el doar venituri)

#### S4.10 — Raport Pregatit pentru Contabil **[FEZABIL]**
- **Ce face:** Export structurat Excel cu coloane standard contabilitate romaneasca pentru o perioada selectata.
- **Exemplu concret:** Contabilul cere situatia Q1 2026. "Export Contabil" -> Excel cu numar, data, client, CUI, suma, TVA, total, status.
- **Provider gratuit:** openpyxl (instalat)
- **Efort:** 2h
- **Dep:** Niciuna

#### S4.11 — Export pentru Servicii Gratuite de Facturare **[FEZABIL]**
- **Ce face:** Export structurat al datelor facturii in format compatibil cu platforme gratuite de facturare online care genereaza e-Factura XML. Buton "Exporta pentru e-Factura" -> CSV/JSON cu toate campurile necesare CIUS-RO.
- **Exemplu concret:** Genereaza factura in Command Center. Exporta datele. Le importi intr-o platforma gratuita de e-Factura care semneaza si uploadeaza pe SPV.
- **Provider gratuit:** Export CSV/JSON (zero cost). Platforme gratuite: SmartBill (free tier 25 facturi/luna), oblio.eu (free tier).
- **Efort:** 2h
- **Dep:** S4.1 (Serii facturi), S4.5 (Multi-linie)
- **Nota:** certSIGN eliminat (platit). Generarea directa XML CIUS-RO + semnare necesita certificat digital (~100 RON/an). Alternativa gratuita: export date -> platforma gratuita care se ocupa de semnare.

#### NEW4 — ANAF Verificare CUI (Auto-populate Client) **[FEZABIL]**
- **Ce face:** La introducerea CUI-ului clientului, campurile de denumire si adresa se completeaza automat din baza ANAF.
- **Exemplu concret:** Tastezi CUI "43978110", sistem returneaza automat "CIP INSPECTION SRL", adresa, status TVA.
- **Provider gratuit:** ANAF REST API `https://webservicesp.anaf.ro/PlatitorTvaRest/api/v8/ws/tva` (gratuit, fara auth, fara card)
- **Efort:** 1-2h
- **Dep:** Niciuna
- **Nota:** Versiunea API se schimba periodic — URL configurabil in Vault, nu hardcodat.

**Ordine recomandata:** S4.1 -> S4.5 -> S4.3 -> NEW4 -> S4.10 -> S4.6 -> S4.4 -> S4.7 -> S4.8 -> S4.2 -> S4.9 -> S4.11

---

## 5. ITP Inspectii Auto

> **Status actual:** CRUD inspectii, import CSV/Excel, statistici lunare/brand/venituri/combustibil (Recharts), alerta expirare 30 zile, export CSV/Excel.

#### S5.1 — Fisa Client Auto (Istoric per Proprietar) **[FEZABIL]**
- **Ce face:** Legatura vehicul-proprietar. Fisa proprietarului cu toate vehiculele si istoricul ITP per vehicul.
- **Exemplu concret:** Dl. Ionescu, a 3-a oara la ITP. Introduci telefonul, apare fisa: Dacia Logan (2x OK), Ford Focus (1x OK, 1x respins).
- **Provider gratuit:** SQLite tabel `vehicle_owners` + FK
- **Efort:** 3h
- **Dep:** Niciuna

#### S5.2 — Alerta Expirare Configurabila + Email/Telegram **[FEZABIL]**
- **Ce face:** Zile configurabile (15/30/60), trimitere email/Telegram de reminder catre client.
- **Exemplu concret:** 30 zile inainte, email automat: "ITP-ul vehiculului dv. Dacia Logan AB-01-POP expira pe 25 Apr."
- **Provider gratuit:** APScheduler + Gmail SMTP / Telegram Bot API
- **Efort:** 2-3h
- **Dep:** Niciuna

#### S5.3 — Motiv Respingere ITP cu Clasificare **[FEZABIL]**
- **Ce face:** La ITP respins, inregistrezi motivele din lista predefinita. Statistici pe motive de respingere.
- **Exemplu concret:** 45% respingeri din cauza franelor. Recomanzi service auto partener.
- **Provider gratuit:** SQLite coloana `rejection_reasons` (JSON)
- **Efort:** 2h
- **Dep:** Niciuna

#### S5.4 — Calendar ITP (Programari) **[FEZABIL]**
- **Ce face:** Calendar vizual cu sloturi disponibile. Gestionarea capacitatii zilnice.
- **Exemplu concret:** Miercuri: 6 din 8 sloturi ocupate. Client suna, vezi direct ca ai loc la 14:00 si 15:00.
- **Provider gratuit:** SQLite tabel `itp_appointments` + React calendar grid
- **Efort:** 3-4h
- **Dep:** S5.1 (Fisa Client — optional)

#### S5.5 — Raport Fiscal ITP **[FEZABIL]**
- **Ce face:** Raport structurat cu incasari ITP pe luna: numar inspectii, pret, total, export Excel.
- **Exemplu concret:** "Martie 2026: 127 inspectii x 100 RON = 12.700 RON venituri ITP."
- **Provider gratuit:** openpyxl (instalat)
- **Efort:** 2h
- **Dep:** Niciuna

#### S5.6 — Import din Sistemul RAR (Export Manual) **[FEZABIL CU EFORT MARE]**
- **Ce face:** Parseaza fisierele exportate manual din aplicatia RAR (CSV/Excel/PDF) daca aceasta permite export.
- **Exemplu concret:** Exporti din RAR un CSV cu inspectiile zilei. Importi in Command Center cu un click.
- **Provider gratuit:** CSV/Excel parsing (Python standard)
- **Efort:** 4-6h (depinde de formatul real RAR)
- **Dep:** Niciuna
- **Nota:** NU exista API public RAR/DRPCIV. Scraping exclus (risc legal). Fezabil DOAR daca RAR permite export.

#### S5.7 — Heatmap Activitate ITP **[FEZABIL]**
- **Ce face:** Calendar heatmap (GitHub-style) cu intensitatea activitatii ITP per zi.
- **Exemplu concret:** Heatmap arata ca luni = 25+ masini, vineri = 8-10. Programezi administrativ vinerea.
- **Provider gratuit:** react-calendar-heatmap (open-source) sau Recharts custom
- **Efort:** 2h
- **Dep:** Niciuna

#### S5.8 — Statistici per Inspector **[FEZABIL]**
- **Ce face:** Atribuire inspector per inspectie. Statistici: inspectii, rata respingere, venituri per inspector.
- **Exemplu concret:** Inspector A: 450/luna, 18% respingere. Inspector B: 380/luna, 24% respingere.
- **Provider gratuit:** SQLite coloana `inspector_name`
- **Efort:** 1-2h
- **Dep:** Niciuna

#### S5.9 — Notificari Scadente Non-ITP (RCA, Revizie, Rovinieta) **[FEZABIL]**
- **Ce face:** Pe langa ITP, urmaresti si RCA, revizie anuala, rovinieta. Alerte similare.
- **Exemplu concret:** RCA Popescu expira 15 mai. La 30 zile inainte: alerta + posibil redirect catre asigurator partener.
- **Provider gratuit:** SQLite coloane pe `vehicles` + APScheduler
- **Efort:** 2h
- **Dep:** S5.1 (Fisa Client)

#### S5.10 — Export Raport Anual ITP **[FEZABIL]**
- **Ce face:** Raport anual comprehensiv: total inspectii, rate, top marci, combustibil, evolutie venituri, comparatie.
- **Exemplu concret:** "2025: 1.847 inspectii, 73% promovate, top Dacia (31%), VW (18%), Ford (12%). Venituri: 184.700 RON (+12% vs 2024)."
- **Provider gratuit:** Recharts + reportlab/openpyxl
- **Efort:** 3h
- **Dep:** Niciuna

**Ordine recomandata:** S5.1 -> S5.3 -> S5.2 -> S5.5 -> S5.4 -> S5.7 -> S5.10 -> S5.8 -> S5.9 -> S5.6

---

## 6. Quick Tools

> **Status actual:** Command Palette (Ctrl+K), QR Generator, Notepad cu auto-save, Calculator avansat, Password Generator, Barcode Generator. Voice Notes — DEFERRED.

#### S6.1 — Voice Notes cu Transcriere Automata **[FEZABIL CU LIMITARE]**
- **Ce face:** Inregistrezi mesaj vocal, Web Speech API transcrie automat in text, salveaza in Notepad.
- **Exemplu concret:** Pe telefon, apesi microfon: "Reaminteste-mi sa sun clientul Bosch." Nota apare text in Notepad.
- **Provider gratuit:** Web Speech API (necesita internet pt romana) + MediaRecorder API (offline inregistrare)
- **Efort:** 2-3h
- **Dep:** Niciuna

#### S6.2 — Notepad cu Foldere si Tag-uri **[FEZABIL]**
- **Ce face:** Note organizate in foldere + tag-uri. Cautare fulltext.
- **Exemplu concret:** 50 de note dupa cateva luni. Cauti "Bosch" — gasesti toate notele relevante indiferent de folder.
- **Provider gratuit:** SQLite tabele `note_folders` + coloane noi
- **Efort:** 2-3h
- **Dep:** Niciuna

#### S6.3 — Color Picker Avansat **[FEZABIL]**
- **Ce face:** Input HEX/RGB/HSL, conversie, picker vizual, palete salvate, extragere culori din imagine.
- **Exemplu concret:** Client trimite logo, vrei HEX-ul culorii. Upload imagine, click pe culoare -> `#E63946`.
- **Provider gratuit:** Frontend pur (Canvas API `getImageData`)
- **Efort:** 2h
- **Dep:** Niciuna

#### S6.4 — Text Diff (Comparare Texte) **[FEZABIL]**
- **Ce face:** 2 campuri text, comparare vizuala cu highlight pe diferente (adaugiri verde, stergeri rosu).
- **Exemplu concret:** Doua versiuni contract — vezi exact ce s-a schimbat fara sa citesti tot.
- **Provider gratuit:** diff-match-patch (Google, Apache license, 50kB) sau jsdiff
- **Efort:** 1-2h
- **Dep:** Niciuna

#### S6.5 — Convertor Data/Timp cu Fusuri Orare **[FEZABIL]**
- **Ce face:** Conversie fusuri orare, calcul intervale, zile lucratoare, format data RO/US/ISO.
- **Exemplu concret:** Client german: "Meeting on 03/15/2026 at 2 PM CET". Introduci -> Romania: 15 martie 15:00 EET.
- **Provider gratuit:** `Intl.DateTimeFormat` API (nativ browser)
- **Efort:** 2h
- **Dep:** Niciuna

#### S6.6 — Generator Semnatura Email HTML **[FEZABIL]**
- **Ce face:** Formular cu date + template HTML. Buton "Copiaza HTML" pentru Gmail/Outlook.
- **Exemplu concret:** Semnatura CIP Inspection SRL cu logo, telefon, adresa Nadlac, CUI. Copiezi in Gmail.
- **Provider gratuit:** Frontend pur
- **Efort:** 1-2h
- **Dep:** Niciuna

#### S6.7 — Regex Tester **[FEZABIL]**
- **Ce face:** Camp text + regex + highlight pe matches. Explicatie AI optionala. Colectie regex-uri comune.
- **Exemplu concret:** Extragi CUI-uri dintr-un document: testezi `/RO\d{6,10}/g`, highlight pe matches.
- **Provider gratuit:** `new RegExp()` JS nativ + Gemini (explicatie)
- **Efort:** 1-2h
- **Dep:** Niciuna

#### S6.8 — Calculator Financiar (Rate, Dobanzi, Amortizare) **[FEZABIL]**
- **Ce face:** Calcul rate leasing, dobanda simpla/compusa, tabel amortizare, conversie EUR/RON la curs BNR live.
- **Exemplu concret:** Echipament ITP leasing: 15.000 EUR, 20% avans, 36 rate, 8%. Rata lunara 398 EUR, total 17.328 EUR.
- **Provider gratuit:** Frontend pur (formule PMT/PV/FV) + BNR XML feed
- **Efort:** 2-3h
- **Dep:** Niciuna

#### S6.9 — Screenshot Annotation Tool **[FEZABIL CU EFORT MARE]**
- **Ce face:** Upload screenshot, adaugi sageti, text, dreptunghiuri, blur pe zone sensibile. Export PNG.
- **Exemplu concret:** Screenshot problema -> sageata rosie pe zona cu eroarea + text "Bug aici". Trimiti pe email.
- **Provider gratuit:** Canvas API (2D drawing)
- **Efort:** 4-6h
- **Dep:** Niciuna

#### S6.10 — Convertor Numere (Zecimal/Binar/Hex/Octal/Roman) **[FEZABIL]** *QUICK WIN*
- **Ce face:** Input in orice baza, celelalte se actualizeaza live. + numere romane.
- **Exemplu concret:** HEX `0x1A4` -> decimal 420, binar 110100100, octal 644.
- **Provider gratuit:** Frontend pur (`parseInt/toString`)
- **Efort:** 30 min
- **Dep:** Niciuna

#### NEW1 — TTS Text-to-Speech **[FEZABIL]**
- **Ce face:** Buton "Asculta" pe orice text din aplicatie. Backend: edge-tts genereaza audio. Frontend: Web Speech API playback. Voce neurala romaneasca Microsoft.
- **Exemplu concret:** Esti in masina, deschizi o traducere pe telefon, apesi "Asculta" — textul se citeste cu voce naturala in romana in timp ce conduci.
- **Provider gratuit:** edge-tts (`pip install edge-tts`) — Microsoft Neural Romanian voices, zero API key, nelimitat. Fallback: Web Speech API browser.
- **Efort:** 2-3h
- **Dep:** Niciuna

**Ordine recomandata:** S6.10 -> NEW1 -> S6.1 -> S6.4 -> S6.2 -> S6.8 -> S6.5 -> S6.7 -> S6.6 -> S6.3 -> S6.9

---

## 7. Convertor Fisiere

> **Status actual:** PDF->DOCX, DOCX->PDF (COM), Imagine->Text (OCR), CSV/Excel<->JSON, ZIP, redimensionare imagini batch, merge PDF, split PDF, compresie imagini.

#### S7.1 — Conversie DOCX <-> HTML **[FEZABIL]**
- **Ce face:** Convertor bidirectional DOCX-HTML. mammoth pentru DOCX->HTML (calitate buna).
- **Exemplu concret:** Contract Word -> HTML pentru publicare web sau email HTML formatat.
- **Provider gratuit:** mammoth (Python, MIT) + python-docx + BeautifulSoup
- **Efort:** 2-3h
- **Dep:** Niciuna

#### S7.2 — Extragere Imagini din PDF **[FEZABIL]**
- **Ce face:** Extrage toate imaginile din PDF ca fisiere PNG/JPEG individuale.
- **Exemplu concret:** Manual tehnic cu 200 diagrame -> 200 fisiere PNG numerotate, gata de utilizat.
- **Provider gratuit:** PyMuPDF `page.get_images()` (deja instalat)
- **Efort:** 1h
- **Dep:** Niciuna

#### S7.3 — Watermark pe PDF/Imagini **[FEZABIL]**
- **Ce face:** Text/imagine watermark pe PDF (toate/selectate) si imagini. Opacitate, pozitie, culoare configurabile.
- **Exemplu concret:** Traducere draft cu "DRAFT — CIP Inspection SRL" diagonal, semitransparent. Versiune finala fara watermark.
- **Provider gratuit:** PyMuPDF + Pillow (ambele instalate)
- **Efort:** 2h
- **Dep:** Niciuna

#### S7.4 — Redactare (Blackout) Informatii Sensibile din PDF **[FEZABIL]**
- **Ce face:** Redactare permanenta (nu overlay) a zonelor selectate din PDF. GDPR compliant.
- **Exemplu concret:** Contract referinta trimis clientului — elimini permanent CNP, adresa, alte date personale altui client.
- **Provider gratuit:** PyMuPDF `page.add_redact_annot()` + `apply_redactions()`
- **Efort:** 2-3h
- **Dep:** Niciuna

#### S7.5 — Conversie Batch cu Coada si Progress **[FEZABIL]**
- **Ce face:** Upload 20 fisiere, coada cu progress bar per fisier, notificare la final, download all ca ZIP.
- **Exemplu concret:** 20 DOCX -> PDF. Pornesti conversia, faci altceva. "Conversia completa: 18 reusite, 2 erori. Descarca ZIP."
- **Provider gratuit:** WebSocket progress (existent) + SQLite queue
- **Efort:** 3-4h
- **Dep:** Niciuna

#### S7.6 — Rotatie si Aliniere Automata Documente Scanate **[FEZABIL]**
- **Ce face:** Auto-deskew inainte de OCR. Calitate OCR creste semnificativ.
- **Exemplu concret:** Contract scanat cu telefonul, usor rotit. Auto-deskew il indreapta la orizontal.
- **Provider gratuit:** deskew (`pip install deskew`, MIT) sau scipy.ndimage.rotate
- **Efort:** 1-2h
- **Dep:** Niciuna

#### S7.7 — Conversie Audio -> Text (Transcriere) **[FEZABIL]**
- **Ce face:** Upload audio (MP3/WAV/M4A), transcriere text via Groq Whisper sau Gemini Audio.
- **Exemplu concret:** Inregistrare sedinta 45 min -> transcriere completa. Dai la AI pentru rezumat.
- **Provider gratuit:** Groq Whisper large-v3 (30 req/min, free tier) -> Gemini Flash Audio (1000 req/zi) -> whisper.cpp local (offline)
- **Efort:** 3-4h
- **Dep:** Niciuna
- **Nota:** OpenAI Whisper eliminat (no free tier fiabil). Groq Whisper = calitate excelenta, gratuit.

#### S7.8 — Semnatura Vizuala pe PDF **[FEZABIL]**
- **Ce face:** Canvas API pentru desenare semnatura + PyMuPDF pentru aplicare pe PDF. NU semnatura electronica calificata.
- **Exemplu concret:** Contract PDF simplu de la partener. Adaugi semnatura pe pagina finala, salvezi PDF semnat.
- **Provider gratuit:** Canvas API + PyMuPDF (instalat)
- **Efort:** 2-3h
- **Dep:** Niciuna
- **Nota:** Semnatura electronica calificata eliminata (toti providerii sunt platiti). Aceasta e doar semnatura vizuala.

#### S7.9 — Protectie PDF cu Parola **[FEZABIL]**
- **Ce face:** Encrypt/decrypt PDF cu parola. AES-256.
- **Exemplu concret:** Traducere confidentiala protejata cu parola. Client primeste fisier + parola separat.
- **Provider gratuit:** PyMuPDF `doc.save(encryption=fitz.PDF_ENCRYPT_AES_256)`
- **Efort:** 1h
- **Dep:** Niciuna

#### S7.10 — Preview Inainte si Dupa Conversie **[FEZABIL CU EFORT MARE]**
- **Ce face:** Preview vizual original vs. convertit side-by-side, inainte de descarcare.
- **Exemplu concret:** DOCX->PDF cu tabele complexe. Preview arata ca un tabel e truncat pe pag 3. Ajustezi marginile.
- **Provider gratuit:** pdf.js (Mozilla) + mammoth (DOCX->HTML)
- **Efort:** 4-6h
- **Dep:** Niciuna

#### NEW8 — EasyOCR (OCR Imbunatatit pentru Romana) **[FEZABIL]**
- **Ce face:** OCR mai bun decat Tesseract pentru texte romanesti, in special pe documente scanate de calitate medie.
- **Exemplu concret:** Document scanat cu diacritice romanesti — EasyOCR recunoaste corect "sustinerea" vs Tesseract care da "susfinerea".
- **Provider gratuit:** EasyOCR (`pip install easyocr`) — gratuit, offline, suport limba romana
- **Efort:** 2h
- **Dep:** Niciuna
- **Nota:** PaddleOCR eliminat (necesita GPU). EasyOCR ruleaza pe CPU.

**Ordine recomandata:** S7.2 -> S7.9 -> S7.6 -> NEW8 -> S7.3 -> S7.4 -> S7.1 -> S7.8 -> S7.5 -> S7.7 -> S7.10

---

## 8. File Manager

> **Status actual:** Browse, CRUD fisiere, upload/download, duplicate finder MD5, FTS5 fulltext, tag-uri, favorite, auto-organizare pe extensie.

#### S8.1 — Preview Documente Direct in Browser **[FEZABIL]**
- **Ce face:** Click pe fisier -> preview inline fara descarcare. PDF render, DOCX/XLSX conversie HTML.
- **Exemplu concret:** 30 contracte PDF. Click pe fiecare, il citesti direct. Gasesti contractul cautat rapid.
- **Provider gratuit:** pdf.js (Mozilla) + mammoth + openpyxl->JSON->HTML
- **Efort:** 3-4h
- **Dep:** Niciuna

#### S8.2 — Versioning Simplu (Istoric Versiuni per Fisier) **[FEZABIL]**
- **Ce face:** La re-upload cu acelasi nume, versiunea veche se arhiveaza. Restaurare versiuni anterioare.
- **Exemplu concret:** Upload "Contract_Bosch_v1.docx". Peste o luna re-upload cu modificari. Ambele versiuni pastrate.
- **Provider gratuit:** SQLite tabel `file_versions` + redenumire fisier
- **Efort:** 2-3h
- **Dep:** Niciuna

#### S8.3 — Partajare Temporara cu Link **[FEZABIL]**
- **Ce face:** Link temporar (24h/7 zile) pentru un fisier, accesibil fara autentificare. Expira automat.
- **Exemplu concret:** Client nu primeste attachment pe email (prea mare). Link temporar 48h trimis pe WhatsApp.
- **Provider gratuit:** SQLite tabel `shared_links` (UUID token)
- **Efort:** 2h
- **Dep:** Niciuna

#### S8.4 — Recunoastere OCR la Upload cu Index Automat **[FEZABIL CU EFORT MARE]**
- **Ce face:** La upload PDF/imagine, OCR ruleaza automat in background si indexeaza in FTS5.
- **Exemplu concret:** Upload 10 contracte scanate. Dupa 30 sec, toate cautabile fulltext. Cauti "clauza penalitate".
- **Provider gratuit:** Tesseract (instalat) + EasyOCR + FTS5
- **Efort:** 4-6h
- **Dep:** Niciuna

#### S8.5 — Statistici Stocare cu Recomandari de Curatare **[FEZABIL]**
- **Ce face:** Analiza completa: fisiere neutilizate >6 luni, temporare, top foldere, top 20 fisiere mari.
- **Exemplu concret:** "node_modules din Proiect_Vechi ocupa 1.2 GB, neaccesat 8 luni. Recomand stergere."
- **Provider gratuit:** os.stat() + SQLite queries
- **Efort:** 2h
- **Dep:** Niciuna

#### S8.6 — Comparare Fisiere (Diff pe Documente Text) **[FEZABIL]**
- **Ce face:** Selectezi 2 fisiere, diff vizual cu highlighting. Integrat din File Manager.
- **Exemplu concret:** Versiunea 1 si 2 contract. "Compara" -> vezi exact paragrafele schimbate.
- **Provider gratuit:** difflib (Python standard library)
- **Efort:** 2h
- **Dep:** Niciuna

#### S8.7 — Smart Collections (Dosare Virtuale cu Reguli) **[FEZABIL]**
- **Ce face:** Dosare inteligente cu reguli: "Toate PDF-urile din luna curenta", "Tag:client+Bosch", ">5MB azi".
- **Exemplu concret:** Smart Collection "De livrat azi": fisiere cu tag "in lucru" + data azi. Lista de lucru a zilei.
- **Provider gratuit:** SQLite tabel `smart_collections` (rules_json)
- **Efort:** 3-4h
- **Dep:** Niciuna

#### S8.8 — Backup Automat in Google Drive (Selectiv) **[FEZABIL]**
- **Ce face:** Foldere configurate se sincronizeaza automat cu Drive la interval. Nu tot FM, ci doar folderele importante.
- **Exemplu concret:** "Contracte_Semnate" se sync zilnic la 02:00 pe Drive. Laptop crapa -> contracte in Drive.
- **Provider gratuit:** Google Drive API (integrat Faza 13) + APScheduler
- **Efort:** 2-3h
- **Dep:** Niciuna

#### S8.9 — Thumbnail Grid View pentru Imagini **[FEZABIL]**
- **Ce face:** View grid thumbnail-uri in loc de lista text. Toggle list/grid.
- **Exemplu concret:** "Fotografii_ITP" cu 200 poze. Grid View -> identifici rapid poza vizual.
- **Provider gratuit:** Pillow (instalat) + React responsive img
- **Efort:** 2-3h
- **Dep:** Niciuna

#### S8.10 — Rename Batch Inteligent cu Pattern **[FEZABIL]**
- **Ce face:** Selectezi fisiere, aplici pattern de redenumire: `{data}_{seq}_{original}`. Preview inainte.
- **Exemplu concret:** 15 fisiere haotice -> `2026-03-15_Bosch_{001..015}.pdf` instant.
- **Provider gratuit:** Python str.format() + endpoint batch
- **Efort:** 2h
- **Dep:** Niciuna

#### NEW6 — Share Target API (PWA) **[FEZABIL]**
- **Ce face:** PWA share target — partajezi din orice aplicatie Android direct in Command Center File Manager.
- **Exemplu concret:** Primesti PDF pe WhatsApp. Apesi "Share" -> alegi "Command Center" -> fisierul ajunge direct in File Manager.
- **Provider gratuit:** Web Share Target API (standard PWA, zero cost). Necesita manifest.json `share_target` entry.
- **Efort:** 2-3h
- **Dep:** Niciuna

**Ordine recomandata:** S8.10 -> S8.1 -> S8.2 -> S8.3 -> NEW6 -> S8.9 -> S8.8 -> S8.5 -> S8.6 -> S8.7 -> S8.4

---

## 9. Vault (API Keys)

> **Status actual:** Fernet encryption + PBKDF2 + master password, stocheaza 10 API keys, interface CRUD.

#### S9.1 — Categorii si Grupare Keys per Modul **[FEZABIL]**
- **Ce face:** Keys organizate pe categorii: AI Keys, Translation Keys, Integration Keys. Acces per modul.
- **Exemplu concret:** Translator acceseaza doar "Translation Keys". AI acceseaza "AI Keys".
- **Provider gratuit:** SQLite coloana `category`
- **Efort:** 1h
- **Dep:** Niciuna

#### S9.2 — Monitorizare Utilizare Keys **[FEZABIL]**
- **Ce face:** Tracker per key: apeluri/tokeni consumati din Command Center. Grafic temporal.
- **Exemplu concret:** Gemini API: 743 apeluri/30 zile, 234 din AI Chat, 509 din Translator. Trend: +23%.
- **Provider gratuit:** SQLite tabel `key_usage` + Recharts
- **Efort:** 2-3h
- **Dep:** Niciuna

#### S9.3 — Alerta la Apropierea Limitei Free Tier **[FEZABIL]**
- **Ce face:** Camp `free_tier_limit` per key. Alerta la 80% si 90% consum. Comutare automata pe fallback.
- **Exemplu concret:** DeepL: 500K chars, la 400K (80%) alerta galbena, la 450K (90%) alerta rosie + switch automat Azure.
- **Provider gratuit:** SQLite + logica threshold
- **Efort:** 2h
- **Dep:** S9.2 (Monitorizare Utilizare)

#### S9.4 — Rotatie Automata Keys (Failover Transparent) **[FEZABIL]**
- **Ce face:** Key returneaza eroare -> comuta automat la backup key pentru acelasi serviciu. Zero intrerupere.
- **Exemplu concret:** 2 keys Gemini (personal + business). Key 1 rate limit -> key 2 preia transparent.
- **Provider gratuit:** Logica Python in fallback chain
- **Efort:** 2h
- **Dep:** Niciuna

#### S9.5 — Test Conectivitate per Key (Ping) **[FEZABIL]**
- **Ce face:** Buton "Testeaza" per key — request minim de test, returneaza status, latenta, model disponibil.
- **Exemplu concret:** Key Groq noua -> "Testeaza" -> "Groq API: OK, 234ms, model: llama-3.3-70b".
- **Provider gratuit:** httpx request minim per provider
- **Efort:** 2h
- **Dep:** Niciuna

#### S9.6 — Import/Export Securizat Keys (Backup Criptat) **[FEZABIL]**
- **Ce face:** Export toate key-urile ca fisier `.vault` criptat AES-256. Import pe alt dispozitiv cu parola.
- **Exemplu concret:** Reinstalezi Windows. Import fisier + parola -> toate key-urile restaurate in 10 secunde.
- **Provider gratuit:** Fernet encryption (deja folosit)
- **Efort:** 2h
- **Dep:** Niciuna

#### S9.7 — Log Activitate per Key **[FEZABIL]**
- **Ce face:** Audit log: timestamp, modul, endpoint, succes/eroare per key. Filtrabil, exportabil.
- **Exemplu concret:** OpenAI key: 50 apeluri in weekend cand n-ai lucrat. Verifici: Scheduler (normal) sau suspect.
- **Provider gratuit:** SQLite tabel `key_access_log`
- **Efort:** 2h
- **Dep:** Niciuna

#### S9.8 — Reminder Reinnoire Keys cu Data Expirare **[FEZABIL]**
- **Ce face:** Coloana `expires_at` per key. Alerta la 14 zile inainte.
- **Exemplu concret:** Token GitHub expira 1 mai 2026. La 17 aprilie: "Token GitHub expira in 14 zile."
- **Provider gratuit:** APScheduler + SQLite
- **Efort:** 1h
- **Dep:** Niciuna

#### S9.9 — Validare Format Key la Salvare **[FEZABIL]** *QUICK WIN*
- **Ce face:** Regex per tip serviciu la adaugare key. Detecteaza erori de copiere.
- **Exemplu concret:** Key Gemini cu spatiu la final -> "Formatul nu corespunde pattern-ului Gemini (AIzaXXXX...)."
- **Provider gratuit:** Dict de regex-uri Python
- **Efort:** 30 min
- **Dep:** Niciuna

#### S9.10 — Dashboard Sanatate API Keys **[FEZABIL]**
- **Ce face:** Ecran cu status per key: verde (OK), galben (netestat >7 zile), rosu (eroare), gri (neconfigurat).
- **Exemplu concret:** 8 keys verzi, 1 galbena (Perplexity, nefolosit 2 saptamani), 1 rosie (Azure — expirata ieri).
- **Provider gratuit:** Combina S9.2 + S9.5 + S9.8
- **Efort:** 2-3h
- **Dep:** S9.2, S9.5, S9.8

**Ordine recomandata:** S9.9 -> S9.5 -> S9.1 -> S9.6 -> S9.2 -> S9.4 -> S9.3 -> S9.8 -> S9.7 -> S9.10

---

## 10. Automatizari

> **Status actual:** Task Scheduler vizual (CRUD, manual trigger, run history), Shortcuts, Uptime Monitor, API Tester, Health Monitor. DEFERRED: web scraping, notificari unificate, webhook.

#### S10.1 — Sistem Notificari Unificate **[FEZABIL]**
- **Ce face:** Bell icon in Header cu toate alertele: facturi restante, ITP expirare, limite API, task-uri esuate. Mark as read, filtre.
- **Exemplu concret:** Dimineata: "2 ITP-uri expira in 7 zile", "Factura restanta 5 zile", "Backup esuat ieri la 02:00".
- **Provider gratuit:** SQLite tabel `notifications` + React bell component
- **Efort:** 3-4h
- **Dep:** Niciuna

#### S10.2 — Raport Zilnic/Saptamanal pe Email/Telegram **[FEZABIL]**
- **Ce face:** Task schedulat: rezumat activitate pe email/Telegram. Calcule, traduceri, ITP-uri, facturi, erori.
- **Exemplu concret:** Luni 08:00: "Saptamana 10-16 Martie: 12 calcule, 8 traduceri, 3 facturi (4.200 RON), 127 ITP-uri, 0 erori."
- **Provider gratuit:** APScheduler + Gmail SMTP / Telegram Bot API
- **Efort:** 2-3h
- **Dep:** Niciuna

#### S10.3 — Webhook Incoming **[FEZABIL]**
- **Ce face:** Endpoint POST `/api/webhook/in` care primeste JSON si declansaza actiuni configurate.
- **Exemplu concret:** Formular oferta pe site. La completare, webhook la Command Center -> creare client + calcul pre-completat.
- **Provider gratuit:** FastAPI endpoint + SQLite `webhook_log`
- **Efort:** 2-3h
- **Dep:** Niciuna

#### S10.4 — Macro Recorder (Secvente de Actiuni) **[FEZABIL CU EFORT MARE]**
- **Ce face:** Inregistrezi secventa de actiuni (calcul -> oferta -> email -> calendar), o salvezi ca macro, o rulezi cu un click.
- **Exemplu concret:** Macro "Flux Client Nou": 1) Calcul pret, 2) Oferta PDF, 3) Email client, 4) Calendar follow-up +3 zile.
- **Provider gratuit:** SQLite tabel `macros` (steps_json) + motor executie
- **Efort:** 8-12h (3-5 sesiuni)
- **Dep:** Module Calculator, Invoice, Gmail, Calendar (toate exista)

#### S10.5 — Conditii in Task Scheduler (If/Then) **[FEZABIL]**
- **Ce face:** Task-uri cu conditii: "DOAR daca facturi restante >30 zile", "DOAR daca uptime <95%".
- **Exemplu concret:** Task "Alerta cashflow": zilnic 09:00, verifica restante >30 zile. DACA exista -> email. DACA nu -> nimic.
- **Provider gratuit:** SQLite coloana `condition_json` + motor evaluare
- **Efort:** 3-4h
- **Dep:** Niciuna

#### S10.6 — Monitorizare Performanta Aplicatie **[FEZABIL]**
- **Ce face:** Dashboard metrici: timp raspuns per endpoint API, endpoint-uri lente, query-uri SQLite lente, memory.
- **Exemplu concret:** `/api/filemanager/search` are 3.2s. Cauza: FTS5 fara index. Identifici si rezolvi.
- **Provider gratuit:** Middleware FastAPI logging + SQLite `api_metrics` + Recharts
- **Efort:** 3h
- **Dep:** Niciuna

#### S10.7 — Backup Automat Configurabil (Local + Drive) **[FEZABIL]**
- **Ce face:** Config din UI: ce se include, frecventa, destinatie, retentie. Zero interventie manuala.
- **Exemplu concret:** Zilnic 03:00: DB + Contracte + Vault criptat -> local + Drive. Retentie 30 zile.
- **Provider gratuit:** backup.py existent + APScheduler + Drive API
- **Efort:** 2-3h
- **Dep:** Niciuna

#### S10.8 — Log Centralizat cu Cautare si Filtre **[FEZABIL]**
- **Ce face:** Un singur log din toate modulele, cautabil per modul, nivel, interval de timp.
- **Exemplu concret:** Gmail nu merge. Filtrezi: modul=integrations, nivel=ERROR, 24h -> "SMTP connection refused: port 587 blocked".
- **Provider gratuit:** RotatingFileHandler (existent) + endpoint `/api/logs`
- **Efort:** 3h
- **Dep:** Niciuna

#### S10.9 — Simulate Task (Dry Run) **[FEZABIL]**
- **Ce face:** "Simuleaza" per task — ruleaza dry-run, arata ce ar face fara a executa.
- **Exemplu concret:** Task "Stergere fisiere vechi >180 zile" -> simuleaza -> lista exacta a 47 fisiere ce ar fi sterse.
- **Provider gratuit:** Parametru `dry_run=True` pe functii
- **Efort:** 2h
- **Dep:** Niciuna

#### S10.10 — Webhook Out la Evenimente **[FEZABIL]**
- **Ce face:** La anumite evenimente (factura emisa, traducere finalizata, ITP expirat), POST la URL configurate.
- **Exemplu concret:** Factura emisa -> Zapier primeste datele -> le adauga in Google Sheets "Registru Venituri".
- **Provider gratuit:** httpx POST + Vault (URL-uri configurate)
- **Efort:** 2h
- **Dep:** Niciuna

#### NEW2 — Web Push Notifications VAPID **[FEZABIL]**
- **Ce face:** Notificari native Android din PWA fara Telegram sau alta aplicatie externa. Chiar cand aplicatia e inchisa.
- **Exemplu concret:** ITP expirat -> notificare nativa Android direct din Command Center PWA instalat pe telefon.
- **Provider gratuit:** pywebpush (`pip install pywebpush`, zero cost, standard web) + `ServiceWorkerRegistration.pushManager`
- **Efort:** 3-4h
- **Dep:** Niciuna

#### NEW9 — Cross-Module Workflows **[FEZABIL CU EFORT MARE]**
- **Ce face:** Fluxuri automatizate end-to-end: Calc->Invoice->Email->Calendar->Alert. Toate modulele exista, lipsesc conexiunile.
- **Exemplu concret:** "Flux Proiect Traducere": Upload fisier -> Traducere automata -> Quality check AI -> Generare factura cu pret calculat -> Email client.
- **Provider gratuit:** Toate modulele existente, doar orchestrare noua
- **Efort:** 6-10h (2-3 sesiuni per flux)
- **Dep:** Module relevante sa fie functionale (sunt)

**Ordine recomandata:** S10.1 -> NEW2 -> S10.2 -> S10.3 -> S10.8 -> S10.5 -> S10.9 -> S10.7 -> S10.10 -> S10.6 -> S10.4 -> NEW9

---

## 11. Integrari Externe

> **Status actual:** Gmail (SMTP/IMAP), Google Drive (REST), Google Calendar (REST CRUD), GitHub (httpx repos/commits/issues), Status Dashboard.

#### S11.1 — Gmail: Inbox cu Filtre si Categorii **[FEZABIL]**
- **Ce face:** Vizualizare inbox cu filtre: necitite, cu atasamente, per expeditor. Categorii auto.
- **Exemplu concret:** "Necitite + Atasament PDF" -> emailuri cu documente de procesat, fara scanare tot inbox.
- **Provider gratuit:** IMAP (deja integrat)
- **Efort:** 3-4h
- **Dep:** Niciuna

#### S11.2 — Gmail: Compunere Email cu Template-uri + Traducere Inline **[FEZABIL]**
- **Ce face:** Editor email cu template-uri (oferta, factura, urmarire). Buton "Traduce EN" inline.
- **Exemplu concret:** Template "Transmitere Factura", pre-completat cu date client, "Traduce EN" pt client german, trimite.
- **Provider gratuit:** SMTP (functional) + Translator (existent)
- **Efort:** 3-4h
- **Dep:** Niciuna

#### S11.3 — Google Drive: Sincronizare Selectiva Foldere **[FEZABIL]**
- **Ce face:** Perechi folder local <-> Drive. Sync unidirectional (backup) sau bidirectional.
- **Exemplu concret:** "Traduceri_Livrate" -> Drive/CIP_Inspection/Traduceri. Clientul cu acces Drive vede automat.
- **Provider gratuit:** Google Drive API (integrat) + APScheduler
- **Efort:** 3-4h
- **Dep:** Niciuna

#### S11.4 — Google Calendar: Integrare cu ITP Programari **[FEZABIL]**
- **Ce face:** Programari ITP sync automat cu Google Calendar. Vizibile din Calendar app nativa.
- **Exemplu concret:** Programezi ITP 25 martie 10:00. Apare in Google Calendar: "ITP — Dacia Logan AB-01-XXX — Popescu."
- **Provider gratuit:** Google Calendar API (integrat)
- **Efort:** 2-3h
- **Dep:** S5.4 (Calendar ITP)

#### S11.5 — GitHub: Dashboard Proiecte **[FEZABIL]**
- **Ce face:** Issues, PRs, commits, status CI/CD. Creare issues din Command Center.
- **Exemplu concret:** Bug gasit -> "Creeaza issue" direct fara a deschide GitHub.com.
- **Provider gratuit:** GitHub API (integrat)
- **Efort:** 2-3h
- **Dep:** Niciuna

#### S11.6 — Notificari Email Digest **[FEZABIL]**
- **Ce face:** Un singur email zilnic de digest: rezumat facturi, ITP, backup, erori. Reduce email noise.
- **Exemplu concret:** 08:00: "Digest: 2 ITP expira 15 zile, 1 factura restanta +10 zile, backup OK, 0 erori."
- **Provider gratuit:** APScheduler + Gmail SMTP
- **Efort:** 2h
- **Dep:** S10.1 (Notificari Unificate — sursa date)

#### S11.7 — Google Contacts Import CSV **[FEZABIL]**
- **Ce face:** Import contacte Google via CSV (export din Google Contacts) pentru auto-complete clienti.
- **Exemplu concret:** Scrii "Bosc..." la factura -> auto-complete "Bosch Romania — contact@bosch.ro" din contacte importate.
- **Provider gratuit:** CSV import (Google permite export contacts ca CSV)
- **Efort:** 2h
- **Dep:** Niciuna
- **Nota:** OAuth complet eliminat (efort mare). Import CSV e alternativa simpla si gratuita.

#### S11.8 — GitHub: Auto-Commit Backup Configuratii **[FEZABIL]**
- **Ce face:** La modificare config (reguli Vault, template-uri, glosar) -> auto-commit in GitHub.
- **Exemplu concret:** Adaugi 10 termeni glosar -> commit automat: "chore: add 10 terms to glossary (auto-backup 2026-03-19)".
- **Provider gratuit:** GitHub API (integrat)
- **Efort:** 2h
- **Dep:** Niciuna

#### S11.9 — Telegram Bot pentru Notificari **[FEZABIL]**
- **Ce face:** Notificari push pe Telegram. Setup 2 minute via @BotFather. Mai rapid de vazut pe telefon decat email.
- **Exemplu concret:** Task scheduler esuat la 02:00. Dimineata pe Telegram: "Backup task failed — Drive quota exceeded."
- **Provider gratuit:** Telegram Bot API (complet gratuit, practic nelimitat)
- **Efort:** 1-2h
- **Dep:** Niciuna

#### S11.10 — Status Page Integrari cu Auto-Reconnect **[FEZABIL]**
- **Ce face:** Status dashboard extins: test periodic per integrare, auto-refresh token daca expirat.
- **Exemplu concret:** Token Drive expirat -> dashboard arata "Drive: token expirat" + buton "Reconnect".
- **Provider gratuit:** APScheduler + teste periodice
- **Efort:** 2-3h
- **Dep:** Niciuna

**Ordine recomandata:** S11.9 -> S11.2 -> S11.1 -> S11.3 -> S11.4 -> S11.6 -> S11.8 -> S11.7 -> S11.5 -> S11.10

---

## 12. Rapoarte & Statistici

> **Status actual:** Disk stats, system info, timeline activitate (BarChart), fisiere neutilizate, jurnal cu mood, bookmarks, export JSON, file stats.

#### S12.1 — Dashboard KPI Business **[FEZABIL]**
- **Ce face:** Un ecran cu toti indicatorii cheie: venituri luna curenta vs. precedenta (%), clienti activi, traduceri, ITP-uri, facturi restante.
- **Exemplu concret:** "Martie 2026: 14.200 RON (+8% vs Feb), 23 clienti, 34 traduceri, 127 ITP-uri, 2 restante (3.400 RON)."
- **Provider gratuit:** Recharts + SQLite agregate
- **Efort:** 3-4h
- **Dep:** Niciuna

#### S12.2 — Raport Comparativ An vs. An (YoY) **[FEZABIL]**
- **Ce face:** Grafic comparativ aceeasi perioada an curent vs. an anterior.
- **Exemplu concret:** "Q1 2026 vs Q1 2025: Venituri +22%, ITP +8%, Traduceri +35%. Trend: crestere sanatoasa."
- **Provider gratuit:** SQLite queries agregate + Recharts
- **Efort:** 2-3h
- **Dep:** Niciuna

#### S12.3 — Raport Productivitate Personala **[FEZABIL]**
- **Ce face:** Ore active/zi, module folosite, varfuri de activitate, streak-uri consecutive.
- **Exemplu concret:** "Saptamana trecuta: 38h, Translator 12h, Calculator 8h, AI 7h. Varf: Marti 09-12. Streak: 14 zile."
- **Provider gratuit:** SQLite `activity_log` + Recharts
- **Efort:** 2-3h
- **Dep:** Niciuna

#### S12.4 — Export Complet per Modul **[FEZABIL]**
- **Ce face:** Export individual per modul: calcule Excel, traduceri CSV, ITP-uri Excel, facturi PDF. Filtrabil pe perioada.
- **Exemplu concret:** Contabilul cere ITP Q1. Export > ITP > Q1 2026 > Excel -> fisier structurat gata.
- **Provider gratuit:** openpyxl (instalat)
- **Efort:** 3-4h
- **Dep:** Niciuna

#### S12.5 — Predictii Business (AI-Powered) **[FEZABIL]**
- **Ce face:** AI + regresie liniara analizeaza date istorice, face predictii venituri, tendinte, sezonalitate.
- **Exemplu concret:** "Prognoza Aprilie 2026: 15.800-17.200 RON (interval 80%). Factori: +8%/luna + sezonalitate ITP."
- **Provider gratuit:** scipy linregress + Gemini Flash (interpretare text)
- **Efort:** 3-4h
- **Dep:** Niciuna

#### S12.6 — Jurnal cu Cautare Full-Text si Export **[FEZABIL]**
- **Ce face:** Jurnal existent + FTS5 + export PDF/DOCX formatat + statistici mood.
- **Exemplu concret:** Cauti "Bosch" in jurnal -> toate zilele mentionate. Export ultimele 3 luni ca PDF.
- **Provider gratuit:** FTS5 + reportlab + python-docx
- **Efort:** 2h
- **Dep:** Niciuna

#### S12.7 — Heatmap Calendar Activitate (GitHub-Style) **[FEZABIL]**
- **Ce face:** Calendar heatmap pe tot anul cu intensitatea activitatii totale per zi (calcule + traduceri + ITP + altele).
- **Exemplu concret:** 2026: verde intens ian-mar, galben august (concediu). Vizualizare anuala productivitate.
- **Provider gratuit:** react-calendar-heatmap (open-source, 5kB) sau Recharts custom SVG
- **Efort:** 2h
- **Dep:** Niciuna

#### S12.8 — Raport Utilizare API (Costuri Potentiale) **[FEZABIL]**
- **Ce face:** Toti providerii AI/traducere: apeluri, tokeni, echivalent cost daca ai fi pe tier platit.
- **Exemplu concret:** "Martie: Gemini 1.240 apeluri, ~2.1M tokens (~$21 echivalent). DeepL 280K chars (~$14). Total economii: ~$35/luna."
- **Provider gratuit:** token_tracker (existent Faza 15B)
- **Efort:** 2-3h
- **Dep:** Niciuna

#### S12.9 — Alerta Anomalii **[FEZABIL]**
- **Ce face:** Detectare automata: volum anormal mare (bug scheduler), volum mic (serviciu oprit), consum API anormal.
- **Exemplu concret:** Scheduler ruleaza task de 500 ori in 10 min (bug loop). Detectare + oprire automata.
- **Provider gratuit:** Python medie + std deviation + APScheduler
- **Efort:** 2-3h
- **Dep:** Niciuna

#### S12.10 — Raport Satisfactie Client (Manual) **[FEZABIL]**
- **Ce face:** Scor 1-5 + comentariu dupa fiecare livrare. Statistici per client, per serviciu, tendinta.
- **Exemplu concret:** Bosch traducere 5/5 "livrare rapida". Dacia manual 3/5 "terminologie inconsistenta pag 15". Media: 4.2/5.
- **Provider gratuit:** SQLite tabel `client_satisfaction` + Recharts
- **Efort:** 2h
- **Dep:** Niciuna

**Ordine recomandata:** S12.1 -> S12.7 -> S12.4 -> S12.2 -> S12.3 -> S12.8 -> S12.5 -> S12.6 -> S12.9 -> S12.10

---

## 13. Quick Tools Extra

> **Status actual:** Extensie Quick Tools cu tool-uri suplimentare in `backend/modules/quick_tools_extra/`.

#### S13.1 — Clipboard Manager Avansat (Sync PC<->Android) **[FEZABIL]**
- **Ce face:** Clipboard history cu cautare, pin, sync cross-device via Tailscale. Diferentiator fata de Win+V.
- **Exemplu concret:** Copiezi IBAN pe PC. Deschizi Command Center pe telefon -> Clipboard -> gasesti IBAN.
- **Provider gratuit:** SQLite + WebSocket real-time
- **Efort:** 2-3h
- **Dep:** Niciuna

#### S13.2 — Focus Timer (Pomodoro Adaptat) **[FEZABIL]**
- **Ce face:** Timer customizabil + integrare Jurnal: la final "Ce ai realizat?" -> salveaza automat.
- **Exemplu concret:** Focus 45 min -> "Ce ai realizat?" -> "Tradus 12 pag Bosch". Jurnal: 3h focus traduceri azi.
- **Provider gratuit:** Frontend pur (setInterval + Notification API)
- **Efort:** 1-2h
- **Dep:** Niciuna

#### S13.3 — Snippet Manager (Texte Frecvente) **[FEZABIL]**
- **Ce face:** Colectie texte frecvente: anteturi emailuri, clauze contractuale, raspunsuri clienti. Accesibil din Ctrl+K.
- **Exemplu concret:** Ctrl+K -> "clauza confidentialitate" -> apare clauza standard de copiat. Nu mai cauti prin fisiere.
- **Provider gratuit:** SQLite tabel `snippets` + Command Palette integrare
- **Efort:** 2h
- **Dep:** Niciuna

#### S13.4 — Convertor Markdown <-> HTML <-> Text **[FEZABIL]** *QUICK WIN*
- **Ce face:** 3 textarea-uri cu conversie live intre MD, HTML si text plain.
- **Exemplu concret:** Email in Markdown -> HTML formatat pentru Gmail. Sau HTML copiat de pe site -> text curat.
- **Provider gratuit:** marked.js (3kB) + turndown (7kB) + DOMParser
- **Efort:** 45 min
- **Dep:** Niciuna

#### S13.5 — Generator Contracte Rapide (Mini-Wizard) **[FEZABIL]**
- **Ce face:** Wizard 5 pasi: tip contract -> date client -> sume -> termen -> generare DOCX.
- **Exemplu concret:** Client nou fara contract. Wizard 2 min -> Contract_Prestari_Bosch_2026-03-19.docx gata de semnat.
- **Provider gratuit:** python-docx (instalat)
- **Efort:** 3-4h
- **Dep:** Niciuna

#### S13.6 — Scurtaturi Navigare Personalizate **[FEZABIL]**
- **Ce face:** URL-uri frecvente (RAR, ANAF, furnizori) accesibile din Ctrl+K.
- **Exemplu concret:** Ctrl+K -> "RAR" -> deschide portal RAR. Nu mai cauti bookmark-uri in browser.
- **Provider gratuit:** SQLite tabel `quick_links`
- **Efort:** 1h
- **Dep:** Niciuna

#### S13.7 — Notepad Sync Real-Time PC<->Telefon **[FEZABIL]**
- **Ce face:** WebSocket push pentru modificari instant pe ambele device-uri simultan.
- **Exemplu concret:** Scrii pe telefon, apare instant pe PC. Clipboard cross-device simplu.
- **Provider gratuit:** WebSocket (existent in stack)
- **Efort:** 1-2h
- **Dep:** Niciuna

#### S13.8 — Calculator TVA si Declaratii Fiscale **[FEZABIL]**
- **Ce face:** Calculator fiscal romanesc: TVA 19%, impozit venit 10%, CAS 25%, CASS 10%. Per regim PFA/SRL.
- **Exemplu concret:** Venituri Q1: 42.000 RON -> impozit 6.720 RON, contributii, net de platit contabilului.
- **Provider gratuit:** Frontend pur (formule fiscale)
- **Efort:** 2h
- **Dep:** Niciuna

#### S13.9 — Validator Numere Inmatriculare (ITP Helper) **[FEZABIL]**
- **Ce face:** Validare format romanesc, auto-completare judet din prefix. Previne date incorecte in DB.
- **Exemplu concret:** Introduci "B-12-" -> sugestii format valid. Validare inainte de salvare in ITP.
- **Provider gratuit:** Regex frontend pur
- **Efort:** 1h
- **Dep:** Niciuna

#### S13.10 — To-Do List cu Prioritati si Deadline (GTD Lite) **[FEZABIL]**
- **Ce face:** Task manager: status (To Do/In Lucru/Finalizat), prioritate, deadline, categorie. Drag-and-drop.
- **Exemplu concret:** Urgent "Trimite factura Bosch — deadline 15:00", Normal "Actualizeaza glosar Continental".
- **Provider gratuit:** SQLite tabel `todos` + React DnD
- **Efort:** 3-4h
- **Dep:** Niciuna

**Ordine recomandata:** S13.4 -> S13.6 -> S13.9 -> S13.3 -> S13.1 -> S13.7 -> S13.8 -> S13.2 -> S13.10 -> S13.5

---

## 14. CRM (Modul NOU)

> **Status actual:** Modul inexistent. Datele client sunt dispersate in `invoices`, `itp_inspections`, `calculations`.

#### NEW5.1 — Client Lifecycle Management **[FEZABIL]**
- **Ce face:** Centralizare date client: toate interactiunile (calcule, traduceri, facturi, ITP) vizibile per client. Fisa unica.
- **Exemplu concret:** Deschizi fisa "Bosch Romania" -> vezi: 12 calcule, 8 traduceri, 5 facturi (total 23.400 RON), ultima interactiune acum 3 zile.
- **Provider gratuit:** SQLite tabel `crm_clients` + JOIN pe tabele existente
- **Efort:** 3-4h
- **Dep:** Niciuna

#### NEW5.2 — Communication Timeline per Client **[FEZABIL]**
- **Ce face:** Cronologie completa per client: emailuri trimise/primite, facturi, oferte, note, apeluri.
- **Exemplu concret:** Timeline Bosch: 15 ian oferta, 20 ian contract semnat, 25 ian factura, 1 feb email follow-up, 5 feb plata confirmata.
- **Provider gratuit:** SQLite agregate din `invoices` + `activity_log` + `chat_sessions` + Gmail
- **Efort:** 3-4h
- **Dep:** NEW5.1

#### NEW5.3 — Segmentare Clienti **[FEZABIL]**
- **Ce face:** Clasificare automata: Gold (>10.000 RON/an), Silver (5-10K), Bronze (<5K). Tags custom.
- **Exemplu concret:** 3 clienti Gold (Bosch, Continental, Dacia), 8 Silver, 15 Bronze. Gold primesc discount 15% si prioritate.
- **Provider gratuit:** SQLite query agregate + coloana `segment`
- **Efort:** 2h
- **Dep:** NEW5.1

#### NEW5.4 — Pipeline (Lead -> Oferta -> Contract -> Factura -> Plata) **[FEZABIL]**
- **Ce face:** Kanban vizual cu statusul fiecarui client/proiect in pipeline.
- **Exemplu concret:** Board: Lead (2 clienti noi) -> Oferta trimisa (3) -> Contract semnat (1) -> Facturat (2) -> Platit (5).
- **Provider gratuit:** SQLite tabel `crm_pipeline` + React Kanban board
- **Efort:** 4-6h
- **Dep:** NEW5.1

#### NEW5.5 — Reminder-uri Follow-Up **[FEZABIL]**
- **Ce face:** Alerte automate: client fara interactiune >30 zile, oferta trimisa fara raspuns >7 zile, factura restanta.
- **Exemplu concret:** "Continental nu a comandat nimic de 45 zile. Ultima comanda: 12 feb. Trimite email de reactivare?"
- **Provider gratuit:** APScheduler + SQLite queries
- **Efort:** 2h
- **Dep:** NEW5.1, S10.1 (Notificari)

#### NEW5.6 — Client Lifetime Value (CLV) **[FEZABIL]**
- **Ce face:** Valoare totala facturata per client, frecventa comenzi, predictie venituri viitoare.
- **Exemplu concret:** Top 5 clienti: Bosch 45.000 RON (3 ani), Continental 32.000 RON (2 ani), Dacia 28.000 RON.
- **Provider gratuit:** SQLite agregate + scipy regresie
- **Efort:** 2h
- **Dep:** NEW5.1

**Ordine recomandata:** NEW5.1 -> NEW5.3 -> NEW5.2 -> NEW5.6 -> NEW5.4 -> NEW5.5

---

## 15. Infrastructura Cross-Module

> Imbunatatiri de infrastructura care afecteaza toate modulele: securitate, performanta, mobil, AI strategy, backup, testing, UI/UX, DevOps, documentatie.

### 15A. Securitate & Privacy

#### Z1.1 — Path Traversal Sandboxing Test **[FEZABIL]**
- **Ce face:** Testare sistematica cu input malitios pe File Manager. Verificare `../../../Windows/System32`.
- **Efort:** 1h | **Dep:** Niciuna

#### Z1.2 — Validare Input-uri Toate Endpoint-urile **[FEZABIL CU EFORT MARE]**
- **Ce face:** 53 tabele = 53+ seturi campuri. Verificare Pydantic strict pe toate rutele.
- **Efort:** 6-8h | **Dep:** Niciuna

#### Z1.3 — Middleware Token Autentificare Simplu **[FEZABIL]**
- **Ce face:** Header `X-Internal-Token` pe toate endpoint-urile. Protectie daca Tailscale compromis.
- **Efort:** 2h | **Dep:** Niciuna

#### Z1.4 — Audit Secrete Hardcodate **[FEZABIL]**
- **Ce face:** Verificare nicio cheie API hardcodata in cod sau .env commituit in Git.
- **Efort:** 1h | **Dep:** Niciuna

#### Z1.5 — Fisiere Uploadate Content-Disposition **[FEZABIL]**
- **Ce face:** Fisiere executabile servite cu `attachment` nu `inline`. Previne XSS din .html uploadat.
- **Efort:** 30 min | **Dep:** Niciuna

#### Z1.6 — CORS Policy Restrictiva **[FEZABIL]** *QUICK WIN*
- **Ce face:** Verificare `allow_origins` nu contine `*` in productie.
- **Efort:** 15 min | **Dep:** Niciuna

#### Z1.7 — Rate Limiting pe Endpoint-urile AI **[FEZABIL]**
- **Ce face:** slowapi sau asyncio.Semaphore per provider. Previne epuizare cota din loop accidental.
- **Efort:** 1-2h | **Dep:** Niciuna

#### Z1.8 — Audit Dependinte Python CVE **[FEZABIL]**
- **Ce face:** `pip audit` sau `safety check` pe requirements.txt. Identifica pachete vulnerabile.
- **Efort:** 30 min | **Dep:** Niciuna

#### Z1.9 — Protectie Directory Listing **[FEZABIL]** *QUICK WIN*
- **Ce face:** Verificare FastAPI nu serveste listing directoare.
- **Efort:** 15 min | **Dep:** Niciuna

#### Z1.10 — Logging Securizat (fara date sensibile) **[FEZABIL]**
- **Ce face:** Filtru logging care mascheaza pattern-uri sensibile (chei API, CNP-uri, continut confidential).
- **Efort:** 1h | **Dep:** Niciuna

#### Z1.11 — Content Security Policy Headers **[FEZABIL]** *QUICK WIN*
- **Ce face:** CSP headers in FastAPI middleware. Previne XSS in PWA.
- **Efort:** 30 min | **Dep:** Niciuna

**Ordine:** Z1.6 -> Z1.9 -> Z1.11 -> Z1.5 -> Z1.1 -> Z1.7 -> Z1.4 -> Z1.10 -> Z1.8 -> Z1.3 -> Z1.2

### 15B. Performanta & Optimizare

#### Z2.1 — Indecsi SQLite Lipsa **[FEZABIL]** *QUICK WIN*
- **Ce face:** `CREATE INDEX` pe coloanele frecvente din WHERE, ORDER BY, JOIN. Exemplu: `idx_activity_timestamp`.
- **Efort:** 20 min | **Dep:** Niciuna

#### Z2.2 — VACUUM si ANALYZE Periodic **[FEZABIL]** *QUICK WIN*
- **Ce face:** Task saptamanal APScheduler: compactare + statistici query planner. -10-30% dimensiune DB.
- **Efort:** 30 min | **Dep:** Niciuna

#### Z2.3 — Caching In-Memory Dashboard **[FEZABIL]**
- **Ce face:** Dict Python cu TTL 60s pentru query-uri agregate lente. Reduce load pe SQLite.
- **Efort:** 1-2h | **Dep:** Z2.1

#### Z2.4 — React Lazy Loading **[FEZABIL]**
- **Ce face:** `React.lazy()` + `Suspense` pentru paginile rar accesate. -30-50% timp incarcare initiala.
- **Efort:** 1-2h | **Dep:** Niciuna

#### Z2.5 — WebSocket Connection Pooling **[FEZABIL]**
- **Ce face:** Verificare o singura conexiune persistenta per sesiune, nu reconectare la fiecare request.
- **Efort:** 1h | **Dep:** Niciuna

#### Z2.6 — Debounce pe Search Inputs **[FEZABIL]** *QUICK WIN*
- **Ce face:** Debounce 300ms pe toate campurile de cautare. -80% query-uri inutile.
- **Efort:** 30 min | **Dep:** Niciuna

#### Z2.7 — Task Queue SQLite pentru Operatii Grele **[FEZABIL CU EFORT MARE]**
- **Ce face:** Tabel `task_queue` cu status + worker asyncio. OCR batch, traduceri mari, export rapoarte.
- **Efort:** 4-6h | **Dep:** Niciuna

#### Z2.8 — Service Worker Cache Strategy **[FEZABIL]**
- **Ce face:** `NetworkFirst` pentru API, `CacheFirst` pentru assets. Previne date vechi din cache.
- **Efort:** 1-2h | **Dep:** Niciuna

#### Z2.9 — GZip Middleware **[FEZABIL]** *QUICK WIN*
- **Ce face:** O singura linie: `app.add_middleware(GZipMiddleware)`. -60-80% dimensiune raspunsuri.
- **Efort:** 5 min | **Dep:** Niciuna

#### Z2.10 — Paginare Toate Endpoint-urile **[FEZABIL]**
- **Ce face:** `limit=50, offset=0` implicit pe toate listele. Previne ingheatare UI la 10K+ records.
- **Efort:** 2-3h | **Dep:** Niciuna

#### Z2.11 — HTTP/2 Support **[FEZABIL]**
- **Ce face:** `pip install h2` + `--http h2` flag. Multiplexare request-uri pe o singura conexiune TCP.
- **Efort:** 30 min | **Dep:** Niciuna (beneficiu maxim cu HTTPS Tailscale)

**Ordine:** Z2.9 -> Z2.1 -> Z2.6 -> Z2.2 -> Z2.10 -> Z2.4 -> Z2.3 -> Z2.8 -> Z2.5 -> Z2.11 -> Z2.7

### 15C. Experienta Mobila Android-First

#### Z3.1 — Voice Input via Web Speech API **[FEZABIL]**
- **Ce face:** Buton microfon in chat AI si cautare. Chrome Android, fara cheie API.
- **Efort:** 1-2h | **Dep:** Niciuna
- **Nota:** Merge cu S2.5 — implementare unica, buton in chat + cautare

#### Z3.2 — Touch Targets 44x44px **[FEZABIL]**
- **Ce face:** `min-h-[44px] min-w-[44px]` pe butoane Calculator, Translator, ITP, File Manager.
- **Efort:** 1h | **Dep:** Niciuna

#### Z3.3 — Pull-to-Refresh **[FEZABIL]**
- **Ce face:** Reincarca date cu swipe-down pe ITP list, History, Dashboard.
- **Efort:** 1-2h | **Dep:** Niciuna

#### Z3.4 — Mod Offline Partial Extins **[FEZABIL CU EFORT MARE]**
- **Ce face:** Ultimele 50 calcule in localStorage, setari Vault criptat in IndexedDB, glosar cache local.
- **Efort:** 4-6h | **Dep:** Z2.8

#### Z3.5 — Share Sheet Nativ Android **[FEZABIL]**
- **Ce face:** `navigator.share()` pe rezultate calculator si facturi PDF. Trimitere rapida via WhatsApp/Email.
- **Efort:** 1h | **Dep:** Niciuna

#### Z3.6 — Camera Access OCR Rapid **[FEZABIL]**
- **Ce face:** `<input type="file" accept="image/*" capture="environment">` deschide camera direct.
- **Efort:** 30 min | **Dep:** Niciuna

#### Z3.7 — Swipe Gestures pe Liste **[FEZABIL]**
- **Ce face:** Swipe-left pe ITP (Delete/Edit), History (Copy price), File Manager (Download/Delete).
- **Efort:** 2h | **Dep:** Niciuna

#### Z3.8 — Fix Zoom Neintentionat pe Input-uri **[FEZABIL]** *QUICK WIN*
- **Ce face:** `font-size: 16px` pe toate campurile input. Elimina auto-zoom Android.
- **Efort:** 15 min | **Dep:** Niciuna

#### Z3.9 — Web Push Notifications Native **[FEZABIL CU EFORT MARE]**
- **Ce face:** Notificari native Android din PWA cu pywebpush.
- **Efort:** 3-4h | **Dep:** Niciuna
- **Nota:** Merge cu NEW2 (Web Push VAPID) — implementare unica

#### Z3.10 — Bottom Navigation Bar Android **[FEZABIL]**
- **Ce face:** Bara navigare jos cu 4-5 iconite pe ecrane mici. Sidebar pe desktop, bottom bar pe mobil.
- **Efort:** 2-3h | **Dep:** Niciuna

**Ordine:** Z3.8 -> Z3.2 -> Z3.6 -> Z3.5 -> Z3.1 -> Z3.10 -> Z3.3 -> Z3.7 -> Z3.9 -> Z3.4

### 15D. AI Strategy — Maximizare Cota Gratuita

#### Z4.1 — Cerebras ca Provider Primar (Viteza) **[FEZABIL]**
- **Ce face:** Cerebras 1M tok/zi, OpenAI-compatibil. Chain: Cerebras -> Gemini -> Groq -> Mistral -> SambaNova.
- **Efort:** 1-2h | **Dep:** Z4.3

#### Z4.2 — Mistral pentru Documente Mari **[FEZABIL]**
- **Ce face:** Mistral ~1B tok/luna, context window mare, dar 2 RPM. Provider specializat documente.
- **Efort:** 1-2h | **Dep:** Z4.3

#### Z4.3 — Tracking Cota per Provider Real-Time **[FEZABIL]**
- **Ce face:** Tabel `provider_usage`. Bare progres: "Cerebras: 234K / 1M azi". Alerta la 80%.
- **Efort:** 2-3h | **Dep:** Niciuna

#### Z4.4 — Rotatie Automata pe Baza Cotei (Smart Routing) **[FEZABIL]**
- **Ce face:** Provider la >90% cota -> switch automat la urmatorul. Zero interventie manuala.
- **Efort:** 2h | **Dep:** Z4.3

#### Z4.5 — Provider Diferit per Tip Task **[FEZABIL]**
- **Ce face:** Chat -> Cerebras (viteza), Traduceri -> Gemini (multilingv), Rezumat -> Mistral (context), Quality -> Groq.
- **Efort:** 2h | **Dep:** Z4.3, Z4.4

#### Z4.6 — Prompt Caching Local **[FEZABIL]** *QUICK WIN*
- **Ce face:** Dict `{hash(prompt): (response, timestamp)}` cu TTL 1 ora. -20-40% tokeni.
- **Efort:** 45 min | **Dep:** Niciuna

#### Z4.7 — LibreTranslate Self-Hosted **[FEZABIL CU EFORT MARE]**
- **Ce face:** Traduceri nelimitate EN<->RO. Calitate 70-80% vs DeepL. Pozitia 3 in chain traduceri.
- **Efort:** 3-4h | **Dep:** Niciuna
- **Nota:** Pe Windows necesita Docker sau Visual C++ Build Tools.

#### Z4.8 — Argos Translate Offline **[FEZABIL]**
- **Ce face:** Traducere 100% offline. Calitate 60-70% vs DeepL. DOAR ultimul fallback.
- **Efort:** 1-2h | **Dep:** Niciuna

#### Z4.9 — Prompt Templates per Modul **[FEZABIL]**
- **Ce face:** Template-uri optimizate per modul. Un prompt bun = -30-50% tokeni vs prompt vag.
- **Efort:** 2h | **Dep:** Niciuna

#### Z4.10 — AI Offline Fallback **[FEZABIL]**
- **Ce face:** Daca toti providerii down, functii critice (Calculator, Notepad) folosesc reguli Python locale.
- **Efort:** 2h | **Dep:** Niciuna

**Ordine:** Z4.6 -> Z4.3 -> Z4.9 -> Z4.10 -> Z4.1 -> Z4.4 -> Z4.5 -> Z4.2 -> Z4.7 -> Z4.8

### 15E. Backup, Recovery & Business Continuity

#### Z7.1 — Backup Orar (inlocuieste Litestream) **[FEZABIL]**
- **Ce face:** `backup.py` existent cu schedule orar via APScheduler. RPO 1 ora vs. 24 ore actual.
- **Efort:** 1h | **Dep:** Niciuna
- **Nota:** Litestream pe Windows e experimental. Backup orar e alternativa sigura.

#### Z7.2 — Procedura Reinstalare Completa **[FEZABIL]**
- **Ce face:** `DISASTER_RECOVERY.md` cu pasi exacti: Python, clone, pip install, restaurare DB, Tailscale, Vault.
- **Efort:** 1-2h | **Dep:** Niciuna

#### Z7.3 — Verificare Automata Backup **[FEZABIL]**
- **Ce face:** Task saptamanal: descarca backup, deschide DB, verifica date, log/alerta.
- **Efort:** 1-2h | **Dep:** Niciuna

#### Z7.4 — Backup Selectiv per Modul **[FEZABIL]**
- **Ce face:** Date critice (facturi, clienti, ITP) = backup zilnic + Drive. Date reconstructibile = saptamanal local.
- **Efort:** 1-2h | **Dep:** Niciuna

#### Z7.5 — Versionare DB cu Rollback per Tabel **[FEZABIL]**
- **Ce face:** Snapshot tabel inainte de migrare: `CREATE TABLE _backup_invoices_20260319 AS SELECT *`.
- **Efort:** 1h | **Dep:** Niciuna

#### Z7.6 — Backup Configuratii in GitHub **[FEZABIL]**
- **Ce face:** Glosar, template-uri, shortcuts -> auto-commit JSON in GitHub la fiecare modificare.
- **Efort:** 1-2h | **Dep:** Niciuna

#### Z7.7 — OneDrive ca Backup Secundar **[FEZABIL]**
- **Ce face:** 5GB gratuit OneDrive via rclone. Redundanta fata de Google Drive.
- **Efort:** 1h | **Dep:** Niciuna

#### Z7.8 — Health Check la Pornire **[FEZABIL]**
- **Ce face:** La start: `PRAGMA integrity_check`, verifica migrarile, verifica Vault. Warning daca fail.
- **Efort:** 1h | **Dep:** Niciuna

#### Z7.9 — Retentie Inteligenta Backup-uri (GFS) **[FEZABIL]**
- **Ce face:** Grandfather-Father-Son: 7 zilnice + 4 saptamanale + 3 lunare = 14 backup-uri cu acoperire buna.
- **Efort:** 1h | **Dep:** Niciuna

#### Z7.10 — Export Complet Portabil **[FEZABIL]**
- **Ce face:** Buton "Exporta tot": ZIP cu date JSON/CSV, fisiere importante, configuratii, CLAUDE.md.
- **Efort:** 2-3h | **Dep:** Niciuna

**Ordine:** Z7.8 -> Z7.9 -> Z7.5 -> Z7.1 -> Z7.3 -> Z7.2 -> Z7.4 -> Z7.6 -> Z7.10 -> Z7.7

### 15F. Testing Strategy

#### Z8.1 — Unit Tests Motorul de Preturi **[FEZABIL]**
- **Ce face:** pytest pe base_rate, word_rate, ensemble cu fisierele de referinta (26 PDF-uri).
- **Efort:** 2-3h | **Dep:** Niciuna

#### Z8.2 — Unit Tests Migration System **[FEZABIL]**
- **Ce face:** DB in memorie, ruleaza toate migrarile, verifica tabele si coloane.
- **Efort:** 1-2h | **Dep:** Niciuna

#### Z8.3 — Integration Tests Endpoint-uri Critice **[FEZABIL]**
- **Ce face:** pytest + httpx.AsyncClient pe /api/calc, /api/invoice, /api/translator, /api/itp.
- **Efort:** 3-4h | **Dep:** Z8.10

#### Z8.4 — E2E Test Playwright **[FEZABIL CU EFORT MARE]**
- **Ce face:** Flux complet: pornire -> upload PDF -> calcul pret -> generare factura -> verificare PDF pe disc.
- **Efort:** 4-6h | **Dep:** Z8.10

#### Z8.5 — Teste Regresie Bug-uri Fixate **[FEZABIL]**
- **Ce face:** Test care reproduce conditia bug-ului (ex: DOCX->PDF COM threading). Previne reaparitie.
- **Efort:** 1h per bug | **Dep:** Niciuna

#### Z8.6 — Test Automat Android via Playwright Emulare **[FEZABIL]**
- **Ce face:** Playwright viewport mobil. Detecteaza ~70% din problemele mobile (NU inlocuieste test real).
- **Efort:** 2-3h | **Dep:** Z8.4

#### Z8.7 — Coverage Report **[FEZABIL]**
- **Ce face:** `pytest --cov=backend --cov-report=html`. Tinta: 30% minim, 60% bun.
- **Efort:** 30 min | **Dep:** Z8.1 + Z8.2 + Z8.3

#### Z8.8 — GitHub Actions CI/CD **[FEZABIL]**
- **Ce face:** La fiecare git push, ruleaza automat toate testele pytest. Email daca pica.
- **Efort:** 1-2h | **Dep:** Cel putin Z8.1 sau Z8.2

#### Z8.9 — Smoke Test la Pornire **[FEZABIL]**
- **Ce face:** Script 5 secunde: backend porneste, DB raspunde, module loaded, health 200.
- **Efort:** 1h | **Dep:** Niciuna

#### Z8.10 — Test Data Fixtures **[FEZABIL]**
- **Ce face:** `tests/fixtures/` cu JSON: 5 clienti, 10 facturi, 20 ITP, 3 PDF mici.
- **Efort:** 1-2h | **Dep:** Niciuna

#### Z8.11 — Schemathesis Auto-Fuzzing **[FEZABIL]**
- **Ce face:** Genereaza automat sute de teste din OpenAPI spec. Gaseste bug-uri fara scriere manuala teste.
- **Efort:** 30 min | **Dep:** Niciuna (backend pornit)

**Ordine:** Z8.10 -> Z8.9 -> Z8.1 -> Z8.2 -> Z8.11 -> Z8.3 -> Z8.5 -> Z8.7 -> Z8.6 -> Z8.4 -> Z8.8

### 15G. UI/UX Design System

#### Z9.1 — Design Tokens Centralizati **[FEZABIL]**
- **Ce face:** `tailwind.config.js` cu `brand-primary`, `status-success`, etc. O schimbare -> tot proiectul.
- **Efort:** 1-2h | **Dep:** Niciuna

#### Z9.2 — Componenta Loading State Uniforma **[FEZABIL]**
- **Ce face:** `<LoadingState />` cu 3 variante: spinner, skeleton card, skeleton table.
- **Efort:** 1-2h | **Dep:** Z9.1

#### Z9.3 — Componenta Error State Uniforma **[FEZABIL]**
- **Ce face:** `<ErrorState message={} onRetry={} />` cu iconita, mesaj, buton "Reincearca".
- **Efort:** 1h | **Dep:** Z9.1

#### Z9.4 — Toast Notifications Standardizate **[FEZABIL]** *QUICK WIN*
- **Ce face:** Succes=verde, eroare=rosu, warning=galben, info=albastru. Durate: 3s/5s/4s/3s.
- **Efort:** 45 min | **Dep:** Niciuna

#### Z9.5 — Dark/Light Mode **[FEZABIL CU EFORT MARE]**
- **Ce face:** Toggle Dark/Light in Header. Tailwind `darkMode: 'class'` + localStorage.
- **Efort:** 3-4h | **Dep:** Z9.1

#### Z9.6 — Typography Scale Consistent **[FEZABIL]**
- **Ce face:** `text-2xl font-bold` titluri pagini, `text-lg font-semibold` sectiuni, `text-sm text-gray-400` metadata.
- **Efort:** 1h | **Dep:** Niciuna

#### Z9.7 — Spacing Standardizat Carduri **[FEZABIL]**
- **Ce face:** Componenta `<Card>` wrapper cu stiluri fixe. Inlocuieste carduri ad-hoc.
- **Efort:** 1-2h | **Dep:** Z9.1

#### Z9.8 — Empty States Ilustrate **[FEZABIL]**
- **Ce face:** `<EmptyState title="" description="" action={} />` cu ilustratie SVG pe paginile goale.
- **Efort:** 1-2h | **Dep:** Z9.7

#### Z9.9 — Keyboard Shortcuts Panel **[FEZABIL]**
- **Ce face:** Panel accesibil din Header (?) cu lista completa shortcut-uri: Ctrl+K, Ctrl+Shift+O etc.
- **Efort:** 1h | **Dep:** Niciuna

#### Z9.10 — Animatii si Tranzitii Subtile **[FEZABIL]**
- **Ce face:** `transition-all duration-200` pe butoane, `animate-fadeIn` la carduri/modale.
- **Efort:** 1h | **Dep:** Niciuna

**Ordine:** Z9.4 -> Z9.1 -> Z9.6 -> Z9.7 -> Z9.2 -> Z9.3 -> Z9.8 -> Z9.9 -> Z9.10 -> Z9.5

### 15H. DevOps & Workflow

#### Z10.1 — Git Branching Strategy **[FEZABIL]**
- **Ce face:** `main` = stabil, `feature/X` = dezvoltare. Merge --squash la finalizare.
- **Efort:** 30 min | **Dep:** Niciuna

#### Z10.2 — Pre-Commit Hooks **[FEZABIL]**
- **Ce face:** La fiecare commit: black (Python), flake8, eslint (JS). Commit refuzat daca pica.
- **Efort:** 1h | **Dep:** Niciuna

#### Z10.3 — Changelog Automat (Conventional Commits) **[FEZABIL]**
- **Ce face:** Format `feat:`, `fix:`, `docs:`. `git-cliff` genereaza CHANGELOG.md automat.
- **Efort:** 1h | **Dep:** Z10.1

#### Z10.4 — Versionare Semantica Automata **[FEZABIL]**
- **Ce face:** `bump2version` incrementeaza automat din commit messages. Tag-uri git.
- **Efort:** 1h | **Dep:** Z10.3

#### Z10.5 — Hotfix Procedure **[FEZABIL]**
- **Ce face:** Documentare pasi exacti: branch hotfix, fix, smoke test, merge, restart. Sub 15 min.
- **Efort:** 30 min | **Dep:** Z10.1

#### Z10.6 — Claude Commands Extinse **[FEZABIL]**
- **Ce face:** `/backup-now`, `/test-all`, `/health-check`, `/api-status` in `.claude/commands/`.
- **Efort:** 1-2h | **Dep:** Niciuna

#### Z10.7 — Script Setup Complet PC Nou **[FEZABIL]**
- **Ce face:** `setup_fresh.bat`: verifica Python/Node, pip install, npm install, Tesseract, Task Scheduler.
- **Efort:** 2-3h | **Dep:** Z7.2

#### Z10.8 — Environment Variables per Mediu **[FEZABIL]**
- **Ce face:** `.env.development` / `.env.production`. Debug, CORS, log level diferentiate.
- **Efort:** 1h | **Dep:** Niciuna

#### Z10.9 — Monitorizare Uptime cu Alerta **[FEZABIL]**
- **Ce face:** Health endpoint nu raspunde 30s -> mesaj Telegram automat.
- **Efort:** 1h | **Dep:** S11.9 (Telegram)

#### Z10.10 — README cu Screenshots **[FEZABIL]**
- **Ce face:** Screenshot Dashboard, Calculator, Translator + instructiuni 3 pasi.
- **Efort:** 1h | **Dep:** Niciuna

**Ordine:** Z10.8 -> Z10.6 -> Z10.1 -> Z10.2 -> Z10.9 -> Z10.7 -> Z10.5 -> Z10.3 -> Z10.4 -> Z10.10

### 15I. Documentatie Utilizator

#### Z11.1 — Manual Rapid per Modul **[FEZABIL]**
- **Ce face:** 1 pagina MD per modul: "Ce face", "3 pasi", "Erori comune".
- **Efort:** 3-4h total | **Dep:** Niciuna

#### Z11.2 — FAQ Situatii Frecvente **[FEZABIL]**
- **Ce face:** "De ce nu merge DeepL?" -> verifica cota. "De ce e lenta cautarea?" -> VACUUM.
- **Efort:** 1-2h | **Dep:** Niciuna

#### Z11.3 — Keyboard Shortcuts Cheatsheet **[FEZABIL]**
- **Ce face:** Tabel imprimabil cu toate shortcut-urile.
- **Efort:** 30 min | **Dep:** Z9.9

#### Z11.4 — Ghid Configurare API Keys **[FEZABIL]**
- **Ce face:** Pasi exacti per provider: unde te inregistrezi, unde gasesti cheia, cum adaugi in Vault.
- **Efort:** 1-2h | **Dep:** Niciuna

#### Z11.5 — Troubleshooting Guide **[FEZABIL]**
- **Ce face:** Simptom -> Cauza -> Rezolvare. Top 20 probleme.
- **Efort:** 2h | **Dep:** Niciuna

#### Z11.6 — Release Notes per Versiune **[FEZABIL]**
- **Ce face:** "Ce e nou", "Ce s-a imbunatatit", "Ce s-a rezolvat" per set functii.
- **Efort:** 30 min per release | **Dep:** Z10.3

#### Z11.7 — Ghid Backup si Restaurare (non-tehnic) **[FEZABIL]**
- **Ce face:** Termeni simpli: "Cum fac backup manual" -> buton in UI.
- **Efort:** 1h | **Dep:** Z7.10

#### Z11.8 — Ghid Android (specific mobil) **[FEZABIL]**
- **Ce face:** Instalare PWA, Tailscale, functii offline, camera OCR, partajare fisiere.
- **Efort:** 1h | **Dep:** Niciuna

#### Z11.9 — Glossar Termeni **[FEZABIL]**
- **Ce face:** MAPE, ensemble, TM, FTS5, ITP, CUI, SPV. Util la sesiuni Claude Code.
- **Efort:** 30 min | **Dep:** Niciuna

#### Z11.10 — Architecture Decision Records **[FEZABIL]**
- **Ce face:** "De ce SQLite?", "De ce Tailscale?", "De ce Python global?" Context + Decizie + Motivare.
- **Efort:** 1-2h | **Dep:** Niciuna

**Ordine:** Z11.5 -> Z11.2 -> Z11.4 -> Z11.8 -> Z11.1 -> Z11.9 -> Z11.10 -> Z11.3 -> Z11.7 -> Z11.6

### 15J. GDPR Compliance

#### NEW10 — GDPR Compliance Module **[FEZABIL]**
- **Ce face:** Right to be forgotten (stergere completa date client din toate tabelele), export date client (JSON/CSV), tracking consimtamant per client, audit trail operatii date personale.
- **Exemplu concret:** Client cere stergerea tuturor datelor. Buton "Sterge complet" -> confirmare -> sterge din invoices, calculations, crm, ITP, activity_log. Export PDF cu dovada stergerii.
- **Provider gratuit:** SQLite CASCADE DELETE + Python script audit
- **Efort:** 4-6h
- **Dep:** Niciuna

---

## 16. Analiza Generala Proiect

### 16.1 — Perspectiva Generala

Roland Command Center este un proiect ambitios si bine executat tehnic. 18 faze majore implementate in 3 zile intensive (2026-03-17 -> 2026-03-19), ceea ce arata arhitectura bine planificata si flux disciplinat.

**Puncte forte:**
- Arhitectura modulara scalabila (auto-discovery backend + manifest frontend)
- Zero cost operational — folosirea inteligenta a free tier-urilor
- Acces multi-device confirmat: `https://desktop-cjuecmn.tail7bc485.ts.net:8000`
- AI integrat in fiecare modul, nu izolat intr-un chatbot
- Disciplina documentare: CLAUDE.md, GHID_TESTARE.md, .claude/rules/ (5 fisiere auto-incarcate)
- Logging persistent: RotatingFileHandler + raportare erori frontend
- Silent launcher: START_Silent.vbs + STOP_Silent.bat
- Automatizare reguli dezvoltare: .claude/rules/ gestioneaza tracking, validare, siguranta cod

### 16.2 — Slabiciuni Identificate

#### CRITICE
| ID | Slabiciune | Status | Rezolvare |
|----|-----------|--------|-----------|
| W1 | Testare Android incompleta | NEREZOLVAT | Parcurge sistematic GHID_TESTARE.md pe dispozitiv fizic |
| W2 | DOCX->PDF depinde de Word (COM) | PARTIAL | Fix COM threading aplicat. Adauga fallback LibreOffice |
| W3 | 53 tabele SQLite fara optimizare | NEREZOLVAT | Z2.1 (indexuri) + Z2.2 (VACUUM) |

#### IMPORTANTE
| ID | Slabiciune | Status | Rezolvare |
|----|-----------|--------|-----------|
| W4 | Nu exista rollback DB | ATENUAT | backup.py exista. Adauga Z7.5 (snapshot pre-migrare) |
| W5 | Error handling frontend neuniform | NEREZOLVAT | Audit .catch() pe toate fetch()-urile |
| W6 | MAPE 32% sub tinta 25% | NEREZOLVAT | S1.1 (calibrare interactiva) |
| W7 | Gmail/Drive SMTP/IMAP nu OAuth | FUNCTIONAL | Planifica OAuth pe termen mediu (6-12 luni) |
| W8 | Notificari unificate DEFERRED | NEREZOLVAT | S10.1 — cea mai impactanta investitie UX |

#### MINORE
| ID | Slabiciune | Status | Rezolvare |
|----|-----------|--------|-----------|
| W9 | Voice Notes DEFERRED | NEREZOLVAT | S6.1 — finalizare feature |
| W10 | Dark/Light mode DEFERRED | NEREZOLVAT | Z9.5 — implementabil cu Tailwind |

### 16.3 — Sugestii Arhitecturale

| ID | Sugestie | Descriere |
|----|---------|-----------|
| A1 | Task Queue SQLite | Tabel `task_queue` pentru OCR batch, traduceri mari, export rapoarte (Z2.7) |
| A2 | Caching Layer | Dict Python cu TTL 60s pentru query-uri dashboard (Z2.3) |
| A3 | Config Module UI | Setari (MAPE target, limiti, retentie, thresholds) editabile din UI, nu hardcodate |
| A4 | Health Check Detaliat | `/api/health/detailed` cu status per modul, ultima eroare, timestamp activitate |
| A5 | Log Viewer UI | Endpoint `/api/logs` cu filtre modul/nivel/interval — S10.8 |

### 16.4 — Provider Chains Actualizate

**AI Text Generation — Free Tier Permanent (fara card bancar):**

| Provider | Cota zilnica | Cota lunara | Signup |
|----------|-------------|-------------|--------|
| Cerebras | 1.000.000 tok | ~30M tok | cloud.cerebras.ai |
| Gemini Flash | 250.000 tok | ~7.5M tok | aistudio.google.com |
| Groq | ~400.000 tok | ~12M tok | console.groq.com |
| Mistral AI | ~33M tok (2 RPM) | ~1B tok | console.mistral.ai |
| SambaNova | 200.000 tok | ~6M tok | sambanova.ai |
| Cohere | ~33 calls/zi | 1.000 calls | dashboard.cohere.com |

> **OpenAI:** Functioneaza cu credit pre-existent ($5+). Free tier nou returneaza erori. NU crea conturi noi. Daca credit se epuizeaza, OpenAI se dezactiveaza automat din chain.

**Traduceri — Free Tier Permanent:**

| Provider | Cota lunara | Card necesar |
|----------|-------------|--------------|
| Azure Translator F0 | 2.000.000 chars | Nu |
| DeepL API Free | 500.000 chars | Nu |
| Google Translate | 500.000 chars | Da (dar $300 credit initial) |
| MyMemory | 1.500.000 chars | Nu |
| LibreTranslate local | Nelimitat | Nu (Docker sau build tools) |
| Argos Translate local | Nelimitat | Nu (calitate 60-70% vs DeepL) |

**TTS — Gratuit:**

| Provider | Limita | Card necesar |
|----------|--------|--------------|
| edge-tts | Nelimitat | Nu |
| Web Speech API | Nelimitat (browser) | Nu |
| Azure TTS F0 | 5M chars/luna | Nu (dar necesita cont Azure) |

**Notificari — Gratuit (inlocuiesc SMS platit):**

| Provider | Cota | Card necesar |
|----------|------|--------------|
| Telegram Bot API | Practic nelimitat | Nu |
| Web Push (PWA) | Nelimitat | Nu |
| Discord Webhooks | 5 req/2sec | Nu |
| ntfy.sh | Nelimitat | Nu |
| Brevo Email | 9.000/luna | Nu |
| Resend.com | 3.000/luna | Nu |
| Gmail SMTP | 15.000/luna | Nu |

### 16.5 — Prioritizare Recomandata

| Prio | Actiune | Motivare | Efort |
|------|---------|---------|-------|
| 1 | **TOP 15 Quick Wins** (sectiunea de sus) | Impact imediat, efort minim | ~7-8h |
| 2 | **Testare sistematica Android** | Functii DONE dar netestate | 1-2 sesiuni |
| 3 | **Notificari Unificate (S10.1)** + **Web Push (NEW2)** | Cel mai mare impact UX | 1-2 sesiuni |
| 4 | **TTS (NEW1)** + **Voice Notes (S6.1)** | Utilitate maxima pe mobil | 1 sesiune |
| 5 | **BNR Curs Valutar (NEW3)** + **ANAF CUI (NEW4)** | Integrari API oficiale RO | 1 sesiune |
| 6 | **Calibrare MAPE (S1.1)** | Core feature sub target | 1 sesiune |
| 7 | **Status Plata Facturi (S4.3)** | Cash flow management | 1 sesiune |
| 8 | **CRM Module (NEW5)** | Client lifecycle centralizat | 2-3 sesiuni |
| 9 | **Securitate (Z1.*)** | Protectie date clienti | 2-3 sesiuni |
| 10 | **Performanta (Z2.*)** | Viteza pe Android | 2-3 sesiuni |
| 11 | **AI Strategy (Z4.*)** | +2M tokeni/zi gratuit | 1-2 sesiuni |
| 12 | **Export e-Factura (S4.11)** | Conformitate legala | 1 sesiune |
| 13 | **Testing (Z8.*)** | Stabilitate termen lung | 3-4 sesiuni |
| 14 | **Cross-Module Workflows (NEW9)** | Automatizare business | 3-5 sesiuni |
| 15 | **AI Agent Tool Use (S2.6)** | Salt calitativ major dar efort mare | 8-12 sesiuni |

### 16.6 — Concluzie

Proiectul e remarcabil ca volum si viteza. Riscul principal nu e lipsa functionalitatilor, ci **stabilitatea si testarea** celor existente. Recomandare:

1. **Testeze si stabilizezi** ce exista (mai ales Android)
2. **Quick Wins** — 15 imbunatatiri in 7-8 ore
3. **Finalizezi DEFERRED** — notificari, voice notes, TTS
4. **Integrari RO** — BNR, ANAF CUI (gratuit, valoare imediata)
5. **CRM** — centralizezi datele client dispersate
6. **Adaugi functionalitati noi** in ordinea prioritatilor

**Total itemi roadmap:** ~210 (130 module + 80 infrastructura)
**Itemi [FEZABIL]:** ~180 | **[FEZABIL CU EFORT MARE]:** ~25 | **[EXCLUDE/ELIMINAT]:** ~5
**Quick Wins (sub 2h):** 15 itemi
**Conditie:** 100% GRATUIT — nicio functie nu necesita abonament sau plata

---

*Document generat: 2026-03-20*
*Surse: SUGESTII_SI_ANALIZA_COMMAND_CENTER_V2.md + 12_ZONE_IMBUNATATIRE_GRATUITE_V2.md + 10 functii noi*
*Conditie: 100% gratuit — nicio functie necesita abonament sau plata*
*Stack: FastAPI Python 3.13 + React 18 + SQLite + Tailscale HTTPS*
*Provideri platiti eliminati: e-Factura certSIGN, e-Signature, Perplexity, OpenAI (din chain-uri noi), Whisper OpenAI, SMS Romania, PaddleOCR, Coqui TTS, Piper TTS*
