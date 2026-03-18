# Progress Tracking — After Every Implementation

**Trigger:** After EVERY implementation execution (not just at session end).
**Mandatory** — runs automatically, no confirmation needed.

## Checklist (all 4 steps, every time):

1. **Mark progress** in `99_Roland_Work_Place/0.0_PLAN_EXTINDERE_COMPLET.md`:
   - `✅ Description (YYYY-MM-DD) — technical details` for DONE
   - `🔄 Description` for IN PROGRESS
   - `⏸️ Description` for PENDING/DEFERRED
   - Add new items for implemented features not yet listed
   - Include test status: `✅ Testat Android OK` | `✅ Testat local OK` | `🧪 Netestat Android` | `🧪 Bug fixat, re-test necesar`
   - Maintain per-phase counter: "X/Y testat Android"

2. **Regenerate HTML** — update `99_Roland_Work_Place/0.0_PLAN_EXTINDERE_COMPLET.html`:
   - Update the PHASES JavaScript array to match .md changes
   - Include `tested` property on each item
   - Preserve existing HTML structure (interactive selector, dark theme, checkboxes)

3. **Update CLAUDE.md** Project Status section:
   - Compress to 1 line per phase/wave with status
   - Update any changed statuses

4. **Update `.claude/PROJECT_STATUS.md`** snapshot:
   - Compact auto-generated status for quick session context
