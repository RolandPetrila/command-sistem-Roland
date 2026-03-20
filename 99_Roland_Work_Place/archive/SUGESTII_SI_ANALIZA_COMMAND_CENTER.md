# Roland Command Center — Sugestii Funcționalități & Analiză Proiect

> **Generat:** 2026-03-19  
> **Scop:** Document de referință pentru sesiunile Claude Code — sugestii noi funcționalități per modul + analiză arhitecturală sinceră.  
> **Instrucțiuni pentru Claude Code:** Analizează fiecare sugestie din perspectiva stack-ului existent (FastAPI + React 18 + SQLite + arhitectura modulară din `backend/modules/` + `frontend/src/modules/`). Marchează fiecare item ca [FEZABIL], [FEZABIL CU EFORT MARE], sau [NEFEZABIL/EXCLUD] cu justificare scurtă. Prioritizează pe baza valorii pentru CIP Inspection SRL (ITP auto + traduceri tehnice, single-user Roland).

---

## CUPRINS

1. [Modul: Calculator Preț Traduceri](#1-modul-calculator-preț-traduceri)
2. [Modul: AI Chat & Documente](#2-modul-ai-chat--documente)
3. [Modul: Traducător](#3-modul-traducător)
4. [Modul: Facturare (Invoice)](#4-modul-facturare-invoice)
5. [Modul: ITP Inspecții Auto](#5-modul-itp-inspecții-auto)
6. [Modul: Quick Tools](#6-modul-quick-tools)
7. [Modul: Convertor Fișiere](#7-modul-convertor-fișiere)
8. [Modul: File Manager](#8-modul-file-manager)
9. [Modul: Vault (API Keys)](#9-modul-vault-api-keys)
10. [Modul: Automatizări](#10-modul-automatizări)
11. [Modul: Integrări Externe](#11-modul-integrări-externe)
12. [Modul: Rapoarte & Statistici](#12-modul-rapoarte--statistici)
13. [Modul: Quick Tools Extra](#13-modul-quick-tools-extra)
14. [Analiză Generală Proiect](#14-analiză-generală-proiect)

---

## 1. Modul: Calculator Preț Traduceri

> **Status actual:** Ensemble 3 metode (base_rate, word_rate, KNN), MAPE 32%, dashboard competitori, AI explicație preț, 26 PDF-uri referință.

### S1.1 — Calibrare MAPE Interactivă în UI
**Descriere:** Panou vizual unde poți ajusta manual ponderile celor 3 metode (base_rate, word_rate, KNN) cu slidere, iar MAPE se recalculează instant pe setul de date istorice.  
**Exemplu:** Muți sliderul KNN de la 33% la 50%, graficul arată imediat că MAPE scade de la 32% la 27%. Dai save și noile ponderi sunt active.  
**Valoare:** Directă — te ajută să atingi ținta sub 25% MAPE fără să rulezi `calibrate.py` din terminal.

### S1.2 — Istoric Calcule cu Căutare și Filtre
**Descriere:** Tabel paginat cu toate calculele anterioare, filtrabil după: client, pereche de limbi, tip document, interval preț, dată. Export CSV.  
**Exemplu:** Cauți toate calculele pentru clientul "Dacia" din ultimele 6 luni — vezi că prețul mediu a fost 450 RON și poți vedea cum a evoluat.  
**Valoare:** Medie-mare — util pentru negocieri cu clienți recurenți.

### S1.3 — Template-uri de Calcul per Client
**Descriere:** Salvezi profilul unui client (pereche de limbi preferată, tip document obișnuit, reducere acordată, termen de plată). La calcul nou, selectezi clientul și câmpurile se pre-completează.  
**Exemplu:** Clientul "Bosch Romania" cere mereu traduceri tehnice EN→RO, 15% reducere fideltate. Selectezi din dropdown și calculul pornește cu aceste setări.  
**Valoare:** Mare — economisești timp la clienți recurenți.

### S1.4 — Calcul Batch pentru Mai Multe Fișiere Simultan
**Descriere:** Încarci 5-10 fișiere deodată, calculatorul rulează pe fiecare și returnează un tabel sumar cu prețuri individuale + total.  
**Exemplu:** Un client trimite un pachet de 8 documente tehnice. Le încarci pe toate, primești tabel cu preț per fișier și total lot: 3.240 RON.  
**Valoare:** Mare — util pentru proiecte mari, economisește 10-15 min per calcul batch.

### S1.5 — Comparare Două Calcule Side-by-Side
**Descriere:** Selectezi 2 calcule din istoric și le afișezi în paralel: features, preț, metodă dominantă, diferență procentuală.  
**Exemplu:** Compari calculul pentru un manual tehnic auto de 50 pagini din 2025 vs. unul similar din 2024 — observi că prețul a crescut cu 8% datorită ajustării ratelor.  
**Valoare:** Medie — util pentru analize și justificarea creșterilor de tarif.

### S1.6 — Notă de Ofertă PDF Automată din Calcul
**Descriere:** Buton "Generează Ofertă" după calcul — produce un PDF profesional cu: antet CIP Inspection, detalii document, prețul calculat, termen de livrare, valabilitate ofertă 30 zile.  
**Exemplu:** Calculezi prețul, dai "Generează Ofertă", primești un PDF gata de trimis pe email clientului — fără Word, fără editare manuală.  
**Valoare:** Foarte mare — automatizează un pas manual care durează 10-15 min.

### S1.7 — Alertă Prețuri Neactualizate
**Descriere:** Sistem de avertizare dacă fișierele de referință tarifară (cele 26 PDF-uri) nu au fost actualizate de mai mult de X luni configurabil.  
**Exemplu:** La 6 luni de la ultima actualizare, apare un banner galben: "Tarifele de referință pot fi depășite — ultima actualizare: 2025-09-15". Dai click și ești dus direct la File Manager → folder referință.  
**Valoare:** Medie — previne calcule eronate bazate pe tarife vechi.

### S1.8 — Grafic Evoluție Prețuri Proprii vs. Piață (Trend)
**Descriere:** Grafic temporal (line chart Recharts) cu evoluția prețului tău mediu per pagină în timp, suprapus cu min/max piață din fișierul Competitori.  
**Exemplu:** Graficul arată că în Q4 2025 prețul tău mediu era cu 12% sub media pieței — indiciu că poți crește tarifele fără să pierzi clienți.  
**Valoare:** Mare — date pentru decizii de business.

### S1.9 — Câmp "Urgență" cu Suprataxă Automată
**Descriere:** Checkbox "Traducere urgentă (24h)" care aplică automat o suprataxă configurabilă (ex: +30%) la prețul calculat, cu mențiune în ofertă/factură.  
**Exemplu:** Client sună că are nevoie de traducere contractului până mâine dimineață. Bifezi "Urgență 24h", prețul devine 650 RON în loc de 500 RON, cu notă explicativă în PDF.  
**Valoare:** Mare — monetizează urgențele care acum poate nu sunt taxate explicit.

### S1.10 — Export Raport Lunar Calculator
**Descriere:** Raport automat lunar: număr calcule efectuate, valoare totală estimată (sumă prețuri calculate), clienți noi vs. recurenți, metodă dominantă, MAPE curent.  
**Exemplu:** La 1 martie primești emailul automat: "Februarie 2026: 43 calcule, valoare totală estimată 18.500 RON, 5 clienți noi, MAPE: 29%."  
**Valoare:** Medie — overview business fără să deschizi aplicația.

---

## 2. Modul: AI Chat & Documente

> **Status actual:** Chat SSE streaming (Gemini→OpenAI→Groq), 6 endpoint-uri documente, OCR+AI, 10 API keys, evaluare calitate traducere, provider selector, token indicator, context-aware cu date din DB.

### S2.1 — Sesiuni Chat cu Titlu Auto-Generat și Organizare pe Categorii
**Status implementare:** ⚠️ Sesiunile persistente (SQLite CRUD) sunt **deja implementate** în Faza 15A. Această sugestie se referă la îmbunătățiri suplimentare ale funcției existente.  
**Descriere:** Extinde sesiunile existente cu: titlu auto-generat de AI din primele mesaje, organizare pe categorii (Traduceri / Facturare / ITP / General), pin la favorite, arhivare sesiuni vechi.  
**Exemplu:** Sesiunile apar grupate: "📁 Traduceri (12 sesiuni)", "📁 ITP (5 sesiuni)". Pinezi sesiunea "Analiza Contract Bosch 2026" pentru acces rapid. Arhivezi tot ce e mai vechi de 3 luni.  
**Valoare:** Medie — fundația există, organizarea lipsește.

### S2.2 — Prompt Templates cu Variabile Editabile
**Descriere:** Librărie de prompturi predefinite cu variabile `{{document}}`, `{{client}}`, `{{suma}}`. Selectezi template-ul, completezi variabilele, trimiți.  
**Exemplu:** Template "Generează email ofertă": "Bună ziua {{client}}, vă transmitem oferta pentru traducerea documentului {{document}} în valoare de {{suma}} RON, cu livrare în {{termen}} zile lucrătoare."  
**Valoare:** Foarte mare — elimină rescrierea acelorași prompturi de zeci de ori.

### S2.3 — Mod "Lucrează pe Document" — AI cu Fișier Atașat Persistent
**Descriere:** Încarci un document (PDF/DOCX) care rămâne "activ" pe toată durata sesiunii. Poți pune mai multe întrebări despre el fără să îl re-încarci.  
**Exemplu:** Încarci un contract de 30 pagini. Întrebi: "Care sunt clauzele de penalitate?" → "Există termen de exclusivitate?" → "Rezumă obligațiile furnizorului". Documentul rămâne în context toată conversația.  
**Valoare:** Foarte mare — actualemnte fiecare întrebare pe document necesită probabil re-upload.

### S2.4 — Comparare Răspunsuri Multi-Provider (Side-by-Side)
**Descriere:** Trimiți același prompt la 2-3 provideri simultan și răspunsurile apar în coloane paralele cu timp de răspuns și token count per provider.  
**Exemplu:** Trimiți aceeași traducere la Gemini, OpenAI și Groq. Compari calitatea celor 3 variante și alegi cea mai bună — fără să copiezi/lipești între taburi.  
**Valoare:** Mare pentru traduceri și texte unde calitatea contează.

### S2.5 — Voice Input (Speech-to-Text) via Web Speech API
**Descriere:** Buton microfon în chat — vorbești, textul apare automat în câmpul de input. Folosește Web Speech API (gratuit, offline, în browser).  
**Exemplu:** Ești în mașină sau ai mâinile ocupate. Apeși microfon: "Generează o ofertă pentru traducerea unui manual tehnic auto de 80 de pagini din engleză în română." Textul apare scris, trimiți.  
**Valoare:** Mare pentru utilizarea pe Android/telefon — exact cazul tău.

### S2.6 — AI Agent cu Acces la Module (Tool Use)
**Descriere:** AI poate executa acțiuni în aplicație: calculează un preț, caută în documente, creează o factură, adaugă o notă — pe baza unui prompt natural.  
**Exemplu:** "Calculează prețul pentru fișierul contract_dacia.pdf și creează o factură pentru clientul Dacia cu prețul rezultat." AI execută pașii automat, tu confirmi la final.  
**Valoare:** Foarte mare — salt calitativ față de un simplu chatbot.

### S2.7 — Perplexity Integration pentru Căutare cu Citări
**Descriere:** Ai deja Perplexity API în resurse (neutilizat). Adaugi un buton/comandă `/search` în chat — Perplexity răspunde cu informații actuale + surse citate.  
**Exemplu:** `/search tarife traduceri tehnice auto Romania 2026` — Perplexity returnează prețuri actuale de pe piață cu linkuri la surse. Nu mai cauți manual pe Google.  
**Valoare:** Mare — completează AI-ul generativ cu informații live și verificate.

### S2.8 — AI Batch Processing pe Folder
**Descriere:** Selectezi un folder din File Manager și un prompt template — AI procesează toate documentele pe rând și salvează rezultatele (rezumat/extragere/clasificare) per fișier.  
**Exemplu:** Selectezi folderul "Contracte 2025" cu 40 PDF-uri + prompt "Extrage: client, valoare contract, dată semnare, termen". Primești un tabel Excel cu datele extrase din toate contractele.  
**Valoare:** Foarte mare — automatizează ore de muncă manuală.

### S2.9 — Sistem Feedback pe Răspunsuri AI (Thumbs + Notă)
**Descriere:** Butoane thumbs up/down pe fiecare răspuns AI, opțional o notă scurtă. Datele se salvează în SQLite și generează statistici: ce tip de prompturi dau răspunsuri bune per provider.  
**Exemplu:** Gemini dă un răspuns slab la o traducere tehnică. Dai thumbs down + notă "terminologie auto incorectă". Peste timp, statisticile arată că Gemini performează slab pe texte tehnice auto → treci OpenAI pe prima poziție pentru acel tip.  
**Valoare:** Medie — îmbunătățire continuă a calității prin date reale.

### S2.10 — Export Conversație ca Document (PDF/DOCX/MD)
**Descriere:** Buton "Exportă conversație" — generează un document formatat cu toată sesiunea de chat: prompt-uri, răspunsuri, timestamp-uri, provider folosit.  
**Exemplu:** Ai avut o sesiune de 2 ore cu AI pentru analiza unui contract complex. Exportezi ca PDF și îl arhivezi împreună cu contractul — documentație completă a analizei.  
**Valoare:** Medie — util pentru arhivare și trimitere către terți.

---

## 3. Modul: Traducător

> **Status actual:** 5 provideri (DeepL→Azure→Google→Gemini→OpenAI), Translation Memory FTS5, glosar tehnic CRUD, traducere fișiere PDF/DOCX, detecție limbă, tracking chars DeepL, istoric.

### S3.1 — Glosar Tehnic per Client
**Descriere:** Poți crea glosare separate per client (nu doar per domeniu). Când traduci pentru un client specific, se aplică automat glosarul lui — terminologia preferată de acel client.  
**Exemplu:** Clientul "Continental" preferă "unitate de control" în loc de "ECU", "frână de mână electrică" în loc de "EPB". Glosarul "Continental" se activează automat când selectezi clientul.  
**Valoare:** Mare — calitate superioară și consistență pentru clienți recurenți.

### S3.2 — Memorie de Traducere cu Vizualizare și Editare
**Descriere:** Interfață vizuală pentru Translation Memory: poți vedea toate segmentele salvate, le poți edita/șterge manual, poți importa/exporta TM în format TMX (standard industrie).  
**Exemplu:** Observi că TM are salvat o traducere greșită: "airbag lateral" → "pernă laterală" (prea formal). O editezi direct la "airbag lateral" → "airbag de parte". Toate traducerile viitoare vor folosi varianta corectă.  
**Valoare:** Mare — TM-ul este un activ valoros care crește în timp, trebuie să poți îl îngriji.

### S3.3 — Traducere cu Păstrare Formatare Avansată (DOCX Stiluri)
**Descriere:** La traducerea DOCX, păstrează nu doar textul ci și stilurile Word (heading-uri, bold, italic, tabele, liste, note de subsol), nu doar textul brut.  
**Exemplu:** Traduci un manual tehnic cu Heading 1, Heading 2, tabele cu specificații, note de subsol. Documentul tradus are exact aceeași structură vizuală — nu e un text flat fără formatare.  
**Valoare:** Foarte mare — diferența între un produs finit și unul care mai necesită 2 ore de reformatare.

### S3.4 — Mod Revizuire Traducere (Track Changes)
**Descriere:** Interfață cu 3 coloane: original | traducere AI | traducerea ta revizuită. Modifici în coloana 3, sistemul trackează exact ce ai schimbat față de propunerea AI.  
**Exemplu:** AI traduce "engine control unit" → "unitate motor control". Tu corectezi în "unitate de comandă motor". Sistemul marchează modificarea și o poate adăuga automat în TM sau Glosar.  
**Valoare:** Foarte mare — flux de lucru profesional CAT (Computer-Assisted Translation).

### S3.5 — Statistici Utilizare DeepL cu Prognoză
**Descriere:** Dashboard cu: caractere DeepL consumate luna aceasta, caractere rămase, prognoză dată epuizare cotă pe baza ritmului actual, grafic consum zilnic.  
**Exemplu:** Ai 500.000 chars/lună. Astăzi e 19 martie și ai consumat 380.000. Sistemul avertizează: "La ritmul actual, cota se epuizează pe 23 martie — mai sunt 4 zile. Consideră trecerea pe Azure Translator pentru restul lunii."  
**Valoare:** Mare — eviți surpriza că DeepL nu mai funcționează la mijlocul unui proiect.

### S3.6 — Proiecte de Traducere cu Status
**Descriere:** Grupezi mai multe fișiere dintr-un proiect (ex: "Manual Ford Focus 2026 — 12 fișiere"), urmărești progresul per fișier (în așteptare/în lucru/finalizat/livrat), deadline.  
**Exemplu:** Proiect "Bosch — Cataloage Piese Q1 2026": 8 fișiere, deadline 28 martie. Vezi că 5 sunt finalizate, 2 în lucru, 1 în așteptare. 3 zile rămase, ritm OK.  
**Valoare:** Mare pentru proiecte cu livrabile multiple.

### S3.7 — Detecție și Avertizare Termeni Netraduși
**Descriere:** După traducere, AI verifică dacă există termeni din glosar care apar în original dar NU în traducere (posibil lipsă sau tradus incorect). Generează o listă de verificare.  
**Exemplu:** Glosarul conține "ABS" → "sistem antibloc". În traducere, AI detectează că "ABS" apare de 4 ori în original dar zero ori în traducere (sau apare ca "sistem de frânare" — generic). Alerta îți atrage atenția.  
**Valoare:** Mare — asigurare calitate automată înainte de livrare.

### S3.8 — Traducere Email Direct din Modul Gmail
**Descriere:** Integrare cu modulul de Gmail — poți deschide un email primit și da "Traduce" direct, fără copy-paste. Traducerea apare sub emailul original.  
**Exemplu:** Primești un email în germană de la un furnizor auto. Dai "Traduce" din interfața Gmail → apare traducerea RO în 3 secunde, fără să ieși din aplicație.  
**Valoare:** Medie-mare — elimină un pas frecvent (copy → Google Translate → back).

### S3.9 — Raport Lunar Traduceri (Volume, Venituri, Provideri)
**Descriere:** Raport automat cu: caractere traduse total, distribuție per provider, documente procesate, limbă predominantă, estimare valoare generată (legat de calculator).  
**Exemplu:** "Februarie 2026: 2.4M caractere traduse (DeepL 68%, Google 22%, Gemini 10%), 34 documente, EN→RO 89%, valoare estimată asociată: 12.400 RON."  
**Valoare:** Medie — date pentru optimizarea costurilor și argumentare business.

### S3.10 — Traducere Live (Tastare în Timp Real)
**Descriere:** Mod "live" în care pe măsură ce tastezi în câmpul sursă, traducerea apare automat cu 500ms delay (debounce). Ideal pentru texte scurte, emailuri, mesaje.  
**Exemplu:** Tastezi în română și traducerea în engleză apare imediat alături — perfect pentru compunerea unui email direct în engleză, fără să scrii mai întâi în română și să trimiți la traducere.  
**Valoare:** Medie — confort pentru texte scurte, frecvente.

---

## 4. Modul: Facturare (Invoice)

> **Status actual:** Generator facturi PDF (reportlab), CRUD clienți, istoric comenzi, raport lunar grafice, export Excel/CSV, template documente, email smtplib, scanner facturi OCR.

### S4.1 — Serii de Facturi Configurabile și Numerotare Automată
**Descriere:** Configurezi seria (ex: "CIP-2026-") și numerotarea se face automat secvențial. Sistemul verifică să nu existe duplicate și avertizează la gaps în serie.  
**Exemplu:** Prima factură a anului: CIP-2026-001. La a 15-a: CIP-2026-015. Dacă ai șters accidental CIP-2026-007, sistemul te avertizează la generarea raportului că seria are un gap.  
**Valoare:** Mare — conformitate fiscală, evită probleme la inspecții financiare.

### S4.2 — Facturi Recurente / Abonamente
**Descriere:** Marchezi un client ca "recurent" cu sumă fixă lunară și ziua de facturare. Sistemul generează automat factura la data configurată sau îți trimite o alertă să o aprobi.  
**Exemplu:** Client cu retainer lunar de 1.500 RON. La 1 ale fiecărei luni, primești notificare: "Factură recurentă pentru [Client] gata — aprobă sau modifică". Un click și e trimisă pe email.  
**Valoare:** Mare dacă ai clienți cu contracte recurente.

### S4.3 — Status Plată cu Urmărire Scadențe
**Descriere:** Fiecare factură are status: Emisă / Trimisă / Parțial plătită / Plătită / Restantă. Alertă automată la X zile după scadență. Dashboard cu totalul restant.  
**Exemplu:** Factura CIP-2026-034 are scadență 15 martie. Astăzi e 20 martie — apare în roșu "Restantă 5 zile — total restant: 2.400 RON". Buton direct "Trimite reminder email".  
**Valoare:** Foarte mare — cash flow management, nu mai uiți de facturi neîncasate.

### S4.4 — Proforma / Ofertă cu Conversie în Factură
**Descriere:** Creezi o proformă sau ofertă (document fără număr de factură fiscal). Când clientul confirmă, o convertești în factură reală cu un click — se populează automat.  
**Exemplu:** Trimiti proforma 2026-P-05 clientului. El confirmă. Dai "Convertește în factură" → devine CIP-2026-038, cu toate datele copiate, fără re-introducere manuală.  
**Valoare:** Mare — flux de lucru corect și eficient.

### S4.5 — Multi-Linie pe Factură (Descrieri Multiple)
**Descriere:** O factură poate conține mai multe linii/servicii cu descriere, cantitate, preț unitar, TVA per linie. Total calculat automat.  
**Exemplu:** Factură pentru "Traducere manual + Revizuire + Apostilare document": 3 linii separate cu prețuri diferite, TVA 0% (serviciu export), total 1.850 RON.  
**Valoare:** Mare — o singură factură acoperă proiecte complexe cu mai multe servicii.

### S4.6 — Trimitere Factură prin WhatsApp (via Clipboard)
**Descriere:** Buton "Trimite WhatsApp" — generează un mesaj pre-compus cu link/PDF-ul facturii copiat în clipboard + deschide WhatsApp Web cu numărul clientului pre-completat.  
**Exemplu:** Clientul preferă WhatsApp în loc de email. Dai "Trimite WA", se deschide `web.whatsapp.com?phone=0721...` cu mesajul gata, tu dai doar Send.  
**Valoare:** Medie — mulți clienți din România preferă WhatsApp față de email formal.

### S4.7 — Import Facturi Furnizori în Registru Cheltuieli
**Descriere:** Folosind OCR-ul existent, scanezi și facturile primite de la furnizori (nu doar emise). Se creează automat un registru de cheltuieli, separat de registrul de venituri.  
**Exemplu:** Primești factura de la furnizorul de hârtie: scaneziez cu telefonul (upload), OCR extrage datele, intră automat în "Cheltuieli Martie 2026". Raportul lunar arată și profitul estimat (venituri - cheltuieli).  
**Valoare:** Mare — tabloul complet al businessului, nu doar veniturile.

### S4.8 — Generare Automată Contract din Template la Factură Nouă
**Descriere:** La crearea unei facturi noi (sau proforma), opțional se generează automat și un contract de prestări servicii din template — populat cu datele clientului și sumele din factură.  
**Exemplu:** Client nou, factură 3.000 RON. Bifezi "Generează contract" → se produce un DOCX cu datele clientului, suma, termenul de livrare, clauze standard. Semnați contractul, facturezi la finalizare.  
**Valoare:** Mare — protecție juridică, profesionalism.

### S4.9 — Dashboard Financiar: Venituri, Cheltuieli, Profit
**Descriere:** Grafice combinate (line + bar chart, Recharts): venituri lunare, cheltuieli (dacă implementezi S4.7), profit estimat, comparație an curent vs. an anterior.  
**Exemplu:** Grafic pe 12 luni: bare albastre venituri, bare roșii cheltuieli, linie verde profit. Poți vedea imediat că Q4 2025 a avut cel mai mare profit dar Q1 2026 e sub target.  
**Valoare:** Foarte mare — vizibilitate completă asupra stării financiare a CIP Inspection.

### S4.10 — Raport Pregătit pentru Contabil (Export Structurat)
**Descriere:** Export structurat al tuturor facturilor dintr-o perioadă în format pregătit pentru contabil: Excel cu coloane standard (număr, dată, client, CUI client, sumă fără TVA, TVA, total, status plată).  
**Exemplu:** La final de trimestru, contabilul îți cere situația facturilor. Selectezi Q1 2026, dai "Export Contabil" → primești un Excel în format pe care îl primesc în general contabilii români.  
**Valoare:** Mare — economisești ore de pregătire manuală a documentelor pentru contabilitate.

---

## 5. Modul: ITP Inspecții Auto

> **Status actual:** CRUD inspecții, import CSV/Excel, statistici lunare/brand/venituri/combustibil (Recharts), alertă expirare 30 zile, export CSV/Excel.

### S5.1 — Fișă Client Auto (Istoric per Proprietar)
**Descriere:** Legătura între vehicul și proprietar — un proprietar poate avea mai multe mașini. Fișa proprietarului arată toate vehiculele și istoricul ITP per vehicul.  
**Exemplu:** Dl. Ionescu aduce mașina a 3-a oară la ITP. Când introduci numărul de telefon, sistemul afișează fișa lui: Dacia Logan (2x ITP OK), Ford Focus (1x ITP, 1x respins), BMW (nou). Îi oferi discount client fidel.  
**Valoare:** Mare — relație cu clienții, nu doar evidență anonimă de vehicule.

### S5.2 — Alertă Expirare Configurabilă (15 / 30 / 60 Zile) + SMS/Email
**Descriere:** Configurezi X zile înainte de expirare pentru alertare. Dacă ai numărul de telefon al clientului, poți trimite SMS (via API SMS gratuit) sau email de reminder.  
**Exemplu:** La 30 zile înainte de expirare ITP-ul unui Logan al lui Popescu, sistemul trimite automat un SMS: "Bună ziua, ITP-ul vehiculului dv. Dacia Logan AB-01-POP expiră pe 25 Apr. Vă așteptăm la CIP Inspection, Str. X."  
**Valoare:** Foarte mare — marketing pasiv, fidelizare clienți, venit recurent.

### S5.3 — Motiv Respingere ITP cu Clasificare
**Descriere:** La ITP respins, înregistrezi motivul/motivele (frâne, lumini, emisii, caroserie etc.) din listă predefinită. Statistici pe motive de respingere.  
**Exemplu:** Statisticile arată că 45% din respingeri sunt din cauza frânelor. Poți colabora cu un service auto local și să recomezi clienților — sau să avertizezi: "La mașinile pe benzină post-2015, 60% sunt respinse din cauza emisiilor."  
**Valoare:** Medie — date operaționale valoroase, posibilă sursă de parteneriate.

### S5.4 — Calendar ITP (Programări)
**Descriere:** Calendar vizual cu sloturile disponibile pentru ITP (ex: 2 mașini/oră, program 8-16). Clienții pot fi programați, sistemul gestionează capacitatea zilnică.  
**Exemplu:** Miercuri 22 martie: 8 sloturile — 6 ocupate, 2 libere. Îți sună un client, vezi direct că mai ai loc la 14:00 și 15:00. Programezi și îi trimiți confirmare pe email.  
**Valoare:** Mare — organizare operațională, evită cozile și clienții dezamăgiți.

### S5.5 — Raport Fiscal ITP (Venituri per Lună, TVA, Bon Fiscal)
**Descriere:** Raport structurat cu toate încasările ITP pe lună: număr inspecții, preț unitar (dacă e fix), total încasări, estimare TVA dacă e cazul. Pregătit pentru contabil.  
**Exemplu:** "Martie 2026: 127 inspecții × 100 RON = 12.700 RON venituri ITP. Export PDF/Excel pentru contabil."  
**Valoare:** Mare — simplifică evidența fiscală pentru activitatea ITP.

### S5.6 — Import Automat din RAR/DRPCIV (Dacă API Disponibil)
**Descriere:** Dacă există vreun API public sau fișier exportabil din sistemul RAR/DRPCIV, importi direct datele fără introducere manuală. Dacă nu există API, cel puțin parsarea unui format de export standard RAR.  
**Notă:** Conform planului, scraping-ul direct este exclus (risc legal). Aceasta se referă doar la date exportate legitim de tine din sistemul RAR.  
**Exemplu:** Exporti din aplicația RAR un CSV cu inspecțiile zilei. Îl imporți în Command Center cu un click — nu mai introduci manual fiecare intrare.  
**Valoare:** Foarte mare dacă e fezabil tehnic și legal.

### S5.7 — Heatmap Activitate (Zile Aglomerate vs. Liniștite)
**Descriere:** Calendar heatmap (similar GitHub contributions) cu intensitatea activității ITP per zi — câte mașini ai inspectat. Identifici zilele/perioadele aglomerate.  
**Exemplu:** Heatmap-ul arată că luni sunt cele mai aglomerate (25+ mașini), vineri cele mai liniștite (8-10 mașini). Poți programa activitățile administrative (facturare, contabilitate) vinerea.  
**Valoare:** Medie — optimizare operațională.

### S5.8 — Statistici per Inspector (Dacă Ai Angajați)
**Descriere:** Dacă CIP Inspection are mai mulți inspectori, fiecare inspecție se atribuie unui inspector. Statistici: inspecții per inspector, rată de respingere, venituri generate.  
**Exemplu:** Inspector A: 450 inspecții/lună, rată respingere 18%. Inspector B: 380 inspecții/lună, rată respingere 24%. Date pentru bonusuri de performanță.  
**Valoare:** Medie-mare dacă există personal multiplu.

### S5.9 — Notificări Automate la Apropierea Reviziei Periodice (Nu ITP)
**Descriere:** Pe lângă ITP, poți urmări și alte scadențe: revizie anuală, asigurare RCA, rovinietă. Le adaugi la profilul vehiculului și primești alerte similare cu ITP-ul.  
**Exemplu:** Clientul Popescu are RCA care expiră pe 15 mai. La 30 zile înainte, primești alerta: "RCA-ul lui Popescu expiră în 30 zile." Poți trimite un reminder sau direcționa la un asigurator partener.  
**Valoare:** Medie — serviciu adăugat față de simpla evidență ITP.

### S5.10 — Export Raport Anual ITP (Statistici Complete)
**Descriere:** Raport anual comprehensiv: total inspecții, rată de promovare/respingere, top 10 mărci, distribuție combustibil, evoluție venituri lunare, comparație vs. anul anterior.  
**Exemplu:** "Raport ITP 2025: 1.847 inspecții, 73% promovate, top mărci Dacia (31%), Volkswagen (18%), Ford (12%). Venituri totale: 184.700 RON (+12% vs. 2024)."  
**Valoare:** Mare — document pentru planificare, bancă, asociații de profil.

---

## 6. Modul: Quick Tools

> **Status actual:** Command Palette (Ctrl+K), QR Generator, Notepad cu auto-save, Calculator avansat, Password Generator, Barcode Generator. Voice Notes — DEFERRED.

### S6.1 — Voice Notes cu Transcriere Automată (Finalizare Feature Deferred)
**Descriere:** Înregistrezi un mesaj vocal, Web Speech API îl transcrie automat în text și îl salvează în Notepad sau ca notă separată. Offline-first (Web Speech API nu necesită internet).  
**Exemplu:** Conduci mașina, îți vine o idee. Deschizi Command Center pe telefon (PWA), apeși microfon: "Reamintește-mi să sun clientul Bosch despre contractul de primăvară." Nota apare text în Notepad.  
**Valoare:** Foarte mare pentru utilizarea mobilă — feature-ul deferred merită finalizat.

### S6.2 — Notepad cu Foldere și Tag-uri
**Descriere:** Notele se pot organiza în foldere (ex: "Clienți", "Idei", "Operațional") și tag-uri. Căutare fulltext în toate notele.  
**Exemplu:** Ai 50 de note după câteva luni. Cauți "Bosch" și găsești toate notele care menționează clientul Bosch, indiferent de folder.  
**Valoare:** Mare — notepad-ul simplu devine un sistem de note serios (Notion lite).

### S6.3 — Color Picker Avansat
**Descriere:** Tool de color picking: input HEX/RGB/HSL, conversie între formate, picker vizual, palate salvate, extragere culori dintr-o imagine uploadată.  
**Exemplu:** Clientul îți trimite un logo și vrea să știe codul HEX al culorii principale. Uploadezi imaginea în Color Picker, click pe culoare → `#E63946`.  
**Valoare:** Medie — util ocazional pentru materiale grafice.

### S6.4 — Text Diff (Comparare Texte)
**Descriere:** Doi câmpi text, comparare vizuală cu highlight pe diferențe (adăugiri verde, ștergeri roșu, modificări galben). Util pentru versiuni de contracte/traduceri.  
**Exemplu:** Ai două versiuni ale unui contract. Lipești ambele în Text Diff și imediat vezi exact ce s-a schimbat în versiunea nouă față de cea veche — fără să citești tot contractul.  
**Valoare:** Mare — deși există și în modulul AI Docs, o versiune simplă standalone e mai rapidă pentru texte scurte.

### S6.5 — Convertor Dată/Timp cu Fusuri Orare
**Descriere:** Convertor rapid între fusuri orare, calcul intervale între date, adăugare/scădere zile lucrătoare, convertor format dată (RO ↔ US ↔ ISO).  
**Exemplu:** Clientul german scrie "Meeting on 03/15/2026 at 2 PM CET". Introduci rapid și vezi că în România este 15 martie 2026 ora 15:00 (EET). Calculezi și că termenul de livrare de 10 zile lucrătoare = 29 martie.  
**Valoare:** Medie — util pentru colaborări internaționale.

### S6.6 — Generator Semnătură Email HTML
**Descriere:** Template wizard: introduci date (nume, titlu, telefon, email, adresă), alegi un design din 3-4 template-uri, primești codul HTML gata de copiat în Gmail/Outlook.  
**Exemplu:** Generezi semnătura profesională pentru CIP Inspection SRL cu logo (dacă e disponibil), număr de telefon, adresă Nădlac, CUI. Copiezi HTML-ul și îl configurezi în Gmail.  
**Valoare:** Medie — o dată configurat, nu mai revii la el.

### S6.7 — Regex Tester
**Descriere:** Câmp text + câmp regex + highlight pe matches, cu explicație plain-English a ce face regex-ul (via AI), colecție de regex-uri comune salvate.  
**Exemplu:** Vrei să extragi toate CUI-urile dintr-un document. Testezi `/RO\d{6,10}/g`, sistemul evidențiază toate match-urile în text și confirmă că pattern-ul e corect.  
**Valoare:** Medie — util pentru automatizări și procesarea datelor.

### S6.8 — Calculator Financiar (Rate, Dobânzi, Amortizare)
**Descriere:** Calculator specializat: rate de leasing, dobândă simplă/compusă, tabel amortizare, conversie între EUR/RON la cursul BNR live.  
**Exemplu:** Vrei să cumperi un echipament ITP în leasing. Introduci: valoare 15.000 EUR, avans 20%, 36 rate, dobândă 8%. Primești: rată lunară 398 EUR, total plătit 17.328 EUR, dobândă totală 2.328 EUR.  
**Valoare:** Medie-mare pentru decizii de investiții în business.

### S6.9 — Screenshot Annotation Tool
**Descriere:** Uploadezi un screenshot sau îl lipești din clipboard, poți adăuga săgeți, text, dreptunghiuri de evidențiere (highlight), blur pe zone sensibile. Export PNG.  
**Exemplu:** Vrei să raportezi o problemă dintr-o aplicație furnizorului. Faci screenshot, îl deschizi în tool, adaugi o săgeată roșie pe zona cu problema + text "Eroare apare aici". Trimiți imagine adnotată pe email.  
**Valoare:** Medie — elimină nevoia de tool extern (Paint, Greenshot etc.).

### S6.10 — Convertor Numere (Zecimal ↔ Binar ↔ Hex ↔ Octal + Roman)
**Descriere:** Convertor rapid cu toate bazele de numerație + numere romane. Input în orice câmp, celelalte se actualizează live.  
**Exemplu:** Valoare HEX dintr-un document tehnic: `0x1A4`. Introduci în câmpul HEX, instant vezi: decimal 420, binar 110100100, octal 644.  
**Valoare:** Mică — nișat, dar fezabil în <1 oră implementare.

---

## 7. Modul: Convertor Fișiere

> **Status actual:** PDF→DOCX, DOCX→PDF (COM), Imagine→Text (OCR), CSV/Excel↔JSON, ZIP, redimensionare imagini batch, merge PDF, split PDF, compresie imagini. Multe netestate pe Android.

### S7.1 — Conversie DOCX → HTML și HTML → DOCX
**Descriere:** Convertor bidirecțional între DOCX și HTML curat. Util pentru publicare web sau pentru a edita un document Word într-un editor HTML.  
**Exemplu:** Ai un contract în Word și vrei să îl publici pe un site sau să îl trimiți ca email HTML. Convertești în HTML, editezi ce trebuie, sau invers — primești un HTML de pe undeva și îl convertești în DOCX editabil.  
**Valoare:** Medie.

### S7.2 — Extragere Imagini din PDF
**Descriere:** Extrage toate imaginile dintr-un PDF (diagrame, fotografii, logo-uri) ca fișiere individuale PNG/JPEG, cu posibilitatea de a selecta ce pagini.  
**Exemplu:** Manual tehnic auto cu 200 de diagrame. Extragi toate imaginile automat → 200 fișiere PNG numerotate, gata de utilizat în alte documente sau baza de date.  
**Valoare:** Medie — util pentru procesarea documentelor tehnice.

### S7.3 — Adăugare Watermark pe PDF/Imagini
**Descriere:** Adaugi text sau imagine ca watermark pe PDF (toate paginile sau selectate) și pe imagini. Configurabil: opacitate, poziție, culoare, rotație.  
**Exemplu:** Trimiți o traducere în draft clientului pentru aprobare. Adaugi watermark "DRAFT — CIP Inspection SRL" diagonal pe fiecare pagină, semitransparent. Când e aprobat, generezi versiunea fără watermark.  
**Valoare:** Mare — protecție documente, flux de lucru profesional.

### S7.4 — Redactare (Blackout) Informații Sensibile din PDF
**Descriere:** Selectezi zone dintr-un PDF (prin coordonate sau căutare text) care se înlocuiesc permanent cu dreptunghiuri negre — nu doar mascate vizual, ci eliminate definitiv.  
**Exemplu:** Trimiți unui client un contract de referință dar trebuie să elimini datele altui client (GDPR). Selectezi și redactezi CNP, adresă, alte date personale — permanent, nu reversibil.  
**Valoare:** Mare — conformitate GDPR, flux standard în firmele de traduceri.

### S7.5 — Conversie Batch cu Coadă de Așteptare și Progress
**Descriere:** Uploadezi 20 de fișiere pentru conversie, se creează o coadă cu progress bar per fișier, notificare la final, download all ca ZIP.  
**Exemplu:** 20 de DOCX-uri de convertit în PDF. Le încarci pe toate, pornești conversia, faci altceva. La finalizare apare notificare: "Conversia completă: 18 reușite, 2 cu erori. Descarcă ZIP."  
**Valoare:** Mare — actual probabil e fișier cu fișier.

### S7.6 — Rotație și Aliniere Automată Documente Scanate
**Descriere:** Detectează automat documentele scanate strâmb și le îndreaptă. Util înainte de OCR pentru rezultate mai bune.  
**Exemplu:** Scanezi un contract fizic cu telefonul, ieșit ușor rotit. Înainte de OCR, aplici "auto-deskew" — documentul se rotește automat la orizontal. Calitatea OCR crește semnificativ.  
**Valoare:** Medie-mare — îmbunătățire directă a calității OCR.

### S7.7 — Conversie Audio → Text (Transcriere)
**Descriere:** Uploadi un fișier audio (MP3, WAV, M4A) și îl transcrii în text via Whisper API (OpenAI free tier) sau Gemini Audio.  
**Exemplu:** Ai o înregistrare a unei ședințe de 45 minute. Uploadezi fișierul audio, după 2-3 minute primești transcrierea completă text. Poți da direct la AI pentru rezumat sau extragere decizii.  
**Valoare:** Mare — capabilitate complet nouă, utilă pentru întâlniri, interviuri, note vocale.

### S7.8 — Semnătură Digitală Simplă pe PDF (Vizuală)
**Descriere:** Adaugi o semnătură vizuală pe un PDF — desenată cu mouse/touch sau uploadată ca imagine PNG. Nu este semnătură electronică qualificată, ci vizuală simplistă.  
**Notă:** Nu înlocuiește semnătura electronică legală — pentru documente cu valoare juridică, folosește un serviciu certificat.  
**Exemplu:** Primești un contract PDF simplu de la un partener mic care acceptă semnătură scanată. Deschizi în Convertor, adaugi semnătura pe pagina finală, salvezi PDF semnat.  
**Valoare:** Medie — util pentru documente informale.

### S7.9 — Protecție PDF cu Parolă (Encrypt/Decrypt)
**Descriere:** Adaugi o parolă de deschidere sau de editare unui PDF. Sau elimini parola dintr-un PDF pe care îl deții legitim.  
**Exemplu:** Trimiți o traducere confidențială unui client. Protejezi PDF-ul cu parola "CIPClient2026". Clientul primește fișierul + parola separat (pe telefon). Documente sensibile, transfer securizat.  
**Valoare:** Medie — în contextul firmei de traduceri, confidențialitatea documentelor e importantă.

### S7.10 — Preview Înainte și După Conversie (Side-by-Side)
**Descriere:** Înainte de descărcare, un preview vizual al documentului original vs. documentul convertit — să verifici că formatarea s-a păstrat corect.  
**Exemplu:** Convertești un DOCX cu tabele complexe în PDF. Preview-ul arată că un tabel e truntat pe pagina 3. Poți ajusta marginile sau accepta rezultatul — înainte să descarci și să observi problema.  
**Valoare:** Mare — evită descărcarea unor fișiere defecte.

---

## 8. Modul: File Manager

> **Status actual:** Browse, CRUD fișiere, upload/download, duplicate finder (MD5), FTS5 fulltext, tag-uri, favorite, auto-organizare pe extensie. Securitate path traversal implementată.

### S8.1 — Preview Documentelor Direct în Browser (PDF, DOCX, XLSX)
**Descriere:** Click pe un fișier → se deschide un preview inline fără descărcare. PDF render cu PDF.js, DOCX/XLSX conversie la HTML pentru preview rapid.  
**Exemplu:** Ai 30 de contracte PDF în folder. Faci click pe fiecare și îl citești direct în browser fără să descarci. Găsești repede contractul căutat.  
**Valoare:** Mare — actual probabil e nevoie de descărcare pentru a vizualiza.

### S8.2 — Versioning Simplu (Istoric Versiuni per Fișier)
**Descriere:** Când re-uploadezi un fișier cu același nume, versiunea veche se arhivează automat (nu se șterge). Poți vedea și restaura versiunile anterioare.  
**Exemplu:** Uploadezi "Contract_Bosch_v1.docx". Peste o lună uploadezi din nou cu modificări. Sistemul păstrează ambele versiuni. Dacă clientul revine la versiunea veche, o restaurezi instant.  
**Valoare:** Mare — protecție împotriva pierderilor accidentale.

### S8.3 — Partajare Temporară cu Link (Single-User Context)
**Descriere:** Generezi un link temporar (24h/7 zile) pentru un fișier, accesibil fără autentificare. Link-ul expiră automat. Util pentru a trimite rapid un document unui client fără email.  
**Notă:** Deși în plan era exclus pentru single-user, în contextul trimiterilor către clienți devine util.  
**Exemplu:** Clientul nu primește attachmentul pe email (prea mare, filtrat). Generezi link temporar 48h: `https://tail.../share/abc123xyz` și îl trimiți pe WhatsApp. Clientul descarcă direct.  
**Valoare:** Mare în contextul comunicării cu clienții.

### S8.4 — Recunoaștere OCR la Upload cu Index Automat
**Descriere:** La uploadul oricărui PDF scanat sau imagine, OCR rulează automat în background și indexează textul în FTS5 — fără acțiune manuală.  
**Exemplu:** Uploadezi 10 contracte scanate. Fără să faci nimic altceva, după 30 secunde toate sunt căutabile fulltext. Cauți "clauză penalitate" și găsești toate contractele care conțin această frază.  
**Valoare:** Foarte mare — transformă documente opace în documente căutabile automat.

### S8.5 — Statistici Stocare cu Recomandări de Curățare
**Descriere:** Dincolo de duplicate finder (existent) — analiză completă: fișiere neutilizate >6 luni, fișiere temporare, folder-ele cele mai mari, top 20 fișiere după dimensiune cu recomandare de arhivare/ștergere.  
**Exemplu:** "Folderul node_modules din Proiect_Vechi ocupă 1.2 GB și nu a fost accesat de 8 luni. Recomand arhivare sau ștergere." Dai click → arhivează sau șterge direct din recomandare.  
**Valoare:** Medie — disk space management, util pe termen lung.

### S8.6 — Comparare Fișiere (Diff pe Documente Text)
**Descriere:** Selectezi 2 fișiere text/DOCX și le compari cu diff vizual. Integrat cu modulul existent de comparare documente din AI.  
**Exemplu:** Versiunea 1 și versiunea 2 a unui contract. Le selectezi din File Manager, dai "Compară" → vezi exact ce paragrafe s-au schimbat, fără să le deschizi separat.  
**Valoare:** Mare — flux natural pornind din File Manager.

### S8.7 — Smart Collections (Dosare Virtuale cu Reguli)
**Descriere:** Creezi "dosare inteligente" cu reguli automate: "Toate PDF-urile din luna curentă", "Toate fișierele cu tag:client+Bosch", "Fișiere > 5MB modificate azi". Se actualizează dinamic.  
**Exemplu:** Smart Collection "De livrat azi": toate fișierele cu tag "în lucru" + data modificată azi. Dimineața, deschizi colecția și ai exact lista de lucru a zilei.  
**Valoare:** Mare — organizare dinamică fără structuri de foldere rigide.

### S8.8 — Backup Automat în Google Drive (Selectiv)
**Descriere:** Configurezi care foldere se sincronizează automat cu Google Drive la interval (ex: zilnic la 02:00). Nu tot File Manager-ul, ci folderele importante (contracte, facturi, traduceri livrate).  
**Exemplu:** Folderul "Contracte_Semnate" se sincronizează automat în Drive zilnic. Dacă laptopul crapă, ai toate contractele în Drive. Fără backup manual.  
**Valoare:** Foarte mare — protecție date critice de business.

### S8.9 — Thumbnail Grid View pentru Imagini
**Descriere:** View alternativ pentru foldere cu imagini: în loc de listă cu text, afișezi un grid de thumbnail-uri pentru vizualizare rapidă.  
**Exemplu:** Folderul "Fotografii_ITP" cu 200 poze de la inspecții. În Grid View vezi toate thumbnail-urile simultan, identifici rapid poza căutată vizual în loc să cauți după nume de fișier.  
**Valoare:** Medie — confort pentru foldere cu imagini.

### S8.10 — Rename Batch Inteligent cu Pattern
**Descriere:** Selectezi mai multe fișiere și aplici un pattern de redenumire: `{data}_{numar_secvential}_{nume_original}`. Preview înainte de aplicare.  
**Exemplu:** 15 fișiere primite de la client cu nume haotice: "scan001.pdf", "IMG_20260315.jpg" etc. Aplici pattern: `2026-03-15_Bosch_{001..015}` → devinstant "2026-03-15_Bosch_001.pdf"... etc.  
**Valoare:** Medie-mare — organizare rapidă a fișierelor primite de la clienți.

---

## 9. Modul: Vault (API Keys)

> **Status actual:** Fernet encryption + PBKDF2 + master password, stochează 10 API keys, interface CRUD.

### S9.1 — Categorii și Grupare Keys per Modul
**Descriere:** Organizezi cheile pe categorii: AI Keys, Translation Keys, Integration Keys, Business Keys. Fiecare modul poate accesa doar categoria lui.  
**Exemplu:** Modulul Translator accesează doar "Translation Keys" (DeepL, Azure, Google). Modulul AI accesează "AI Keys" (Gemini, OpenAI, Groq). Separare logică clară.  
**Valoare:** Medie — organizare, utilă pe măsură ce numărul de keys crește.

### S9.2 — Monitorizare Utilizare Keys (Calls/Tokens Consumate)
**Descriere:** Tracker pentru fiecare key: câte apeluri/tokens au fost consumate din Command Center (nu total pe cont, ci doar din aplicație). Grafic temporal.  
**Exemplu:** Gemini API: "743 apeluri în ultimele 30 zile, din care 234 din modul AI Chat, 509 din modul Translator. Trend: +23% față de luna trecută."  
**Valoare:** Mare — înțelegi ce module consumă cel mai mult și poți optimiza.

### S9.3 — Alertă la Apropierea Limitei Free Tier
**Descriere:** Configurezi limitele free tier per key (ex: DeepL 500K chars/lună, OpenAI $5/lună). La atingerea a 80%, primești alertă în dashboard.  
**Exemplu:** DeepL: limita configurată 500K chars. La 400K (80%), apare alertă galbenă. La 450K (90%), alertă roșie. Sistemul poate comuta automat pe provider fallback.  
**Valoare:** Mare — eviți întreruperi neașteptate ale serviciilor.

### S9.4 — Rotație Automată Keys (Failover Transparent)
**Descriere:** Dacă o key returnează eroare (rate limit, expirat, invalid) — sistemul comută automat la key-ul de backup pentru același serviciu, dacă ai configurat una.  
**Exemplu:** Ai 2 keys Gemini (personal + business). Dacă key-ul 1 atinge rate limit, key-ul 2 preia automat fără eroare vizibilă pentru utilizator.  
**Valoare:** Mare — disponibilitate ridicată, zero întreruperi.

### S9.5 — Test Conectivitate per Key (Ping)
**Descriere:** Buton "Testează" per key — trimite un request minim de test și returnează: status (OK/EROARE), latență, versiune API dacă disponibilă.  
**Exemplu:** Adaugi o key nouă Groq. Dai "Testează" → "✅ Groq API: OK, 234ms, model disponibil: llama-3.3-70b". Sau "❌ Key invalidă — verifică formatul."  
**Valoare:** Mare — elimini guess-work la configurare sau depanare.

### S9.6 — Import/Export Securizat Keys (Backup Criptat)
**Descriere:** Exporti toate key-urile ca un fișier criptat AES-256 cu o parolă separată. Poți importa pe alt dispozitiv sau restaura după reinstalare.  
**Exemplu:** Reinstalezi Windows sau muți proiectul pe un alt laptop. Importezi fișierul criptat + introduci parola → toate key-urile sunt restaurate în 10 secunde.  
**Valoare:** Mare — fără asta, la o reinstalare trebuie să re-introduci manual toate key-urile.

### S9.7 — Log Activitate per Key (Cine a Folosit, Când, Ce Modul)
**Descriere:** Audit log: fiecare utilizare a unei key se loghează (timestamp, modul, endpoint apelat, succes/eroare). Filtrabil și exportabil.  
**Exemplu:** Observi că OpenAI key a generat 50 de apeluri în weekend când nu ai lucrat. Verifici log-ul: toate provin din Scheduler (task automat). Normal sau suspect — poți verifica.  
**Valoare:** Medie — securitate și debugging.

### S9.8 — Reminder Reînnoire Keys cu Dată Expirare
**Descriere:** Configurezi data de expirare pentru keys care au (ex: Azure trial keys, tokenuri GitHub cu expirare). Alertă la 14 zile înainte.  
**Exemplu:** Token GitHub setat să expire la 1 mai 2026. La 17 aprilie: alertă "Token GitHub expiră în 14 zile — reînnoiește din GitHub Settings."  
**Valoare:** Medie — eviți întreruperi din cauza key-urilor expirate neobservate.

### S9.9 — Validare Format Key la Salvare
**Descriere:** La adăugarea unei key, sistemul validează formatul (regex per tip serviciu): Gemini keys încep cu "AIza...", OpenAI cu "sk-...", GitHub cu "ghp_..." etc.  
**Exemplu:** Introduci o key Gemini dar ai copiat-o greșit (cu un spațiu la final). Sistemul avertizează: "Formatul nu corespunde pattern-ului Gemini (AIzaXXXX...). Verifică key-ul." Salvezi totuși dacă ești sigur.  
**Valoare:** Medie — previne erori de copiere, debugging mai rapid.

### S9.10 — Dashboard Sănătate API Keys (Overview)
**Descriere:** Un singur ecran cu status-ul tuturor keys: verde (OK, testat recent), galben (neobservat în >7 zile), roșu (eroare la ultimul test), gri (neconfigurat). Cu data ultimului test și latență medie.  
**Exemplu:** La deschiderea Vault-ului, vezi instant: 8 keys verzi ✅, 1 galbenă ⚠️ (Perplexity, nefolosit de 2 săptămâni), 1 roșie ❌ (Azure — key expirată ieri).  
**Valoare:** Mare — overview instant fără să testezi manual una câte una.

---

## 10. Modul: Automatizări

> **Status actual:** Task Scheduler vizual (CRUD, manual trigger, run history), Shortcuts personalizate, Uptime Monitor (async ping), API Tester (HTTP cu template-uri salvate), Health Monitor (disk, memory, DB, modules, API keys, erori recente). DEFERRED: web scraping, moduri de lucru, notificări unificate, webhook.

### S10.1 — Finalizare: Sistem Notificări Unificate (Feature Deferred)
**Descriere:** Centru de notificări (bell icon în header) cu toate alertele din toate modulele: facturi restante, ITP-uri care expiră, limite API, task-uri eșuate, alerte uptime. Mark as read, filtre per tip.  
**Exemplu:** Dimineața deschizi Command Center, bell-ul arată 3 notificări: "2 ITP-uri expiră în 7 zile", "Factură CIP-2026-034 restantă 5 zile", "Task scheduler: backup eșuat ieri la 02:00".  
**Valoare:** Foarte mare — agregă toate alertele dintr-un singur loc.

### S10.2 — Automatizare: Raport Zilnic/Săptămânal pe Email
**Descriere:** Task schedulat care generează automat un rezumat al activității (calcule, traduceri, ITP-uri, facturi emise) și îl trimite pe emailul tău.  
**Exemplu:** În fiecare luni dimineață la 08:00 primești emailul: "Săptămâna 10-16 Martie: 12 calcule preț, 8 traduceri procesate, 3 facturi emise (total 4.200 RON), 127 ITP-uri, 0 erori sistem."  
**Valoare:** Mare — awareness pasiv, fără să deschizi aplicația.

### S10.3 — Webhook Incoming (Feature Deferred — Simplificat)
**Descriere:** Endpoint unic `/api/webhook/in` care primește POST requests de la servicii externe (Zapier, Make/Integromat, formulare online) și declanșează acțiuni configurate.  
**Exemplu:** Ai un formular de ofertă pe site. La completare, formularul trimite un webhook la Command Center cu datele clientului → se creează automat o înregistrare client + un calcul pre-completat.  
**Valoare:** Mare — integrare cu orice serviciu extern fără API complex.

### S10.4 — Macro Recorder (Secvențe de Acțiuni)
**Descriere:** Înregistrezi o secvență de acțiuni în aplicație (ex: calculează preț → generează ofertă PDF → trimite email → adaugă în Calendar), o salvezi ca macro și o poți rula cu un click.  
**Exemplu:** Macro "Flux Complet Client Nou": 1) Calcul preț din fișier, 2) Generare ofertă PDF, 3) Trimitere email client, 4) Creare eveniment Calendar "Follow-up [client] +3 zile". Un click face toate 4 pași.  
**Valoare:** Foarte mare — automatizează fluxurile de lucru repetitive complete.

### S10.5 — Condiții în Task Scheduler (If/Then)
**Descriere:** Task-urile pot avea condiții: "Rulează backup DOAR dacă există >50 fișiere noi în folder", "Trimite alertă DOAR dacă uptime < 95%", "Generează raport DOAR dacă sunt facturi neplătite".  
**Exemplu:** Task "Alertă cashflow": rulează zilnic la 09:00, verifică facturi restante > 30 zile. DACĂ există → trimite email cu lista. DACĂ nu există → nu face nimic (nu primești emailuri inutile).  
**Valoare:** Mare — task scheduler inteligent vs. simplu cron.

### S10.6 — Monitorizare Performanță Aplicație (Metrici Interne)
**Descriere:** Dashboard cu metrici de performanță: timp mediu de răspuns per endpoint API, endpoint-urile cele mai lente, query-urile SQLite lente (>100ms), memory usage backend.  
**Exemplu:** Observi că `/api/filemanager/search` are timp mediu 3.2s. Cauza: FTS5 fără index pe un câmp. Identifici și rezolvi problema de performanță — aplicația devine mai rapidă.  
**Valoare:** Medie-mare — debugging proactiv înainte că problemele să devină vizibile.

### S10.7 — Backup Automat Configurabil (Local + Drive)
**Descriere:** Task scheduler pentru backup: ce se include (DB, fișiere, configurații, keys criptate), frecvență, destinație (local + opțional Drive), retenție (păstrează ultimele X backup-uri).  
**Exemplu:** Backup zilnic la 03:00: DB SQLite + fișierele din "Contracte" + Vault criptat → salvate în `C:\Backup\CommandCenter\` + copiate în Drive. Retenție 30 zile. Zero intervenție manuală.  
**Valoare:** Foarte mare — protecție date, "set and forget".

### S10.8 — Log Centralizat cu Căutare și Filtre (toate modulele)
**Descriere:** Un singur log care agregă evenimentele din toate modulele, căutabil și filtrabil: per modul, per nivel (INFO/WARN/ERROR), per interval de timp.  
**Exemplu:** Ceva nu funcționează cu Gmail. Deschizi Log Centralizat, filtrezi: modul=integrations, nivel=ERROR, ultimele 24h → găsești "SMTP connection refused: port 587 blocked" în 3 secunde.  
**Valoare:** Mare — debugging mult mai rapid față de log-urile dispersate per modul.

### S10.9 — Simulate Task (Dry Run)
**Descriere:** Buton "Simulează" per task scheduler — rulează task-ul în mod dry-run (fără să execute acțiunile reale) și arată ce ar face: ce fișiere ar procesa, ce emailuri ar trimite, ce date ar modifica.  
**Exemplu:** Ai configurat un task "Ștergere fișiere vechi >180 zile". Dai "Simulează" → îți arată lista exactă a 47 fișiere ce ar fi șterse. Verifici că nu sunt fișiere importante printre ele, abia apoi activezi task-ul real.  
**Valoare:** Mare — siguranță înainte de a activa automatizări cu impact distructiv.

### S10.10 — Integrare Zapier/Make via Webhook Out
**Descriere:** La anumite evenimente din Command Center (factură emisă, traducere finalizată, ITP expirat), sistemul poate trimite automat un webhook OUT către Zapier/Make pentru a declanșa acțiuni externe.  
**Exemplu:** La emiterea unei facturi → Zapier primește datele → le adaugă automat în Google Sheets "Registru Venituri 2026" → trimite SMS de confirmare pe telefonul tău. Fără nicio acțiune manuală.  
**Valoare:** Mare — conectare cu ecosistemul de automatizări externe fără API custom.

---

## 11. Modul: Integrări Externe

> **Status actual:** Gmail (SMTP/IMAP — trimitere, citire, reply), Google Drive (REST — listare, upload, download), Google Calendar (REST — CRUD evenimente), GitHub (httpx — repos, commits, issues), Status Dashboard. Implementare simplificată fără OAuth complex.

### S11.1 — Gmail: Inbox cu Filtre și Categorii
**Descriere:** Vizualizare inbox Gmail cu filtre: necitite, cu atașamente, per expeditor, per subiect. Categorii auto: Clienți, Furnizori, Notificări, Personal.  
**Exemplu:** Filtrezi "Necitite + Atașament PDF" → vezi direct emailurile cu documente de procesat, fără să scanezi tot inbox-ul.  
**Valoare:** Mare — inbox Command Center mai util decât interfața standard Gmail pentru workflow-ul tău.

### S11.2 — Gmail: Compunere Email cu Template-uri + Traducere Inline
**Descriere:** Compui un email direct în Command Center cu template-uri predefinite (ofertă, factură, urmărire plată). Buton "Traduce în EN" direct în câmpul de text înainte de trimitere.  
**Exemplu:** Selectezi template "Transmitere Factură", se pre-completează cu datele clientului activ din baza de date, modifici suma, dai "Traduce EN" pentru clientul german, trimiți. Tot din Command Center, fără să deschizi Gmail.  
**Valoare:** Foarte mare — fluxul complet factură → email în același loc.

### S11.3 — Google Drive: Sincronizare Selectivă Foldere Specifice
**Descriere:** Configurezi perechi de sincronizare: folder local (File Manager) ↔ folder Drive. Sincronizare unidirecțională (local→Drive pentru backup) sau bidirecțională.  
**Exemplu:** Folderul "Traduceri_Livrate" se sincronizează automat cu Drive/CIP_Inspection/Traduceri_Livrate. Clientul cu acces la Drive vede automat traducerile livrate fără să îi trimiți tu fișierele manual.  
**Valoare:** Mare — colaborare cu clienți via Drive fără email attachment-uri.

### S11.4 — Google Calendar: Integrare cu Modulul ITP (Programări)
**Descriere:** Programările ITP (dacă implementezi S5.4) se sincronizează automat cu Google Calendar — și invers, evenimentele din Calendar apar în modulul ITP.  
**Exemplu:** Programezi un client ITP pentru 25 martie la 10:00. Apare automat în Google Calendar ca eveniment "ITP — Dacia Logan AB-01-XXX — Popescu Ion". Poți vedea și din telefon via Google Calendar app nativă.  
**Valoare:** Mare — calendar unificat, nu două locuri separate.

### S11.5 — GitHub: Dashboard Proiecte cu Issues și Pull Requests
**Descriere:** Dashboard cu toate repo-urile tale GitHub: issues deschise, PR-uri în așteptare, commit-uri recente, status CI/CD. Poți crea issues direct din Command Center.  
**Exemplu:** Lucrezi la Command Center și găsești un bug. Deschizi modulul GitHub din Command Center, creezi issue "Bug: DOCX→PDF fail pe fișiere >10MB" fără să deschizi GitHub.com.  
**Valoare:** Medie — confort pentru workflow de development.

### S11.6 — Notificări Email Unificate cu Digest
**Descriere:** În loc de notificări individuale per email, sistemul agregă alertele din zi și trimite un singur email zilnic de digest la ora configurată: rezumat facturi, ITP-uri, backup, erori.  
**Exemplu:** Ora 08:00: "Digest zilnic CIP Inspection: 2 ITP-uri expiră în 15 zile, 1 factură restantă +10 zile, backup OK, 0 erori sistem."  
**Valoare:** Mare — reduci email noise, o singură verificare pe zi.

### S11.7 — Integrare Google Contacts pentru Auto-Complete Clienți
**Descriere:** Sincronizare cu Google Contacts — la introducerea unui email sau nume de client, auto-complete din contactele Google. Dacă adaugi un client nou în Command Center, se adaugă și în Google Contacts.  
**Exemplu:** Scrii "Bosc..." în câmpul client la factură → auto-complete sugerează "Bosch Romania — contact@bosch.ro" din Google Contacts. Nu mai cauți manual datele de contact.  
**Valoare:** Medie-mare — eliminare introducere duplicate a datelor.

### S11.8 — GitHub: Auto-Commit Backup Configurații
**Descriere:** La fiecare modificare majoră de configurație (reguli Vault, template-uri, glosar), sistemul face auto-commit în repo GitHub cu mesaj descriptiv. Versionare automatizată a configurațiilor.  
**Exemplu:** Adaugi 10 termeni noi în Glosar Tehnic → commit automat: "chore: add 10 terms to technical glossary (auto-backup 2026-03-19)". Dacă strici accidental glosarul, `git revert` salvează situația.  
**Valoare:** Medie — siguranță pentru configurații importante.

### S11.9 — Integrare Slack / Telegram pentru Notificări
**Descriere:** Trimiți notificări importante pe Slack (dacă folosești) sau Telegram bot (gratuit, ușor de configurat) în loc de email. Mai rapid de văzut pe telefon.  
**Exemplu:** Task scheduler eșuat la 02:00. La 08:00 deschizi Telegram și ai mesajul: "@RolandBot: ❌ Backup task failed — Error: Drive quota exceeded. Acțiune necesară."  
**Valoare:** Medie-mare pentru alerte critice în timp real pe telefon.

### S11.10 — Status Page Integrări cu Auto-Reconnect
**Descriere:** Status dashboard extins (există deja unul basic): test automat periodic per integrare (Gmail IMAP ping, Drive auth, Calendar auth, GitHub token valid), cu auto-refresh token dacă expirat.  
**Exemplu:** Token Drive expirat (refresh tokens durează 6 luni). Dashboard arată ⚠️ Drive: token expirat. Buton "Reconnect" → re-autentificare fără să cauți manualul de configurare.  
**Valoare:** Mare — disponibilitate crescută a integrărilor, debug rapid.

---

## 12. Modul: Rapoarte & Statistici

> **Status actual:** Disk stats, system info (Python, OS, uptime), timeline activitate (BarChart), fișiere neutilizate, jurnal personal cu mood, bookmarks grupate pe categorii, export complet JSON, file stats per extensie.

### S12.1 — Dashboard KPI Business (Tablou de Bord Executiv)
**Descriere:** Un singur ecran cu toți indicatorii cheie ai businessului: venituri luna curentă vs. luna precedentă, număr clienți activi, traduceri procesate, ITP-uri efectuate, facturi restante, tendință ultimele 6 luni.  
**Exemplu:** Ecranul principal Reports arată: "Martie 2026: 14.200 RON venituri (+8% vs. Feb), 23 clienți activi, 34 traduceri, 127 ITP-uri, ⚠️ 2 facturi restante (3.400 RON)."  
**Valoare:** Foarte mare — o privire și știi cum stă businessul.

### S12.2 — Raport Comparativ An vs. An (YoY)
**Descriere:** Grafic comparativ cu aceeași perioadă din anul precedent: venituri, volum ITP, volum traduceri. Evidențiază creșterea sau scăderea.  
**Exemplu:** "Q1 2026 vs Q1 2025: Venituri +22% (38.400 vs 31.500 RON). ITP-uri +8% (387 vs 358). Traduceri +35% (102 vs 75 documente). Trend: creștere sănătoasă."  
**Valoare:** Mare — perspectivă strategică, date pentru planificarea anului următor.

### S12.3 — Raport Productivitate Personală
**Descriere:** Analiză a activității tale în aplicație: ore active per zi, module cele mai folosite, vârfuri de activitate (ore, zile săptămână), streak-uri (zile consecutive de utilizare).  
**Exemplu:** "Săptămâna trecută: activ 38h, modulele cele mai utilizate: Translator (12h), Calculator (8h), AI (7h). Vârf de activitate: Marți 09:00-12:00. Streak curent: 14 zile consecutive."  
**Valoare:** Medie — self-awareness, optimizare program de lucru.

### S12.4 — Raport Export Complet per Modul (Nu Doar JSON Global)
**Descriere:** Export individual per modul: toate calculele ca Excel, toate traducerile ca CSV, toate ITP-urile ca Excel, toate facturile ca PDF/Excel. Filtrabil pe perioadă.  
**Exemplu:** Contabilul cere evidența ITP pe trimestrul 1. Dai Export > Modul ITP > Q1 2026 > Excel → fișier structurat cu toate câmpurile relevante, gata de trimis.  
**Valoare:** Mare — flexibilitate la export față de un singur JSON global.

### S12.5 — Predicții Business (AI-Powered)
**Descriere:** AI analizează datele istorice și face predicții: "La ritmul actual, vei depăși 200.000 RON venituri anuale pentru prima dată în 2026." Sau: "Sezonul ITP de vară (mai-iulie) a generat istoric 35% din veniturile anuale."  
**Exemplu:** "Bazat pe ultimele 18 luni de date: prognoz venituri Aprilie 2026: 15.800-17.200 RON (interval 80% confidence). Factori: creștere 8%/lună + sezonalitate ITP."  
**Valoare:** Mare — planificare financiară bazată pe date reale.

### S12.6 — Jurnal cu Căutare Full-Text și Export
**Descriere:** Jurnalul personal (existent) extins cu: căutare fulltext în toate intrările, export ca PDF/DOCX (jurnal frumos formatat), statistici mood (câte intrări per mood pe an), linkuri între intrări.  
**Exemplu:** Cauți în jurnal "Bosch" → găsești toate zilele în care ai menționat clientul Bosch. Exportezi ultimele 3 luni ca PDF — document de reflecție personală sau jurnal de proiect.  
**Valoare:** Medie.

### S12.7 — Heatmap Calendar Activitate (GitHub-Style)
**Descriere:** Calendar heatmap pe tot anul: fiecare zi e colorată în funcție de activitate totală (calcule + traduceri + ITP + alte acțiuni). Verde intens = zi productivă, alb = zi liberă.  
**Exemplu:** Heatmap 2026 arată clar: verde intens lunile ianuarie-martie, galben în august (concediu), roșu în decembrie 2025 (perioadă dificilă). Vizualizare anuală a productivității.  
**Valoare:** Medie — motivație, auto-awareness.

### S12.8 — Raport Utilizare API (Costuri Potențiale)
**Descriere:** Raport cu toți providerii AI și de traducere: apeluri totale, tokeni consumați, echivalent cost dacă ai fi pe tier plătit. Arată valoarea reală a tier-urilor gratuite utilizate.  
**Exemplu:** "Luna Martie: Gemini Flash — 1.240 apeluri, ~2.1M tokens (valoare echivalentă: ~$21 dacă plătit). DeepL — 280.000 chars ($14 echivalent). Total economii free tier: ~$35/lună."  
**Valoare:** Medie — awareness despre valoarea reală a resurselor gratuite folosite.

### S12.9 — Alertă Anomalii (Activitate Neobișnuită)
**Descriere:** Sistemul detectează automat anomalii: volum neobișnuit de mare (posibil bug în scheduler), volum neobișnuit de mic (serviciu oprit), erori repetate, consum API anormal.  
**Exemplu:** Schedulerulul rulează un task de 500 de ori în 10 minute din cauza unui bug (loop). Sistemul detectează: "Anomalie: task X a rulat de 500 de ori în 10 minute (normal: 1 dată/zi). Scheduler oprit automat."  
**Valoare:** Mare — self-healing parțial, previne costuri sau degradarea sistemului.

### S12.10 — Raport Satisfacție Client (Manual)
**Descriere:** Sistem simplu de urmărire satisfacție clienți: după fiecare livrare, notezi manual scorul (1-5) și un comentariu scurt. Statistici: scor mediu per client, per tip serviciu, tendință.  
**Exemplu:** Client Bosch, traducere contract, scor 5/5 "foarte mulțumit, livrare rapidă". Client Dacia, manual tehnic, scor 3/5 "terminologie inconsistentă pe pagina 15". Statistici: scor mediu 4.2/5 în martie.  
**Valoare:** Medie — urmărire calitate servicii, date pentru îmbunătățire.

---

## 13. Modul: Quick Tools Extra

> **Status actual:** Conținut incert din documentație — probabil extensie a Quick Tools cu tool-uri suplimentare. Claude Code să verifice ce există în `backend/modules/quick_tools_extra/` și să completeze analiza.

### S13.1 — Clipboard Manager Avansat (vs. Win+V Basic)
**Descriere:** Clipboard history cu căutare, categorii, pin la favorite, sync între PC și telefon (via backend). Mai avansat decât Win+V nativ.  
**Notă:** Era exclus din plan (Win+V existent), dar sinc PC-Android îl diferențiază.  
**Exemplu:** Copiezi un IBAN pe PC. Deschizi Command Center pe telefon → Clipboard → găsești IBAN-ul copiat mai devreme. Sync bidirecțional via backend Tailscale.  
**Valoare:** Mare — sync clipboard PC↔Android e ceva ce Win+V nu face.

### S13.2 — Focus Timer (Pomodoro Adaptat)
**Descriere:** Timer customizabil: 25/45/60 min focus + pauze. Corelat cu Jurnalul — la sfârșitul unui focus block, îți cere: "Ce ai realizat?" Statistici săptămânale focus time.  
**Notă:** Era exclus din plan, dar integrarea cu jurnalul îl diferențiază de un simplu timer.  
**Exemplu:** Pornești un focus block de 45 min. La final: "Ce ai realizat?" — notezi "Tradus 12 pagini contract Bosch". Jurnalul arată automat că ai petrecut 3h de focus pe traduceri în această zi.  
**Valoare:** Medie.

### S13.3 — Snippet Manager (Texte Frecvente)
**Descriere:** Colecție de texte pe care le folosești des: anteturi emailuri, clauze contractuale standard, semnături, termeni și condiții, răspunsuri frecvente la clienți. Accesibile din Command Palette.  
**Notă:** Era exclus din plan (VS Code snippets), dar pentru texte business (nu cod) e diferit.  
**Exemplu:** Tastezi în Command Palette "clauza confidentialitate" → apare clauza standard pe care o copiezi în contractul curent. Nu mai cauți prin fișiere vechi.  
**Valoare:** Mare pentru texte de business frecvente.

### S13.4 — Convertor Markdown ↔ HTML ↔ Text
**Descriere:** Convertești rapid între Markdown, HTML și text plain. Preview live al rezultatului.  
**Exemplu:** Ai un email scris în Markdown (cu **bold** și - liste). Convertești în HTML pentru a-l trimite formatat în Gmail. Sau convertești HTML copiat de pe un site în text plain curat fără tag-uri.  
**Valoare:** Medie.

### S13.5 — Generator Contracte Rapide (Mini-Wizard)
**Descriere:** Wizard cu 5 pași care generează un contract simplu de prestări servicii: selectezi tipul (traducere / ITP / serviciu general), completezi câmpurile (client, sumă, termen), primești DOCX gata.  
**Exemplu:** Client nou fără contract propriu. Parcurgi wizard-ul în 2 minute: selectezi "Contract Traducere", introduci datele, dai "Generează" → Contract_Prestari_Bosch_2026-03-19.docx gata de semnat.  
**Valoare:** Mare — CIP Inspection are nevoie de contracte pentru fiecare prestare de servicii.

### S13.6 — Scurtături de Navigare Personalizate (Bookmarklete)
**Descriere:** Definești scurtături de navigare rapide pentru URL-uri frecvente (portal RAR, ANAF, portal instanță, portal OSIM, furnizori). Accesibile din Command Palette sau un panel dedicat.  
**Exemplu:** Apeși Ctrl+K → tastezi "RAR" → se deschide portal.mfinante.gov.ro/etax sau oricare URL configurat de tine. Nu mai cauți bookmark-uri în browser.  
**Valoare:** Medie — confort zilnic.

### S13.7 — Notepad Colaborativ (Shared Notes via Tailscale)
**Descriere:** Un notepad special vizibil de pe toate device-urile (PC + telefon) în timp real, util pentru a transfera text rapid între dispozitive fără email/WhatsApp cu tine însuți.  
**Exemplu:** Ești pe telefon și vrei să trimiți rapid un text pe PC. Scrii în "Shared Notepad" de pe telefon. Pe PC apare instant (via WebSocket Tailscale). Copiezi pe PC. Funcționează ca un clipboard cross-device.  
**Valoare:** Mare — rezolvă exact nevoia de transfer rapid PC↔telefon.

### S13.8 — Calculator TVA și Declarații Fiscale Simple
**Descriere:** Calculator specializat pentru nevoile fiscale ale CIP Inspection: calculul TVA (dacă e înregistrat ca plătitor TVA), impozit pe venit PFA/SRL, calcul dividende.  
**Exemplu:** Introduci veniturile trimestrului Q1: 42.000 RON. Calculatorul arată: impozit pe venit 16% = 6.720 RON, contribuții sociale dacă aplicabil, net de plătit contabilului la termen.  
**Valoare:** Mare — tool util zilnic/trimestrial pentru planificare fiscală.

### S13.9 — Metronom / Instrument Tempo (Scos din Context Business)
**Descriere:** Acest tip de tool nu are relevanță pentru CIP Inspection SRL.  
**Recomandare:** Înlocuiește cu **Generator Numere de Înmatriculare Format Valid** — validator și generator de numere de înmatriculare în format ARO (AB-01-XXX) pentru modulul ITP.  
**Exemplu:** Introduci un număr parțial "B-12-" → sugestii format valid. Sau validezi dacă un număr introdus de client respectă formatul corect înainte de a-l salva în baza de date ITP.  
**Valoare:** Medie pentru ITP.

### S13.10 — To-Do List cu Priorități și Deadline (GTD Lite)
**Descriere:** Task manager simplu, diferit de Notepad: tasks cu status (To Do / În Lucru / Finalizat), prioritate (Urgent/Normal/Low), deadline, categorie (Clienți/Admin/Tehnic).  
**Exemplu:** Tasks de astăzi: 🔴 Urgent "Trimite factură Bosch — deadline 15:00", 🟡 Normal "Actualizează glosarul cu termeni Continental", 🟢 Low "Verifică backup drive".  
**Valoare:** Mare — organizare zilnică, complementar cu Jurnalul (retrospectiv) și Calendar (planificat).

---

## 14. Analiză Generală Proiect

### 14.1 — Perspectivă Generală

Roland Command Center este un proiect ambițios și bine executat tehnic. Conform `PLAN_EXECUTIE.md`, 18 faze majore au fost implementate în **3 zile intensive** (2026-03-17 → 2026-03-19), ceea ce arată o arhitectură bine planificată și un flux de lucru extrem de disciplinat. Baza e solidă: arhitectura modulară, sistemul de migrări DB, Tailscale HTTPS, PWA, Vault criptat — toate sunt decizii tehnice corecte pentru cazul de utilizare.

**Puncte forte clare:**
- Arhitectură modulară scalabilă (auto-discovery backend + manifest frontend)
- Zero cost operațional — folosirea inteligentă a free tier-urilor
- Acces multi-device confirmat funcțional: `https://desktop-cjuecmn.tail7bc485.ts.net:8000`
- AI integrat în fiecare modul (15B.1-15B.10), nu izolat într-un chatbot separat
- Disciplina de documentare exemplară: `CLAUDE.md` (restructurat la 116 linii), `GHID_TESTARE.md` (instrucțiuni per funcție cu status ✅/🧪/❌), `ANALIZA_FISIERE.md` (228 fișiere catalogate), `CHANGELOG_RULES.md`, `.claude/rules/` (5 fișiere reguli auto-încărcate)
- Logging persistent: `RotatingFileHandler` backend + raportare erori frontend (Faza 15A)
- Silent launcher: `START_Silent.vbs` + `STOP_Silent.bat` — zero ferestre terminal vizibile

---

### 14.2 — Slăbiciuni Identificate

#### 🔴 Critice (pot cauza probleme serioase)

**W1 — Testarea pe Android este incompletă**
Din `GHID_TESTARE.md` (existent în `99_Roland_Work_Place/`): multe funcții sunt marcate "🧪 Netestat" pe telefon — în special în Convertor, File Manager și module noi. Riscul real: funcții care par DONE dar se sparg la primul test pe telefon.  
*Corecție față de versiunea anterioară:* `GHID_TESTARE.md` **există deja** și conține instrucțiuni "Test Telefon" per funcție. Ceea ce lipsește nu e documentul ci **execuția** testelor marcate 🧪. Accesează `https://desktop-cjuecmn.tail7bc485.ts.net:8000` de pe Android și parcurge sistematic toate itemele din GHID_TESTARE.md.

**W2 — DOCX→PDF depinde de Microsoft Word instalat (COM)** *(parțial rezolvat)*
`docx2pdf` pe Windows folosește COM automation — Word trebuie instalat. **Fix parțial aplicat deja** în Faza 12: `pythoncom.CoInitialize()` rezolvă crashurile în contexte threaded (FastAPI async). Rămâne totuși o dependință de Word ca aplicație instalată.  
*Recomandare:* Adaugă un fallback explicit: dacă `docx2pdf` eșuează → încearcă `libreoffice --headless --convert-to pdf` (LibreOffice, gratuit). Testează pe o mașină fără Word pentru a confirma fallback-ul funcționează.

**W3 — 53 tabele SQLite fără optimizare explicită**
53 tabele în SQLite cu 14 migrări — nu e neapărat o problemă acum, dar pe termen lung, fără indecși corecți și VACUUM periodic, query-urile lente vor apărea, mai ales pe FTS5.  
*Recomandare:* Adaugă un task schedulat săptămânal de `VACUUM` și `ANALYZE` pe SQLite. Verifică că FTS5 are indecșii corecți pe câmpurile căutate frecvent.

#### 🟡 Importante (afectează calitatea dar nu blochează)

**W4 — Nu există mecanism de rollback DB (doar forward migrations)**
Dacă o migrare eșuează la jumătate, DB-ul poate rămâne în stare inconsistentă. Nu există migrări inverse (down migrations).  
*Context din proiect:* `backup.py` există și sincronizează DB-ul cu Google Drive (implementat în Wave 1). Aceasta atenuează riscul — poți restaura manual din backup. Riscul real rămâne la migrările parțial executate.  
*Recomandare:* Adaugă în `run_migrations()` un `BEGIN TRANSACTION` / `ROLLBACK` per migrare. Dacă o migrare eșuează, DB-ul revine la starea anterioară automat.

**W5 — Gestionarea erorilor frontend nu e uniformă**
Implementat rapid în mai multe sesiuni, există riscul că unele module au error handling bun (try/catch + toast) și altele au erori care dispar în console fără feedback vizibil utilizatorului.  
*Recomandare:* Audit rapid al tuturor fetch()-urilor din React — verifică că fiecare are .catch() cu toast de eroare vizibil.

**W6 — MAPE 32% la calculator — sub ținta de 25%**
Calculatorul de bază (core feature) nu e la performanța dorită.  
*Recomandare:* Prioritizează implementarea S1.1 (calibrare interactivă) — e investiție mică, impact mare pe exactitate.

**W7 — Integrările Gmail/Drive folosesc SMTP/IMAP în loc de OAuth**
SMTP/IMAP cu App Password funcționează, dar Google poate depreca App Passwords în viitor. Limitări: nu poți citi etichete Gmail complexe, nu poți accesa Drive Shared Drives.  
*Recomandare:* Nu e urgent acum, dar planifică migrarea la OAuth 2.0 pe termen mediu (6-12 luni).

**W8 — Notificările unificate sunt DEFERRED**
Fără un centru de notificări, alertele importante (ITP expirat, factură restantă, backup eșuat) sunt probabil dispersate sau absente. Aceasta reduce dramatic valoarea practică a modulelor de alertare.  
*Recomandare:* Finaliza notificările unificate (S10.1) este probabil cea mai impactantă investiție în experiența de utilizare a întregii aplicații.

#### 🟢 Minore (polish, quality of life)

**W9 — Voice Notes DEFERRED**
Feature-ul care ar crește cel mai mult utilitatea pe mobile (exact cazul de față — discuția din mașină) este deferred fără motiv tehnic major.

**W10 — Dark/Light mode DEFERRED**
Aplicația e dark-first. Pe unele telefoane Android și în condiții de lumină puternică (în mașină la soare), un mod light ar fi mai ușor de citit.

---

### 14.3 — Sugestii de Îmbunătățire Arhitecturală

**A1 — Introducere Queue pentru Task-uri Asincrone Grele**
OCR batch, traduceri fișiere mari, export rapoarte mari — toate rulează în FastAPI BackgroundTasks. Aceasta e OK pentru sarcini mici, dar pentru 20+ fișiere simultan, riscă să blocheze procesul. Soluție simplă: o coadă bazată pe SQLite (un tabel `task_queue` cu status) procesată de un worker periodic.

**A2 — Caching Layer pentru Date Frecvent Accesate**
Dashboard-ul și rapoartele fac probabil multiple query-uri SQLite la fiecare vizită. Adaugă un cache simplu in-memory (Python `functools.lru_cache` sau un dict simplu) pentru query-urile agregative care nu se schimbă în ultimul minut.

**A3 — Separarea Configurației de Cod (Config File)**
Parametri ca `MAPE target`, `DeepL limit 500K`, `backup retention 30 days`, `alert thresholds` sunt probabil hardcoded în cod sau în DB fără UI. Un fișier `config.yaml` sau un modul "Setări" în UI ar permite ajustarea fără a edita cod.

**A4 — Health Check Endpoint Îmbunătățit**
`/api/health` există, dar adaugă și `/api/health/detailed` care returnează: status per modul (OK/degraded/down), ultima eroare per modul, timestamp ultima activitate per modul. Util pentru monitoring și debugging.

**A5 — Logging Unificat: Extindere și UI de Vizualizare** *(fundația există)*
`RotatingFileHandler` + raportare erori frontend sunt **deja implementate** în Faza 15A. Ceea ce lipsește este un **UI de vizualizare** a log-urilor direct din browser — endpoint `/api/logs` cu filtre per modul, per nivel (INFO/WARN/ERROR), per interval de timp.  
*Exemplu:* Ceva nu merge cu Gmail. Deschizi "Logs" din Command Center, filtrezi: modul=integrations, nivel=ERROR, ultimele 24h → găsești eroarea în 3 secunde fără să accesezi fișierul fizic de pe Windows.

---

### 14.4 — Prioritizare Recomandată pentru Sesiunile Următoare

| Prioritate | Sugestie | Motivare | Efort estimat |
|-----------|---------|---------|--------------|
| 🔴 1 | **Testare sistematică Android** (toate modulele) | Funcții DONE dar netestate = funcții broken nedescoperite | 1-2 sesiuni |
| 🔴 2 | **Notificări Unificate (S10.1)** — finalizare feature deferred | Cel mai mare impact pe UX — agregă toate alertele | 1-2 sesiuni |
| 🟡 3 | **Voice Notes (S6.1)** — finalizare feature deferred | Utilitate maximă pe mobile/Android | 0.5 sesiuni |
| 🟡 4 | **Calibrare MAPE Interactivă (S1.1)** | Calculator core feature sub target calitativ | 1 sesiune |
| 🟡 5 | **Sesiuni Chat Salvate (S2.1)** | Transforma AI chat din tool izolat în asistent persistent | 1-2 sesiuni |
| 🟡 6 | **Prompt Templates (S2.2)** | Elimina rescrierea acelorași prompturi | 0.5 sesiuni |
| 🟡 7 | **Status Plată Facturi (S4.3)** | Cash flow management direct | 1 sesiune |
| 🟢 8 | **Backup Automat Drive (S8.8)** | Protecție date critice business | 1 sesiune |
| 🟢 9 | **Dashboard KPI Business (S12.1)** | Vizibilitate completă businessului | 1 sesiune |
| 🟢 10 | **Macro Recorder (S10.4)** | Automatizare fluxuri de lucru complete | 2-3 sesiuni |

---

### 14.5 — Concluzie

Proiectul este remarcabil ca volum și viteză de implementare. Riscul principal acum nu este lipsa funcționalităților, ci **stabilitatea și testarea** celor existente. Recomand să rezisti tentației de a adăuga imediat 130 de funcții noi din lista de mai sus și să urmezi această ordine:

1. **Testează și stabilizezi** ce există (mai ales Android)
2. **Finalizezi feature-urile DEFERRED** (notificări, voice notes)
3. **Adaugi funcționalități noi** în ordinea priorităților de mai sus

Funcționalitățile cu cel mai mare raport valoare/efort pentru businessul tău specific (CIP Inspection — ITP + traduceri) sunt: alertele ITP pe email/SMS clienți, status plată facturi, sesiuni AI persistente, și calibrarea calculatorului sub 25% MAPE.

---

*Document generat: 2026-03-19 | Actualizat cu context complet: 2026-03-19*  
*Surse: `CLAUDE.md` + `0_0_PLAN_EXTINDERE_COMPLET.md` + `PLAN_EXECUTIE.md` + `ANALIZA_FISIERE.md` + `GHID_TESTARE.md` + `Documentare_Extindere_Proiect.md` + `CHANGELOG_RULES.md` + `backend/CLAUDE.md` + `frontend/CLAUDE.md`*  
*Vers. 1.1 — Pentru revizuire Claude Code în contextul folderului `99_Roland_Work_Place/`*
