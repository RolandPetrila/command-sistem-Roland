"""
Multi-provider AI chain: Gemini Flash (primary) → Cerebras → Groq → Mistral → OpenAI (legacy).

Providers are initialized lazily. API keys are read from:
1. Environment variables (GEMINI_API_KEY, CEREBRAS_API_KEY, GROQ_API_KEY, MISTRAL_API_KEY)
2. ai_config SQLite table (set from UI)
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import time
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
    model = "gemini-2.5-flash"

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
    model = "llama-3.3-70b-versatile"

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


class CerebrasProvider(BaseProvider):
    name = "cerebras"
    model = "qwen-3-235b-a22b-instruct-2507"

    async def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=self.api_key, base_url="https://api.cerebras.ai/v1")
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
        client = AsyncOpenAI(api_key=self.api_key, base_url="https://api.cerebras.ai/v1")
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


class MistralProvider(BaseProvider):
    name = "mistral"
    model = "mistral-small-latest"

    async def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=self.api_key, base_url="https://api.mistral.ai/v1")
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
        client = AsyncOpenAI(api_key=self.api_key, base_url="https://api.mistral.ai/v1")
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
    "cerebras": CerebrasProvider,
    "groq": GroqProvider,
    "mistral": MistralProvider,
    "openai": OpenAIProvider,
}

ENV_KEY_MAP = {
    "gemini": "GEMINI_API_KEY",
    "cerebras": "CEREBRAS_API_KEY",
    "groq": "GROQ_API_KEY",
    "mistral": "MISTRAL_API_KEY",
    "openai": "OPENAI_API_KEY",
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


def _reorder_providers(providers: list[BaseProvider], preferred: str | None) -> list[BaseProvider]:
    """Move preferred provider to front of the chain."""
    if not preferred or preferred == "auto":
        return providers
    reordered = []
    rest = []
    for p in providers:
        if p.name == preferred:
            reordered.insert(0, p)
        else:
            rest.append(p)
    return reordered + rest


# Z4.6 — Prompt cache: reuse responses for identical prompts within TTL
import asyncio as _asyncio
_prompt_cache: dict[str, tuple[float, dict]] = {}
_prompt_lock = _asyncio.Lock()
_CACHE_TTL = 3600  # 1 hour
_CACHE_MAX = 200   # max entries


def _cache_key(prompt: str, system_prompt: str | None) -> str:
    h = hashlib.md5(f"{system_prompt or ''}|||{prompt}".encode(), usedforsecurity=False).hexdigest()
    return h


async def ai_generate(prompt: str, system_prompt: str | None = None, preferred_provider: str | None = None) -> dict:
    """Generate response using first available provider. Caches identical prompts for 1h."""
    # Check cache (lock protects concurrent access)
    ck = _cache_key(prompt, system_prompt)
    async with _prompt_lock:
        if ck in _prompt_cache:
            cached_at, cached_result = _prompt_cache[ck]
            if time.time() - cached_at < _CACHE_TTL:
                return {**cached_result, "cached": True}
            else:
                del _prompt_cache[ck]

    providers = _reorder_providers(await get_provider_chain(), preferred_provider)
    if not providers:
        raise RuntimeError(
            "Niciun provider AI configurat. Adaugă o cheie API în setările AI."
        )

    errors = []
    for provider in providers:
        try:
            text = await provider.generate(prompt, system_prompt)
            result = {"text": text, "provider": provider.name, "model": provider.model}
            # Store in cache (evict oldest if full)
            async with _prompt_lock:
                if len(_prompt_cache) >= _CACHE_MAX:
                    oldest = min(_prompt_cache, key=lambda k: _prompt_cache[k][0])
                    del _prompt_cache[oldest]
                _prompt_cache[ck] = (time.time(), result)
            return result
        except Exception as e:
            errors.append(f"{provider.name}: {e}")
            logger.warning(f"Provider {provider.name} failed: {e}")
            continue

    raise RuntimeError(f"Toți providerii AI au eșuat: {'; '.join(errors)}")


async def ai_generate_stream(
    prompt: str, system_prompt: str | None = None, preferred_provider: str | None = None
) -> AsyncGenerator[dict, None]:
    """Stream response from first available provider. Yields dicts with 'chunk' and 'provider'."""
    providers = _reorder_providers(await get_provider_chain(), preferred_provider)
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
