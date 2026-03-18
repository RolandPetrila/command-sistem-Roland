"""
Multi-provider AI chain: Gemini Flash (primary) → OpenAI (fallback) → Groq (fallback).

Providers are initialized lazily. API keys are read from:
1. Environment variables (GEMINI_API_KEY, OPENAI_API_KEY, GROQ_API_KEY)
2. ai_config SQLite table (set from UI)
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import AsyncGenerator, Optional

from app.db.database import get_db

logger = logging.getLogger(__name__)


# --- Provider implementations ---

class BaseProvider:
    name: str = "base"
    model: str = ""

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        raise NotImplementedError

    async def generate_stream(self, prompt: str, system_prompt: str | None = None) -> AsyncGenerator[str, None]:
        raise NotImplementedError
        yield  # make it a generator


class GeminiProvider(BaseProvider):
    name = "gemini"
    model = "gemini-2.0-flash"

    async def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        import google.generativeai as genai
        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel(
            self.model,
            system_instruction=system_prompt,
        )
        response = await model.generate_content_async(prompt)
        return response.text

    async def generate_stream(self, prompt: str, system_prompt: str | None = None) -> AsyncGenerator[str, None]:
        import google.generativeai as genai
        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel(
            self.model,
            system_instruction=system_prompt,
        )
        response = await model.generate_content_async(prompt, stream=True)
        async for chunk in response:
            if chunk.text:
                yield chunk.text


class OpenAIProvider(BaseProvider):
    name = "openai"
    model = "gpt-4o-mini"

    async def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=self.api_key)
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        response = await client.chat.completions.create(
            model=self.model,
            messages=messages,
        )
        return response.choices[0].message.content

    async def generate_stream(self, prompt: str, system_prompt: str | None = None) -> AsyncGenerator[str, None]:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=self.api_key)
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        stream = await client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True,
        )
        async for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                yield content


class GroqProvider(BaseProvider):
    name = "groq"
    model = "llama-3.1-70b-versatile"

    async def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        from groq import AsyncGroq
        client = AsyncGroq(api_key=self.api_key)
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        response = await client.chat.completions.create(
            model=self.model,
            messages=messages,
        )
        return response.choices[0].message.content

    async def generate_stream(self, prompt: str, system_prompt: str | None = None) -> AsyncGenerator[str, None]:
        from groq import AsyncGroq
        client = AsyncGroq(api_key=self.api_key)
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        stream = await client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True,
        )
        async for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                yield content


# --- Provider chain ---

PROVIDER_CLASSES = {
    "gemini": GeminiProvider,
    "openai": OpenAIProvider,
    "groq": GroqProvider,
}

ENV_KEY_MAP = {
    "gemini": "GEMINI_API_KEY",
    "openai": "OPENAI_API_KEY",
    "groq": "GROQ_API_KEY",
}


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


async def get_provider_chain() -> list[BaseProvider]:
    """Build ordered list of available providers."""
    providers = []
    for name, cls in PROVIDER_CLASSES.items():
        env_var = ENV_KEY_MAP[name]
        api_key = os.environ.get(env_var) or await _get_db_key(f"{name}_api_key")
        if api_key:
            providers.append(cls(api_key))
            logger.info(f"AI provider '{name}' available")
    return providers


async def get_available_providers() -> list[dict]:
    """Return list of configured provider names + models (no keys)."""
    result = []
    for name in PROVIDER_CLASSES:
        env_var = ENV_KEY_MAP[name]
        api_key = os.environ.get(env_var) or await _get_db_key(f"{name}_api_key")
        result.append({
            "name": name,
            "model": PROVIDER_CLASSES[name].model,
            "configured": bool(api_key),
        })
    return result


async def ai_generate(prompt: str, system_prompt: str | None = None) -> dict:
    """Generate response using first available provider."""
    providers = await get_provider_chain()
    if not providers:
        raise RuntimeError(
            "Niciun provider AI configurat. Adaugă o cheie API în setările AI."
        )

    errors = []
    for provider in providers:
        try:
            text = await provider.generate(prompt, system_prompt)
            return {"text": text, "provider": provider.name, "model": provider.model}
        except Exception as e:
            errors.append(f"{provider.name}: {e}")
            logger.warning(f"Provider {provider.name} failed: {e}")
            continue

    raise RuntimeError(f"Toți providerii AI au eșuat: {'; '.join(errors)}")


async def ai_generate_stream(
    prompt: str, system_prompt: str | None = None
) -> AsyncGenerator[dict, None]:
    """Stream response from first available provider. Yields dicts with 'chunk' and 'provider'."""
    providers = await get_provider_chain()
    if not providers:
        yield {"error": "Niciun provider AI configurat. Adaugă o cheie API în setările AI."}
        return

    for provider in providers:
        try:
            async for chunk in provider.generate_stream(prompt, system_prompt):
                yield {"chunk": chunk, "provider": provider.name, "model": provider.model}
            yield {"done": True, "provider": provider.name, "model": provider.model}
            return
        except Exception as e:
            logger.warning(f"Provider {provider.name} stream failed: {e}")
            continue

    yield {"error": f"Toți providerii AI au eșuat."}
