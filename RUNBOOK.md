# RUNBOOK — Roland Command Center

Operatiuni de urgenta — 1 pagina. Pentru context detaliat: `docs/plan.md`, `CLAUDE.md`, `.meta/status.yaml`.

## Pornire / Oprire

```
python start.py                # dev cu Cloudflare tunnel public (DEFAULT)
python start.py dev            # dev fara tunnel
python start.py prod           # production (build + serve frontend)
python start.py tunnel         # numai tunnel public (restart URL)
python start.py stop           # opreste TOATE procesele
```

**Auto-start la login:** Task Scheduler `RolandCC_AutoStart` (User Logon, delay 30s).
**Re-register task:** `schtasks /Create /TN RolandCC_AutoStart /XML scripts/auto-start-task.xml /F`

## URLs

- Local: `http://127.0.0.1:8000` (backend) + `http://localhost:5173` (frontend dev)
- Tailscale: `https://desktop-cjuecmn.tail7bc485.ts.net:8000`
- Cloudflare quick: `https://*.trycloudflare.com` (URL random per restart, vezi `.meta/status.yaml` sau `python start.py`)
- Cloudflare named: setup prin `python scripts/setup_named_tunnel.py` (URL stabil pe `*.cfargotunnel.com`)
- Health endpoint: `http://127.0.0.1:8000/api/health` → `{"status":"ok"}`

## Backup / Restore DB

```
curl -X POST http://localhost:8000/api/reports/backup          # backup manual SQLite
curl http://localhost:8000/api/reports/db-integrity            # check integrity
curl http://localhost:8000/api/reports/export/critical-json -o backup_data.json
```

**Auto-backup:** SQLite zilnic via cron in `automations` (Faza 32 AXA D).
**Locatie backup-uri:** `backend/data/backups/*.db` (gitignored).
**Restore:** Stop backend → copy backup peste `backend/data/roland.db` → restart.

## Recovery la erori

| Simptom                   | Cauza tipica         | Fix                                                             |
| ------------------------- | -------------------- | --------------------------------------------------------------- |
| Backend nu porneste       | uvicorn zombie       | `python start.py stop` apoi `taskkill /F /IM python.exe`        |
| Port 8000 ocupat          | proces stale         | `netstat -aon \| findstr ":8000"` apoi `taskkill /F /PID <pid>` |
| Frontend HMR nu reincarca | vite hot stale       | Ctrl+C in terminal Vite, restart                                |
| Tunnel URL expirat        | quick tunnel restart | `python start.py tunnel` (URL nou)                              |
| DB locked                 | concurrent write     | wait 5s + retry (busy_timeout=5000 deja)                        |
| Import error la pornire   | Syntax error nou     | `python -c "from app.main import app"` pentru detalii           |
| PWA nu se actualizeaza    | service worker cache | Browser DevTools → Application → Service Workers → Update       |

## Tailscale acces remote

```
tailscale status                                          # verifica conexiune
ping desktop-cjuecmn.tail7bc485.ts.net                    # verifica DNS
tailscale cert desktop-cjuecmn.tail7bc485.ts.net          # regenerare TLS cert (anual)
```

Acces Android: Chrome → `https://desktop-cjuecmn.tail7bc485.ts.net:8000`

## Config esential

- **API Keys:** Windows User Environment Variables (`C:\Users\ALIENWARE\.api-keys\` + `verify.ps1`)
- **Backend config:** `backend/.env` (Gmail App Password, Telegram Chat ID — vezi `docs/todo.md` 1.1 + 1.5)
- **Cloudflare token:** `cloudflared/tunnel_token.txt` (gitignored)
- **TLS cert:** `backend/certs/` (gitignored, Tailscale)

## Logs

- `logs/backend.log` — backend stdout/stderr (gitignored)
- `logs/vite.log` — frontend dev server (gitignored)
- `logs/watchdog.log` — Faza 34 watchdog audit (gitignored)
- `.workspace/audit-outputs/root-sweeper.log` — root cleanup warnings

## Verificare sistem (Rule 08)

```bash
cd backend && set PYTHONIOENCODING=utf-8 && python -c "from app.main import app; print('Import OK')"
curl http://127.0.0.1:8000/api/health
cd frontend && npx vite build      # daca s-a modificat frontend
```

## Sync .meta/ manual

```bash
python .claude/scripts/sync-meta.py --verbose     # regenereaza .meta/status.yaml
python .claude/scripts/indexer.py --verbose       # regenereaza .meta/sitemap.yaml
python .claude/scripts/root-sweeper.py            # warn root files
```

## Escalation

- **Owner principal:** Roland Petrila (petrilarolly@gmail.com)
- **Locatie sursa master API keys:** vezi `C:\Users\ALIENWARE\.api-keys\master-location.txt`
- **Repository git:** https://github.com/RolandPetrila/command-sistem-Roland.git
- **Backup off-site:** Google Drive `G:\My Drive\Roly\4. Artificial Inteligence\1.0_Traduceri\NOU_Calculator_Pret_Traduceri`

## Compliance & legal

- Date fiscale (facturi, ITP): tabela `audit_log_critic` cu trigger on UPDATE/DELETE (Faza 33)
- Audit ANAF: e-Factura UBL 2.1 generator in `backend/modules/invoice/efactura.py`
- Retentie date: backup SQLite zilnic local + GDrive copy (Faza 32)
