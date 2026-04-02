"""
Google Drive integration logic — pure functions, no route decorators.

Uses httpx async client for REST API calls.
"""

from __future__ import annotations

import json
import uuid
from typing import Any

import httpx
from fastapi import HTTPException

from .models import _get_config_key


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DRIVE_API_BASE = "https://www.googleapis.com/drive/v3"
DRIVE_UPLOAD_BASE = "https://www.googleapis.com/upload/drive/v3"


# ---------------------------------------------------------------------------
# Auth helper
# ---------------------------------------------------------------------------

async def get_drive_headers() -> dict[str, str]:
    """Returnează header-ele de autorizare pentru Google Drive API."""
    token = await _get_config_key("google_drive_token")
    if not token:
        raise HTTPException(400, "Google Drive nu este configurat. Adaugă google_drive_token în Setări AI.")
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Logic functions
# ---------------------------------------------------------------------------

async def check_drive_status() -> dict:
    """Verifică dacă token-ul Drive e valid, returnează status dict."""
    token = await _get_config_key("google_drive_token")
    configured = bool(token)

    if configured:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"{DRIVE_API_BASE}/about?fields=user",
                    headers={"Authorization": f"Bearer {token}"},
                )
                if resp.status_code == 200:
                    user_info = resp.json().get("user", {})
                    return {
                        "provider": "google_drive",
                        "configured": True,
                        "connected": True,
                        "user": user_info.get("displayName", ""),
                        "email": user_info.get("emailAddress", ""),
                        "message": "Google Drive conectat.",
                    }
                else:
                    return {
                        "provider": "google_drive",
                        "configured": True,
                        "connected": False,
                        "message": "Token Google Drive expirat sau invalid. Re-autentifică din Setări.",
                    }
        except Exception:
            return {
                "provider": "google_drive",
                "configured": True,
                "connected": False,
                "message": "Nu s-a putut verifica conexiunea Google Drive.",
            }

    return {
        "provider": "google_drive",
        "configured": False,
        "connected": False,
        "message": "Lipsește google_drive_token din Setări AI.",
    }


async def list_drive_files(
    headers: dict[str, str],
    query: str,
    folder_id: str,
    max_results: int,
) -> list[dict]:
    """Listează fișierele din Google Drive. Returns list of file dicts."""
    q_parts = []
    if query:
        safe_query = query.replace("\\", "\\\\").replace("'", "\\'")
        q_parts.append(f"name contains '{safe_query}'")
    if folder_id:
        q_parts.append(f"'{folder_id}' in parents")
    q_parts.append("trashed = false")

    params: dict[str, Any] = {
        "pageSize": max_results,
        "fields": "files(id,name,mimeType,size,modifiedTime,webViewLink)",
        "orderBy": "modifiedTime desc",
    }
    if q_parts:
        params["q"] = " and ".join(q_parts)

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"{DRIVE_API_BASE}/files", headers=headers, params=params
        )

    if resp.status_code == 401:
        raise HTTPException(401, "Token Google Drive expirat. Re-autentifică din Setări.")
    if resp.status_code != 200:
        raise HTTPException(resp.status_code, f"Eroare Google Drive API: {resp.text}")

    data = resp.json()
    return data.get("files", [])


async def upload_drive_file(
    headers: dict[str, str],
    file_name: str,
    mime_type: str,
    file_content: bytes,
    folder_id: str,
) -> dict:
    """Încarcă un fișier pe Google Drive (multipart upload). Returns API response dict."""
    metadata: dict[str, Any] = {"name": file_name}
    if folder_id:
        metadata["parents"] = [folder_id]

    boundary = f"boundary_{uuid.uuid4().hex}"

    body_parts = []
    body_parts.append(f"--{boundary}\r\n".encode())
    body_parts.append(b"Content-Type: application/json; charset=UTF-8\r\n\r\n")
    body_parts.append(json.dumps(metadata).encode("utf-8"))
    body_parts.append(f"\r\n--{boundary}\r\n".encode())
    body_parts.append(f"Content-Type: {mime_type}\r\n\r\n".encode())
    body_parts.append(file_content)
    body_parts.append(f"\r\n--{boundary}--".encode())

    multipart_body = b"".join(body_parts)

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{DRIVE_UPLOAD_BASE}/files?uploadType=multipart",
            headers={
                **headers,
                "Content-Type": f"multipart/related; boundary={boundary}",
            },
            content=multipart_body,
        )

    if resp.status_code == 401:
        raise HTTPException(401, "Token Google Drive expirat.")
    if resp.status_code not in (200, 201):
        raise HTTPException(resp.status_code, f"Eroare upload Drive: {resp.text}")

    return resp.json()


async def download_drive_file(headers: dict[str, str], file_id: str) -> dict:
    """Obține metadata fișierului din Drive (inclusiv webContentLink). Returns file metadata dict."""
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"{DRIVE_API_BASE}/files/{file_id}",
            headers=headers,
            params={"fields": "id,name,mimeType,size,webContentLink"},
        )

    if resp.status_code == 401:
        raise HTTPException(401, "Token Google Drive expirat.")
    if resp.status_code == 404:
        raise HTTPException(404, "Fișier negăsit pe Drive.")
    if resp.status_code != 200:
        raise HTTPException(resp.status_code, f"Eroare Drive: {resp.text}")

    return resp.json()
