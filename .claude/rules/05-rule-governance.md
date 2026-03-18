# Rule Governance Protocol

**Trigger:** When user requests modification/addition/deletion of any rule.

## Process:

1. **Read ALL existing rules** from `.claude/rules/`
2. **Analyze request**: logical consistency, conflicts with existing rules
3. **Adapt wording** for clarity and consistency with existing rule style
4. **Present BEFORE/AFTER** comparison to user
5. **AFTER confirmation**: apply changes and log

## Logging
File: `99_Roland_Work_Place/CHANGELOG_RULES.md`

Format:
```
### [YYYY-MM-DD] — [filename] — [ADD/MODIFY/DELETE]
**Before:** [previous text or "N/A" for new rules]
**After:** [new text or "N/A" for deletions]
**Reason:** [why the change was made]
```

## Rule Priority (conflict resolution)

Rules in `.claude/rules/` and project `CLAUDE.md` take PRIORITY over `~/.claude/CLAUDE.md` global rules when there is a direct conflict.

### Global rules that DO NOT APPLY to this project:
- **R-CLEAN** — does not apply (project structure defined in local CLAUDE.md)
- **R-WORK** — does not apply (local conventions: 99_Roland_Work_Place/ without dated subfolders)
- **R-SYNC** — does not apply (project has no Gemini/Codex equivalent)
- **R-SNAPSHOT** — does not apply (tracking via PLAN_EXTINDERE + .claude/rules/, not PENDING_IMPLEMENTARI.md)

### Global rules REPLACED by local equivalents:
- **R-BRIEF** and **R-MODE** from global → replaced by `02-pre-implementation.md` for tasks in this project. One briefing process, not three overlapping ones.
