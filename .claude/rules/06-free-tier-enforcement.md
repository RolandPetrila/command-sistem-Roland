# Free Tier Enforcement — Provider & Cost Policy

**Trigger:** When adding ANY new external API, provider, library, or service to the project.
**Mandatory** — NO exceptions without explicit user approval.

## Core Principle

This project operates on a **ZERO COST** budget. Every external service MUST have a functional free tier.

## Provider Approval Checklist

Before adding any new provider, verify ALL of these:

1. **Free tier exists and is PERMANENT** (not trial credits that expire)
2. **No credit card required at signup** — exception: user already has active account (Azure, Google Cloud, DeepL)
3. **Free tier is FUNCTIONAL** — actually works, not "quota exceeded" immediately (e.g., OpenAI free tier is dead)
4. **Compatible with Python FastAPI on Windows 10** — pip installable or REST API via httpx
5. **No data retention concerns** — check if free tier data is used for training (flag if yes)

If ANY check fails → DO NOT add. Propose free alternative or remove the feature.

## Approved Provider Chains (2026-03-20)

### AI Text Generation
```
1. Gemini 2.5 Flash (primary — quality, 10 RPM, 250 RPD)
2. Cerebras Qwen3-235B (1M tokens/day, ultra-fast, 30 RPM)
3. Groq Llama 3.3 70B (30 RPM, fast)
4. Mistral Small latest (1B tokens/month, 2 RPM)
5. OpenAI gpt-4o-mini (legacy — free tier non-functional, kept for backward compat)
```
REMOVED: OpenAI (free tier non-functional), Perplexity (paid only)

### Translation
```
1. DeepL Free (500K chars/month — best quality EU languages)
2. Azure Translator F0 (2M chars/month — largest free volume)
3. Google Cloud Translation (500K chars/month)
4. MyMemory (50K chars/day — no signup needed)
5. LibreTranslate local (unlimited — medium quality RO)
```
REMOVED: OpenAI translation (paid)

### Text-to-Speech (TTS)
```
1. edge-tts (Microsoft Neural, unlimited, no key, RO voices)
2. Web Speech API browser (zero server, built-in)
3. Azure TTS F0 (500K chars/month — if account exists)
```

### OCR
```
1. Tesseract local (existing, unlimited)
2. EasyOCR (deep learning, better on poor scans, RO support)
3. OCR.space cloud (500 req/day fallback)
```

### Notifications
```
1. Web Push VAPID (standard web, unlimited, free)
2. Telegram Bot API (unlimited, free)
3. ntfy.sh self-hosted (unlimited)
4. Email digest (Gmail SMTP + Brevo + Resend)
```
REMOVED: SMS (no free option in Romania)

### Embeddings / Semantic Search
```
1. Gemini Embeddings (free with existing API key)
2. all-MiniLM-L6-v2 local (offline, pip install)
```

### Business APIs Romania
```
- BNR Exchange Rate XML (free, no auth)
- ANAF Verificare CUI REST (free, no auth)
```

## Violation Response

If a paid service is accidentally introduced:
1. Flag immediately in code review
2. Find free alternative from CATALOG_API_GRATUITE.md
3. Replace before merging
4. Update this file if provider chains change

## Reference

Full API catalog with limits, code snippets, and comparison:
`99_Roland_Work_Place/CATALOG_API_GRATUITE.md`
