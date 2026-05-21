# Zona lucru asistent AI

Zona dedicata pentru work-in-progress al asistentului AI. Conform blueprint Native Workspace v2.1 (P6 — zona de lucru separata).

## Distinctie cheie

- **`.workspace/`** (acest folder) — zona AI work: drafts, RCA, audit-outputs
- **`99_Roland_Work_Place/`** — zona USER personala: notite, capturi, audit-uri user
- **`docs/`** — narrative arhitectural commited

## Continut

| Folder            | Scop                                                                                | Tracked?                                  |
| ----------------- | ----------------------------------------------------------------------------------- | ----------------------------------------- |
| `drafts/`         | Planuri WIP pre-aprobare user (propuneri de implementare, planuri faze, brainstorm) | ✅ commited                               |
| `investigations/` | Bug analyses, RCA (root cause analysis), profiling, debug outputs                   | ✅ commited (au valoare istorica)         |
| `audit-outputs/`  | Rezultate `/audit`, `/security-review`, `/perf` skill calls                         | ❌ gitignored (volume mare, regenerabile) |
| `scratchpad.md`   | Notite scurte work-in-session, idei rapide                                          | ✅ commited                               |

## Reguli

1. Nimic in `.workspace/` NU e activ in production
2. Promovare la `docs/` cand devine plan oficial sau decizie acceptata
3. Arhivare la `.archive/` cand depasit (P7 — arhiva over delete)
4. Plan-uri activate (in curs de implementare) → `PLAN_*.md` la radacina (mut in .archive/ dupa finalizare)
