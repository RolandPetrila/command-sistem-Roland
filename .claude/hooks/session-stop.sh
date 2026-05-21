#!/bin/bash
# Hook: Stop — Reminder + root sweeper warn
# Read-only, silent fail (exit 0)
# Conform blueprint Native Workspace v2.1 (E7, R7)

set +e
WORKSPACE="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$WORKSPACE" || exit 0

# 1. Reminder progres
echo "[SESSION END] Reminder: If you implemented something, run /update-status before closing."

# 2. Root sweeper warn (P4, R7 — NU blocheaza)
if command -v python >/dev/null 2>&1 && [ -f ".claude/scripts/root-sweeper.py" ]; then
    python .claude/scripts/root-sweeper.py 2>/dev/null || true
fi

# 3. Reminder regenerate sitemap (rar, doar la create/delete fisiere)
echo "[SESSION END] Daca s-au creat/sters fisiere: python .claude/scripts/indexer.py"

exit 0
