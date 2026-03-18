# Validation & Testing — After Phase Completion

**Trigger:** At completion of any Wave or Phase implementation.
**Mandatory** — do NOT proceed to next wave without full validation.

## Validation Process:

### Step 1 — Test All Implemented Features
- Test every feature from the completed phase
- If something doesn't work → fix immediately, do NOT move on

### Step 2 — Create/Update Test Guide
File: `99_Roland_Work_Place/GHID_TESTARE.md`

For EACH implemented feature, include:
- **Feature name** + short description
- **Test Web (PC)** — exact steps to test in browser on PC
- **Test Phone (Android)** — exact steps to test via Tailscale on phone
- **Expected result** — what should happen if working correctly
- **Status** — `✅ Testat OK` / `🧪 Netestat` / `❌ Bug cunoscut`

Organize by phases with clear sections and easy navigation.

### Step 3 — User Confirmation Required
- User must explicitly confirm they tested and are satisfied
- Only THEN can the next wave/phase begin

### Step 4 — Update Test Markers
When user confirms a feature works on Android → mark `✅ Testat Android OK (YYYY-MM-DD)` in:
- `0.0_PLAN_EXTINDERE_COMPLET.md`
- `GHID_TESTARE.md`
