# MEMORIE CLAUDE CODE — Toate Mecanismele Disponibile

> **Scop:** Referință completă pentru verificare periodică, editare și optimizare a regulamentelor Claude Code.
> **Aplicabil:** Orice proiect, orice folder de lucru.

---

## A) INSTRUCȚIUNI CITITE AUTOMAT (fără acțiune din partea ta)

### A1. CLAUDE.md — Rădăcina proiectului
- **Locație:** `<proiect>/CLAUDE.md`
- **Scope:** PROIECT
- **Citit automat:** DA — la fiecare mesaj, în fiecare sesiune
- **Limită recomandată:** ~200 rânduri (se consumă tokeni la fiecare mesaj)
- **Ce conține ideal:** Overview proiect, status curent, key files, conventions, how to run
- **Ce NU trebuie să conțină:** Reguli detaliate (merg în .claude/rules/), documentație lungă
- **Unde se editează:** Direct în fișier, orice editor

### A2. CLAUDE.md — Global (toate proiectele)
- **Locație:** `~/.claude/CLAUDE.md`
- **Scope:** GLOBAL — se aplică în TOATE proiectele, TOATE sesiunile
- **Citit automat:** DA — la fiecare mesaj, indiferent de proiect
- **Ce conține ideal:** Regulament general, identitate AI, format erori, securitate, recovery
- **Atenție:** Modificările aici afectează TOATE proiectele — risc HIGH

### A3. CLAUDE.md — Nested în subdirectoare
- **Locație exemplu:** `<proiect>/backend/CLAUDE.md`, `<proiect>/frontend/CLAUDE.md`
- **Scope:** PROIECT — subfolder specific
- **Citit automat:** DA — când se lucrează pe fișiere din acel folder
- **Ce conține ideal:** Reguli specifice acelui subfolder (pattern-uri, convenții locale)
- **Avantaj:** Regulile se încarcă doar când sunt relevante — nu poluează contextul

### A4. .claude/rules/*.md
- **Locație:** `<proiect>/.claude/rules/`
- **Scope:** PROIECT
- **Citit automat:** DA — TOATE fișierele din folder, la fiecare mesaj
- **Ce conține ideal:** Reguli detaliate separate pe domeniu, un fișier per subiect
- **Exemple fișiere:**
  - `decizii_permanente.md` — ce nu se rediscută
  - `reguli_auto_update.md` — reguli de actualizare automată
  - `roadmap.md` — harta fazelor cu status
  - `arhitectura.md` — structura proiectului, pattern-uri
- **Avantaj:** CLAUDE.md rămâne scurt, regulile sunt organizate logic

### A5. Memory files
- **Locație index:** `~/.claude/projects/<proiect-sanitizat>/memory/MEMORY.md`
- **Locație fișiere:** Același folder, fișiere `.md` individuale
- **Scope:** PROIECT (dar stocat global, per working directory)
- **Citit automat:** DA — indexul MEMORY.md la fiecare mesaj (limită 200 rânduri)
- **Ce conține ideal:** Feedback utilizator, preferințe, referințe externe, decizii tehnice confirmate
- **Ce NU conține:** Reguli de implementare, status proiect (astea merg în rules/)
- **Tipuri:** user, feedback, project, reference

---

## B) HOOKS — Acțiuni automate la evenimente

Hooks se configurează în `settings.local.json` (per proiect) sau `~/.claude/settings.json` (global).

### B1. SessionStart
- **Când rulează:** La deschiderea fiecărei sesiuni noi
- **Util pentru:** Afișare status proiect, verificare elemente pendinte, reminder-uri
- **Exemplu:**
```json
{
  "hooks": {
    "SessionStart": [{
      "hooks": [{
        "type": "command",
        "command": "python scripts/show_status.py",
        "timeout": 10
      }]
    }]
  }
}
```

### B2. Stop
- **Când rulează:** La închiderea sesiunii (inclusiv clear, resume, compact)
- **Util pentru:** Auto-update documentație, salvare status final sesiune
- **Exemplu:**
```json
{
  "hooks": {
    "Stop": [{
      "hooks": [{
        "type": "command",
        "command": "python scripts/auto_update_docs.py"
      }]
    }]
  }
}
```

### B3. PostToolUse (Edit|Write)
- **Când rulează:** După fiecare editare/creare de fișier
- **Matcher:** `"Edit|Write"` — doar la aceste tool-uri
- **Util pentru:** Verificări automate (formatare, validare, linting)
- **Exemplu:**
```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Edit|Write",
      "hooks": [{
        "type": "command",
        "command": "python scripts/post_edit_check.py"
      }]
    }]
  }
}
```

### B4. PreToolUse
- **Când rulează:** Înainte de executarea unui tool
- **Util pentru:** Blocare acțiuni periculoase, validare input
- **Poate returna:** `{ "decision": "block", "reason": "..." }` pentru a bloca acțiunea

### B5. PostToolUse (Bash)
- **Matcher:** `"Bash"`
- **Util pentru:** Logging comenzi executate, verificare post-execuție

### B6. PreCompact
- **Când rulează:** Înainte de compactarea contextului (când conversația devine prea lungă)
- **Matcher:** `"manual"` sau `"auto"`
- **Util pentru:** Salvare informații critice care nu trebuie pierdute la compactare

### B7. PostCompact
- **Când rulează:** După compactare
- **Util pentru:** Reinjectare context critic pierdut la compactare

### B8. UserPromptSubmit
- **Când rulează:** Când utilizatorul trimite un mesaj
- **Util pentru:** Validare input, logging
- **Atenție:** Adaugă overhead la FIECARE mesaj — folosește cu prudență

### B9. Notification
- **Când rulează:** La notificări sistem
- **Util pentru:** Alertare externă (email, webhook)

### B10. PermissionRequest
- **Când rulează:** Înainte de afișarea promptului de permisiune
- **Util pentru:** Auto-approve sau auto-deny bazat pe reguli custom

### B11. PostToolUseFailure
- **Când rulează:** După ce un tool eșuează
- **Util pentru:** Logging erori, retry logic, alertare

### B12. SubagentStart / SubagentStop
- **Când rulează:** La pornirea/oprirea unui sub-agent
- **Util pentru:** Monitorizare agenți, logging

### B13. InstructionsLoaded
- **Când rulează:** După încărcarea instrucțiunilor (CLAUDE.md, rules, etc.)
- **Util pentru:** Validare reguli, verificare coerență

### Tipuri de hooks

| Tip | Ce face | Disponibil la |
|-----|---------|---------------|
| **command** | Rulează o comandă shell | Toate evenimentele |
| **prompt** | Evaluează o condiție cu LLM | Doar PreToolUse, PostToolUse, PermissionRequest |
| **agent** | Rulează un agent cu tool-uri | Doar PreToolUse, PostToolUse, PermissionRequest |
| **http** | Trimite POST la un URL | Toate evenimentele |

### Output JSON din hooks (ce poate returna un hook)

```json
{
  "systemMessage": "Mesaj afișat utilizatorului",
  "continue": false,
  "stopReason": "Motiv blocare",
  "suppressOutput": false,
  "decision": "block",
  "reason": "Explicație",
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "Context injectat înapoi în model",
    "permissionDecision": "allow | deny | ask",
    "permissionDecisionReason": "Motiv decizie",
    "updatedInput": {}
  }
}
```

### Proprietăți opționale pe hooks

| Proprietate | Ce face |
|-------------|---------|
| `timeout` | Timeout în secunde |
| `statusMessage` | Mesaj afișat în spinner cât rulează |
| `once` | Dacă true, hook-ul rulează o singură dată apoi se elimină |
| `async` | Dacă true, rulează în background fără să blocheze |
| `asyncRewake` | Dacă true, rulează în background și trezește modelul la exit code 2 |

---

## C) COMENZI ȘI AGENȚI CUSTOM

### C1. Slash commands
- **Locație:** `<proiect>/.claude/commands/`
- **Scope:** PROIECT
- **Citit automat:** NU — invocat manual cu `/nume-comanda`
- **Ce conține:** Un fișier `.md` per comandă, cu promptul complet
- **Exemple:** `/update-docs`, `/status`, `/test-guide`, `/pre-wave`
- **Format fișier:** Markdown cu instrucțiuni — Claude le execută ca prompt

### C2. Agenți custom
- **Locație:** `<proiect>/.claude/agents/`
- **Scope:** PROIECT
- **Citit automat:** NU — invocați prin Agent tool din conversație
- **Ce conține:** Fișier `.md` cu frontmatter (model, tools) + system prompt
- **Exemple:** agent actualizare documentație, agent veghere regulament, agent teste
- **Format:**
```markdown
---
name: nume-agent
model: sonnet
tools: ["Read", "Edit", "Write", "Glob", "Grep"]
---
Ești un agent dedicat pentru [scop]...
```

---

## D) CONFIGURARE

### D1. settings.json (proiect, comis în git)
- **Locație:** `<proiect>/.claude/settings.json`
- **Scope:** PROIECT — shared cu toți (dacă e în git)
- **Ce conține:** Permisiuni, hooks, env vars comune
- **Atenție:** Comis în git — nu pune secrete aici

### D2. settings.local.json (proiect, NU în git)
- **Locație:** `<proiect>/.claude/settings.local.json`
- **Scope:** PROIECT — doar local, override peste settings.json
- **Ce conține:** Permisiuni personale, hooks locale, override-uri
- **Aici se pun hooks-urile personale** — nu afectează alte mașini

### D3. settings.json (global)
- **Locație:** `~/.claude/settings.json`
- **Scope:** GLOBAL — toate proiectele
- **Ce conține:** Preferințe globale (theme, model, permissions globale)

### D4. Ordine de încărcare (prioritate)
```
~/.claude/settings.json         (global — baza)
  → .claude/settings.json       (proiect — override)
    → .claude/settings.local.json (local — CÂȘTIGĂ)
```
Settings-urile se merge-uiesc. Local override > proiect > global.

---

## E) MCP SERVERS

### E1. .mcp.json
- **Locație:** `<proiect>/.mcp.json` sau `~/.claude/.mcp.json`
- **Scope:** PROIECT sau GLOBAL
- **Ce face:** Definește tool-uri externe (servere MCP)
- **Potențial util:** Servere MCP custom pentru integrări specifice

---

## F) PLUGINS

### F1. Marketplace plugins
- **Configurare:** `settings.json` → `enabledPlugins`
- **Scope:** PROIECT sau GLOBAL
- **Ce face:** Extinde capabilitățile Claude Code cu plugin-uri din marketplace
- **Format:** `"plugin-name@marketplace-id": true`

---

## G) ALTE SETĂRI RELEVANTE

| Setare | Locație | Ce face |
|--------|---------|---------|
| `model` | settings.json | Model implicit (opus/sonnet/haiku) |
| `effortLevel` | settings.json | Nivel efort persistent (low/medium/high) |
| `language` | settings.json | Limbă preferată răspunsuri |
| `autoMemoryEnabled` | settings.json | Activare/dezactivare auto-memory |
| `autoMemoryDirectory` | settings.json | Director custom pentru memory (suportă ~/) |
| `plansDirectory` | settings.json | Director custom pentru planuri |
| `respectGitignore` | settings.json | Respectă .gitignore la căutări |
| `cleanupPeriodDays` | settings.json | Retenție transcrieri (zile, 0 = dezactivat) |
| `attribution` | settings.json | Text atribuire commituri/PR-uri |
| `fastMode` | settings.json | Mod rapid (același model, output mai rapid) |
| `alwaysThinkingEnabled` | settings.json | Thinking activat permanent |
| `voiceEnabled` | settings.json | Mod voce (dictare hold-to-talk) |
| `defaultView` | settings.json | Vizualizare implicită: "chat" sau "transcript" |
| `showThinkingSummaries` | settings.json | Afișare rezumate thinking (ctrl+o) |
| `syntaxHighlightingDisabled` | settings.json | Dezactivare syntax highlighting în diff-uri |
| `spinnerTipsEnabled` | settings.json | Afișare tips în spinner |
| `promptSuggestionEnabled` | settings.json | Sugestii de prompt activate |

---

## H) CHEAT SHEET — CE FOLOSESC ȘI UNDE

| Nevoie | Mecanism | Scope |
|--------|----------|-------|
| Reguli care se aplică MEREU în toate proiectele | `~/.claude/CLAUDE.md` | GLOBAL |
| Status proiect, overview | `<proiect>/CLAUDE.md` | PROIECT |
| Reguli detaliate per domeniu | `.claude/rules/*.md` | PROIECT |
| Reguli specifice subfolder | `backend/CLAUDE.md`, `frontend/CLAUDE.md` | PROIECT subfolder |
| Preferințe și feedback utilizator | Memory files | PROIECT |
| Acțiune automată la start sesiune | Hook SessionStart | PROIECT/GLOBAL |
| Acțiune automată la final sesiune | Hook Stop | PROIECT/GLOBAL |
| Verificare automată după editare | Hook PostToolUse | PROIECT/GLOBAL |
| Salvare context la compactare | Hook PreCompact | PROIECT/GLOBAL |
| Reinjectare context după compactare | Hook PostCompact | PROIECT/GLOBAL |
| Blocare acțiuni periculoase | Hook PreToolUse | PROIECT/GLOBAL |
| Comandă rapidă invocată manual | `.claude/commands/*.md` | PROIECT |
| Agent specializat reutilizabil | `.claude/agents/*.md` | PROIECT |
| Tool-uri externe | MCP servers (`.mcp.json`) | PROIECT/GLOBAL |
| Permisiuni și hooks locale | `settings.local.json` | PROIECT |
| Permisiuni și hooks globale | `~/.claude/settings.json` | GLOBAL |

---

## I) STRUCTURA RECOMANDATĂ GENERICĂ

```
<proiect>/
├── CLAUDE.md                          ← overview + status (~120-200 rânduri)
├── backend/
│   └── CLAUDE.md                      ← reguli specifice backend
├── frontend/
│   └── CLAUDE.md                      ← reguli specifice frontend
├── .claude/
│   ├── settings.json                  ← hooks + permisiuni (comis în git)
│   ├── settings.local.json            ← override-uri locale (NU în git)
│   ├── rules/
│   │   ├── decizii_permanente.md      ← decizii confirmate
│   │   ├── reguli_auto_update.md      ← reguli de actualizare automată
│   │   ├── roadmap.md                 ← harta proiectului cu status live
│   │   └── arhitectura.md             ← structura, pattern-uri, convenții
│   ├── commands/
│   │   ├── update-docs.md             ← /update-docs
│   │   ├── status.md                  ← /status
│   │   └── test-guide.md              ← /test-guide
│   └── agents/
│       ├── doc-updater.md             ← agent actualizare documentație
│       └── rule-guardian.md           ← agent veghere regulament
│
GLOBAL (în ~/.claude/):
├── CLAUDE.md                          ← regulament global (toate proiectele)
├── settings.json                      ← preferințe globale
└── projects/<proiect>/memory/         ← memory files per proiect
```

---

## J) VERIFICARE PERIODICĂ — CHECKLIST

Folosește această listă la fiecare verificare/optimizare:

- [ ] CLAUDE.md root — sub 200 rânduri? Status actualizat?
- [ ] .claude/rules/ — fișierele reflectă deciziile curente?
- [ ] CLAUDE.md nested (subdirectoare) — există și sunt relevante?
- [ ] Hooks — funcționează? Testează cu `echo '{}' | <comanda>`
- [ ] Memory files — sunt la zi? Există duplicate?
- [ ] Commands — sunt utile? Se folosesc efectiv?
- [ ] Agents — sunt definiți? Prompt-urile sunt clare?
- [ ] settings.local.json — permisiunile acoperă tool-urile folosite?
- [ ] Documentație execuție — reflectă realitatea din cod?
- [ ] Fișiere vechi — pot fi arhivate sau eliminate?

---

## K) LISTĂ COMPLETĂ EVENIMENTE HOOKS

Din schema oficială Claude Code:

```
PreToolUse, PostToolUse, PostToolUseFailure,
Notification, UserPromptSubmit, SessionStart, SessionEnd,
Stop, SubagentStart, SubagentStop,
PreCompact, PostCompact, PermissionRequest,
Setup, TeammateIdle, TaskCompleted,
Elicitation, ElicitationResult, ConfigChange,
WorktreeCreate, WorktreeRemove, InstructionsLoaded
```

---

*Document referință — aplicabil oricărui proiect Claude Code.*
*Sursa: Schema oficială settings.json + documentație Claude Code.*
