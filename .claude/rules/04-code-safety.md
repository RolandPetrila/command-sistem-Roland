# Code Safety Checks

## 1. Git Safety
**Trigger:** Before any major refactoring (moving files, restructuring modules, DB schema changes).

- Check for uncommitted changes
- If uncommitted changes exist → propose `git add [specific files] + commit` BEFORE refactoring
- After refactoring → propose commit with clear description
- **NEVER use `git add -A` or `git add .`** — always add specific files by name
- Does NOT block — only warns and proposes

## 2. URL Hardcoded Check
**Trigger:** Any modification to `frontend/src/api/client.js`.

- Verify file does NOT contain hardcoded `localhost` (exception: comments)
- URLs must use `window.location.origin` or be relative
- WebSocket: dynamic protocol (`ws:`/`wss:` based on `location.protocol`)
- If hardcoded URL found → IMMEDIATE warning
- Origin: Audit CRITICAL-2

## 3. DB Migration Check
**Trigger:** Any modification to files in `app/db/` or `backend/modules/*/models.py`.

- Check if the change adds/modifies tables or columns
- If yes → verify corresponding SQL file exists in `migrations/`
- If missing → warn and propose creating the SQL migration file
- Origin: Audit CRITICAL-4
