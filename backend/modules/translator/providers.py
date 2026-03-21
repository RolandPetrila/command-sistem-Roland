"""
Translation provider chain: DeepL (best) -> Azure -> Google -> Gemini -> OpenAI.

Providers are initialized lazily. API keys are read from:
1. Environment variables (DEEPL_API_KEY, AZURE_TRANSLATOR_KEY)
2. ai_config SQLite table (same as AI module)
"""

from __future__ import annotations

import logging
import os
import re
from typing import Optional

import httpx

from app.db.database import get_db

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helper: read API key from ai_config table
# ---------------------------------------------------------------------------

async def _get_db_key(name: str) -> str | None:
    """Read API key from ai_config table."""
    try:
        async with get_db() as db:
            cursor = await db.execute(
                "SELECT value FROM ai_config WHERE key = ?", (name,)
            )
            row = await cursor.fetchone()
            return row["value"] if row else None
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Provider base
# ---------------------------------------------------------------------------

class TranslationProvider:
    """Base class for translation providers."""

    name: str = "base"

    async def translate_text(
        self, text: str, source_lang: str, target_lang: str
    ) -> str:
        raise NotImplementedError

    async def is_available(self) -> bool:
        return False


# ---------------------------------------------------------------------------
# 1. DeepL
# ---------------------------------------------------------------------------

class DeepLProvider(TranslationProvider):
    name = "deepl"

    LANG_MAP = {
        "en": "EN", "ro": "RO", "de": "DE", "fr": "FR", "es": "ES",
        "it": "IT", "pt": "PT", "nl": "NL", "pl": "PL", "ru": "RU",
        "ja": "JA", "zh": "ZH", "bg": "BG", "cs": "CS", "da": "DA",
        "el": "EL", "et": "ET", "fi": "FI", "hu": "HU", "lt": "LT",
        "lv": "LV", "sk": "SK", "sl": "SL", "sv": "SV",
    }

    def __init__(self, api_key: str):
        self.api_key = api_key
        # Free keys end with ":fx"
        if api_key.strip().endswith(":fx"):
            self.base_url = "https://api-free.deepl.com/v2"
        else:
            self.base_url = "https://api.deepl.com/v2"

    async def is_available(self) -> bool:
        return bool(self.api_key)

    async def translate_text(
        self, text: str, source_lang: str, target_lang: str
    ) -> str:
        src = self.LANG_MAP.get(source_lang.lower(), source_lang.upper())
        tgt = self.LANG_MAP.get(target_lang.lower(), target_lang.upper())

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{self.base_url}/translate",
                headers={"Authorization": f"DeepL-Auth-Key {self.api_key}"},
                json={
                    "text": [text],
                    "source_lang": src,
                    "target_lang": tgt,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data["translations"][0]["text"]

    async def get_usage(self) -> dict:
        """Return DeepL character usage stats."""
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{self.base_url}/usage",
                headers={"Authorization": f"DeepL-Auth-Key {self.api_key}"},
            )
            resp.raise_for_status()
            data = resp.json()
            return {
                "provider": "deepl",
                "character_count": data.get("character_count", 0),
                "character_limit": data.get("character_limit", 0),
            }


# ---------------------------------------------------------------------------
# 2. Azure Translator
# ---------------------------------------------------------------------------

class AzureTranslatorProvider(TranslationProvider):
    name = "azure"

    BASE_URL = "https://api.cognitive.microsofttranslator.com/translate"

    def __init__(self, api_key: str, region: str = "global"):
        self.api_key = api_key
        self.region = region

    async def is_available(self) -> bool:
        return bool(self.api_key)

    async def translate_text(
        self, text: str, source_lang: str, target_lang: str
    ) -> str:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                self.BASE_URL,
                params={
                    "api-version": "3.0",
                    "from": source_lang.lower(),
                    "to": target_lang.lower(),
                },
                headers={
                    "Ocp-Apim-Subscription-Key": self.api_key,
                    "Ocp-Apim-Subscription-Region": self.region,
                    "Content-Type": "application/json",
                },
                json=[{"text": text}],
            )
            resp.raise_for_status()
            data = resp.json()
            return data[0]["translations"][0]["text"]


# ---------------------------------------------------------------------------
# 3. Google Translate (direct HTTP, no googletrans dependency)
# ---------------------------------------------------------------------------

class GoogleTranslateProvider(TranslationProvider):
    name = "google"

    # Unofficial Google Translate endpoint (free, no key needed)
    TRANSLATE_URL = "https://translate.googleapis.com/translate_a/single"

    async def is_available(self) -> bool:
        return True  # No API key needed

    async def translate_text(
        self, text: str, source_lang: str, target_lang: str
    ) -> str:
        params = {
            "client": "gtx",
            "sl": source_lang.lower(),
            "tl": target_lang.lower(),
            "dt": "t",
            "q": text,
        }
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(self.TRANSLATE_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
            # Response format: [[["translated text","original text",...],...],...]
            translated_parts = []
            if data and data[0]:
                for segment in data[0]:
                    if segment and segment[0]:
                        translated_parts.append(segment[0])
            return "".join(translated_parts)


# ---------------------------------------------------------------------------
# 4. Gemini Flash (AI fallback)
# ---------------------------------------------------------------------------

class GeminiTranslationProvider(TranslationProvider):
    name = "gemini"

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def is_available(self) -> bool:
        return bool(self.api_key)

    async def translate_text(
        self, text: str, source_lang: str, target_lang: str
    ) -> str:
        import google.generativeai as genai

        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel(
            "gemini-2.5-flash",
            system_instruction=(
                "Esti un traducator profesionist. Traduci EXACT textul primit, "
                "fara explicatii, fara note suplimentare. Pastreaza formatarea originala. "
                f"Raspunde EXCLUSIV in {target_lang.upper()}. "
                "Returneaza DOAR traducerea, nimic altceva."
            ),
        )
        prompt = (
            f"Traduce urmatorul text din {source_lang.upper()} in {target_lang.upper()}:\n\n"
            f"{text}"
        )
        response = await model.generate_content_async(prompt)
        return response.text.strip()


# ---------------------------------------------------------------------------
# 5. OpenAI GPT-4o-mini (AI fallback)
# ---------------------------------------------------------------------------

class OpenAITranslationProvider(TranslationProvider):
    name = "openai"

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def is_available(self) -> bool:
        return bool(self.api_key)

    async def translate_text(
        self, text: str, source_lang: str, target_lang: str
    ) -> str:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=self.api_key)
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Esti un traducator profesionist. Traduci EXACT textul primit, "
                        "fara explicatii, fara note suplimentare. Pastreaza formatarea originala. "
                        f"Raspunde EXCLUSIV in {target_lang.upper()}. "
                        "Returneaza DOAR traducerea, nimic altceva."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Traduce urmatorul text din {source_lang.upper()} in {target_lang.upper()}:\n\n"
                        f"{text}"
                    ),
                },
            ],
        )
        return response.choices[0].message.content.strip()


# ---------------------------------------------------------------------------
# Provider chain
# ---------------------------------------------------------------------------

ENV_KEY_MAP = {
    "deepl": "DEEPL_API_KEY",
    "azure": "AZURE_TRANSLATOR_KEY",
    "gemini": "GEMINI_API_KEY",
    "openai": "OPENAI_API_KEY",
}

DB_KEY_MAP = {
    "deepl": "deepl_api_key",
    "azure": "azure_translator_key",
    "gemini": "gemini_api_key",
    "openai": "openai_api_key",
}


async def _get_key(provider_name: str) -> str | None:
    """Get API key from env or DB."""
    env_var = ENV_KEY_MAP.get(provider_name)
    if env_var:
        key = os.environ.get(env_var)
        if key:
            return key
    db_key = DB_KEY_MAP.get(provider_name)
    if db_key:
        return await _get_db_key(db_key)
    return None


async def get_translation_chain() -> list[TranslationProvider]:
    """Build ordered list of available translation providers."""
    providers: list[TranslationProvider] = []

    # 1. DeepL
    deepl_key = await _get_key("deepl")
    if deepl_key:
        providers.append(DeepLProvider(deepl_key))
        logger.info("Translator provider 'deepl' disponibil")

    # 2. Azure
    azure_key = await _get_key("azure")
    if azure_key:
        region = os.environ.get("AZURE_TRANSLATOR_REGION", "global")
        providers.append(AzureTranslatorProvider(azure_key, region))
        logger.info("Translator provider 'azure' disponibil")

    # 3. Google Translate (no key needed)
    google_provider = GoogleTranslateProvider()
    if await google_provider.is_available():
        providers.append(google_provider)
        logger.info("Translator provider 'google' disponibil")

    # 4. Gemini
    gemini_key = await _get_key("gemini")
    if gemini_key:
        providers.append(GeminiTranslationProvider(gemini_key))
        logger.info("Translator provider 'gemini' disponibil")

    # 5. OpenAI
    openai_key = await _get_key("openai")
    if openai_key:
        providers.append(OpenAITranslationProvider(openai_key))
        logger.info("Translator provider 'openai' disponibil")

    return providers


_VALID_LANGS = {"ro", "en"}


async def translate_with_chain(
    text: str, source_lang: str, target_lang: str, preferred_provider: str | None = None
) -> dict:
    """
    Translate text using the provider chain (fallback).

    Returns: {"translated_text": str, "provider": str}
    Raises RuntimeError if all providers fail.
    """
    if target_lang.lower() not in _VALID_LANGS:
        raise ValueError(f"Target language '{target_lang}' not in allowed list: {_VALID_LANGS}")
    if source_lang.lower() not in _VALID_LANGS:
        raise ValueError(f"Source language '{source_lang}' not in allowed list: {_VALID_LANGS}")

    providers = await get_translation_chain()

    if not providers:
        raise RuntimeError(
            "Niciun provider de traducere configurat. "
            "Adauga o cheie API (DeepL, Azure, Gemini sau OpenAI) in setarile AI."
        )

    # If a specific provider is requested, try it first
    if preferred_provider and preferred_provider != "auto":
        reordered = []
        for p in providers:
            if p.name == preferred_provider:
                reordered.insert(0, p)
            else:
                reordered.append(p)
        providers = reordered

    errors = []
    for provider in providers:
        try:
            translated = await provider.translate_text(text, source_lang, target_lang)
            return {"translated_text": translated, "provider": provider.name}
        except Exception as e:
            errors.append(f"{provider.name}: {e}")
            logger.warning("Translator provider %s a esuat: %s", provider.name, e)
            continue

    raise RuntimeError(
        f"Toti providerii de traducere au esuat: {'; '.join(errors)}"
    )


async def get_available_translation_providers() -> list[dict]:
    """Return list of configured translation providers (no keys exposed)."""
    result = []

    for name in ["deepl", "azure", "google", "gemini", "openai"]:
        if name == "google":
            gp = GoogleTranslateProvider()
            configured = await gp.is_available()
        else:
            key = await _get_key(name)
            configured = bool(key)
        result.append({"name": name, "configured": configured})

    return result


# ---------------------------------------------------------------------------
# Language detection
# ---------------------------------------------------------------------------

async def detect_language(text: str) -> dict:
    """
    Detect the language of a text using langdetect.

    Returns: {"language": "en", "confidence": 0.99}
    """
    try:
        from langdetect import detect_langs
        import asyncio

        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(None, detect_langs, text)
        if results:
            best = results[0]
            return {"language": str(best.lang), "confidence": round(best.prob, 3)}
        return {"language": "unknown", "confidence": 0.0}
    except Exception as e:
        logger.warning("Detectia limbii a esuat: %s", e)
        return {"language": "unknown", "confidence": 0.0}


# ---------------------------------------------------------------------------
# DeepL usage
# ---------------------------------------------------------------------------

async def get_deepl_usage() -> dict | None:
    """Get DeepL API usage statistics. Returns None if DeepL not configured."""
    deepl_key = await _get_key("deepl")
    if not deepl_key:
        return None
    try:
        provider = DeepLProvider(deepl_key)
        return await provider.get_usage()
    except Exception as e:
        logger.warning("Nu s-a putut obtine usage DeepL: %s", e)
        return {"provider": "deepl", "error": str(e)}
