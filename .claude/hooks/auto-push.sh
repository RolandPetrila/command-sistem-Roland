#!/usr/bin/env bash
# Auto-commit + push hook (Stop event) — silent daca nu sunt modificari.
# Extras din Skeleton 20 — Blueprints/_skeleton/20_git_auto_push_stop_hook.md
set +e
WORKSPACE="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$WORKSPACE" || exit 0
LOG_FILE="$WORKSPACE/.claude/hooks/auto-push.log"

log() {
  printf '[%s] %s | %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$1" "$2" >> "$LOG_FILE" 2>/dev/null || true
}

branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || true)"
if [[ -z "$branch" || "$branch" == "HEAD" ]]; then
  log SKIP_DETACHED "no branch (detached HEAD?)"
  exit 0
fi

status="$(git status --porcelain 2>/dev/null)"
if [[ -z "$status" ]]; then
  log NO_CHANGES "git status empty"
  exit 0
fi

change_count="$(printf '%s\n' "$status" | grep -c '.')"

git add . 2>&1 >/dev/null

ts="$(date '+%Y-%m-%d %H:%M:%S')"
msg="auto: $ts [$change_count file(s)]"

if ! git commit -m "$msg" 2>&1 >/dev/null; then
  log NO_COMMIT "files_seen=$change_count; likely all ignored"
  exit 0
fi

push_output="$(git push origin "$branch" 2>&1)"
push_rc=$?
if [[ $push_rc -ne 0 ]]; then
  echo "[auto-push] FAIL push origin $branch (rezolva manual: git pull --rebase; git push)" >&2
  log FAIL_PUSH "files=$change_count; commit_local_kept; err=$push_output"
  exit 0
fi

echo "[auto-push] OK: $change_count file(s) -> origin/$branch @ $ts" >&2
log OK "files=$change_count; pushed_to_origin_$branch"
exit 0
