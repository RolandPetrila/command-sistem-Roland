"""
API endpoints pentru Integrări Externe — Gmail, Google Drive, Google Calendar, GitHub.

Gmail:    SMTP (trimitere) + IMAP (citire) cu app password din ai_config.
Drive:    REST API cu httpx + token OAuth din ai_config.
Calendar: REST API cu httpx + token OAuth din ai_config.
GitHub:   REST API cu httpx + personal access token din ai_config.

Chei necesare în ai_config:
  gmail_email, gmail_app_password
  google_drive_token, google_calendar_token
  github_token
"""

from __future__ import annotations

import asyncio
import email
import imaplib
import json
import logging
import re
import smtplib
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import decode_header
from typing import Any

import io
import uuid

import httpx
from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, field_validator

from app.core.activity_log import log_activity
from app.db.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/integrations", tags=["integrations"])


# ---------------------------------------------------------------------------
# Helpers
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


# ===========================================================================
# GMAIL
# ===========================================================================

@router.get("/gmail/status")
async def gmail_status():
    """Verifică dacă Gmail este configurat."""
    email_addr = await _get_config_key("gmail_email")
    app_password = await _get_config_key("gmail_app_password")
    configured = bool(email_addr and app_password)
    return {
        "provider": "gmail",
        "configured": configured,
        "email": email_addr if configured else None,
        "message": "Gmail configurat." if configured else "Lipsesc cheile gmail_email și/sau gmail_app_password din Setări AI.",
    }


@router.get("/gmail/messages")
async def gmail_list_messages(
    q: str = Query("", description="Criteriu de căutare IMAP"),
    max_results: int = Query(20, ge=1, le=100),
):
    """Listează ultimele email-uri din inbox via IMAP."""
    email_addr = await _get_config_key("gmail_email")
    app_password = await _get_config_key("gmail_app_password")
    if not email_addr or not app_password:
        raise HTTPException(400, "Gmail nu este configurat. Adaugă gmail_email și gmail_app_password în Setări AI.")

    def _imap_list(addr: str, pwd: str, search_q: str, limit: int) -> list[dict]:
        """Blocking IMAP fetch — runs in thread via asyncio.to_thread."""
        imap = None
        try:
            imap = imaplib.IMAP4_SSL("imap.gmail.com")
            imap.login(addr, pwd)
            imap.select("INBOX", readonly=True)

            search_criteria = f'({search_q})' if search_q else "ALL"
            status, data = imap.search(None, search_criteria)
            if status != "OK":
                return []

            msg_ids = data[0].split()
            msg_ids = list(reversed(msg_ids))[:limit]

            messages = []
            for msg_id in msg_ids:
                status, msg_data = imap.fetch(msg_id, "(RFC822.SIZE BODY[HEADER.FIELDS (FROM SUBJECT DATE)])")
                if status != "OK" or not msg_data or not msg_data[0]:
                    continue

                raw_header = msg_data[0][1] if isinstance(msg_data[0], tuple) else b""
                if isinstance(raw_header, bytes):
                    header_msg = email.message_from_bytes(raw_header)
                else:
                    continue

                messages.append({
                    "id": msg_id.decode() if isinstance(msg_id, bytes) else str(msg_id),
                    "from": _decode_mime_header(header_msg.get("From")),
                    "subject": _decode_mime_header(header_msg.get("Subject")),
                    "date": header_msg.get("Date", ""),
                })

            return messages
        finally:
            if imap:
                try:
                    imap.logout()
                except Exception:
                    pass

    try:
        messages = await asyncio.to_thread(_imap_list, email_addr, app_password, q, max_results)

        await log_activity(
            action="integrations.gmail.list",
            summary=f"Listat {len(messages)} email-uri",
        )

        return {"messages": messages, "total": len(messages)}

    except imaplib.IMAP4.error as exc:
        logger.error("Eroare IMAP Gmail: %s", exc)
        raise HTTPException(500, f"Eroare conectare Gmail IMAP: {exc}")
    except Exception as exc:
        logger.error("Eroare Gmail: %s", exc)
        raise HTTPException(500, f"Eroare Gmail: {exc}")


@router.get("/gmail/messages/{message_id}")
async def gmail_read_message(message_id: str):
    """Citește un email complet din inbox via IMAP."""
    email_addr = await _get_config_key("gmail_email")
    app_password = await _get_config_key("gmail_app_password")
    if not email_addr or not app_password:
        raise HTTPException(400, "Gmail nu este configurat.")

    def _imap_read(addr: str, pwd: str, mid: str) -> dict | None:
        """Blocking IMAP read — runs in thread via asyncio.to_thread."""
        imap = None
        try:
            imap = imaplib.IMAP4_SSL("imap.gmail.com")
            imap.login(addr, pwd)
            imap.select("INBOX", readonly=True)

            status, msg_data = imap.fetch(mid.encode(), "(RFC822)")
            if status != "OK" or not msg_data or not msg_data[0]:
                return None

            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            # Colectează atașamentele (doar metadata)
            attachments = []
            if msg.is_multipart():
                for part in msg.walk():
                    filename = part.get_filename()
                    if filename:
                        attachments.append({
                            "filename": _decode_mime_header(filename),
                            "content_type": part.get_content_type(),
                            "size": len(part.get_payload(decode=True) or b""),
                        })

            return {
                "id": mid,
                "from": _decode_mime_header(msg.get("From")),
                "to": _decode_mime_header(msg.get("To")),
                "subject": _decode_mime_header(msg.get("Subject")),
                "date": msg.get("Date", ""),
                "body": _extract_email_body(msg),
                "attachments": attachments,
            }
        finally:
            if imap:
                try:
                    imap.logout()
                except Exception:
                    pass

    try:
        result = await asyncio.to_thread(_imap_read, email_addr, app_password, message_id)
        if result is None:
            raise HTTPException(404, "Email negăsit.")

        await log_activity(
            action="integrations.gmail.read",
            summary=f"Citit email: {result['subject'][:80]}",
        )

        return result

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Eroare citire email: %s", exc)
        raise HTTPException(500, f"Eroare citire email: {exc}")


@router.post("/gmail/send")
async def gmail_send(req: EmailSendRequest):
    """Trimite un email prin SMTP Gmail cu app password."""
    email_addr = await _get_config_key("gmail_email")
    app_password = await _get_config_key("gmail_app_password")
    if not email_addr or not app_password:
        raise HTTPException(400, "Gmail nu este configurat. Adaugă gmail_email și gmail_app_password în Setări AI.")

    def _smtp_send(addr: str, pwd: str, request: EmailSendRequest) -> None:
        """Blocking SMTP send — runs in thread via asyncio.to_thread."""
        smtp_conn = None
        try:
            msg = MIMEMultipart()
            msg["From"] = addr
            msg["To"] = request.to
            msg["Subject"] = request.subject

            # CC apare in header-ul mesajului
            if request.cc:
                msg["Cc"] = ", ".join(request.cc)

            content_type = "html" if request.html else "plain"
            msg.attach(MIMEText(request.body, content_type, "utf-8"))

            # Destinatarii SMTP = To + CC + BCC (BCC NU apare in header)
            all_recipients = [request.to]
            all_recipients.extend(request.cc)
            all_recipients.extend(request.bcc)

            smtp_conn = smtplib.SMTP_SSL("smtp.gmail.com", 465)
            smtp_conn.login(addr, pwd)
            smtp_conn.sendmail(addr, all_recipients, msg.as_string())
        finally:
            if smtp_conn:
                try:
                    smtp_conn.quit()
                except Exception:
                    pass

    try:
        await asyncio.to_thread(_smtp_send, email_addr, app_password, req)

        cc_info = f", CC: {', '.join(req.cc)}" if req.cc else ""
        bcc_info = f", BCC: {len(req.bcc)} dest." if req.bcc else ""
        await log_activity(
            action="integrations.gmail.send",
            summary=f"Email trimis către {req.to}{cc_info}{bcc_info}: {req.subject[:80]}",
        )

        return {"status": "ok", "message": f"Email trimis cu succes către {req.to}."}

    except smtplib.SMTPAuthenticationError:
        raise HTTPException(401, "Autentificare Gmail eșuată. Verifică app password.")
    except Exception as exc:
        logger.error("Eroare trimitere email: %s", exc)
        raise HTTPException(500, f"Eroare trimitere email: {exc}")


@router.get("/gmail/attachment")
async def gmail_download_attachment(
    message_id: str = Query(..., description="ID-ul mesajului IMAP"),
    attachment_index: int = Query(0, ge=0, description="Indexul atașamentului (pornind de la 0)"),
):
    """Descarcă un atașament dintr-un email via IMAP."""
    email_addr = await _get_config_key("gmail_email")
    app_password = await _get_config_key("gmail_app_password")
    if not email_addr or not app_password:
        raise HTTPException(400, "Gmail nu este configurat.")

    def _imap_attachment(addr: str, pwd: str, mid: str, att_idx: int) -> tuple[str, str, bytes]:
        """Blocking IMAP attachment fetch — runs in thread via asyncio.to_thread.
        Returns (filename, content_type, payload) or raises."""
        imap = None
        try:
            imap = imaplib.IMAP4_SSL("imap.gmail.com")
            imap.login(addr, pwd)
            imap.select("INBOX", readonly=True)

            status, msg_data = imap.fetch(mid.encode(), "(RFC822)")
            if status != "OK" or not msg_data or not msg_data[0]:
                raise ValueError("EMAIL_NOT_FOUND")

            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            # Colectează toate atașamentele
            attachments = []
            if msg.is_multipart():
                for part in msg.walk():
                    fn = part.get_filename()
                    if fn:
                        attachments.append(part)

            if not attachments:
                raise ValueError("NO_ATTACHMENTS")

            if att_idx >= len(attachments):
                raise ValueError(f"INDEX_OUT_OF_RANGE:{len(attachments)}")

            target_part = attachments[att_idx]
            filename = _decode_mime_header(target_part.get_filename() or "attachment")
            content_type = target_part.get_content_type() or "application/octet-stream"
            payload = target_part.get_payload(decode=True)

            if not payload:
                raise ValueError("EMPTY_ATTACHMENT")

            return filename, content_type, payload
        finally:
            if imap:
                try:
                    imap.logout()
                except Exception:
                    pass

    try:
        filename, content_type, payload = await asyncio.to_thread(
            _imap_attachment, email_addr, app_password, message_id, attachment_index
        )

        await log_activity(
            action="integrations.gmail.attachment",
            summary=f"Descărcat atașament: {filename} din email {message_id}",
        )

        return StreamingResponse(
            io.BytesIO(payload),
            media_type=content_type,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    except ValueError as exc:
        err = str(exc)
        if err == "EMAIL_NOT_FOUND":
            raise HTTPException(404, "Email negăsit.")
        elif err == "NO_ATTACHMENTS":
            raise HTTPException(404, "Emailul nu conține atașamente.")
        elif err.startswith("INDEX_OUT_OF_RANGE:"):
            count = err.split(":")[1]
            raise HTTPException(404, f"Index atașament invalid. Emailul are {count} atașament(e).")
        elif err == "EMPTY_ATTACHMENT":
            raise HTTPException(404, "Atașamentul este gol.")
        raise HTTPException(500, f"Eroare descărcare atașament: {exc}")
    except HTTPException:
        raise
    except imaplib.IMAP4.error as exc:
        logger.error("Eroare IMAP descărcare atașament: %s", exc)
        raise HTTPException(500, f"Eroare conectare Gmail IMAP: {exc}")
    except Exception as exc:
        logger.error("Eroare descărcare atașament: %s", exc)
        raise HTTPException(500, f"Eroare descărcare atașament: {exc}")


# ===========================================================================
# GOOGLE DRIVE
# ===========================================================================

DRIVE_API_BASE = "https://www.googleapis.com/drive/v3"
DRIVE_UPLOAD_BASE = "https://www.googleapis.com/upload/drive/v3"


async def _drive_headers() -> dict[str, str]:
    """Returnează header-ele de autorizare pentru Google Drive API."""
    token = await _get_config_key("google_drive_token")
    if not token:
        raise HTTPException(400, "Google Drive nu este configurat. Adaugă google_drive_token în Setări AI.")
    return {"Authorization": f"Bearer {token}"}


@router.get("/drive/status")
async def drive_status():
    """Verifică dacă Google Drive este configurat."""
    token = await _get_config_key("google_drive_token")
    configured = bool(token)

    if configured:
        # Verifică dacă token-ul e valid
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


@router.get("/drive/files")
async def drive_list_files(
    query: str = Query("", description="Căutare în Drive"),
    folder_id: str = Query("", description="ID folder Drive"),
    max_results: int = Query(20, ge=1, le=100),
):
    """Listează fișierele din Google Drive."""
    headers = await _drive_headers()

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

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{DRIVE_API_BASE}/files", headers=headers, params=params
            )

        if resp.status_code == 401:
            raise HTTPException(401, "Token Google Drive expirat. Re-autentifică din Setări.")
        if resp.status_code != 200:
            raise HTTPException(resp.status_code, f"Eroare Google Drive API: {resp.text}")

        data = resp.json()
        files = data.get("files", [])

        await log_activity(
            action="integrations.drive.list",
            summary=f"Listat {len(files)} fișiere Drive",
        )

        return {"files": files, "total": len(files)}

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Eroare Google Drive: %s", exc)
        raise HTTPException(500, f"Eroare Google Drive: {exc}")


@router.post("/drive/upload")
async def drive_upload_file(
    file: UploadFile = File(..., description="Fișierul de încărcat"),
    folder_id: str = Query("", description="ID folder destinație"),
):
    """
    Încarcă un fișier cu conținut pe Google Drive (multipart upload).
    Acceptă orice tip de fișier prin form upload.
    """
    headers = await _drive_headers()

    file_name = file.filename or "untitled"
    mime_type = file.content_type or "application/octet-stream"

    metadata: dict[str, Any] = {"name": file_name}
    if folder_id:
        metadata["parents"] = [folder_id]

    try:
        file_content = await file.read()

        # Google Drive API v3 multipart upload:
        # POST https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart
        # Body: multipart/related cu metadata JSON + conținut fișier
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

        result = resp.json()

        size_kb = len(file_content) / 1024
        await log_activity(
            action="integrations.drive.upload",
            summary=f"Fișier încărcat pe Drive: {file_name} ({size_kb:.1f} KB)",
            details={"file_id": result.get("id"), "size_bytes": len(file_content)},
        )

        return {
            "status": "ok",
            "message": f"Fișier '{file_name}' încărcat pe Google Drive ({size_kb:.1f} KB).",
            "file": result,
        }

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Eroare upload Drive: %s", exc)
        raise HTTPException(500, f"Eroare upload Drive: {exc}")


@router.get("/drive/download/{file_id}")
async def drive_download_file(file_id: str):
    """Descarcă un fișier din Google Drive (returnează link de descărcare)."""
    headers = await _drive_headers()

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            # Obține metadata fișierului
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

        file_meta = resp.json()

        await log_activity(
            action="integrations.drive.download",
            summary=f"Descărcare Drive: {file_meta.get('name', file_id)}",
        )

        return {
            "file": file_meta,
            "download_url": file_meta.get("webContentLink", ""),
            "message": "Folosește download_url pentru a descărca fișierul.",
        }

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Eroare descărcare Drive: %s", exc)
        raise HTTPException(500, f"Eroare descărcare Drive: {exc}")


# ===========================================================================
# GOOGLE CALENDAR
# ===========================================================================

CALENDAR_API_BASE = "https://www.googleapis.com/calendar/v3"


async def _calendar_headers() -> dict[str, str]:
    """Returnează header-ele de autorizare pentru Google Calendar API."""
    token = await _get_config_key("google_calendar_token")
    if not token:
        raise HTTPException(400, "Google Calendar nu este configurat. Adaugă google_calendar_token în Setări AI.")
    return {"Authorization": f"Bearer {token}"}


@router.get("/calendar/status")
async def calendar_status():
    """Verifică dacă Google Calendar este configurat."""
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


@router.get("/calendar/events")
async def calendar_list_events(
    days: int = Query(7, ge=1, le=90, description="Câte zile înainte"),
):
    """Listează evenimentele din calendarul principal pentru următoarele N zile."""
    headers = await _calendar_headers()

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

    try:
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

        await log_activity(
            action="integrations.calendar.list",
            summary=f"Listat {len(events)} evenimente Calendar ({days} zile)",
        )

        return {"events": events, "total": len(events), "days": days}

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Eroare Google Calendar: %s", exc)
        raise HTTPException(500, f"Eroare Google Calendar: {exc}")


@router.post("/calendar/events")
async def calendar_create_event(req: CalendarEventCreate):
    """Creează un eveniment nou în Google Calendar."""
    headers = await _calendar_headers()

    event_body = {
        "summary": req.summary,
        "description": req.description,
        "start": {"dateTime": req.start, "timeZone": "Europe/Bucharest"},
        "end": {"dateTime": req.end, "timeZone": "Europe/Bucharest"},
    }

    try:
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

        created = resp.json()

        await log_activity(
            action="integrations.calendar.create",
            summary=f"Eveniment creat: {req.summary}",
            details={"event_id": created.get("id")},
        )

        return {
            "status": "ok",
            "message": f"Eveniment '{req.summary}' creat cu succes.",
            "event": {
                "id": created.get("id"),
                "summary": created.get("summary"),
                "htmlLink": created.get("htmlLink"),
            },
        }

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Eroare creare eveniment: %s", exc)
        raise HTTPException(500, f"Eroare creare eveniment: {exc}")


@router.delete("/calendar/events/{event_id}")
async def calendar_delete_event(event_id: str):
    """Șterge un eveniment din Google Calendar."""
    headers = await _calendar_headers()

    try:
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

        await log_activity(
            action="integrations.calendar.delete",
            summary=f"Eveniment șters: {event_id}",
        )

        return {"status": "ok", "message": "Eveniment șters cu succes."}

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Eroare ștergere eveniment: %s", exc)
        raise HTTPException(500, f"Eroare ștergere eveniment: {exc}")


@router.put("/calendar/events/{event_id}")
async def calendar_update_event(event_id: str, req: CalendarEventUpdate):
    """Actualizează un eveniment existent în Google Calendar (PATCH parțial)."""
    headers = await _calendar_headers()

    # Construiește doar câmpurile trimise (non-None)
    patch_body: dict[str, Any] = {}
    if req.summary is not None:
        patch_body["summary"] = req.summary
    if req.description is not None:
        patch_body["description"] = req.description
    if req.start is not None:
        patch_body["start"] = {"dateTime": req.start, "timeZone": "Europe/Bucharest"}
    if req.end is not None:
        patch_body["end"] = {"dateTime": req.end, "timeZone": "Europe/Bucharest"}

    if not patch_body:
        raise HTTPException(400, "Niciun câmp de actualizat. Trimite cel puțin un câmp (summary, start, end, description).")

    try:
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

        updated = resp.json()
        changed_fields = list(patch_body.keys())

        await log_activity(
            action="integrations.calendar.update",
            summary=f"Eveniment actualizat: {updated.get('summary', event_id)} ({', '.join(changed_fields)})",
            details={"event_id": event_id, "changed_fields": changed_fields},
        )

        return {
            "status": "ok",
            "message": f"Eveniment '{updated.get('summary', event_id)}' actualizat cu succes.",
            "event": {
                "id": updated.get("id"),
                "summary": updated.get("summary"),
                "description": updated.get("description", ""),
                "start": updated.get("start", {}).get("dateTime", ""),
                "end": updated.get("end", {}).get("dateTime", ""),
                "htmlLink": updated.get("htmlLink", ""),
            },
        }

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Eroare actualizare eveniment: %s", exc)
        raise HTTPException(500, f"Eroare actualizare eveniment: {exc}")


# ===========================================================================
# GITHUB
# ===========================================================================

GITHUB_API_BASE = "https://api.github.com"


async def _github_headers() -> dict[str, str]:
    """Returnează header-ele de autorizare pentru GitHub API."""
    token = await _get_config_key("github_token")
    if not token:
        raise HTTPException(400, "GitHub nu este configurat. Adaugă github_token în Setări AI.")
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
    }


@router.get("/github/status")
async def github_status():
    """Verifică dacă GitHub este configurat."""
    token = await _get_config_key("github_token")
    configured = bool(token)

    if configured:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"{GITHUB_API_BASE}/user",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Accept": "application/vnd.github.v3+json",
                    },
                )
                if resp.status_code == 200:
                    user = resp.json()
                    return {
                        "provider": "github",
                        "configured": True,
                        "connected": True,
                        "user": user.get("login", ""),
                        "name": user.get("name", ""),
                        "repos": user.get("public_repos", 0),
                        "message": "GitHub conectat.",
                    }
                else:
                    return {
                        "provider": "github",
                        "configured": True,
                        "connected": False,
                        "message": "Token GitHub invalid sau expirat.",
                    }
        except Exception:
            return {
                "provider": "github",
                "configured": True,
                "connected": False,
                "message": "Nu s-a putut verifica conexiunea GitHub.",
            }

    return {
        "provider": "github",
        "configured": False,
        "connected": False,
        "message": "Lipsește github_token din Setări AI.",
    }


@router.get("/github/repos")
async def github_list_repos(
    max_results: int = Query(30, ge=1, le=100),
):
    """Listează repo-urile utilizatorului GitHub."""
    headers = await _github_headers()

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{GITHUB_API_BASE}/user/repos",
                headers=headers,
                params={
                    "sort": "updated",
                    "direction": "desc",
                    "per_page": max_results,
                },
            )

        if resp.status_code == 401:
            raise HTTPException(401, "Token GitHub invalid.")
        if resp.status_code != 200:
            raise HTTPException(resp.status_code, f"Eroare GitHub API: {resp.text}")

        repos = []
        for repo in resp.json():
            repos.append({
                "id": repo.get("id"),
                "name": repo.get("name"),
                "full_name": repo.get("full_name"),
                "description": repo.get("description", ""),
                "private": repo.get("private", False),
                "language": repo.get("language", ""),
                "stars": repo.get("stargazers_count", 0),
                "updated_at": repo.get("updated_at", ""),
                "html_url": repo.get("html_url", ""),
            })

        await log_activity(
            action="integrations.github.repos",
            summary=f"Listat {len(repos)} repo-uri GitHub",
        )

        return {"repos": repos, "total": len(repos)}

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Eroare GitHub repos: %s", exc)
        raise HTTPException(500, f"Eroare GitHub: {exc}")


@router.get("/github/repo/{owner}/{repo}/commits")
async def github_repo_commits(
    owner: str,
    repo: str,
    max_results: int = Query(20, ge=1, le=100),
    branch: str = Query("main", description="Branch-ul din care se listează commit-urile"),
):
    """Listează ultimele commit-uri dintr-un repo GitHub (pe un branch specificat)."""
    headers = await _github_headers()

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/commits",
                headers=headers,
                params={"per_page": max_results, "sha": branch},
            )

        if resp.status_code == 401:
            raise HTTPException(401, "Token GitHub invalid.")
        if resp.status_code == 404:
            raise HTTPException(404, f"Repo {owner}/{repo} negăsit.")
        if resp.status_code == 409:
            raise HTTPException(404, f"Branch-ul '{branch}' nu există în {owner}/{repo}.")
        if resp.status_code != 200:
            raise HTTPException(resp.status_code, f"Eroare GitHub API: {resp.text}")

        commits = []
        for c in resp.json():
            commit_info = c.get("commit", {})
            author_info = commit_info.get("author", {})
            commits.append({
                "sha": c.get("sha", "")[:8],
                "message": commit_info.get("message", ""),
                "author": author_info.get("name", ""),
                "date": author_info.get("date", ""),
                "html_url": c.get("html_url", ""),
            })

        await log_activity(
            action="integrations.github.commits",
            summary=f"Listat {len(commits)} commit-uri: {owner}/{repo} (branch: {branch})",
        )

        return {"commits": commits, "total": len(commits), "repo": f"{owner}/{repo}", "branch": branch}

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Eroare GitHub commits: %s", exc)
        raise HTTPException(500, f"Eroare GitHub: {exc}")


@router.post("/github/repo/{owner}/{repo}/issues")
async def github_create_issue(owner: str, repo: str, req: GitHubIssueCreate):
    """Creează un issue nou într-un repo GitHub."""
    headers = await _github_headers()

    issue_body: dict[str, Any] = {
        "title": req.title,
        "body": req.body,
    }
    if req.labels:
        issue_body["labels"] = req.labels

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues",
                headers={**headers, "Content-Type": "application/json"},
                json=issue_body,
            )

        if resp.status_code == 401:
            raise HTTPException(401, "Token GitHub invalid.")
        if resp.status_code == 404:
            raise HTTPException(404, f"Repo {owner}/{repo} negăsit.")
        if resp.status_code not in (200, 201):
            raise HTTPException(resp.status_code, f"Eroare creare issue: {resp.text}")

        created = resp.json()

        await log_activity(
            action="integrations.github.issue",
            summary=f"Issue creat: {req.title} ({owner}/{repo})",
            details={"issue_number": created.get("number"), "url": created.get("html_url")},
        )

        return {
            "status": "ok",
            "message": f"Issue #{created.get('number')} creat cu succes.",
            "issue": {
                "number": created.get("number"),
                "title": created.get("title"),
                "html_url": created.get("html_url"),
                "state": created.get("state"),
            },
        }

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Eroare creare issue: %s", exc)
        raise HTTPException(500, f"Eroare GitHub: {exc}")


# ===========================================================================
# STATUS GENERAL
# ===========================================================================

@router.get("/status")
async def integrations_status_overview():
    """Prezentare generală a tuturor integrărilor — care sunt configurate și conectate."""
    results = {}

    # Gmail
    gmail_email = await _get_config_key("gmail_email")
    gmail_pass = await _get_config_key("gmail_app_password")
    results["gmail"] = {
        "provider": "gmail",
        "configured": bool(gmail_email and gmail_pass),
        "email": gmail_email or None,
    }

    # Google Drive
    drive_token = await _get_config_key("google_drive_token")
    results["google_drive"] = {
        "provider": "google_drive",
        "configured": bool(drive_token),
    }

    # Google Calendar
    cal_token = await _get_config_key("google_calendar_token")
    results["google_calendar"] = {
        "provider": "google_calendar",
        "configured": bool(cal_token),
    }

    # GitHub
    gh_token = await _get_config_key("github_token")
    results["github"] = {
        "provider": "github",
        "configured": bool(gh_token),
    }

    configured_count = sum(1 for v in results.values() if v["configured"])

    return {
        "integrations": results,
        "configured_count": configured_count,
        "total_count": len(results),
        "message": f"{configured_count}/{len(results)} integrări configurate.",
    }
