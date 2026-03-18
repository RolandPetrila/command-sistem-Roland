# Plan Execuție — Roland Command Center (fost Calculator Preț Traduceri)

## FAZA 0 — Setup + Structură
- [x] 0.1 Structura completă de foldere (backend + frontend)
- [x] 0.2 backend/requirements.txt
- [x] 0.3 frontend/package.json
- [x] 0.4 CLAUDE.md complet
- [x] 0.5 PLAN_EXECUTIE.md
- [x] 0.6 update_tracking.py
- [x] 0.7 Research competitori (cu Playwright MCP) — 12 site-uri, date reale colectate (2026-03-17)

## FAZA 1 — Motor Analiză PDF
- [x] 1.1 analyzer.py — extracție features PDF/DOCX
- [x] 1.2 Test analyzer pe 26 fișiere reper — 25/26 OK (3600.pdf timeout 26MB)
- [x] 1.3 Analiză exploratorie: corelație features ↔ preț — pages/words corelate pozitiv cu prețul

## FAZA 2 — Motor de Preț (Ensemble)
- [x] 2.1 base_rate.py — Metoda 1: preț/pagină
- [x] 2.2 word_rate.py — Metoda 2: preț/cuvânt
- [x] 2.3 similarity.py — Metoda 3: KNN + cache referințe
- [x] 2.4 ensemble.py — combinare ponderată + fallback
- [x] 2.5 calibration.py + calibrate.py
- [x] 2.6 Test ensemble pe 26 fișiere — funcțional, necesită calibrare fină

## FAZA 3 — Validare + Self-learning
- [x] 3.1 validation.py — 3 niveluri
- [x] 3.2 self_learning.py
- [x] 3.3 Integrare market_rates.json
- [x] 3.4 Comparare prețuri ensemble vs competitori — endpoint funcțional

## FAZA 4 — Backend API (FastAPI)
- [x] 4.1 main.py — FastAPI + CORS + WebSocket
- [x] 4.2 db/ — SQLite tabele
- [x] 4.3 routes_upload.py + magic bytes validation
- [x] 4.4 routes_price.py + WebSocket progress + validate-price endpoint
- [x] 4.5 routes_history.py
- [x] 4.6 routes_calibrate.py
- [x] 4.7 routes_files.py + symlink protection
- [x] 4.8 routes_settings.py
- [x] 4.9 routes_competitors.py

## FAZA 5 — Frontend React
- [x] 5.1 Setup Vite + React + Tailwind
- [x] 5.2 Layout: Sidebar + Header + ErrorBoundary
- [x] 5.3 DashboardPage
- [x] 5.4 UploadPage (DropZone + FileList + ProgressBar)
- [x] 5.5 Componente preț (PriceCard + Breakdown + Methods + Competitors + Confidence + SelfLearn)
- [x] 5.6 HistoryPage
- [x] 5.7 CalibrationPage
- [x] 5.8 FileBrowserPage
- [x] 5.9 SettingsPage

## FAZA 6 — Integrare + Test E2E
- [x] 6.1 Conectare completă frontend ↔ backend — CORS OK, health OK, frontend HTTP 200
- [x] 6.2 Test: upload → progress → preț → modificare % — upload+calculate funcțional
- [x] 6.3 Test batch: upload multiplu — testat cu 120.pdf, endpoint funcțional
- [x] 6.4 Test self-learning — validate-price returnează success
- [x] 6.5 Test file browser — listare fișiere funcțională
- [x] 6.6 Test pe 26 fișiere — 25/26 parsate, ensemble funcțional, calibrare necesară
- [x] 6.7 Actualizare CLAUDE.md + PLAN_EXECUTIE.md

## FAZA 7 — Îmbunătățiri + Protecții (2026-03-17)
- [x] 7.1 DTP automat — Multiplicator DTP bazat pe ratio imagini/tabele per pagină, 4 niveluri (none 1.00 / light 1.10 / medium 1.20 / heavy 1.30), detecție 100% automată
- [x] 7.2 Protecții calibrare — Backup automat, comparație ÎNAINTE/DUPĂ, clamping ponderi (min 15%), respingere automată dacă ponderile sub limită, MAPE warning (>30%)
- [x] 7.3 Buton Revert calibrare — POST /api/calibrate/revert, restaurare calibrare anterioară din backup
- [x] 7.4 Buton Reset calibrare — POST /api/calibrate/reset, revenire la valori implicite
- [x] 7.5 Calcul multi-fișier — Upload + calcul preț individual per fișier, progress per fișier, card total cumulat
- [x] 7.6 Sistem centralizat activitate — backend/data/activity_log.json + GET /api/activity-log, logare fiecare acțiune din panoul de control (upload, calculate, calibrate, validate, settings, delete), max 1000 intrări
- [x] 7.7 Fix START_Calculator.bat — Confirmat --reload inclus, identificat cauza backend fără reload (child workers zombie pe Windows)

## FAZA 8 — Dashboard + Calibrare + Test E2E (2026-03-17)
- [x] 8.1 Calibrare fină — `calibrate.py --verbose` rulat, MAPE 32%, weights: base_rate=0.50, word_rate=0.35, similarity=0.15 (2026-03-17)
- [x] 8.2 Dashboard vizual cu Activity Log — componenta ActivityLog.jsx + integrare DashboardPage, filtru acțiuni, auto-refresh 30s (2026-03-17)
- [x] 8.3 Test multi-file E2E din browser — Playwright: upload 2 PDF (120.pdf + 2100.pdf), calcul individual per fișier, card total cumulat verificat (2026-03-17)
- [x] 8.4 Regulă auto-update PLAN_EXECUTIE.md — instrucțiune în CLAUDE.md + memory file, actualizare automată la finalul fiecărei sesiuni (2026-03-17)
- [x] 8.5 PLAN_EXTINDERE.md — roadmap extindere platformă, Fazele 9-15 planificate (2026-03-17)

## FAZA 8.5 — Plan Extindere + Documentare (2026-03-18)
- [x] 8.5.1 Redenumire proiect → Roland - Command Center (2026-03-18)
- [x] 8.5.2 Rescriere 0.0_PLAN_EXTINDERE_COMPLET.md — 11 faze (8-18), ~82 features validate, filtrate și completate (2026-03-18)
- [x] 8.5.3 Creare Documentare_Extindere_Proiect.md — documentare completă discuție ~15 runde, decizii per fază (2026-03-18)
- [x] 8.5.4 Regenerare 0.0_PLAN_EXTINDERE_COMPLET.html — selector interactiv actualizat cu Faza 18, note per fază, statistici (2026-03-18)

## WAVE 0 — Fundație (2026-03-18) — DONE
- [x] Git init + .gitignore complet
- [x] Fix URL-uri hardcoded (client.js → URL dinamic, WebSocket dinamic)
- [x] Sistem migrare DB (migrations/ + schema_version + run_migrations())
- [x] Module auto-discovery backend (module_discovery.py + modules/calculator/)
- [x] Frontend manifest (modules/manifest.js + sidebar dinamic cu categorii colapsibile)
- [x] Activity log → SQLite (migrare completă, async, JSON înlocuit)

## WAVE 1 — Deploy + Acces (2026-03-18) — DONE
- [x] Tailscale + MagicDNS + HTTPS cert (desktop-cjuecmn.tail7bc485.ts.net)
- [x] TLS config uvicorn + CORS dinamic + sidebar responsive mobile
- [x] vite build → servire statică prin FastAPI (port 8000)
- [x] PWA (manifest + service worker + workbox offline cache)
- [x] API Key Vault (Fernet + PBKDF2, modul modules/vault/)
- [x] Backup DB (backup.py → Google Drive, auto-cleanup >10)
- [x] Auto-start backend (setup_autostart.bat, Task Scheduler)
- [x] START_Production.bat — mod producție cu TLS autodetect

## WAVE 2 — Quick Tools (2026-03-18) — PARTIAL
- [x] Command Palette (Ctrl+K) — fuse.js fuzzy search
- [x] QR Generator — react-qr-code, download PNG, copy clipboard
- [x] Notepad cu auto-save — CRUD + debounce 800ms + activity log
- [ ] Calculator avansat — DEFERRED
- [ ] Password Generator — DEFERRED
- [ ] Barcode Generator — DEFERRED

## FAZA 12 — Convertor Fișiere (2026-03-18) — DONE
- [x] 10 tipuri conversie (PDF↔DOCX, merge/split PDF, compress/resize img, CSV/Excel→JSON, ZIP, OCR)
- [x] Android-safe validation (extension + MIME + octet-stream fallback)
- [x] COM threading fix (pythoncom.CoInitialize)

## FAZA 14 — Manager Fișiere Avansat (2026-03-18) — PARTIAL
- [x] File browser cu preview (PDF, imagini, text)
- [x] Operații CRUD (rename, move, delete, mkdir) — sandboxing + symlink block
- [x] Upload fișiere (drag&drop, auto-rename conflict)
- [x] Download fișiere (FileResponse + activity log)
- [x] Duplicate finder (MD5 hash, grupare, wasted space)
- [ ] Căutare fulltext — DEFERRED
- [ ] Tag-uri — DEFERRED

## RESTRUCTURARE REGULI (2026-03-19) — DONE
- [x] 12 reguli inline CLAUDE.md → 5 fișiere .claude/rules/
- [x] 4 comenzi slash (/update-status, /pre-wave, /test-guide, /rule-change)
- [x] Agent rule-guardian (read-only)
- [x] 4 hooks (session-start/stop, post-edit-check, pre-compact)
- [x] CLAUDE.md slim (354 → 116 linii)
- [x] Nested CLAUDE.md: backend/ + frontend/
- [x] Arhivare 10 fișiere deprecated

## Ramas opțional (calculator)
- [ ] Îmbunătățire acuratețe calibrare (MAPE 32% → sub 25%)
- [ ] Afișare ponderi metode în UI
- [ ] Fix comparație competitori endpoint

## Extindere planificată (vezi 99_Roland_Work_Place/0.0_PLAN_EXTINDERE_COMPLET.md)
- Faza 9: Traducător integrat multi-provider — **NEXT** (core business)
- Faza 10: Facturare & Evidență clienți
- Faza 13: Integrări externe (Gmail, Drive, Calendar, GitHub)
- Faza 15: AI pe documente
- Faza 16: Automatizări & shortcuts
- Faza 17: Rapoarte & polish
- Faza 18: Modul ITP CIP Inspection
