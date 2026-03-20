# Post-Change System Validation — Mandatory

**Trigger:** After completing ANY code modifications in this project (not just waves/phases).
**Mandatory** — do NOT declare work complete without this validation.

## Why This Rule Exists

Code changes can break the startup flow even when individual features work.
Zombie processes, import errors, and port conflicts are invisible until the full system is tested.
This rule ensures no broken system is ever delivered to the user.

## Validation Steps (ALL required, in order):

### Step 1 — Kill Test Processes
After any manual backend/frontend testing during the session:
- Kill all python.exe processes started for testing
- Verify port 8000 is free: `netstat -aon | findstr ":8000"`
- If port is occupied → kill the process before proceeding

### Step 2 — Quick Import Check
```bash
cd C:\Proiecte\NOU_Calculator_Pret_Traduceri\backend
set PYTHONIOENCODING=utf-8
python -c "from app.main import app; print('Import OK')"
```
- If IMPORT ERROR → fix BEFORE anything else
- This catches syntax errors, missing modules, circular imports instantly

### Step 3 — Backend Startup + Health Check
```bash
python -m uvicorn app.main:app --port 8000 --host 127.0.0.1
```
- Wait for "Uvicorn running on" message
- Verify health: `curl http://127.0.0.1:8000/api/health`
- Expected: `{"status":"ok",...}`
- If ANY startup error → fix BEFORE declaring done

### Step 4 — Frontend Build Check (if frontend was modified)
```bash
cd C:\Proiecte\NOU_Calculator_Pret_Traduceri\frontend
npx vite build
```
- Must complete without errors
- `dist/index.html` must exist

### Step 5 — Test Modified Endpoints
- Test each new/modified endpoint with curl (at least one valid + one invalid request)
- For UI changes: verify page loads in browser or Playwright
- If any endpoint fails → fix before proceeding

### Step 6 — Clean Shutdown
- Kill the test backend process
- Verify port 8000 is free again
- Confirm no zombie processes remain

### Step 7 — Report to User
Include in final response:
```
VALIDARE SISTEM:
- Import check: OK/FAIL
- Backend start: OK/FAIL
- Health check: OK/FAIL
- Frontend build: OK/FAIL/N/A
- Endpoint-uri: OK/FAIL/N/A
- Port cleanup: OK/FAIL
```

## Ce NU e acceptabil
- Sa raportezi "gata" bazat doar pe "codul arata corect"
- Sa faci build frontend dar sa nu verifici backend
- Sa lasi procese python din teste care blocheaza START_Roland.bat
- Sa testezi cu Playwright fara sa confirmi ca backend-ul e stabil
- Sa sari validarea "pentru ca e o modificare mica"

## Exceptions
- Documentation-only changes (no code modified)
- Rule/config changes that don't affect runtime
- Git operations only
