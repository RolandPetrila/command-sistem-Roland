# Pre-Implementation Gate — Before Any Wave/Phase

**Trigger:** BEFORE starting implementation of any Wave or Phase.
**Mandatory** — NO code without completing this process.

This rule REPLACES R-BRIEF and R-MODE from global CLAUDE.md for tasks in this project. Only ONE briefing, not three overlapping ones.

## Process (all steps, in order):

### Step 1 — Dependency Check
- Read cross-phase dependencies from `0.0_PLAN_EXTINDERE_COMPLET.md`
- If the feature has unimplemented dependencies → warn and list them
- Does NOT block — only informs

### Step 2 — Suggest Logical Phases
- Order by: dependencies resolved → low effort → high value
- Present recommended Wave/Phase

### Step 3 — Summary Table
```
## Wave/Phase X — [Name] ([N] items, ~[T] estimate)

| # | Feature | What it does (concrete example) | Effort |
|---|---------|--------------------------------|--------|
| 1 | Name    | "Press Ctrl+K, type 'set', jump to Settings" | 1-2h |

Dependencies: [list or "none"]
Visible result: [what the user sees differently after implementation]
```

### Step 4 — Detailed Per-Feature Breakdown
For EACH feature:
- **Current state** (what exists now, if anything)
- **After implementation** (new behavior)
- **Concrete example** (real scenario from user's workflow)
- **Technology** (libraries, APIs)

### Step 5 — Recommendation
- Which features are most useful, which can be deferred, with arguments

### Step 6 — WAIT for explicit user confirmation
- If user wants changes (add/remove items, reorder) → adjust and re-present
- Only AFTER confirmation → start coding
