#!/bin/bash
# Hook: SessionStart — Display project status snapshot
# Read-only, idempotent

STATUS_FILE=".claude/PROJECT_STATUS.md"

if [ -f "$STATUS_FILE" ]; then
    cat "$STATUS_FILE"
else
    echo "[SESSION START] No PROJECT_STATUS.md found. Run /update-status to generate."
fi
