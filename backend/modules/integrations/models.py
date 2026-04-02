"""
Pydantic models, constants, and shared helpers for the Integrations module.

Contains:
- Config key reader (_get_config_key)
- MIME/email parsing helpers
- Status cache (in-memory, 5 min TTL)
- Validation helpers (email format, ISO 8601)
- Pydantic request models
"""

from __future__ import annotations

import email
import re
import time as _time
from datetime import datetime
from email.header import decode_header

from pydantic import BaseModel, field_validator

from app.db.database import get_db


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

async def _get_config_key(key: str) -> str | None:
    """Citește o cheie din tabelul ai_config."""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT value FROM ai_config WHERE key = ?", (key,)
        )
        row = await cursor.fetchone()
        return row["value"] if row else None


def _decode_mime_header(raw: str | None) -> str:
    """Decodează un header MIME (subject, from, etc.)."""
    if not raw:
        return ""
    parts = decode_header(raw)
    decoded = []
    for part, charset in parts:
        if isinstance(part, bytes):
            decoded.append(part.decode(charset or "utf-8", errors="replace"))
        else:
            decoded.append(part)
    return " ".join(decoded)


def _extract_email_body(msg: email.message.Message) -> str:
    """Extrage corpul text din mesajul email."""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    return payload.decode(charset, errors="replace")
            elif content_type == "text/html":
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    return payload.decode(charset, errors="replace")
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            return payload.decode(charset, errors="replace")
    return ""


# ---------------------------------------------------------------------------
# Status cache (R4-32) — 5 min TTL in-memory
# ---------------------------------------------------------------------------

_STATUS_CACHE_TTL = 300  # 5 minutes in seconds
_status_cache: dict[str, dict] = {}


def _cache_get(provider: str) -> dict | None:
    """Return cached status if exists and < TTL old, else None."""
    entry = _status_cache.get(provider)
    if entry and (_time.time() - entry["timestamp"]) < _STATUS_CACHE_TTL:
        return entry["data"]
    return None


def _cache_set(provider: str, data: dict) -> dict:
    """Store status result in cache with current timestamp. Returns data."""
    _status_cache[provider] = {"data": data, "timestamp": _time.time()}
    return data


def _cache_clear() -> None:
    """Clear the entire status cache."""
    _status_cache.clear()


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

_EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


def _validate_email_format(addr: str) -> str:
    """Validate a single email address format."""
    addr = addr.strip()
    if not _EMAIL_RE.match(addr):
        raise ValueError(f"Adresa email invalidă: {addr}")
    return addr


def _validate_iso8601(value: str, field_name: str) -> str:
    """Validate that a string is a parseable ISO 8601 datetime."""
    try:
        datetime.fromisoformat(value)
    except (ValueError, TypeError):
        raise ValueError(
            f"Câmpul '{field_name}' nu este o dată ISO 8601 validă: {value}"
        )
    return value


# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------

class EmailSendRequest(BaseModel):
    to: str
    subject: str
    body: str
    html: bool = False
    cc: list[str] = []
    bcc: list[str] = []

    @field_validator("to")
    @classmethod
    def validate_to(cls, v: str) -> str:
        return _validate_email_format(v)

    @field_validator("cc", "bcc")
    @classmethod
    def validate_cc_bcc(cls, v: list[str]) -> list[str]:
        return [_validate_email_format(addr) for addr in v]


class CalendarEventCreate(BaseModel):
    summary: str
    start: str  # ISO 8601 datetime
    end: str    # ISO 8601 datetime
    description: str = ""

    @field_validator("start")
    @classmethod
    def validate_start(cls, v: str) -> str:
        return _validate_iso8601(v, "start")

    @field_validator("end")
    @classmethod
    def validate_end(cls, v: str, info) -> str:
        v = _validate_iso8601(v, "end")
        start_val = info.data.get("start")
        if start_val:
            try:
                if datetime.fromisoformat(v) < datetime.fromisoformat(start_val):
                    raise ValueError(
                        "Data de final (end) nu poate fi înainte de data de start."
                    )
            except (ValueError, TypeError):
                pass  # start already failed validation; skip comparison
        return v


class CalendarEventUpdate(BaseModel):
    summary: str | None = None
    start: str | None = None   # ISO 8601 datetime
    end: str | None = None     # ISO 8601 datetime
    description: str | None = None

    @field_validator("start")
    @classmethod
    def validate_start(cls, v: str | None) -> str | None:
        if v is not None:
            return _validate_iso8601(v, "start")
        return v

    @field_validator("end")
    @classmethod
    def validate_end(cls, v: str | None, info) -> str | None:
        if v is None:
            return v
        v = _validate_iso8601(v, "end")
        start_val = info.data.get("start")
        if start_val:
            try:
                if datetime.fromisoformat(v) < datetime.fromisoformat(start_val):
                    raise ValueError(
                        "Data de final (end) nu poate fi înainte de data de start."
                    )
            except (ValueError, TypeError):
                pass
        return v


class GitHubIssueCreate(BaseModel):
    title: str
    body: str = ""
    labels: list[str] = []
