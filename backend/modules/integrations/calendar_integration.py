"""
Google Calendar integration logic — pure functions, no route decorators.

Uses httpx async client for REST API calls.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
from fastapi import HTTPException

from .models import _get_config_key


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CALENDAR_API_BASE = "https://www.googleapis.com/calendar/v3"


# ---------------------------------------------------------------------------
# Auth helper
# ---------------------------------------------------------------------------

async def get_calendar_headers() -> dict[str, str]:
    """Returnează header-ele de autorizare pentru Google Calendar API."""
    token = await _get_config_key("google_calendar_token")
    if not token:
        raise HTTPException(400, "Google Calendar nu este configurat. Adaugă google_calendar_token în Setări AI.")
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Logic functions
# ---------------------------------------------------------------------------

async def check_calendar_status() -> dict:
    """Verifică dacă token-ul Calendar e valid, returnează status dict."""
    token = await _get_config_key("google_calendar_token")
    configured = bool(token)

    if configured:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"{CALENDAR_API_BASE}/calendars/primary",
                    headers={"Authorization": f"Bearer {token}"},
                )
                if resp.status_code == 200:
                    cal_info = resp.json()
                    return {
                        "provider": "google_calendar",
                        "configured": True,
                        "connected": True,
                        "calendar": cal_info.get("summary", ""),
                        "message": "Google Calendar conectat.",
                    }
                else:
                    return {
                        "provider": "google_calendar",
                        "configured": True,
                        "connected": False,
                        "message": "Token Google Calendar expirat sau invalid.",
                    }
        except Exception:
            return {
                "provider": "google_calendar",
                "configured": True,
                "connected": False,
                "message": "Nu s-a putut verifica conexiunea Google Calendar.",
            }

    return {
        "provider": "google_calendar",
        "configured": False,
        "connected": False,
        "message": "Lipsește google_calendar_token din Setări AI.",
    }


async def list_calendar_events(headers: dict[str, str], days: int) -> list[dict]:
    """Listează evenimentele din calendarul principal pentru următoarele N zile."""
    now = datetime.now(timezone.utc)
    time_min = now.isoformat()
    time_max = (now + timedelta(days=days)).isoformat()

    params = {
        "timeMin": time_min,
        "timeMax": time_max,
        "singleEvents": "true",
        "orderBy": "startTime",
        "maxResults": 50,
    }

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"{CALENDAR_API_BASE}/calendars/primary/events",
            headers=headers,
            params=params,
        )

    if resp.status_code == 401:
        raise HTTPException(401, "Token Google Calendar expirat.")
    if resp.status_code != 200:
        raise HTTPException(resp.status_code, f"Eroare Calendar API: {resp.text}")

    data = resp.json()
    events = []
    for ev in data.get("items", []):
        events.append({
            "id": ev.get("id"),
            "summary": ev.get("summary", "(Fără titlu)"),
            "description": ev.get("description", ""),
            "start": ev.get("start", {}).get("dateTime", ev.get("start", {}).get("date", "")),
            "end": ev.get("end", {}).get("dateTime", ev.get("end", {}).get("date", "")),
            "location": ev.get("location", ""),
            "status": ev.get("status", ""),
            "htmlLink": ev.get("htmlLink", ""),
        })

    return events


async def create_calendar_event(
    headers: dict[str, str],
    summary: str,
    start: str,
    end: str,
    description: str,
) -> dict:
    """Creează un eveniment nou în Google Calendar. Returns created event dict."""
    event_body = {
        "summary": summary,
        "description": description,
        "start": {"dateTime": start, "timeZone": "Europe/Bucharest"},
        "end": {"dateTime": end, "timeZone": "Europe/Bucharest"},
    }

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            f"{CALENDAR_API_BASE}/calendars/primary/events",
            headers={**headers, "Content-Type": "application/json"},
            json=event_body,
        )

    if resp.status_code == 401:
        raise HTTPException(401, "Token Google Calendar expirat.")
    if resp.status_code not in (200, 201):
        raise HTTPException(resp.status_code, f"Eroare creare eveniment: {resp.text}")

    return resp.json()


async def delete_calendar_event(headers: dict[str, str], event_id: str) -> None:
    """Șterge un eveniment din Google Calendar."""
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.delete(
            f"{CALENDAR_API_BASE}/calendars/primary/events/{event_id}",
            headers=headers,
        )

    if resp.status_code == 401:
        raise HTTPException(401, "Token Google Calendar expirat.")
    if resp.status_code == 404:
        raise HTTPException(404, "Eveniment negăsit.")
    if resp.status_code not in (200, 204):
        raise HTTPException(resp.status_code, f"Eroare ștergere eveniment: {resp.text}")


async def update_calendar_event(
    headers: dict[str, str],
    event_id: str,
    patch_body: dict[str, Any],
) -> dict:
    """Actualizează un eveniment existent în Google Calendar (PATCH parțial). Returns updated event dict."""
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.patch(
            f"{CALENDAR_API_BASE}/calendars/primary/events/{event_id}",
            headers={**headers, "Content-Type": "application/json"},
            json=patch_body,
        )

    if resp.status_code == 401:
        raise HTTPException(401, "Token Google Calendar expirat.")
    if resp.status_code == 404:
        raise HTTPException(404, f"Eveniment negăsit: {event_id}")
    if resp.status_code not in (200, 201):
        raise HTTPException(resp.status_code, f"Eroare actualizare eveniment: {resp.text}")

    return resp.json()
