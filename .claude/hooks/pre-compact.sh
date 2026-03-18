#!/bin/bash
# Hook: PreCompact — Regenerate PROJECT_STATUS.md before context compaction
# This is the only hook that writes (necessary to survive compaction)

STATUS_FILE=".claude/PROJECT_STATUS.md"

# Extract key info from CLAUDE.md
echo "# Roland Command Center — Project Status (auto-generated)" > "$STATUS_FILE"
echo "" >> "$STATUS_FILE"
echo "Generated: $(date '+%Y-%m-%d %H:%M')" >> "$STATUS_FILE"
echo "" >> "$STATUS_FILE"

# Extract Project Status section from CLAUDE.md
if [ -f "CLAUDE.md" ]; then
    sed -n '/^## Project Status/,/^## [^P]/p' CLAUDE.md | head -n -1 >> "$STATUS_FILE"
fi

echo "" >> "$STATUS_FILE"
echo "## Quick Reference" >> "$STATUS_FILE"
echo "- Rules: \`.claude/rules/\` (5 files)" >> "$STATUS_FILE"
echo "- Commands: \`/update-status\`, \`/pre-wave\`, \`/test-guide\`, \`/rule-change\`" >> "$STATUS_FILE"
echo "- Full plan: \`99_Roland_Work_Place/0.0_PLAN_EXTINDERE_COMPLET.md\`" >> "$STATUS_FILE"
echo "- Test guide: \`99_Roland_Work_Place/GHID_TESTARE.md\`" >> "$STATUS_FILE"
