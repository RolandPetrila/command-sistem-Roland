# Roland Command Center

> Panou personal multifuncțional — traduceri, facturare, ITP, AI pe documente, tool-uri rapide, automatizări — totul intr-un singur loc, accesibil PC + Android prin Tailscale + Cloudflare Tunnel.

**Firmă:** CIP Inspection SRL · **User:** Roland Petrila · **Buget:** zero cost (free tier only)

## Quick start

```bash
python start.py            # dev cu HMR + Cloudflare tunnel public
```

Detalii: `RUNBOOK.md`

## Stack

- **Backend:** FastAPI (Python 3.13) + SQLite (aiosqlite) + WebSocket
- **Frontend:** React 18 + Vite + Tailwind + PWA auto-update
- **Deploy:** Tailscale local + Cloudflare Tunnel public + Task Scheduler auto-start

## Module (14)

ai · automations · calculator (pret traduceri) · converter · filemanager · integrations (Gmail/GDrive/Calendar/GitHub) · invoice (cu e-Factura UBL 2.1) · itp · quick_tools (notepad + QR) · quick_tools_extra (calc + pwd + barcode) · reports · timetracking · translator (5 providers) · vault

## Documentatie

| Pentru                         | Vezi                                                 |
| ------------------------------ | ---------------------------------------------------- |
| Stare proiect machine-readable | `.meta/status.yaml`                                  |
| Plan curent + roadmap          | `docs/plan.md`                                       |
| Operatiuni urgenta             | `RUNBOOK.md`                                         |
| Regulament Claude Code         | `CLAUDE.md`                                          |
| Reguli proiect (8)             | `.claude/rules/*.md`                                 |
| Istoric 33 faze detaliat       | `99_Roland_Work_Place/0.0_PLAN_EXTINDERE_COMPLET.md` |
| Decizii arhitecturale          | `.meta/decisions.yaml`                               |
| API gratuite catalog           | `99_Roland_Work_Place/CATALOG_API_GRATUITE.md`       |
| Ghid testare                   | `99_Roland_Work_Place/GHID_TESTARE.md`               |
| Audit-uri externe              | `docs/audit-externe/`                                |

## Structura proiect (Native Workspace pattern)

```
README.md, RUNBOOK.md, CLAUDE.md, start.py, launch_roland.vbs
.meta/         Single Source of Truth (YAML)
docs/          Narrative + handovers + audit-externe
.workspace/    AI work (drafts, investigations)
.archive/      Documente deprecated
99_Roland_Work_Place/  USER_WORKSPACE personala
.claude/       Sistem Claude Code (rules + hooks + scripts)
backend/       FastAPI + 14 module + 355 routes + 25 migrations
frontend/      React + 26 pagini + PWA + manifest navigare
scripts/       PowerShell + Python automation
cloudflared/   Tunnel config (token gitignored)
Fisiere_Reper_Tarif/  26 PDF-uri calibrare pricing
```

## Conventii

- UI in Romana, cod in English
- Currency RON, no VAT, EN ↔ RO only
- Free tier exclusively
- Git: NEVER `git add -A` (add specific files)
- Windows: always `set PYTHONIOENCODING=utf-8`

## License

Privat — uz personal Roland Petrila (CIP Inspection SRL).
