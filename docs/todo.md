# TODO — Roland Command Center

Ultima actualizare: 2026-03-23

---

## 1. ACTIUNI MANUALE ROLAND (necesita input/configurare de la tine)

### 1.1 Gmail App Password

**Ce este:** O parola speciala de 16 caractere generata de Google, necesara pentru ca aplicatia sa citeasca si sa trimita email-uri prin contul tau Gmail (IMAP/SMTP). Este diferita de parola contului Google.

**De ce trebuie:** Fara ea, modulul Integrations > Gmail nu functioneaza (citire inbox, trimitere facturi pe email, notificari email).

**Pasi de executie:**
1. Deschide https://myaccount.google.com/security
2. Activeaza **2-Step Verification** (daca nu e deja activa)
3. Dupa activare, mergi la https://myaccount.google.com/apppasswords
4. Selecteaza "Mail" ca aplicatie si "Windows Computer" ca dispozitiv
5. Apasa "Generate" — vei primi o parola de 16 caractere (ex: `abcd efgh ijkl mnop`)
6. Copiaza parola (fara spatii)

**Cum o integrezi in aplicatie:**
- Deschide fisierul `backend/.env`
- Gaseste linia: `# GMAIL_APP_PASSWORD=`
- Inlocuieste cu: `GMAIL_APP_PASSWORD=abcdefghijklmnop` (parola ta reala, fara spatii)
- Salveaza fisierul
- Reporneste backend-ul (START_Roland.bat stop, apoi START_Roland.bat)

**Verificare:** Dupa repornire, deschide aplicatia > Integrations > Gmail > apasa "Sync Inbox". Daca vezi email-uri = functioneaza.

---

### 1.2 Date ITP — Import inspectii existente

**Ce este:** Importul datelor despre inspectiile ITP efectuate pana acum (vehicule, rezultate, date) in baza de date a aplicatiei.

**De ce trebuie:** Fara date reale, modulul ITP arata 0 inspectii, 0 statistici, 0 alerte expirare. Toate graficele si rapoartele sunt goale.

**Format necesar (CSV):**
```csv
plate,vin,vehicle_type,make,model,year,result,date,inspector_name,expiry_date
AR-01-ABC,WVWZZZ3CZWE123456,autoturism,Volkswagen,Golf,2019,ADMIS,2026-01-15,Petrila Roland,2027-01-15
AR-02-XYZ,WBAPH5C55BA123789,autoturism,BMW,320d,2018,RESPINS,2026-02-20,Petrila Roland,
```

**Campuri:**
- `plate` — numar inmatriculare (ex: AR-01-ABC)
- `vin` — serie sasiu 17 caractere (optional dar recomandat)
- `vehicle_type` — autoturism, autoutilitara, motocicleta, remorca
- `make` — marca (Volkswagen, BMW, Dacia etc.)
- `model` — model (Golf, 320d, Logan)
- `year` — anul fabricatiei
- `result` — ADMIS sau RESPINS
- `date` — data inspectiei (YYYY-MM-DD)
- `inspector_name` — numele inspectorului
- `expiry_date` — data expirare ITP (YYYY-MM-DD), gol daca RESPINS

**Pasi de executie:**
1. Deschide Excel sau Google Sheets
2. Creeaza coloanele de mai sus
3. Completeaza cu inspectiile din ultimele 12 luni (sau cat ai disponibil)
4. Salveaza ca CSV (File > Save As > CSV UTF-8)
5. In aplicatie: ITP > Import > Upload CSV
6. Sau prin API direct: `curl -X POST http://localhost:8000/api/itp/import -F "file=@inspectii.csv"`

**Verificare:** Dupa import, pagina ITP trebuie sa arate inspectiile, Dashboard > "Ziua mea" va afisa alerte expirare, iar Reports va avea date pentru grafice.

---

### 1.3 Clienti si Facturi — Adaugare date reale

**Ce este:** Popularea bazei de date cu clientii reali si facturile emise.

**De ce trebuie:** Revenue reports, payment tracking, recurring invoices — toate depind de date reale. Dashboard arata revenue = 0 RON fara facturi.

**Metoda 1 — Manual din aplicatie (recomandat pentru inceput):**
1. Deschide aplicatia > Facturare > Clienti > Adauga Client
2. Completeaza CUI-ul clientului — butonul "ANAF Auto-fill" va completa automat: denumire, adresa, J-nr, atribut fiscal
3. Salveaza clientul
4. Mergi la Facturare > Factura Noua > selecteaza clientul > adauga servicii > Salveaza > Genereaza PDF
5. Repeta pentru fiecare client activ

**Metoda 2 — Import CSV (pentru volum mare):**
```csv
name,cui,reg_com,address,email,phone,bank,iban
SC Exemplu SRL,12345678,J02/123/2020,Str Exemplu 1 Arad,contact@exemplu.ro,0722123456,BT,RO49AAAA1B31007593840000
```
Import: `curl -X POST http://localhost:8000/api/invoices/clients/import -F "file=@clienti.csv"`

**Exemple tipice de servicii facturate:**
- Traducere tehnica EN-RO, 5000 cuvinte, 0.06 RON/cuvant = 300 RON
- Inspectie tehnica periodica autoturism = 150 RON
- Traducere legalizata acte auto = 100 RON

**Verificare:** Dashboard > Revenue card arata suma totala. Reports > Revenue by Client arata breakdown per client.

---

### 1.4 Test Android — Verificare acces de pe telefon

**Ce este:** Testarea aplicatiei pe telefonul Android prin reteaua Tailscale.

**De ce trebuie:** PWA + responsive CSS sunt implementate dar netestete pe device real. Butoanele pot fi prea mici, layout-ul poate fi stricat pe ecran mic.

**Pasi de executie:**
1. Asigura-te ca Tailscale e instalat SI CONECTAT pe ambele dispozitive (PC + telefon)
2. Pe PC, porneste aplicatia cu `START_Roland.bat`
3. Pe telefon, deschide Chrome si acceseaza: `https://desktop-cjuecmn.tail7bc485.ts.net:8000`
   - IMPORTANT: **https** (nu http), **hostname** (nu IP numeric)
   - Daca cere certificat: Accept / Continue
4. Testeaza fiecare pagina: Dashboard, Calculator, Translator, ITP, Facturare, AI Chat
5. Verifica:
   - Sidebar se deschide/inchide cu buton hamburger?
   - Butoanele sunt suficient de mari pentru deget?
   - Textul e lizibil fara zoom?
   - Formularele functioneaza (tastatura apare, campuri se completeaza)?
   - PDF-urile se descarca?

**Daca nu merge:**
- Verifica Tailscale e "Connected" pe ambele dispozitive
- Verifica ca backend-ul ruleaza pe PC (http://localhost:8000/api/health pe PC)
- Incearca si varianta: `https://100.80.18.55:8000` (IP Tailscale al PC-ului)

**Raportare bug-uri:** Noteaza pagina, ce ai apasat, ce s-a intamplat vs ce te asteptai. Screenshot e ideal.

---

### 1.5 Telegram Chat ID — Configurare notificari

**Ce este:** ID-ul numeric al chat-ului Telegram unde bot-ul trimite notificari (alerte ITP, facturi scadente, backup status).

**De ce trebuie:** Bot-ul este creat (@ris_notif_bot) dar nu stie UNDE sa trimita mesajele. Chat ID-ul `@ris_notif_bot` din .env este username-ul botului, nu un chat ID valid.

**Pasi de executie:**
1. Deschide Telegram pe telefon
2. Cauta bot-ul `@ris_notif_bot` si apasa Start
3. Trimite orice mesaj (ex: "test")
4. Deschide in browser: `https://api.telegram.org/bot8522792443:AAGWhKoGezRp1RXHLp65hJBm8HTz7oaE7FA/getUpdates`
5. In raspunsul JSON, cauta `"chat":{"id": 123456789}` — numarul acela e Chat ID-ul tau
6. Deschide `backend/.env`
7. Inlocuieste `TELEGRAM_CHAT_ID=@ris_notif_bot` cu `TELEGRAM_CHAT_ID=123456789` (numarul real)
8. Reporneste backend-ul

**Verificare:** `curl http://localhost:8000/api/health` — daca Telegram e configurat corect, poti testa cu:
```bash
curl -X POST "https://api.telegram.org/bot8522792443:AAGWhKoGezRp1RXHLp65hJBm8HTz7oaE7FA/sendMessage" -d "chat_id=CHAT_ID_TAU&text=Test notificare Roland"
```
Ar trebui sa primesti mesajul pe Telegram.

---

## 2. IMPLEMENTARI COD (le face Claude la cerere)

### 2.1 AXA B — Imbunatatire Acuratete Pricing (MAPE 32% -> sub 15%)

**Ce este:** Calculatorul de pret traduceri estimeaza pretul unui document bazat pe complexitate, numar cuvinte, limba, domeniu. Acum are o eroare medie de 32% (MAPE), ceea ce inseamna ca pretul estimat difera cu ~32% de pretul real.

**De ce conteaza:** Daca pretul e prea mare, pierzi clienti. Daca e prea mic, pierzi bani. Sub 15% MAPE = utilizabil in practica.

**Ce trebuie facut:**
1. **Colectare date reale** — Ai nevoie de minimum 50-100 de perechi (document, pret facturat real). Cu cat mai multe, cu atat mai bine. Acum sunt doar 26 fisiere in `Fisiere_Reper_Tarif/`.
2. **Feedback loop** — Dupa fiecare factura emisa, sistemul compara pretul calculat cu pretul facturat si invata din diferenta.
3. **Dashboard metrici** — Grafic cu MAPE trend, cele mai mari abateri, acuratete per tip document.

**Cum pregatesti datele:** Creeaza un folder cu documente traduse + un CSV:
```csv
filename,price_ron,word_count,language_pair,domain
contract_vanzare.pdf,450,3200,EN-RO,juridic
manual_tehnic.docx,1200,8500,EN-RO,tehnic
certificat_nastere.pdf,80,350,RO-EN,acte_civile
```
Pune fisierele in `Fisiere_Reper_Tarif/` si CSV-ul alaturi. Cu cat mai multe exemple din ultimele 6-12 luni, cu atat calibrarea va fi mai precisa.

**Cand:** Dupa ce ai adunat minimum 50 de perechi document-pret. Spune-i lui Claude "implementeaza AXA B" si furnizeaza locatia datelor.

---

### 2.2 AXA F — Polish Mobile / Responsive

**Ce este:** Optimizarea interfetei pentru ecran de telefon — butoane mai mari, layout adaptat, touch-friendly.

**De ce conteaza:** Aplicatia e accesibila pe telefon prin Tailscale dar unele elemente pot fi greu de apasat sau textul prea mic.

**Ce trebuie facut:** Dupa testarea Android (punctul 1.4), noteaza toate problemele gasite. Claude le va fixa pe toate intr-o singura sesiune.

**Cand:** Dupa ce testezi pe Android si ai o lista de probleme concrete.

---

### 2.3 Telegram Notificari Active

**Ce este:** Trimiterea automata de alerte pe Telegram: inspectii ITP care expira, facturi scadente, backup status.

**De ce conteaza:** Primesti pe telefon notificari importante fara sa deschizi aplicatia.

**Ce trebuie facut:** Dupa configurarea Chat ID-ului (punctul 1.5), Claude va implementa:
- Alert dimineata (08:00): rezumat zi — inspectii programate, facturi scadente
- Alert la backup reusit/esuat (02:00)
- Alert la ITP care expira in 7 zile

**Cand:** Dupa ce ai configurat Chat ID-ul real.

---

### 2.4 Fix 3 Teste Pre-existente

**Ce este:** 3 teste automatizate care esueaza din motive independente de ultimele modificari.

**Detalii:**
- `test_filemanager_search` — MemoryError la FTS5 fulltext pe fisiere mari
- `test_translate_en_ro` — depinde de API extern (DeepL), esueaza fara internet/cheie valida
- `test_vault_key_get_nonexistent` — logica de autentificare vault nu returneaza 404 corect

**Impact:** Minor. Celelalte 83 teste trec. Aceste 3 nu afecteaza functionalitatea.

**Cand:** Oricand, prioritate scazuta. Spune "fix cele 3 teste esuate".

---

## 3. CONFIGURARI OPTIONALE (nice-to-have, nu critice)

### 3.1 Google Drive Integration

**Ce este:** Conectarea la Google Drive pentru backup automat si acces la fisiere din cloud.

**Cerinte:** OAuth 2.0 credentials de la Google Cloud Console (proiect gratuit).

**Pasi:**
1. Mergi la https://console.cloud.google.com/
2. Creeaza proiect nou (sau foloseste unul existent)
3. Enable "Google Drive API"
4. Credentials > Create OAuth 2.0 Client ID > Desktop App
5. Descarca JSON-ul cu credentials
6. Pune-l in `backend/certs/gdrive_credentials.json`

**Nota:** Backup-ul local SQLite functioneaza deja fara Drive. Drive e doar pentru copie off-site suplimentara.

---

### 3.2 Google Calendar Integration

**Ce este:** Sincronizare programari ITP cu Google Calendar.

**Cerinte:** Acelasi OAuth setup ca la Drive, dar cu "Google Calendar API" enabled.

**Beneficiu:** Programarile ITP apar automat in calendarul Google de pe telefon.

---

### 3.3 GitHub Integration

**Ce este:** Vizualizare commits, issues, PR-uri din aplicatie.

**Cerinte:** Personal Access Token de la https://github.com/settings/tokens (scope: repo).

**Nota:** Util doar daca lucrezi activ cu repo-ul. Nu e necesar pentru functionarea aplicatiei.

---

### 3.4 OCR.space Cloud (backup OCR)

**Ce este:** Serviciu cloud OCR ca fallback pentru Tesseract local.

**Cerinte:** API key gratuit de la https://ocr.space/ocrapi (500 req/zi).

**Cand:** Doar daca Tesseract local nu recunoaste bine textul din anumite documente.

---

## 4. STATUS CURENT PROIECT

| Modul | Status | Observatii |
|-------|--------|------------|
| Dashboard | 90% | "Ziua mea" implementat, depinde de date reale |
| Calculator Pret | 75% | MAPE 32% — necesita calibrare cu date reale (AXA B) |
| Translator | 85% | Functional cu DeepL + Azure + Google + Gemini |
| AI Chat | 75% | Functional cu Gemini + Cerebras + Groq + Mistral |
| Facturare | 90% | PDF corect, recurring, payments, export — necesita clienti reali |
| ITP | 85% | Workflow complet — necesita import date reale |
| Quick Tools | 80% | BNR, ANAF, Notepad, Calculator, QR — toate functionale |
| Convertor | 75% | Depinde de LibreOffice pentru DOCX->PDF |
| File Manager | 80% | Upload, FTS5, tags, favorites, auto-organize |
| Automations | 70% | Cron scheduler functional, backup zilnic programat |
| Integrations | 40% | Necesita OAuth real (Gmail, Drive, Calendar) |
| Reports | 75% | Functional dar date goale fara facturi/ITP reale |
| Vault | 90% | Securitate solida, session tokens, backup, expiry |
| Barcode/Passwords | 80% | Functional, niche usage |

**Total endpoints:** 360+ | **Total teste:** 86 | **Module:** 14 | **Pagini:** 25

---

## 5. INDICATORI DE URMARIT

| Indicator | Acum | Target | Ce masoara |
|-----------|------|--------|------------|
| MAPE Pricing | 32% | sub 15% | Acuratete calculator pret traduceri |
| Date Reale | ~5% | 80%+ | Cat din datele reale sunt importate |
| Backup RPO | 24h (automat) | 24h | Recovery Point Objective — backup zilnic la 02:00 |
| Teste Business | 86 | 120+ | Acoperire teste automate pe fluxuri reale |
| API Keys Active | 6/10 | 8+ | Cate integrari sunt real functionale |
| Mobile Usability | Netestat | 90%+ | Pagini principale functionale pe Android |

---

## 6. ORDINE RECOMANDATA DE EXECUTIE

| Prioritate | Task | Efort | Cine |
|------------|------|-------|------|
| 1 | Telegram Chat ID (1.5) | 5 min | Roland |
| 2 | Gmail App Password (1.1) | 10 min | Roland |
| 3 | Test Android (1.4) | 30 min | Roland |
| 4 | AXA F — Mobile fix (2.2) | 2-3h | Claude (dupa teste Android) |
| 5 | Import clienti reali (1.3) | 30-60 min | Roland |
| 6 | Import ITP date (1.2) | 1-2h | Roland (pregatire CSV) |
| 7 | Telegram notificari (2.3) | 1h | Claude (dupa Chat ID) |
| 8 | Colectare date pricing (2.1) | 2-3h | Roland (pregatire fisiere) |
| 9 | AXA B — Calibrare pricing | 3-4h | Claude (dupa date) |
| 10 | Configurari optionale (3.x) | variabil | Roland + Claude |

---

## 7. COMENZI RAPIDE

```bash
# Pornire aplicatie
START_Roland.bat

# Oprire aplicatie
START_Roland.bat stop

# Rebuild frontend + pornire
START_Roland.bat build

# Backup manual baza de date
curl -X POST http://localhost:8000/api/reports/backup

# Verificare integritate DB
curl http://localhost:8000/api/reports/db-integrity

# Export date critice JSON
curl http://localhost:8000/api/reports/export/critical-json -o backup_data.json

# Rulare teste
cd backend && python -m pytest tests/ -v

# Verificare health
curl http://localhost:8000/api/health
```
