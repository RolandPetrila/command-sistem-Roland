# Error Handling & Diagnostics — Mandatory Convention

**Trigger:** When creating or modifying ANY endpoint, page, or API call.
**Mandatory** — applies to ALL existing and future code.

## Backend: Automatic Error Logging

All API errors (4xx/5xx) are captured automatically by the request logger middleware in `app/main.py`.
- NO manual `log_activity()` needed for error paths
- The middleware logs: method, path, status, duration, response body, client IP, user-agent
- Endpoint code only needs `log_activity()` for SUCCESS paths (business events)

### When adding a new endpoint:
1. Log success with `await log_activity(action="module.action", summary="...", details={...})`
2. Do NOT add try/catch just for logging — let errors propagate to middleware
3. Use `raise HTTPException(status_code, detail="clear message")` for expected errors

## Frontend: Global Toast + Interceptor

All API errors are automatically:
1. **Reported to backend** via axios interceptor → `POST /api/log/frontend`
2. **Shown to user** via global toast notification (top-right corner)
3. **Visible in diagnostics panel** (triangle icon in header)

### When adding a new page:
1. **NEVER use `catch { /* ignore */ }`** for API calls — the toast needs the error to propagate
2. For data-loading catches that set default state: `catch { /* toast handles it */ }` is OK
3. For critical user actions (save, delete, translate): add local error state + show in UI
4. Clipboard and non-API operations: silent catch is acceptable

### Error handling pattern for user actions:
```jsx
try {
  await api.post('/api/endpoint', data);
  // success handling
} catch (err) {
  // Toast fires automatically via interceptor
  // Optionally set local error state for inline display:
  setError(err.response?.data?.detail || 'Eroare la operatie');
}
```

### For blob responses (file downloads):
```jsx
try {
  const { data } = await api.post('/api/endpoint', formData, {
    responseType: 'blob',
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  // Check if response is actually a JSON error
  if (data.type && data.type.includes('json')) {
    const text = await data.text();
    const parsed = JSON.parse(text);
    setError(parsed.detail || 'Eroare');
    return;
  }
  // Process blob...
} catch (err) {
  let errorMsg = err.message;
  if (err.response?.data instanceof Blob) {
    try {
      const text = await err.response.data.text();
      const parsed = JSON.parse(text);
      errorMsg = parsed.detail || text;
    } catch { /* use default */ }
  }
  setError(errorMsg);
}
```

## Diagnostics System

- **Endpoint:** `GET /api/diagnostics` — request stats, recent errors, system info
- **UI Panel:** Triangle icon in Header — opens slide-in panel from any page
- **In-memory stats:** Request count, error count, slow requests (>2s), uptime
- **Persistent log:** All errors stored in `activity_log` SQLite table

## Known Exceptions
- `AIChatPage.jsx` — uses native `fetch()` for SSE streaming (axios doesn't support streaming responses).
  This bypasses the interceptor. Manual error handling + user-visible error state is required for SSE calls.
  Status: ACKNOWLEDGED — SSE requires fetch(), not a rule violation.

## Key Files
- Backend middleware: `app/main.py` → `request_logger` middleware
- Frontend interceptor: `src/api/client.js` → axios response interceptor
- Toast component: `src/components/shared/GlobalToast.jsx`
- Diagnostics panel: `src/components/Layout/Header.jsx` → `DiagnosticsPanel`
