# Roland Command Center — 12 Zone de Îmbunătățire 100% Gratuite

> **Generat:** 2026-03-19  
> **Condiție strictă:** Toate funcțiile din acest document sunt implementabile și funcționabile **exclusiv gratuit**, fără niciun abonament sau cost recurent.  
> **Instrucțiuni pentru Claude Code:** Analizează fiecare sugestie din perspectiva stack-ului existent (FastAPI Python 3.13 + React 18 + SQLite + `backend/modules/` + `.claude/rules/`). Marchează fiecare item ca [FEZABIL], [FEZABIL CU EFORT MARE] sau [EXCLUDE] cu justificare. Prioritizează după valoarea pentru CIP Inspection SRL.

---

## CUPRINS

1. [Securitate & Privacy Audit](#1-securitate--privacy-audit)
2. [Performanță & Optimizare Tehnică](#2-performanță--optimizare-tehnică)
3. [Experiență Mobilă Android-First](#3-experiență-mobilă-android-first)
4. [AI Strategy — Maximizare Cotă Gratuită prin Key Rotation](#4-ai-strategy--maximizare-cotă-gratuită-prin-key-rotation)
5. [Notificări & Integrări Gratuite (înlocuiește SMS plătit)](#5-notificări--integrări-gratuite)
6. [Business Intelligence & Rapoarte Avansate](#6-business-intelligence--rapoarte-avansate)
7. [Backup, Recovery & Business Continuity](#7-backup-recovery--business-continuity)
8. [Testing Strategy Automată](#8-testing-strategy-automată)
9. [UI/UX Design System & Consistență Vizuală](#9-uiux-design-system--consistență-vizuală)
10. [DevOps & Workflow Dezvoltator](#10-devops--workflow-dezvoltator)
11. [Documentație Utilizator Final](#11-documentație-utilizator-final)
12. [Automatizare Fluxuri Cross-Module](#12-automatizare-fluxuri-cross-module)

---

## 1. Securitate & Privacy Audit

> **Cost: 0 EUR — modificări de cod pure, fără dependințe externe plătite**

### Ce se analizează și îmbunătățește

**1.1 — Path Traversal în File Manager (sandboxing)**
Sandboxing-ul există (`allowed_roots` + `pathlib.resolve()`) dar nu a fost testat sistematic cu input malițios. Verificare: încearcă accesul la `../../../Windows/System32` din UI — dacă returnează eroare 403 (nu 500 sau conținut real), e OK. Dacă nu → fix `resolve()` chain.

**1.2 — Validarea input-urilor în toate endpoint-urile FastAPI**
53 tabele SQLite = 53+ seturi de câmpuri care intră din frontend. Verifică că toate rutele folosesc modele Pydantic cu validare strictă (tipuri, lungimi maxime, caractere permise), nu doar `dict` simplu. Fără Pydantic → SQL injection posibil chiar și cu aiosqlite.

**1.3 — Audit endpoint-uri FastAPI fără autentificare**
Toate endpoint-urile sunt publice (Tailscale = autentificare la nivel de rețea). Dacă cineva accesează rețeaua Tailscale (ex: dispozitiv compromis adăugat accidental), are acces complet. Soluție minimă: middleware FastAPI care verifică un header `X-Internal-Token` simplu (stocat în Vault), fără JWT complex.

**1.4 — Secretele din Vault vs. fișiere .env**
Verifică că nicio cheie API nu e hardcodată în cod sau în fișiere `.env` commituite în Git. `.gitignore` trebuie să excludă explicit: `.env`, `*.env`, `backend/data/*.json` (conțin calibrări cu posibil date sensibile), `backend/data/*.db`.

**1.5 — Securitatea fișierelor uploadate**
Validarea magic bytes există, dar verifică că fișierele uploadate sunt servite cu `Content-Disposition: attachment` (nu inline) pentru tipuri executabile. Un `.html` uploadat și servit inline poate executa JavaScript în browser.

**1.6 — CORS policy restrictivă**
CORS dinamic există. Verifică că `allow_origins` nu conține `*` în producție și că lista include doar originile Tailscale reale. Un `*` în CORS + endpoint fără token = oricine cu acces la rețea poate face requests din orice pagină web.

**1.7 — Rate limiting pe endpoint-urile AI**
Endpoint-urile `/api/ai/*` apelează provideri externi. Fără rate limiting local, un loop accidental (sau un bug în frontend) poate epuiza cota gratuită în minute. Adaugă `slowapi` (gratuit, FastAPI-compatibil) sau un simplu `asyncio.Semaphore` per provider.

**1.8 — Audit dependințe Python pentru vulnerabilități cunoscute**
Rulează `pip audit` sau `safety check` (gratuit, open-source) pe `requirements.txt`. Identifică pachete cu CVE-uri cunoscute. Planifică update-uri periodice.

**1.9 — Protecție împotriva directory listing**
Verifică că FastAPI nu servește listing de directoare pentru folderele statice. `StaticFiles(directory=...)` cu `html=False` nu listează, dar verifică comportamentul real.

**1.10 — Logging securizat (fără date sensibile în logs)**
`RotatingFileHandler` există. Verifică că log-urile nu conțin: chei API, parole, CNP-uri din documente OCR, conținut din traduceri confidențiale. Adaugă un filtru de logging care maschează pattern-urile sensibile (regex pe output).

---

## 2. Performanță & Optimizare Tehnică

> **Cost: 0 EUR — optimizări de cod și configurare, fără servicii externe**

### Ce se optimizează

**2.1 — Indecși SQLite lipsă (impact direct pe viteza paginilor)**
Cu 53 tabele și date crescânde, query-urile fără index devin lente. Rulează `EXPLAIN QUERY PLAN` pe cele mai frecvente query-uri (dashboard, history, ITP list, translator history). Adaugă `CREATE INDEX` pentru coloanele din `WHERE`, `ORDER BY`, `JOIN`. Exemplu garantat util: `CREATE INDEX idx_activity_timestamp ON activity_log(timestamp DESC)`.

**2.2 — VACUUM și ANALYZE periodic (SQLite maintenance)**
SQLite nu se auto-optimizează. Adaugă un task schedulat săptămânal (APScheduler există deja) care rulează `VACUUM` (compactare) și `ANALYZE` (actualizare statistici query planner). Impact: reducere dimensiune DB cu 10-30%, query-uri cu 5-20% mai rapide după inserții/ștergeri masive.

**2.3 — Caching in-memory pentru query-urile dashboard**
Dashboard-ul și rapoartele rulează probabil aceleași query-uri SQLite agregative la fiecare vizită. Adaugă un dict Python simplu cu TTL de 60 secunde pentru rezultatele query-urilor lente. `functools.lru_cache` nu funcționează cu async — folosește un dict `{cache_key: (result, timestamp)}`.

**2.4 — React bundle size și lazy loading**
Cu 22+ pagini, bundle-ul React inițial este probabil mare. Adaugă `React.lazy()` + `Suspense` pentru paginile rar accesate (ITP, Automatizări, Rapoarte). Vite suportă code splitting automat cu import dinamic. Impact: timp de încărcare inițială redus cu 30-50%.

**2.5 — WebSocket connection pooling**
Verifică că WebSocket-ul pentru SSE streaming AI nu se reconectează la fiecare request. O singură conexiune persistentă per sesiune este mai eficientă. `useEffect` cleanup în React trebuie să închidă conexiunea la unmount.

**2.6 — Debounce și throttle pe search inputs**
Câmpurile de căutare (File Manager FTS5, Translator history, ITP search) trimit probabil query-uri la fiecare keystroke. Adaugă debounce de 300ms pe toate câmpurile de căutare. Deja există un precedent bun: Notepad auto-save are debounce 800ms.

**2.7 — BackgroundTasks vs. queue pentru operații grele**
OCR batch, traduceri fișiere mari, export rapoarte mari rulează în `FastAPI BackgroundTasks`. Pentru mai mult de 3-4 operații simultane, procesul se blochează. Adaugă un tabel SQLite `task_queue` cu status (pending/running/done/failed) și un worker `asyncio` care procesează câte 2 task-uri simultan.

**2.8 — Service Worker cache strategy optimizată**
PWA-ul are Service Worker cu Workbox. Verifică că strategia de cache este `NetworkFirst` pentru API calls și `CacheFirst` pentru assets statice. O strategie greșită poate servi date vechi din cache mult timp după update.

**2.9 — Compresie gzip pe răspunsurile FastAPI**
Adaugă `from fastapi.middleware.gzip import GZipMiddleware` în `app/main.py`. Un singur rând de cod care reduce cu 60-80% dimensiunea răspunsurilor JSON mari (history, rapoarte, export). Compatibil cu toate browserele.

**2.10 — Paginare pe toate endpoint-urile de listare**
Verifică că toate endpoint-urile care returnează liste au parametri `limit` și `offset`. Un endpoint care returnează toate cele 10.000 de traduceri din istoric fără paginare va îngheța UI-ul. Standardizează la `limit=50, offset=0` implicit pe toate modulele.

---

## 3. Experiență Mobilă Android-First

> **Cost: 0 EUR — modificări frontend + PWA, fără servicii externe**

### Ce se îmbunătățește pentru Android

**3.1 — Voice Input via Web Speech API (offline, fără API extern)**
Web Speech API este disponibil în Chrome Android fără nicio cheie API sau cost. Adaugă un buton microfon în câmpul de chat AI și în câmpul de căutare. Vorbești → textul apare automat. Exact scenariul conversației din mașină. Implementare: `window.SpeechRecognition || window.webkitSpeechRecognition`, ~30 linii JavaScript.

**3.2 — Touch targets dimensionate corect (minimum 44×44px)**
Butoanele mici din desktop pot fi greu de apăsat pe telefon. Adaugă `min-h-[44px] min-w-[44px]` (Tailwind) pe toate butoanele din paginile frecvent folosite pe Android: Calculator, Translator, ITP, File Manager.

**3.3 — Pull-to-refresh pe paginile cu date live**
Implementare nativă în React cu `react-pull-to-refresh` (open-source) sau manual cu `touchstart`/`touchmove` events. Util pentru ITP list, History, Dashboard — reîncarcă datele fără să navighezi departe și înapoi.

**3.4 — Mod offline parțial extins**
Service Worker cachează 9 fișiere. Extinde la: ultimele 50 calcule din history (localStorage), setările din Vault (criptat în IndexedDB), glosarul de traduceri (FTS5 → cache local). Paginile Calculator și Notepad ar trebui să funcționeze complet offline.

**3.5 — Share Sheet nativ Android**
Adaugă buton "Partajează" pe rezultatele calculatorului și pe facturile PDF generate. Folosește `navigator.share()` (Web Share API) — disponibil în Chrome Android 61+, fără instalare. Permite trimiterea rapidă via WhatsApp, Email, SMS din aplicație.

**3.6 — Camera access pentru OCR rapid**
Adaugă un buton "Fotografiază document" în modulul OCR Quick (Ctrl+Shift+O existent). `<input type="file" accept="image/*" capture="environment">` deschide camera Android direct, fără permisiuni complexe. Fotografia merge direct la endpoint-ul OCR existent.

**3.7 — Swipe gestures pe liste**
Implementează swipe-left pe itemele din ITP list (→ Delete/Edit), History (→ Copy price), File Manager (→ Download/Delete). `react-swipeable` (open-source, 2kB) sau CSS `touch-action` nativ. Interacțiune mult mai naturală pe Android.

**3.8 — Prevenire zoom neintențional pe input-uri**
Pe iOS/Android, input-urile cu `font-size < 16px` declanșează zoom automat. Adaugă `font-size: 16px` pe toate câmpurile input din formulare. Alternativ: `<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">` (limitează zoom).

**3.9 — Notificări push native Android via PWA**
Web Push API funcționează în Chrome Android fără aplicație nativă. Backend: `pywebpush` (Python, gratuit). Frontend: `Notification.requestPermission()` + `ServiceWorkerRegistration.pushManager.subscribe()`. Permite notificări native pentru: ITP expirat, factură restantă, task schedulat finalizat — chiar când aplicația e închisă.

**3.10 — Bottom Navigation Bar pe Android (înlocuiește sidebar)**
Pe ecrane mici, sidebar-ul colapsibil nu e ideal. Adaugă o bară de navigare jos cu 4-5 iconițe pentru modulele cel mai folosite (Dashboard, Calculator, Translator, ITP, AI). React component responsive: afișează sidebar pe desktop, bottom bar pe mobil (`useMediaQuery`).

---

## 4. AI Strategy — Maximizare Cotă Gratuită prin Key Rotation

> **Cost: 0 EUR — toți providerii menționați au free tier permanent fără card bancar**

### Provideri AI gratuiți verificați (2025-2026)

Proiectul are deja un fallback chain (Gemini → OpenAI → Groq). Acesta se extinde cu 4 provideri noi, toți cu free tier permanent:

| Provider | Free tier | Limită cheie | Signup | Compatibilitate |
|----------|-----------|--------------|--------|-----------------|
| **Cerebras** | 1.000.000 tokeni/zi | Permanent, fără card | cloud.cerebras.ai | OpenAI-compatibil ✅ |
| **Mistral AI** | ~1 miliard tokeni/lună | 2 req/minut | console.mistral.ai | OpenAI-compatibil ✅ |
| **SambaNova** | 200.000 tokeni/zi | 20 req/zi/model | sambanova.ai | OpenAI-compatibil ✅ |
| **Gemini Flash** | 1.000 req/zi | Permanent, fără card | aistudio.google.com | REST + OpenAI-compat ✅ |
| **Groq** | ~30 req/minut | Permanent, fără card | console.groq.com | OpenAI-compatibil ✅ |
| **Cohere** | 1.000 calls/lună | Permanent, fără card | dashboard.cohere.com | REST Bearer ✅ |

> **Atenție OpenAI:** Free tier tehnic există dar returnează erori „quota exceeded" imediat. Minimum $5 necesar. **Nu include în chain fără credit.**

**4.1 — Extindere fallback chain cu Cerebras ca provider primar pentru viteză**
Cerebras oferă 1.800 tokeni/sec (de ~6x mai rapid decât Gemini) și 1M tokeni/zi gratuit. Adaugă-l PRIMUL în chain pentru task-uri care necesită răspuns rapid (chat, OCR post-procesare, explicație preț). Chain nou recomandat: `Cerebras → Gemini Flash → Groq → Mistral → SambaNova`.

**4.2 — Mistral pentru task-uri complexe (documente mari)**
Mistral are context window mare și ~1B tokeni/lună dar doar 2 RPM. Ideal pentru: rezumat documente lungi, analiză contracte, quality check traduceri. Adaugă-l ca provider specializat pentru task-urile cu documente mari, nu în chain-ul general.

**4.3 — Sistem de tracking cotă per provider în timp real**
Extinde Vault-ul sau modulul AI cu un tabel SQLite `provider_usage` (provider, date, tokens_used, requests_count). La fiecare apel API, incrementează contorul. Dashboard cu bare de progres: "Cerebras: 234.000 / 1.000.000 tokeni azi". Alertă automată la 80% cotă consumată.

**4.4 — Rotație automată pe baza cotei rămase (Smart Routing)**
Logică în backend: înainte de a apela un provider, verifică `tokens_used` din SQLite. Dacă provider-ul primar e la >90% cotă → switch automat la următorul din chain, fără intervenție manuală. Implementare: funcție Python `get_available_provider()` care returnează primul provider cu cotă disponibilă.

**4.5 — Provider diferit per tip de task (specializare)**
Nu toți providerii sunt egali pentru toate task-urile. Configurație recomandată:
- Chat general → Cerebras (viteză maximă)
- Traduceri text → Gemini Flash (multilingv bun)
- Rezumat documente → Mistral (context window mare)
- Quality check → Groq Llama 3.3 (raționament bun)
- Batch procesare nocturnă → SambaNova (cotă separată)

**4.6 — Prompt caching pentru răspunsuri repetitive**
System prompt-ul context-aware (cu statistici din DB) se trimite la fiecare request. Gemini și Cerebras suportă caching implicit. Implementare locală: dict `{hash(system_prompt + user_prompt): (response, timestamp)}` cu TTL de 1 oră. Reduce consumul de tokeni cu 20-40% pentru query-uri similare.

**4.7 — Traduceri AI cu LibreTranslate self-hosted (nelimitat)**
LibreTranslate rulează local pe Windows 10 via `pip install libretranslate` sau Docker. Zero costuri, zero limită de caractere, zero dependință internet. Calitate inferioară DeepL dar superioară fallback-ului AI generic. Adaugă-l ca poziție 3 în chain-ul de traduceri: `DeepL → Azure → LibreTranslate local → Gemini`.

**4.8 — Argos Translate offline pentru EN↔RO (complet offline)**
Argos Translate este o bibliotecă Python (MIT license) cu modele descărcate local (~50-150MB per pereche de limbi). Funcționează 100% offline, fără internet. Instalare: `pip install argostranslate` + descărcare model EN↔RO. Adaugă-l ca ultimul fallback în chain când toate API-urile externe sunt indisponibile.

**4.9 — Prompt templates cu variabile per modul (Zero tokens irosiți)**
Standardizează prompt-urile per modul cu template-uri în SQLite. Un prompt bine scris reduce cu 30-50% numărul de tokeni necesari față de un prompt vag. Exemple: Calculator (200 tokeni max), OCR corectare (100 tokeni), Quality check (300 tokeni). Salvează template-urile cu versioning în `prompt_templates` table.

**4.10 — AI offline fallback pentru funcții critice**
Calculatorul de prețuri și Notepad-ul trebuie să funcționeze fără internet. Adaugă logică: dacă toți providerii AI sunt indisponibili (timeout sau cotă epuizată), funcțiile critice folosesc reguli predefinite locale (Python pur, zero API). Exemplu: explicația prețului din calculator poate genera un text template cu valorile calculate, fără AI.

---

## 5. Notificări & Integrări Gratuite

> **Cost: 0 EUR — SMS plătit eliminat complet, înlocuit cu alternative 100% gratuite**
> **Eliminat față de versiunea anterioară:** SMSLink România (€0.04/SMS), Twilio (~$0.07/SMS)

### Notificări mobile gratuite

**5.1 — Telegram Bot pentru notificări push (recomandat principal)**
Telegram Bot API este complet gratuit, fără limite practice (30 mesaje/sec broadcast, 1 msg/sec per chat). Setup: creezi un bot via @BotFather (2 minute), obții token API, trimiți `POST https://api.telegram.org/bot{token}/sendMessage`. Aplicația Telegram e gratuită pe Android, primești notificări native chiar cu aplicația Command Center închisă. **Înlocuiește complet SMS-ul plătit** pentru: alerte ITP expirat, facturi restante, backup reușit/eșuat, task scheduler status.

**5.2 — Discord Webhook pentru notificări secundare**
Discord Webhooks sunt complet gratuite (5 req/2sec per webhook). Creezi un server Discord personal + canal #command-center-alerts. `POST webhook_url` cu JSON → notificare apare instant pe Android via aplicația Discord. Util pentru: erori sistem, log-uri critice, status daily backup.

**5.3 — Email ca SMS alternativ (Gmail SMTP existent)**
Gmail SMTP (deja implementat în Faza 13) permite trimiterea de emailuri la adrese speciale care se transformă în SMS. Exemplu: `numar@sms.yoigo.com` (Spania) sau alte gateway-uri SMS via email gratuite. **Atenție:** gateway-urile SMS via email nu funcționează fiabil pentru operatorii români (Digi, Orange, Vodafone). Recomandat doar ca backup secundar pentru notificări non-critice.

**5.4 — Web Push Notifications native Android (via PWA)**
Implementare descrisă la punctul 3.9. Permite notificări native Android fără Telegram sau orice altă aplicație externă. Complet gratuit cu `pywebpush` Python. **Avantaj față de Telegram:** utilizatorul nu trebuie să instaleze nimic extra — notificările vin direct din PWA-ul Command Center instalat.

**5.5 — BNR API pentru cursuri valutare (gratuit oficial)**
Banca Națională a României oferă un API XML public oficial la `https://www.bnr.ro/nbrfxrates.xml`. Fără cheie API, fără autentificare, fără limite documentate. Adaugă un endpoint `/api/tools/exchange-rate` care parsează XML-ul BNR și returnează cursul EUR/USD/GBP față de RON. Util în Calculator (conversii prețuri) și în Facturare (sume în valută).

**5.6 — ANAF Verificare CUI (gratuit, API oficial)**
ANAF oferă un serviciu REST public la `https://webservicesp.anaf.ro/PlatitorTvaRest/api/v8/ws/tva` pentru verificarea oricărui CUI românesc. Returnează: denumire firmă, adresă, status TVA, cod CAEN. Integrare în modulul de Facturare: la introducerea CUI-ului clientului, câmpurile de denumire și adresă se completează automat din baza ANAF.

**5.7 — Google Calendar sync bidirecțional (API gratuit)**
API-ul Google Calendar este deja integrat (Faza 13) dar doar pentru CRUD de bază. Extinde cu sync bidirecțional: programările ITP create în Command Center apar automat în Google Calendar, și evenimentele din Calendar (ex: întâlniri clienți) apar în dashboardul Command Center. API-ul Google Calendar este gratuit cu ~1.000.000 queries/zi.

**5.8 — GitHub Webhooks pentru notificări commit (gratuit)**
GitHub trimite automat un POST webhook la orice commit, push sau PR. Adaugă un endpoint `/api/webhooks/github` în modulul Integrări. La fiecare commit în repo-ul Command Center → notificare Telegram automată cu mesajul de commit. Zero cost, zero polling.

**5.9 — Brevo (fostul Sendinblue) — 300 emailuri/zi gratuit**
Brevo oferă **300 emailuri/zi** (~9.000/lună) pe free tier permanent, fără card bancar. REST API simplu. Adaugă-l ca backup pentru SMTP Gmail în chain-ul de email: `Gmail SMTP (500/zi) → Brevo API (300/zi)`. Total: ~800 emailuri/zi, suficient pentru orice nevoie a CIP Inspection.

**5.10 — Resend.com — 3.000 emailuri/lună gratuit**
Resend.com oferă **3.000 emailuri/lună** (100/zi) pe free tier permanent, fără card. REST API modern, documentație excelentă. Adaugă-l ca al treilea provider email în rotație: `Gmail → Brevo → Resend`. **Total rotație email: ~27.000 emailuri/lună gratuit.**

---

## 6. Business Intelligence & Rapoarte Avansate

> **Cost: 0 EUR — datele sunt în SQLite, vizualizările folosesc Recharts (deja instalat)**

### Analize de business din datele existente

**6.1 — Dashboard KPI executiv (o singură pagină cu tot)**
Un ecran cu toți indicatorii cheie: venituri luna curentă vs. luna precedentă (%), număr clienți activi, traduceri procesate, ITP-uri efectuate, facturi restante totale. Toate datele există în SQLite, Recharts e deja instalat. Timp implementare estimat: 2-3 ore.

**6.2 — Profitabilitate per tip serviciu (ITP vs. Traduceri)**
Query SQLite care grupează veniturile pe categorii: ITP (din `itp_inspections`) vs. Traduceri (din `invoices` + `calculations`). Grafic pie/donut Recharts. Arată care activitate generează mai mult venit.

**6.3 — Sezonalitate — când vin mai mulți clienți ITP**
Grupare lunară + zilnică a inspecțiilor ITP pe ultimii 12+ luni. Heatmap calendar (similar GitHub contributions) sau BarChart lunar. Identifici perioadele aglomerate pentru planificarea programărilor.

**6.4 — Client Lifetime Value (CLV) per client**
Join între tabelele `clients`, `invoices`, `calculations`: total valoare facturată per client, frecvență comenzi, ultima comandă. Top 10 clienți după valoare. Util pentru prioritizarea relațiilor și ofertele de fidelizare.

**6.5 — Tendință prețuri proprii vs. piață (trend temporal)**
Prețul mediu calculat per pagină în timp (lunar) suprapus peste `min/max/medie` din `Competitori.md`. Line chart Recharts pe 12 luni. Arată dacă prețurile tale urmăresc piața sau divergent.

**6.6 — Predicție cashflow lunar (regresie liniară simplă)**
Python `scipy.stats.linregress` pe veniturile lunare istorice → predicție următoarele 3 luni cu interval de încredere. Afișat ca line chart cu zonă de incertitudine. Util pentru planificare financiară. `scipy` este deja în `requirements.txt`.

**6.7 — Rata de respingere ITP per marcă auto (statistici operaționale)**
Grupare `itp_inspections` după `brand` + `status` (admis/respins). Sortare descrescătoare după rata de respingere. Afișat ca BarChart Recharts. Date utile pentru: avertizare preventivă clienți, parteneriate cu service-uri auto.

**6.8 — Heatmap activitate personală (GitHub-style)**
Calendar vizual pe tot anul cu intensitatea activității zilnice (număr calcule + traduceri + ITP + alte acțiuni). Verde intens = zi productivă, alb = zi liberă. Date direct din `activity_log` SQLite. Motivație și auto-awareness.

**6.9 — Raport trimestrial automat generat (PDF/Excel)**
Task schedulat la APScheduler care rulează la 1 ale trimestrului: generează automat un PDF/Excel cu: venituri trimestriale, top 5 clienți, ITP-uri, comparație trimestrul anterior. Trimite pe email via Gmail SMTP. Toate bibliotecile (`reportlab`, `openpyxl`) sunt deja instalate.

**6.10 — Export structurat pentru contabil (format standard)**
Buton "Export Contabil" în modulul Facturare: generează Excel cu coloane exacte solicitate de contabilii români (număr factură, dată, CUI client, denumire client, valoare fără TVA, TVA, total, status plată). Filtrabil pe trimestru/an. Economisește ore de pregătire manuală la final de trimestru.

---

## 7. Backup, Recovery & Business Continuity

> **Cost: 0 EUR — Google Drive (15GB gratuit), Litestream (open-source MIT), `backup.py` deja există**

### Strategie completă de protecție date

**7.1 — Litestream: replicare SQLite în timp real pe Google Drive**
`Litestream` (open-source, MIT license) replicează SQLite la fiecare write, în timp real, în orice destinație (local, S3-compatible, Google Drive via rclone). Pe Windows 10: descarcă binarul Windows + configurare YAML de 10 linii. Față de backup-ul zilnic existent, Litestream oferă **Recovery Point Objective de ~1 secundă** (nu 24 ore).

**7.2 — Procedură documentată de reinstalare completă**
Creează `99_Roland_Work_Place/DISASTER_RECOVERY.md` cu pași exacti: 1) instalare Python 3.13, 2) clone din GitHub, 3) `pip install -r requirements.txt`, 4) restaurare DB din Drive, 5) reconfigurare Tailscale, 6) reconfigurare Vault, 7) verificare PWA. Timp de recovery țintă: sub 2 ore pe PC nou.

**7.3 — Verificare automată backup (backup netefstat = backup inexistent)**
Adaugă un task APScheduler săptămânal care: 1) descarcă ultimul backup din Drive, 2) deschide DB-ul descărcat cu aiosqlite, 3) rulează `SELECT COUNT(*) FROM activity_log`, 4) dacă returnează date → backup valid → log "✅ Backup verified", 5) dacă eșuează → alertă Telegram imediată.

**7.4 — Backup selectiv per modul (nu tot DB-ul)**
Backup-ul curent salvează tot `calculator.db`. Adaugă o strategie diferențiată: date critice (facturi, clienți, ITP) → backup zilnic + Drive, date reconstructibile (activity log vechi, cache AI) → backup săptămânal local. Reduce dimensiunea backup-ului cu 40-60%.

**7.5 — Versionare DB cu posibilitate rollback per tabel**
Înainte de fiecare migrare (`run_migrations()`), salvează automat un snapshot al tabelului afectat: `CREATE TABLE IF NOT EXISTS _backup_invoices_20260319 AS SELECT * FROM invoices`. La nevoie, rollback manual: `INSERT INTO invoices SELECT * FROM _backup_invoices_20260319`. Simplu și eficient fără alembic.

**7.6 — Backup configurații în GitHub (versionat automat)**
Configurațiile importante (glosar tehnic, template-uri prompturi, shortcuts personalizate, setări Health Monitor) se exportă automat ca JSON și se commitează în GitHub la fiecare modificare. Spre deosebire de DB-ul binar, acestea sunt versionate și diff-uibile în GitHub.

**7.7 — OneDrive ca backup secundar (5GB gratuit)**
Dacă Google Drive de 15GB devine insuficient, OneDrive oferă 5GB suplimentar gratuit via `rclone` (open-source). `rclone copy` sincronizează folderul de backup local → OneDrive. Nu necesită instalare de aplicație OneDrive desktop.

**7.8 — Script de health-check la pornire**
La pornirea backend-ului (`app/main.py`), adaugă un check automat: verifică integritatea DB-ului (`PRAGMA integrity_check`), verifică că toate migrările au rulat, verifică că Vault-ul e accesibil. Dacă oricare fail → log WARNING dar pornire continuă (nu blochează). Raportul apare în Health Monitor existent.

**7.9 — Retenție inteligentă backup-uri (nu doar ultimele 10)**
Backup-ul curent păstrează ultimele 10 backup-uri. Înlocuiește cu strategie Grandfather-Father-Son: ultimele 7 zilnice + ultimele 4 săptămânale + ultimele 3 lunare = maxim 14 backup-uri cu acoperire mult mai bună.

**7.10 — Export complet portabil (tot proiectul + date)**
Buton "Exportă tot" în Rapoarte: generează un ZIP cu: toate datele din SQLite ca JSON/CSV, toate fișierele importante din File Manager, configurațiile, CLAUDE.md. Un singur fișier portabil care permite restaurarea pe orice PC nou. Diferit de backup-ul DB — acesta e pentru migrare/arhivare.

---

## 8. Testing Strategy Automată

> **Cost: 0 EUR — pytest, Playwright, pytest-asyncio sunt toate open-source gratuit**

### De la zero teste automate la coverage real

**8.1 — Unit tests pentru motorul de prețuri (cel mai critic)**
Motorul de prețuri (ensemble 3 metode, MAPE 32%) nu are teste automate. O modificare accidentală poate strica calculele fără nicio avertizare. Adaugă `tests/test_pricing.py` cu pytest: testează că `base_rate.py`, `word_rate.py` și `ensemble.py` returnează valori în range-ul așteptat pentru fișierele de referință existente (26 PDF-uri din `Fisiere_Reper_Tarif/`).

**8.2 — Unit tests pentru migration system**
Cel mai risky cod din proiect: dacă `run_migrations()` are un bug, toată baza de date se poate corupe. Adaugă teste care: creează o DB în memorie (`aiosqlite::memory:`), rulează toate migrările, verifică că tabelele așteptate există și au coloanele corecte.

**8.3 — Integration tests pentru endpoint-urile critice**
Cele mai importante endpoint-uri de testat automat: `/api/calc/calculate` (calcul preț), `/api/invoice/generate` (generare factură PDF), `/api/translator/translate` (traducere text), `/api/itp/` (CRUD inspecții). `pytest` + `httpx.AsyncClient` cu `app` FastAPI în mod test. Rulează în <30 secunde.

**8.4 — E2E test Playwright pentru fluxul principal**
Playwright este deja menționat în proiect (Playwright MCP). Adaugă `tests/e2e/test_main_flow.py`: 1) pornește aplicația, 2) uploadează un PDF, 3) calculează prețul, 4) generează factura, 5) verifică că PDF-ul există pe disc. Rulat manual înainte de fiecare update major.

**8.5 — Teste de regresie pentru bug-urile fixate**
Pentru fiecare bug rezolvat (ex: bug Android DOCX→PDF din Faza 12, fix COM threading), adaugă un test care reproduce exact condiția care a cauzat bug-ul. Previne reapariția aceluiași bug la viitoare refactorizări.

**8.6 — Test automat Android via Playwright pe Chrome Mobile**
Playwright suportă emulare dispozitiv mobil: `browser.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)`. Rulează testele de bază și pe viewport mobil. Detectează automat paginile care se strică pe Android fără să testezi fizic pe telefon.

**8.7 — pytest-cov pentru coverage report**
`pip install pytest-cov` + `pytest --cov=backend --cov-report=html`. Generează un raport HTML cu ce procent din cod e acoperit de teste. Țintă realistă pentru proiectul curent: 30% coverage (minim decent), 60% coverage (bun).

**8.8 — GitHub Actions CI/CD (rulare automată la fiecare push)**
Proiectul are GitHub inițializat. Adaugă `.github/workflows/tests.yml`: la fiecare `git push`, GitHub rulează automat toate testele pytest pe un runner gratuit (2.000 minute/lună gratuit pentru repo-uri publice sau private cu cont GitHub Pro pe care îl ai). Primești email dacă testele pică.

**8.9 — Smoke test la pornirea backend-ului**
Adaugă un script `tests/smoke_test.py` care rulează în 5 secunde și verifică că: backend pornește, DB-ul răspunde, toate modulele sunt loaded, health endpoint returnează 200. Rulat automat de `START_Production.bat` înainte de a anunța "server ready".

**8.10 — Test data fixtures pentru module**
Creează `tests/fixtures/` cu fișiere JSON de date de test: 5 clienți fictivi, 10 facturi test, 20 inspecții ITP test, 3 fișiere PDF mici pentru upload. Toate testele folosesc aceste fixture-uri, nu date reale din producție. Izolează testele de datele reale.

---

## 9. UI/UX Design System & Consistență Vizuală

> **Cost: 0 EUR — Tailwind CSS deja instalat, shadcn/ui open-source gratuit**

### Coerență vizuală între cele 22+ pagini

**9.1 — Design tokens centralizați în Tailwind config**
Creează `tailwind.config.js` cu culori personalizate: `brand-primary`, `brand-secondary`, `status-success`, `status-warning`, `status-error`. Toate paginile folosesc aceste tokeni în loc de culori hardcodate (`blue-500`, `red-400`). O singură schimbare în config → actualizare pe tot proiectul.

**9.2 — Componentă de loading state uniformă**
Verifică că toate paginile au același indicator de loading (spinner/skeleton). Dacă unele pagini afișează un spinner albastru și altele un text gri, experiența e inconsistentă. Creează un `<LoadingState />` component reutilizabil cu 3 variante: spinner, skeleton card, skeleton table.

**9.3 — Componentă de error state uniformă**
Similar cu loading: creează `<ErrorState message={} onRetry={} />` folosit pe toate paginile la erori API. Include: iconița de eroare, mesajul descriptiv, buton "Reîncearcă". Înlocuiește diversele implementări ad-hoc din 22 pagini.

**9.4 — Toast notifications standardizate**
Verifică că toate modulele folosesc același sistem de toast (există deja un toast component). Standardizează: succes = verde + iconița ✓, eroare = roșu + iconița ✗, warning = galben + iconița ⚠, info = albastru + iconița ℹ. Durate: success 3s, error 5s, warning 4s.

**9.5 — Dark/Light mode (feature DEFERRED, acum implementabil)**
Aplicația e dark-first. Adaugă toggle Dark/Light în Header. Tailwind `darkMode: 'class'` + localStorage persistence. Util în mașină la soare (Light mode mai lizibil). Estimare: 3-4 ore implementare cu Tailwind.

**9.6 — Typography scale consistent**
Verifică că heading-urile (H1, H2, H3), textele de corp și textele mici folosesc clase Tailwind consistente pe toate paginile. Creează un ghid intern: `text-2xl font-bold` pentru titluri pagini, `text-lg font-semibold` pentru secțiuni, `text-sm text-gray-400` pentru metadata.

**9.7 — Spacing și padding standardizat pe carduri**
Toate cardurile (`bg-gray-800 rounded-lg p-4`) trebuie să aibă același padding și border-radius. Creează o componentă `<Card>` wrapper cu stiluri fixe. Înlocuiește cardurile ad-hoc din fiecare pagină.

**9.8 — Empty states ilustrate pe toate paginile**
Paginile goale (fără date) afișează probabil un simplu "No data". Adaugă `<EmptyState title="Nicio factură încă" description="Creează prima factură" action={<Button>Factură nouă</Button>} />` cu o ilustrație SVG simplă. Experiență mult mai prietenoasă.

**9.9 — Keyboard shortcuts documentate și vizibile**
Proiectul are Command Palette (Ctrl+K) și OCR Quick (Ctrl+Shift+O). Adaugă un panel "Shortcuts" accesibil din Header (iconița ?) cu lista completă a tuturor shortcut-urilor disponibile. Format: `Ctrl+K` → Navigare rapidă.

**9.10 — Animații și tranziții subtile**
Adaugă `transition-all duration-200` pe butoane și `animate-fadeIn` (Tailwind custom) la apariția cardurilor/modalelor. Evită animații mari sau lente care obosesc pe mobil. Scopul: feedback vizual instant la interacțiuni, nu efecte decorative.

---

## 10. DevOps & Workflow Dezvoltator

> **Cost: 0 EUR — Git hooks, GitHub Actions (2.000 minute/lună gratuit), toate tool-urile open-source**

### Îmbunătățiri ale fluxului de lucru cu Claude Code

**10.1 — Git branching strategy simplă (main + feature branches)**
Acum probabil totul merge direct pe `main`. Adoptă un workflow simplu: `main` = cod stabil testat, `feature/nume-functie` = dezvoltare nouă. La finalizare: `git merge --squash feature/...` → un singur commit curat pe main. Previne situații în care `main` e broken în mijlocul unei implementări.

**10.2 — Pre-commit hooks pentru calitate cod**
Instalează `pre-commit` (open-source): la fiecare `git commit`, rulează automat: `black` (formatare Python), `flake8` (linting Python), `eslint` (JavaScript). Dacă vreunul pică → commit refuzat. Configurare în `.pre-commit-config.yaml`. Menține calitatea codului constant.

**10.3 — Changelog automat din commit messages (Conventional Commits)**
Adoptă formatul Conventional Commits: `feat: adaugă export Excel`, `fix: repară OCR pe imagini rotite`, `docs: actualizează CLAUDE.md`. Adaugă `git-cliff` (open-source, Rust binary) care generează `CHANGELOG.md` automat din mesajele de commit. Zero efort manual.

**10.4 — Versionare semantică automată**
Versiunea `1.0.0` e hardcodată în `package.json` și CLAUDE.md. Automatizează: `standard-version` (npm) sau `bump2version` (Python) incrementează automat versiunea pe baza commit-urilor (feat → minor, fix → patch, BREAKING → major) și creează un git tag.

**10.5 — Hotfix procedure documentată**
Scenariu: ai găsit un bug critic în producție (ex: facturare nu generează PDF). Documentează pașii exacti: 1) `git checkout -b hotfix/invoice-pdf main`, 2) repară bug-ul, 3) testează smoke test, 4) `git merge hotfix/... main`, 5) restart `START_Production.bat`. Timp țintă: sub 15 minute.

**10.6 — `.claude/commands/` extinse cu comenzi utile**
Adaugă comenzi slash noi în `.claude/commands/`: `/backup-now` (trigger manual backup Drive), `/test-all` (rulare teste pytest), `/health-check` (verificare completă sistem), `/api-status` (test ping toate API key-urile din Vault). Comenzile sunt scripturi Python simple apelate din Claude Code.

**10.7 — Script de setup complet pe PC nou (`setup_fresh.bat`)**
Un singur script care instalează tot: verifică Python 3.13, Node.js 20, Tesseract OCR, `pip install -r requirements.txt`, `npm install`, configurează Task Scheduler. Rulat pe un PC nou → sistem funcțional în 20 minute. Esențial pentru disaster recovery (punctul 7.2).

**10.8 — Environment variables pentru configurare per mediu**
Parametri care diferă între dev și producție (debug mode, CORS origins, log level) trebuie în `.env` nu hardcodați în cod. `python-dotenv` (deja probabil instalat) + `.env.development` / `.env.production`. `START_Calculator.bat` setează `ENV=development`, `START_Production.bat` setează `ENV=production`.

**10.9 — Monitorizare uptime automată cu alertă Telegram**
Uptime Monitor există (Faza 16). Extinde cu: dacă health endpoint-ul propriu (`/api/health`) nu răspunde în 30 secunde → trimite mesaj Telegram automat. Util când pornești PC-ul: primești confirmarea că aplicația e up pe Android.

**10.10 — README.md actualizat cu screenshots actuale**
`README.md` (dacă există pe GitHub) sau creează unul cu: screenshot Dashboard, screenshot Calculator, screenshot Translator, instrucțiuni de instalare din 3 pași. Util dacă revii la proiect după câteva luni și nu îți amintești cum se pornește.

---

## 11. Documentație Utilizator Final

> **Cost: 0 EUR — documentație Markdown pură**

### Ghiduri pentru utilizarea zilnică

**11.1 — Manual rapid de utilizare (1 pagină per modul)**
Creează `99_Roland_Work_Place/MANUAL_UTILIZARE/` cu câte un fișier `.md` per modul (Calculator, Translator, ITP, Facturare, AI, etc.). Fiecare fișier: 1 pagină, format: "Ce face", "Cum se folosește în 3 pași", "Erori comune și soluții". Nu documentație tehnică — ghid practic de utilizare zilnică.

**11.2 — FAQ pentru situații frecvente**
Creează `FAQ.md` cu întrebările reale care vor apărea: "De ce nu merge DeepL?" → verifică quota în Vault, "De ce nu apare factura în PDF?" → verifică că reportlab e instalat, "De ce e lentă căutarea în File Manager?" → rulează VACUUM pe DB. Răspunsuri directe, fără explicații tehnice.

**11.3 — Keyboard shortcuts cheatsheet (1 pagină imprimabilă)**
Un fișier `SHORTCUTS.md` cu toate shortcut-urile disponibile: Ctrl+K (Command Palette), Ctrl+Shift+O (OCR Quick), plus orice shortcut nou adăugat. Format tabel simplu. Poate fi imprimat și lipit lângă monitor.

**11.4 — Ghid de configurare API keys (pas cu pas)**
Creează `SETUP_API_KEYS.md` cu pașii exacți pentru fiecare provider: unde te înregistrezi, unde găsești cheia API, cum o adaugi în Vault, cum verifici că funcționează. Include screenshot-uri text (ASCII art) sau linkuri directe la paginile de signup.

**11.5 — Troubleshooting guide (simptom → cauză → rezolvare)**
Formatul: "Simptom: aplicația nu pornește" → "Cauze posibile: Python nu e în PATH / portul 8000 ocupat / uvicorn zombie" → "Rezolvare: rulează `STOP_Silent.bat`, așteaptă 5 sec, pornește din nou". Acoperă cele mai frecvente 20 de probleme din `GHID_TESTARE.md`.

**11.6 — What's New per versiune (Release Notes)**
La fiecare set de funcții noi implementate, adaugă o secțiune în `CHANGELOG.md` cu: "Ce e nou", "Ce s-a îmbunătățit", "Ce s-a rezolvat". Format simplu, orientat pe beneficii pentru utilizator (nu pe detalii tehnice).

**11.7 — Ghid de backup și restaurare pentru utilizator non-tehnic**
Descrie în termeni simpli (fără Python, fără terminal): "Cum fac backup manual" → buton în interfață, "Cum restaurez după o problemă" → pași cu click-uri în UI. Presupune că utilizatorul viitor (sau tu după 6 luni) nu își amintește detaliile tehnice.

**11.8 — Ghid de utilizare pe Android (specific pentru mobil)**
Creează `ANDROID_GUIDE.md`: cum instalezi PWA-ul, cum accesezi Tailscale de pe telefon, ce funcții merg offline, cum folosești camera pentru OCR, cum partajezi fișiere din Android în File Manager. Specific scenariului de utilizare mobilă real.

**11.9 — Glossar termeni tehnici și business**
Un fișier `GLOSSAR.md` cu termenii specifici proiectului: MAPE, ensemble, Translation Memory, FTS5, ITP, CUI, SPV, e-Factura. Util la sesiunile cu Claude Code când trebuie să explici contextul.

**11.10 — Jurnal de decizii arhitecturale (ADR - Architecture Decision Records)**
Documentează deciziile mari luate în proiect: "De ce SQLite și nu PostgreSQL?", "De ce Tailscale și nu Vercel?", "De ce Python 3.13 global și nu venv?". Format: Context → Decizie → Motivare → Consecințe. Esențial pentru sesiunile viitoare de Claude Code care altfel vor sugera refactorizări inutile.

---

## 12. Automatizare Fluxuri Cross-Module

> **Cost: 0 EUR — toate modulele există, necesită doar conectare între ele**

### Fluxuri end-to-end care traversează mai multe module

**12.1 — Flux complet "Client Nou" (Calculator → Factură → Email → Calendar)**
Un singur buton "Flux Complet" în Calculator care: 1) calculează prețul, 2) pre-completează factura cu datele clientului și prețul, 3) generează PDF, 4) trimite email cu factura atașată, 5) creează eveniment Calendar "Follow-up [client] +3 zile". Tot din un singur click. Estimare: 2-3 ore implementare.

**12.2 — Flux "Proiect Traducere" (File Manager → Translator → Quality Check → Invoice)**
Upload fișier în File Manager → click "Traduce și Facturează" → traducere automată → quality check AI → generare factură cu prețul calculat automat din modul Calculator. Toate modulele există, lipsesc conexiunile între ele.

**12.3 — Flux "Zi de Lucru ITP" (Calendar → ITP → Invoice → Reports)**
Dimineața: Calendar arată programările ITP de azi. La finalizarea fiecărei inspecții: click "Finalizează" → creare automată înregistrare ITP cu status + generare factură → actualizare raport zilnic. Fără introducere duplică de date.

**12.4 — Flux "Procesare Document Primit" (Email → File Manager → OCR → AI → Invoice)**
Email primit cu atașament (factură de la furnizor): 1) detectat automat via IMAP, 2) salvat în File Manager, 3) OCR extrage datele, 4) AI structurează (număr factură, sumă, dată, furnizor), 5) înregistrat automat în Cheltuieli. Automatizare completă a procesării documentelor primite.

**12.5 — Macro Recorder: înregistrare secvențe de acțiuni**
Un mod "Record" care înregistrează secvența de acțiuni făcute în aplicație și o salvează ca macro reutilizabil. Implementare simplificată: log-ul de activitate există deja în SQLite — adaugă un "start recording" / "stop recording" care salvează secvența ca template de pași executabili.

**12.6 — Raport Săptămânal Automat pe Email/Telegram**
APScheduler (deja instalat) + task schedulat luni la 08:00: generează email/mesaj Telegram cu rezumatul săptămânii anterioare: calcule efectuate, traduceri procesate, ITP-uri, venituri estimate, comparație săptămâna precedentă. Fără nicio acțiune manuală.

**12.7 — Alert Inteligent: Facturi Aproape de Scadență**
Task zilnic APScheduler la 09:00: caută facturile cu scadența în 3, 7, 14 zile → trimite alertă Telegram cu lista + sumele. Diferit de statusul de plată static — este o alertă proactivă care ajută la cashflow management.

**12.8 — Sync Automat File Manager → Google Drive (selectiv)**
Folderele marcate ca "Important" în File Manager (ex: Contracte_Semnate, Traduceri_Livrate) se sincronizează automat pe Drive zilnic la 02:00 via task APScheduler + Google Drive API (deja integrat în Faza 13). Nu tot File Manager-ul — doar folderele critice.

**12.9 — Webhook Incoming pentru formulare externe**
Un endpoint `/api/webhooks/incoming` care primește POST requests de la orice serviciu extern (Google Forms, Typeform gratuit, formulare pe site-ul firmei). La completarea unui formular de ofertă de client: datele ajung automat în Command Center și creează o înregistrare client + calcul pre-completat. Fără introducere manuală.

**12.10 — Dashboard Situație Curentă (real-time overview)**
O pagină "Situație Azi" care agregă: facturi neîncasate (suma totală), ITP-uri programate azi, traduceri în curs, ultimele 5 activități, status provideri AI (verde/roșu). Actualizare automată la 30 secunde via WebSocket (deja implementat). Prima pagină deschisă dimineața — zero navigare.

---

## Tabel Sumar — Priorități și Efort

| # | Zonă | Prioritate | Efort estimat | Impact business |
|---|------|-----------|---------------|-----------------|
| 1 | Securitate & Privacy | 🔴 Critică | 2-3 sesiuni | Protecție date clienți |
| 2 | Performanță & Optimizare | 🟡 Importantă | 2-3 sesiuni | Viteză pe Android |
| 3 | Experiență Mobilă | 🔴 Critică | 2-3 sesiuni | Utilizare zilnică pe telefon |
| 4 | AI Strategy & Key Rotation | 🔴 Critică | 1-2 sesiuni | +2M tokeni/zi gratuit |
| 5 | Notificări Gratuite | 🟡 Importantă | 1 sesiune | Înlocuiește SMS plătit |
| 6 | Business Intelligence | 🟡 Importantă | 2 sesiuni | Vizibilitate business |
| 7 | Backup & Recovery | 🔴 Critică | 1 sesiune | Protecție date |
| 8 | Testing Automat | 🟡 Importantă | 3-4 sesiuni | Stabilitate pe termen lung |
| 9 | UI/UX Design System | 🟢 Nice-to-have | 2 sesiuni | Consistență vizuală |
| 10 | DevOps & Workflow | 🟢 Nice-to-have | 1-2 sesiuni | Productivitate dezvoltare |
| 11 | Documentație | 🟢 Nice-to-have | 1 sesiune | Utilizare fără suport |
| 12 | Fluxuri Cross-Module | 🟡 Importantă | 3-4 sesiuni | Automatizare business |

---

## Platforme API Gratuite Verificate (2025-2026)

> Referință rapidă pentru implementarea punctului 4 (AI Key Rotation) și punctului 5 (Notificări)

### AI Text Generation — Free Tier Permanent

| Provider | Cotă zilnică | Cotă lunară | Signup | Card necesar |
|----------|-------------|-------------|--------|--------------|
| **Cerebras** | 1.000.000 tokeni | ~30M tokeni | cloud.cerebras.ai | **Nu** |
| **Gemini Flash** | 250.000 tokeni | ~7,5M tokeni | aistudio.google.com | **Nu** |
| **Groq** | ~400.000 tokeni | ~12M tokeni | console.groq.com | **Nu** |
| **Mistral AI** | ~33M tokeni (limitat la 2 RPM) | ~1B tokeni | console.mistral.ai | **Nu** |
| **SambaNova** | 200.000 tokeni | ~6M tokeni | sambanova.ai | **Nu** |
| **Cohere** | ~33 calls | 1.000 calls | dashboard.cohere.com | **Nu** |

### Traduceri — Free Tier Permanent

| Provider | Cotă lunară | Card necesar | Note |
|----------|-------------|--------------|------|
| **Azure Translator F0** | 2.000.000 caractere | **Nu** | Cel mai generos |
| **DeepL API Free** | 500.000 caractere | **Nu** | Calitate superioară |
| **Google Translate** | 500.000 caractere | Da (dar no charge) | $300 credit inițial |
| **MyMemory** | 1.500.000 caractere | **Nu** | Fără cont necesar |
| **LibreTranslate local** | **Nelimitat** | **Nu** | Self-hosted Python |
| **Argos Translate local** | **Nelimitat** | **Nu** | Offline complet |

### Notificări Gratuite (înlocuiesc SMS-ul plătit)

| Provider | Cotă | Card necesar | Use case |
|----------|------|--------------|----------|
| **Telegram Bot API** | Practic nelimitat | **Nu** | Notificări principale |
| **Discord Webhooks** | 5 req/2sec | **Nu** | Alerte sistem |
| **Web Push (PWA)** | Nelimitat | **Nu** | Notificări native Android |
| **Brevo Email** | 9.000/lună | **Nu** | Email marketing |
| **Resend.com** | 3.000/lună | **Nu** | Email transacțional |
| **Gmail SMTP** | 15.000/lună | **Nu** | Email existent |

---

*Document generat: 2026-03-19 | Vers. 1.0*  
*Surse verificate: tailscale.com, cloud.cerebras.ai, console.mistral.ai, aistudio.google.com, console.groq.com, sambanova.ai, azure.microsoft.com, deepl.com, libretranslate.com, telegram.org, brevo.com, resend.com, bnr.ro, webservicesp.anaf.ro*  
*Condiție: 100% gratuit — nicio funcție din acest document nu necesită abonament sau plată*  
*Stack confirmat: FastAPI Python 3.13 + React 18 + SQLite + Tailscale `desktop-cjuecmn.tail7bc485.ts.net:8000`*
