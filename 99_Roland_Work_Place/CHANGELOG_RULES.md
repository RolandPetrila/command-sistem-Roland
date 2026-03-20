# Changelog — Rule Modifications

### 2026-03-19 — ALL RULES — RESTRUCTURE
**Before:** 12 separate rules (R1-R12) inline in CLAUDE.md (~142 lines)
**After:** 5 consolidated rule files in `.claude/rules/`:
- `01-progress-tracking.md` ← R1+R2+R7+R10
- `02-pre-implementation.md` ← R6+R8+R11
- `03-validation-and-testing.md` ← R9+R12
- `04-code-safety.md` ← R3+R4+R5
- `05-rule-governance.md` ← NEW
**Reason:** Restructurare completă — reguli mutate din CLAUDE.md în `.claude/rules/` pentru auto-load la fiecare mesaj, CLAUDE.md redus de la 354 la ~150 linii, adăugat protocol guvernanță reguli + prioritate local > global.

### 2026-03-20 — 06-free-tier-enforcement.md — ADD
**Before:** N/A (regulă nouă)
**After:** Regulă completă Free Tier Enforcement — zero cost policy, checklist 5 puncte (free tier permanent, no card, funcțional, compatibil Python/FastAPI/Windows, data concerns), provider chains aprobate pentru: AI Text (Gemini→Cerebras→Groq→Mistral→SambaNova), Translation (DeepL→Azure→Google→MyMemory→LibreTranslate), TTS (edge-tts→Web Speech→Azure F0), OCR (Tesseract→EasyOCR→OCR.space), Notifications (Web Push→Telegram→ntfy.sh→Email), Embeddings (Gemini→all-MiniLM local), Business APIs RO (BNR XML, ANAF CUI). Violation response protocol inclus.
**Reason:** Sesiunea de unificare documentație (Faza 19) a stabilit politica zero cost ca regulă permanentă — toate API-urile și serviciile externe trebuie să aibă free tier funcțional permanent. Provideri eliminați: OpenAI (free tier nefuncțional), Perplexity (exclusiv plătit), SMS România (fără opțiune gratuită).
