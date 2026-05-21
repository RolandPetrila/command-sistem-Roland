# GHID DE UTILIZARE: Ecosistemul Roland - Command Center (V21)
## Manual Operativ Gemini CLI - Business Enterprise Edition

---

### 1. Introducere
Ecosistemul Roland este o platformă avansată de management pentru fluxurile de traduceri, integrând AI, facturare automată și calculatoare de preț bazate pe modele de ensemble. Acest ghid este creat pentru a asigura utilizarea corectă a noilor funcții livrate de Gemini CLI.

### 2. Structura Proiectului

- **Backend (FastAPI):** Găzduit în `backend/`, modularizat în 13 sub-module.
- **Frontend (React/Vite):** Găzduit în `frontend/`, conține 25 de pagini operative.
- **Vault:** Secțiune securizată pentru chei API și secrete.
- **Database:** SQLite cu asincronicitate (Aiosqlite).

### 3. Comenzi Operative (Slash Commands)

În cadrul acestui workspace, Gemini CLI răspunde la următoarele comenzi de analiză:

| Comandă | Descriere | Detalii |
| :--- | :--- | :--- |
| `/audit` | Audit de sănătate cod. | Verifică structura, complexitatea și calitatea. |
| `/improve` | Recomandări de modernizare. | Analizează dependențele și pattern-urile tech. |
| `/perf` | Analiză performanță. | Verifică latența bazei de date și a API-urilor externe. |
| `/security` | Audit securitate și compliance. | Verifică Vault, OWASP și conformitatea GDPR. |
| `/ux` | Review UX și accesibilitate. | Analiză flow utilizator și standard WCAG 2.2. |
| `/analiza_totala` | Master Report 360. | Generează un raport consolidat cu priorități P0-P4. |

### 4. Workflow-ul de Analiză (Business Standard)
1. **Identificarea Problemei:** Gemini scanează log-urile și structura pentru a depista bottleneck-uri sau erori de logică (ex: MAPE 32%).
2. **Generarea Raportului:** Orice analiză se salvează automat în `Gemini_Documentatie/` sub folderul corespunzător.
3. **Planificarea (Priorități):** Fiecare raport include un tabel de priorități unificat (**P0 - P4**).
4. **Validarea:** După implementarea manuală a recomandărilor, Gemini CLI poate re-audita sistemul pentru a confirma succesul.

### 5. Documentare & Resurse
Toate rapoartele livrate de Gemini CLI sunt salvate în:
`Gemini_Documentatie/Analiza_Totala/[DATA_ORA]/`

---
*Acest document este auto-sincronizat de Gemini CLI.*
