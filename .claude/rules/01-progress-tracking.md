# Progress Tracking — After Every Implementation

**Trigger:** After EVERY implementation execution (not just at session end).
**Mandatory** — runs automatically, no confirmation needed.
**Order:** Execute AFTER Rule 08 (validation). Logic: first confirm it works, then document progress.

## Checklist (all 4 steps, every time):

1. **Update `docs/plan.md`** (curent + roadmap, max 500 linii):
   - Marcheaza items completate / in progres
   - Adauga features noi nelistate
   - Update sectiunea "Stare curenta" cu numerele actuale (modules, routes, tests)
   - Conform structurii din §3 Roadmap activ

2. **Update istoricul detaliat** `99_Roland_Work_Place/0.0_PLAN_EXTINDERE_COMPLET.md` (1236 linii, faze 0-33):
   - `✅ Description (YYYY-MM-DD) — technical details` for DONE
   - `🔄 Description` for IN PROGRESS
   - `⏸️ Description` for PENDING/DEFERRED
   - Include test status: `✅ Testat Android OK` | `✅ Testat local OK` | `🧪 Netestat Android` | `🧪 Bug fixat, re-test necesar`
   - Maintain per-phase counter: "X/Y testat Android"
   - **Optional**: regenereaza `99_Roland_Work_Place/0.0_PLAN_EXTINDERE_COMPLET.html` (PHASES JS array) — doar daca user-ul foloseste HTML selector

3. **Update `.meta/status.yaml`** structured status:
   - last_commit + last_commit_msg + branch
   - phases.current + phases.latest_done
   - build.routes / migrations counts daca s-au schimbat
   - `python .claude/scripts/sync-meta.ps1` (E5 — cand exista, automat via hooks)

4. **Update `.claude/PROJECT_STATUS.md`** snapshot:
   - Compact auto-generated status for quick session context

5. **Update `CLAUDE.md`** doar pentru schimbari arhitecturale majore (NU per-faza)
