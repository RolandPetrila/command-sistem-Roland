#!/bin/bash
# Hook: PostToolUse (Edit|Write) — Safety checks
# Read-only, only displays warnings

# Check 1: Hardcoded localhost in client.js
CLIENT_JS="frontend/src/api/client.js"
if [ -f "$CLIENT_JS" ]; then
    # Look for hardcoded localhost (not in comments)
    HARDCODED=$(grep -n "localhost" "$CLIENT_JS" | grep -v "^[[:space:]]*//" | grep -v "^[[:space:]]*\*" || true)
    if [ -n "$HARDCODED" ]; then
        echo "[WARNING] Hardcoded localhost found in $CLIENT_JS:"
        echo "$HARDCODED"
        echo "Use window.location.origin or relative URLs instead."
    fi
fi

# Check 2: DB schema changes without migration
# Only trigger if the edited file is in db/ or modules/*/models.py
# This is a passive check - just reminds
