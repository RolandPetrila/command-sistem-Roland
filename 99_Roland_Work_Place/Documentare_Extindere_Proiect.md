# Documentare Extindere Proiect — Roland Command Center

> **Data discuție:** 2026-03-18
> **Participanți:** Roland + Claude Code (Opus 4.6)
> **Runde de clarificare:** ~15 runde
> **Rezultat:** Plan validat, filtrat și completat pentru 0.0_PLAN_EXTINDERE_COMPLET.md

---

## 1. Context și Punct de Plecare

Proiectul a început ca **NOU_Calculator_Pret_Traduceri** — un calculator automat de prețuri pentru traduceri tehnice EN↔RO. După finalizarea fazelor 0-8 (analiză PDF/DOCX, pricing ensemble, calibrare, dashboard, teste E2E), s-a decis extinderea într-un **panou personal multifuncțional**.

Planul inițial (`0.0_PLAN_EXTINDERE_COMPLET.md`) conținea 10 faze (8-17) cu ~90 de features, fuzionate din 3 surse:
- **Opus v1.0** — primul plan de extindere
- **Sonnet ET** — propuneri alternative (Extended Thinking)
- **Opus v1.1** — propuneri noi (P1-P12)

Discuția de clarificare a validat, filtrat și completat acest plan.

---

## 2. Decizie Centrală: Redenumire Proiect

**Vechi:** Calculator Pret Traduceri
**Nou:** **Roland - Command Center**

**Motivare:** Proiectul nu mai este doar un calculator de prețuri. Devine un panou personal cu module de traduceri, facturare, tool-uri, AI, integrări externe și automatizări. Numele reflectă scopul real.

---

## 3. Decizii Generale

### 3.1 Utilizator și Acces
- **Single-user permanent** — doar Roland, nu va avea alți utilizatori
- **Device-uri:** PC desktop (Windows 10) + telefon Android
- **Nu e necesar:** autentificare multi-user, roluri, permisiuni

### 3.2 Buget
- **Exclusiv resurse FREE** — nu se adaugă abonamente noi
- Se folosesc API-urile deja plătite (Claude Pro/Max, Gemini, DeepL)
- Restul: gratuit (OpenAI, Google Translate, Azure, GitHub Pro)

### 3.3 Deploy — Tailscale (nu Vercel/Railway)
- **Decizia:** Tailscale mesh VPN în loc de Vercel + Railway
- **Motivare:**
  - Tailscale e gratuit (100 devices)
  - Nu necesită JWT auth (rețeaua e deja privată)
  - Nu necesită domeniu custom (IP privat Tailscale)
  - Nu necesită CI/CD (se rulează direct pe PC)
  - Nu necesită variabile de mediu în cloud
- **Cum funcționează:** Instalezi Tailscale pe PC + telefon → ambele sunt în aceeași rețea privată → accesezi `http://100.x.y.z:5173` de pe telefon
- **ELIMINAT:** Vercel, Railway, CI/CD GitHub Actions, JWT auth, domeniu custom, Let's Encrypt

### 3.4 Structură Modulară
- **Pattern:** `backend/modules/[modul]/` + `frontend/src/modules/[modul]/`
- **Migrare treptată:** codul existent rămâne, modulele noi se adaugă în structura nouă
- **Fiecare modul:** un router FastAPI + o pagină React + tabele SQLite
- **Baza de date COMUNĂ** (nu per modul) — cerință explicită a utilizatorului

### 3.5 Ordine Implementare
- **Wave 0 (Refactorizare) PRIMUL** — fundație obligatorie
- **Deploy (8) AL DOILEA** — acces de oriunde
- **Tool-uri rapide (11) ÎNAINTEA traducătorului (9)** — quick wins, moral boost
- Restul treptat, în ordinea din PRIORITĂȚI RECOMANDATE

### 3.6 Refactorizare Obligatorie (Post-Audit 2026-03-18)
- **Decizia:** Refactorizarea modulară (fost 8.5bis opțional) devine **8.0 OBLIGATORIU**
- **Motivare:** Structura actuală (7 routere flat, 6 pagini, main.py manual) nu suportă 10+ module noi
- **Include:** module auto-discovery, sidebar dinamic, migrare DB (SQL numerotate + schema_version), activity log → SQLite, fix URL-uri hardcoded, notificări infrastructură
- **Confirmat:** Audit arhitectural 2026-03-18 (16 observații, 4 critice — toate acceptate)

---

## 4. Decizii Per Fază

### Faza 8 — Deploy + PWA + Securitate (RESCRISĂ COMPLET)

**Items eliminate:**
| Item | Motiv eliminare |
|------|----------------|
| 8.2 Frontend deploy Vercel | Înlocuit cu Tailscale |
| 8.3 Backend deploy Railway | Înlocuit cu Tailscale |
| 8.4 Variabile mediu securizate | Nu mai e nevoie (nu mai e cloud) |
| 8.5 Domeniu custom + HTTPS | Tailscale nu necesită |
| 8.6 CI/CD pipeline | Rulare directă pe PC |
| 8.7 Autentificare JWT | Tailscale = rețea privată |

**Items noi:**
| Item | Detalii |
|------|---------|
| 8.2 Tailscale setup | Mesh VPN, IP privat, acces de pe telefon |
| 8.5 Password Vault | Master password + stocare criptată (parole, conturi, API keys) — ca un KeePass integrat |

**Discuție Password Vault → API Key Vault (scope redus post-audit IMPROVEMENT-14):**
- Scope redus la **doar chei API ale aplicației** (DeepL, Google OAuth, GitHub token)
- Funcționează cu master password (nu JWT)
- Criptare: biblioteca `cryptography` (Fernet) + derivare cheie din master password
- NU este password manager complet (a fost redus din KeePass la API key store)

### Faza 9 — Traducător Integrat (ACTUALIZATĂ)

**Schimbare majoră:** Multi-provider chain cu 6 provideri de traduceri:
1. **DeepL** (principal) — abonament existent, calitate superioară EN↔RO
2. **Google Translate** — gratuit, cu păstrare layout documente
3. **Azure Translator** — gratuit, cu păstrare layout documente
4. **Gemini flash** — gratuit, fallback AI
5. **Claude Haiku** — foarte ieftin, fallback AI
6. **OpenAI** — gratuit (tier free), fallback AI

**Discuție layout preservation:**
- Google Translate și Azure Translator pot traduce documente păstrând formatul original (bold, italic, tabele, etc.)
- DeepL files (abonament) face similar, dar limitat la 20/lună
- Celelalte (AI) traduc text brut, fără păstrare layout

### Faza 10 — Facturare (ACTUALIZATĂ)

**Decizii cheie:**
- Legată de modulul traduceri ca ecosistem: fișier → preț → factură → statistici
- Baza de date facturare = COMUNĂ (nu tabel separat per modul)
- Utilizatorul folosește FGO acum (software facturare existent)
- Puține facturi/lună → nu e prioritate imediată
- Scanner facturi primite (10.8) PĂSTRAT — util pentru evidență cheltuieli

### Faza 11 — Tool-uri Rapide (FILTRATĂ MAJOR)

**Înainte:** 13 items | **După:** 6 items

**Motivare eliminări:**
| Item eliminat | Motiv |
|--------------|-------|
| Meteo | Nu aduce valoare suficientă, disponibil pe telefon |
| Curs valutar BNR | Utilizare rară, disponibil pe Google |
| Calculator valutar | Redundant cu cursul BNR |
| Cronometru/Timer | Funcție nativă telefon/PC |
| Convertor unități | Disponibil pe Google, utilizare rară |
| Snippets cod | VS Code are deja snippets integrat |
| Pomodoro | Utilizare rară, multe alternative existente |
| Alerte valutar | Utilizare rară, nu e core business |

**Explicații tehnice date în discuție:**
- **QR Generator:** Generează QR codes din text/URL, util pentru partajare rapidă
- **Coduri de bare:** EAN-13, Code128 — util pentru evidență produse sau ITP
- **Pomodoro:** Tehnică de productivitate (25 min lucru + 5 min pauză) — eliminat pentru că există multe alternative gratuite

**Item adăugat:** 11.6 Password Generator — util, implementare trivială (5 min)

### Faza 12 — Convertor Fișiere (PĂSTRATĂ INTEGRAL)
Toate 9 items păstrate fără modificări.

### Faza 13 — Integrări Externe (PĂSTRATĂ INTEGRAL)
Toate 10 items păstrate fără modificări.

### Faza 14 — Manager Fișiere (FILTRATĂ)

**Eliminat:** 14.10 Partajare temporară fișiere (link unic cu expirare)
**Motiv:** Nu e necesar pentru single-user. Partajarea se face prin Tailscale sau alt mijloc.

### Faza 15 — AI Documente (ACTUALIZATĂ — provideri 100% gratuiți)

**Toate 10 items păstrate** — marcată ca "foarte importantă" de utilizator.

**Schimbare majoră (2026-03-18):** Toți providerii AI înlocuiți cu variante GRATUITE:
- **Claude API eliminat** din toată Faza 15 (costuri per request)
- **Gemini Flash/Pro** (principal) — inclus în planul existent, zero cost suplimentar
- **OpenAI GPT-4o-mini** (fallback 1) — free tier existent
- **Groq — Llama 3.1 70B** (fallback 2) — free tier generos, inferență ultra-rapidă [PROBABIL]
- **Azure AI** (fallback 3) — free tier existent
- **RAG (15.7):** ChromaDB eliminat, înlocuit cu FTS5 + Gemini direct sau Gemini embeddings gratuite
- **Cost total Faza 15:** 0 EUR (de la ~0.01-0.05$/operație anterior)

**Item adăugat:** 15.10 Comparare documente (diff)
- Util pentru traduceri revizuite — compară versiunea originală cu versiunea corectată
- Implementare: `difflib` Python + UI side-by-side cu highlight diferențe

### Faza 16 — Automatizări (FILTRATĂ + ADĂUGAT)

**Items eliminate:**
| Item | Motiv |
|------|-------|
| 16.2 Monitorizare CPU/RAM | Disponibil în Task Manager Windows |
| 16.5 Clipboard manager | Windows 10 are Win+V (clipboard history) |

**Îmbunătățiri:**
- 16.6 devine **Command Palette** (Ctrl+K) — nu doar search, ci acces rapid la orice funcție
- 16.11 devine **webhook generic** — nu doar n8n, orice serviciu poate trimite/primi webhooks

**Item adăugat:** 16.12 Health Monitor & Diagnostics
- Monitorizare erori live în aplicație
- Log streaming pe WebSocket
- Sugestii automate de remediere (pattern matching pe erori cunoscute)
- **Self-healing:** dacă detectează eroare cunoscută → încearcă fix automat

### Faza 17 — Rapoarte & Polish (FILTRATĂ)

**Eliminat:** 17.4 Time tracker per proiect
**Motiv:** Complexitate vs utilitate — nu e prioritar pentru single-user.

**Validare per grupuri:**
- **Grup 1:** 17.1 Statistici disc ✓, 17.2 Timeline ✓, 17.5 Jurnal ✓
- **Grup 2:** 17.6 Linkuri ✓, 17.7 Dark/Light ✓, 17.9 Backup Drive ✓, 17.10 Export PDF ✓
- **Grup 3:** 17.3 Fișiere neutilizate ✓, 17.8 Push notifications ✓

### Faza 18 — ITP CIP Inspection (NOU)

**Decizie:** Modul nou dedicat evidenței inspecțiilor ITP auto.
**Motivare:** Utilizatorul are nevoie de evidență internă pentru inspecții ITP.

**Funcționalități:**
- Evidență ITP-uri (CRUD) — înregistrare manuală + import CSV/Excel
- Statistici: ITP-uri/zi/lună, rata admis/respins, venituri, top mărci auto
- Alertă clienți: ITP expiră în 30 zile → notificare
- Export rapoarte Excel/PDF

**IMPORTANT — risc legal RAR:**
- NU se include scraping de pe site-ul RAR (Registrul Auto Român)
- Scraping-ul site-urilor guvernamentale poate fi ilegal (accesul automatizat la baze de date publice fără acord)
- Modulul folosește DOAR evidență proprie (date introduse manual sau importate din CSV)
- Implementare ULTERIOARĂ — după ce sistemul de bază e funcțional

---

## 5. Resurse Inventariate

### API-uri plătite activ
- **Claude Pro/Max** — acces la modele Anthropic (Opus, Sonnet, Haiku)
- **Gemini API** — acces la modele Google
- **DeepL** — abonament files (20/lună) + conturi suplimentare API (500K caractere)

### API-uri gratuite disponibile
- **OpenAI API** — tier free
- **Perplexity API** — search + AI
- **Azure AI** — tier free
- **GitHub Pro** — repo-uri nelimitate, Actions 2000 min/lună
- **Google Translate** — cu păstrare layout documente
- **Azure Translator** — cu păstrare layout documente

### Tool-uri locale
- **Tesseract OCR** — instalat, funcțional
- **Poppler** — utilitar PDF
- **PDF X-Change Editor Plus** — licență activă
- **Playwright MCP** — browser automation (deja folosit pentru competitor research)
- **3 CLI AI** — Claude Code, Gemini CLI, Codex CLI

---

## 6. Explicații Tehnice Date în Discuție

### Tailscale
Tailscale e un mesh VPN gratuit. Instalezi pe fiecare device (PC + telefon) → primesc IP-uri private (100.x.y.z) → pot comunica direct, fără port forwarding, fără cloud. Backend-ul rulează pe PC, telefonul accesează prin IP-ul Tailscale.

### Password Vault
Similar cu KeePass dar integrat în panou. Master password derivă o cheie de criptare (PBKDF2 → Fernet key). Toate parolele/API keys sunt stocate criptat în SQLite. La deschidere, se cere master password → decriptează totul în memorie.

### Google Translate cu păstrare layout
Google Translate API (documentare oficială) poate traduce documente întregi păstrând formatarea originală (bold, italic, tabele, headere). Similar Azure Translator. Spre deosebire de traducerea AI (care lucrează pe text brut).

### Coduri de bare vs QR
- **QR Code:** matrice 2D, stochează URL/text, scanat cu camera
- **Cod de bare (barcode):** linii verticale, EAN-13 (produse) sau Code128 (inventar), scanat cu scanner dedicat

### RAR și risc legal scraping
RAR (Registrul Auto Român) are site cu date publice despre ITP-uri. Scraping-ul automatizat al site-urilor guvernamentale poate fi considerat acces neautorizat conform legii. Modulul ITP va folosi DOAR date introduse manual.

---

## 7. Propuneri de Completare (Validate în Discuție)

| Propunere | Faza | Status |
|-----------|------|--------|
| Password Generator (configurabil) | 11.6 | INCLUS |
| Comparare documente (diff) | 15.10 | INCLUS |
| Health Monitor & Diagnostics | 16.10 | INCLUS |
| Self-healing (fix automat erori cunoscute) | Extensie 16.10 | INCLUS (în descriere) |
| Refactorizare structură modulară (pas dedicat) | 8.0 | **OBLIGATORIU** (post-audit CRITICAL-3) |

---

## 8. Workflow Terminale Viitoare

Pentru orice terminal AI nou care continuă munca pe acest proiect:

1. **Citește** `0.0_PLAN_EXTINDERE_COMPLET.md` — planul complet cu toate deciziile
2. **Citește** acest fișier (`Documentare_Extindere_Proiect.md`) — context și motivări
3. **Citește** `CLAUDE.md` — instrucțiuni specifice proiect
4. **Citește** `PLAN_EXECUTIE.md` — ce s-a implementat deja (faze 0-8)
5. **Parcurge** HTML selector (`0.0_PLAN_EXTINDERE_COMPLET.html`) — pentru a vedea ce features sunt disponibile

**Flux implementare:**
```
Actualizare .md → Regenerare HTML → Utilizatorul parcurge HTML
→ Bifează features → "Generează Plan" → Copie lista
→ Revine la Claude Code cu lista selectată → Implementare
```

---

## 9. Statistici Finale

| Metric | Valoare |
|--------|---------|
| Faze totale | 11 (Faza 8-18) |
| Features totale | ~85 (revizuit post-audit) |
| Features eliminate | ~18 |
| Features adăugate | 5 (Vault, Password Gen, Doc Diff, Health Monitor, ITP) |
| Features mutate/restructurate | 3 (Command Palette → 11.0, Notificări split A/B, Scanner unificat cu 15.5) |
| Sesiuni estimate | ~40-55 (revizuit post-audit) |
| Cost lunar suplimentar | ~0-3 EUR (zero abonamente noi) |
| Nume proiect | Roland - Command Center |
| Audit arhitectural | 2026-03-18 — 16 observații, 4 critice, toate aplicate |

---

## 10. Audit Arhitectural (2026-03-18)

**Auditor:** Claude Code (Opus 4.6)
**Metodologie:** Review complet al planului de extindere vs. cod existent + best practices
**Rezultat:** 16 observații (4 critice, 3 dependințe, 1 redundanță, 2 reordonări, 5 îmbunătățiri, 1 lipsă)
**Status:** TOATE propunerile CONFIRMATE de utilizator → aplicate în `0.0_PLAN_EXTINDERE_COMPLET.md`

### 10.1 Observații Critice (4)

| ID | Problema | Soluția aplicată |
|----|----------|-----------------|
| CRITICAL-1 | PWA + Tailscale = HTTPS obligatoriu — service workers funcționează DOAR pe HTTPS sau localhost, Tailscale dă IP 100.x.y.z | Sub-items HTTPS/TLS la 8.2: MagicDNS, `tailscale cert`, uvicorn SSL |
| CRITICAL-2 | URL-uri hardcoded în `client.js` (`localhost:8000` liniile 3, 121) → din Android via Tailscale = eșec 100% | Fix obligatoriu Wave 0: `window.location.origin` + WebSocket dinamic |
| CRITICAL-3 | Refactorizare modulară era OPȚIONALĂ (8.5bis) — structura flat (7 routere, 6 pagini) nu suportă 10+ module | 8.5bis → 8.0 OBLIGATORIU, primul pas din Wave 0 |
| CRITICAL-4 | Lipsă migrare DB — `CREATE TABLE IF NOT EXISTS` nu suportă ALTER column pe tabele existente | Sistem SQL numerotate (`migrations/`) + tabelă `schema_version`, parte din Wave 0 |

### 10.2 Observații Dependințe (3)

| ID | Dependință | Rezolvare |
|----|-----------|-----------|
| DEPENDENCY-5 | Email 10.7 depinde de Google OAuth 13.1 (dacă se folosește Gmail API) | Clarificat: 10.7 = smtplib + App Password (independent), 13.3 = upgrade la Gmail API |
| DEPENDENCY-6 | Backup Drive 17.8 depinde de Drive API 13.5-13.6 | OK — ordinea naturală (Faza 13 < Faza 17), doar notat explicit |
| DEPENDENCY-7 | Push notifications 17.7 depinde de PWA 8.3 (service worker) | OK — corect plasat, doar notat explicit |

### 10.3 Observație Redundanță (1)

| ID | Problema | Rezolvare |
|----|----------|-----------|
| REDUNDANT-8 | Scanner facturi 10.8 ≈ Extragere date 15.5 — pipeline identic (OCR → Claude API → JSON structurat) | 10.8 implementează pipeline O SINGURĂ DATĂ ca serviciu reutilizabil, 15.5 doar adaugă template-uri noi |

### 10.4 Observații Reordonare (2)

| ID | Mutare | Motiv |
|----|--------|-------|
| REORDER-9 | Command Palette 16.4 → 11.0 | Cu 10+ module, navigarea devine critică; sidebar static 6 items nu scalează; Ctrl+K = coloana vertebrală |
| REORDER-10 | Notificări 16.6 split: Parte A → Wave 0, Parte B → Faza 16 | Multiple faze necesită notificări (18.7 alerte ITP, 17.8 backup, 10.7 email); infra trebuie devreme |

### 10.5 Observații Îmbunătățire (5)

| ID | Îmbunătățire | Acțiune |
|----|-------------|---------|
| IMPROVEMENT-11 | Estimări subestimate: F8 (2-3→3-4), F9 (4-6→7-10), F15 (5-8→7-10) | Estimări actualizate, total ~33-47 → ~40-55 sesiuni |
| IMPROVEMENT-12 | LibreOffice nu e instalat pe sistem (12.2 îl menționa) | docx2pdf (Word COM pe Windows) = principal, LibreOffice = fallback |
| IMPROVEMENT-13 | RAG (15.7) = overkill pentru single-user cu câteva sute de documente | Marcat OPȚIONAL; alternativă simplă: FTS5 (14.5) + Claude API direct = 90% funcționalitate |
| IMPROVEMENT-14 | Password Vault (8.5) scope creep risk — KeePass complet e mult efort | Redus la "API Key Vault" — stochează DOAR cheile API aplicație (DeepL, OAuth, GitHub) |
| IMPROVEMENT-15 | Activity log JSON (`activity_log.json`, max 1000) nu scalează cu 10+ module | Migrare la tabelă SQLite în Wave 0 |

### 10.6 Observație Lipsă (1)

| ID | Problema | Acțiune |
|----|----------|---------|
| MISSING-16 | Proiectul NU are Git repo (`Is a git repository: false`) | Git init = PRIMUL lucru din Wave 0, înainte de orice refactorizare |

### 10.7 Secțiuni Noi Adăugate în Plan

- **WAVE-uri implementare** (Wave 0/1/2) — ordine concretă de execuție cu referințe la observațiile audit
- **DEPENDINȚE CROSS-FAZĂ** — matrice completă de dependințe inter-fază (12 dependințe documentate)
- **Note arhitecturale extinse** (+3 items: migrare DB, sidebar dinamic, activity log SQLite)

---

*Document generat pe 2026-03-18 de Claude Code (Opus 4.6)*
*Actualizat 2026-03-18: adăugat secțiunea 10 (Audit Arhitectural)*
*Scop: Referință completă pentru deciziile de extindere — citit de terminale viitoare*
