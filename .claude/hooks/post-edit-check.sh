#!/bin/bash
# Hook: PostToolUse (Edit|Write|MultiEdit) — Safety checks + auto-sync .meta/
# Read-only, silent fail (exit 0) — NU blocheaza tool execution
# Conform blueprint Native Workspace v2.1 (E7)

set +e
WORKSPACE="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$WORKSPACE" || exit 0

# Check 1: Hardcoded localhost in client.js (rule 04 code-safety)
CLIENT_JS="frontend/src/api/client.js"
if [ -f "$CLIENT_JS" ]; then
    HARDCODED=$(grep -n "localhost" "$CLIENT_JS" | grep -v "^[[:space:]]*//" | grep -v "^[[:space:]]*\*" || true)
    if [ -n "$HARDCODED" ]; then
        echo "[WARNING] Hardcoded localhost found in $CLIENT_JS:"
        echo "$HARDCODED"
        echo "Use window.location.origin or relative URLs instead."
    fi
fi

# Check 2: Auto-sync .meta/status.yaml (E5/E7 — silent fail)
if [ -f ".meta/status.yaml" ] && command -v python >/dev/null 2>&1; then
    python .claude/scripts/sync-meta.py 2>/dev/null || true
fi

# Check 3: DB schema changes without migration (passive reminder)
# Only trigger if edited files are in db/ or modules/*/models.py
# (passive — not implemented as automatic check yet)

exit 0
