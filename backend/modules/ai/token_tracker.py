"""
Token usage tracking per provider per day.

Tracks AI API usage (requests, tokens, characters) and compares
against configured limits from ai_provider_limits table.

Tables used:
  - ai_token_usage: daily counters per provider
  - ai_provider_limits: configured limits per provider
"""

from __future__ import annotations

import logging
import os
from datetime import date, datetime, timedelta

import httpx

from app.db.database import get_db

logger = logging.getLogger(__name__)


async def track_usage(
    provider: str,
    tokens_in: int = 0,
    tokens_out: int = 0,
    chars: int = 0,
) -> None:
    """
    Record usage for a provider. Called after each AI call.

    Upserts into ai_token_usage: increments counters for (provider, today).
    """
    today = date.today().isoformat()
    try:
        async with get_db() as db:
            await db.execute(
                """
                INSERT INTO ai_token_usage (provider, date, requests_count, tokens_input, tokens_output, chars_count)
                VALUES (?, ?, 1, ?, ?, ?)
                ON CONFLICT(provider, date) DO UPDATE SET
                    requests_count = requests_count + 1,
                    tokens_input   = tokens_input + excluded.tokens_input,
                    tokens_output  = tokens_output + excluded.tokens_output,
                    chars_count    = chars_count + excluded.chars_count
                """,
                (provider, today, tokens_in, tokens_out, chars),
            )
            await db.commit()
    except Exception as e:
        logger.warning("Nu s-a putut salva usage pentru %s: %s", provider, e)


async def get_usage_summary() -> list[dict]:
    """
    Get usage for all providers: today's usage + limits from ai_provider_limits.

    Returns list of dicts:
      [{provider, today_requests, today_chars, today_tokens_in, today_tokens_out,
        daily_limit, monthly_limit, monthly_used, percent_used, notes}]
    """
    today = date.today().isoformat()
    month_start = date.today().replace(day=1).isoformat()

    try:
        async with get_db() as db:
            # Get all known providers from limits table
            cursor = await db.execute(
                "SELECT provider, daily_requests, monthly_chars, monthly_tokens, notes "
                "FROM ai_provider_limits"
            )
            limits = {row["provider"]: dict(row) for row in await cursor.fetchall()}

            # Get today's usage per provider
            cursor = await db.execute(
                "SELECT provider, requests_count, tokens_input, tokens_output, chars_count "
                "FROM ai_token_usage WHERE date = ?",
                (today,),
            )
            today_usage = {row["provider"]: dict(row) for row in await cursor.fetchall()}

            # Get monthly totals per provider
            cursor = await db.execute(
                "SELECT provider, "
                "  SUM(requests_count) AS month_requests, "
                "  SUM(tokens_input) AS month_tokens_in, "
                "  SUM(tokens_output) AS month_tokens_out, "
                "  SUM(chars_count) AS month_chars "
                "FROM ai_token_usage WHERE date >= ? "
                "GROUP BY provider",
                (month_start,),
            )
            monthly_usage = {row["provider"]: dict(row) for row in await cursor.fetchall()}

        # Merge data
        all_providers = set(limits.keys()) | set(today_usage.keys()) | set(monthly_usage.keys())
        result = []

        for prov in sorted(all_providers):
            t = today_usage.get(prov, {})
            m = monthly_usage.get(prov, {})
            lim = limits.get(prov, {})

            daily_limit = lim.get("daily_requests")
            monthly_char_limit = lim.get("monthly_chars")
            monthly_token_limit = lim.get("monthly_tokens")

            today_req = t.get("requests_count", 0)
            month_chars = m.get("month_chars", 0)
            month_req = m.get("month_requests", 0)

            # Calculate percent used (based on most relevant limit)
            percent_used = 0.0
            if daily_limit and daily_limit > 0:
                percent_used = max(percent_used, (today_req / daily_limit) * 100)
            if monthly_char_limit and monthly_char_limit > 0:
                percent_used = max(percent_used, (month_chars / monthly_char_limit) * 100)

            result.append({
                "provider": prov,
                "today_requests": today_req,
                "today_chars": t.get("chars_count", 0),
                "today_tokens_in": t.get("tokens_input", 0),
                "today_tokens_out": t.get("tokens_output", 0),
                "monthly_requests": month_req,
                "monthly_chars": month_chars,
                "daily_limit": daily_limit,
                "monthly_char_limit": monthly_char_limit,
                "monthly_token_limit": monthly_token_limit,
                "percent_used": round(percent_used, 1),
                "notes": lim.get("notes", ""),
            })

        return result

    except Exception as e:
        logger.error("Eroare la citirea usage summary: %s", e)
        return []


async def get_deepl_usage_remote() -> dict:
    """
    Call DeepL API to get real usage: character_count, character_limit.

    Reads the DeepL API key from ai_config or environment.
    Returns dict with character_count, character_limit, percent_used.
    """
    api_key = os.environ.get("DEEPL_API_KEY")

    if not api_key:
        try:
            async with get_db() as db:
                cursor = await db.execute(
                    "SELECT value FROM ai_config WHERE key = 'deepl_api_key'"
                )
                row = await cursor.fetchone()
                if row:
                    api_key = row["value"]
        except Exception:
            pass

    if not api_key:
        return {"error": "Cheie API DeepL neconfigurată", "character_count": 0, "character_limit": 0}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://api-free.deepl.com/v2/usage",
                headers={"Authorization": f"DeepL-Auth-Key {api_key}"},
            )
            resp.raise_for_status()
            data = resp.json()

            char_count = data.get("character_count", 0)
            char_limit = data.get("character_limit", 500000)
            percent = round((char_count / char_limit * 100), 1) if char_limit > 0 else 0

            return {
                "character_count": char_count,
                "character_limit": char_limit,
                "percent_used": percent,
            }
    except httpx.HTTPStatusError as e:
        logger.warning("DeepL API eroare HTTP: %s", e.response.status_code)
        return {"error": f"DeepL API eroare: {e.response.status_code}", "character_count": 0, "character_limit": 0}
    except Exception as e:
        logger.warning("DeepL API eroare: %s", e)
        return {"error": str(e), "character_count": 0, "character_limit": 0}


async def get_provider_usage(provider: str) -> dict:
    """
    Detailed usage for a specific provider.

    Returns today's and monthly breakdown with limits.
    """
    today = date.today().isoformat()
    month_start = date.today().replace(day=1).isoformat()
    days_in_month = (date.today().replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)

    try:
        async with get_db() as db:
            # Today's usage
            cursor = await db.execute(
                "SELECT requests_count, tokens_input, tokens_output, chars_count "
                "FROM ai_token_usage WHERE provider = ? AND date = ?",
                (provider, today),
            )
            today_row = await cursor.fetchone()
            today_data = dict(today_row) if today_row else {
                "requests_count": 0, "tokens_input": 0, "tokens_output": 0, "chars_count": 0
            }

            # Monthly usage
            cursor = await db.execute(
                "SELECT "
                "  SUM(requests_count) AS total_requests, "
                "  SUM(tokens_input) AS total_tokens_in, "
                "  SUM(tokens_output) AS total_tokens_out, "
                "  SUM(chars_count) AS total_chars, "
                "  COUNT(DISTINCT date) AS active_days "
                "FROM ai_token_usage WHERE provider = ? AND date >= ?",
                (provider, month_start),
            )
            monthly_row = await cursor.fetchone()
            monthly_data = dict(monthly_row) if monthly_row else {
                "total_requests": 0, "total_tokens_in": 0, "total_tokens_out": 0,
                "total_chars": 0, "active_days": 0,
            }

            # Last 7 days breakdown
            week_start = (date.today() - timedelta(days=6)).isoformat()
            cursor = await db.execute(
                "SELECT date, requests_count, chars_count "
                "FROM ai_token_usage WHERE provider = ? AND date >= ? "
                "ORDER BY date",
                (provider, week_start),
            )
            daily_history = [dict(r) for r in await cursor.fetchall()]

            # Provider limits
            cursor = await db.execute(
                "SELECT daily_requests, monthly_chars, monthly_tokens, notes "
                "FROM ai_provider_limits WHERE provider = ?",
                (provider,),
            )
            limits_row = await cursor.fetchone()
            limits = dict(limits_row) if limits_row else {}

        # Special case: get remote DeepL usage
        deepl_remote = None
        if provider == "deepl":
            deepl_remote = await get_deepl_usage_remote()

        return {
            "provider": provider,
            "today": today_data,
            "monthly": monthly_data,
            "daily_history": daily_history,
            "limits": limits,
            "deepl_remote": deepl_remote,
            "days_in_month": days_in_month.day,
        }

    except Exception as e:
        logger.error("Eroare la citirea usage pentru %s: %s", provider, e)
        return {"provider": provider, "error": str(e)}
