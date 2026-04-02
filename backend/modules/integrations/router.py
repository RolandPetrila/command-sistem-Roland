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
import imaplib
import io
import logging
import smtplib
import time as _time
from typing import Any

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse

from app.core.activity_log import log_activity

from .models import (
    CalendarEventCreate,
    CalendarEventUpdate,
    EmailSendRequest,
    GitHubIssueCreate,
    _cache_clear,
    _cache_get,
    _cache_set,
    _get_config_key,
)
from .gmail import (
    imap_download_attachment,
    imap_list_labels,
    imap_list_messages,
    imap_read_message,
    smtp_send_email,
)
from .gdrive import (
    check_drive_status,
    download_drive_file,
    get_drive_headers,
    list_drive_files,
    upload_drive_file,
)
from .calendar_integration import (
    check_calendar_status,
    create_calendar_event,
    delete_calendar_event,
    get_calendar_headers,
    list_calendar_events,
    update_calendar_event,
)
from .github_integration import (
    check_github_status,
    create_github_issue,
    get_github_headers,
    list_github_commits,
    list_github_repos,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/integrations", tags=["integrations"])


# ===========================================================================
# GMAIL
# ===========================================================================

@router.get("/gmail/status")
async def gmail_status():
    """Verifică dacă Gmail este configurat."""
    cached = _cache_get("gmail")
    if cached is not None:
        return cached

    email_addr = await _get_config_key("gmail_email")
    app_password = await _get_config_key("gmail_app_password")
    configured = bool(email_addr and app_password)
    result = {
        "provider": "gmail",
        "configured": configured,
        "email": email_addr if configured else None,
        "message": "Gmail configurat." if configured else "Lipsesc cheile gmail_email și/sau gmail_app_password din Setări AI.",
        "cached_at": _time.time(),
    }
    return _cache_set("gmail", result)


@router.get("/gmail/labels")
async def gmail_list_labels():
    """Listează label-urile/folderele disponibile în contul Gmail via IMAP."""
    email_addr = await _get_config_key("gmail_email")
    app_password = await _get_config_key("gmail_app_password")
    if not email_addr or not app_password:
        raise HTTPException(400, "Gmail nu este configurat. Adaugă gmail_email și gmail_app_password în Setări AI.")

    try:
        labels = await asyncio.to_thread(imap_list_labels, email_addr, app_password)
        return {"labels": labels, "total": len(labels)}
    except imaplib.IMAP4.error as exc:
        logger.error("Eroare IMAP labels: %s", exc)
        raise HTTPException(500, f"Eroare conectare Gmail IMAP: {exc}")
    except Exception as exc:
        logger.error("Eroare Gmail labels: %s", exc)
        raise HTTPException(500, f"Eroare Gmail labels: {exc}")


@router.get("/gmail/messages")
async def gmail_list_messages(
    q: str = Query("", description="Criteriu de căutare IMAP"),
    label: str = Query("INBOX", description="Label/folder IMAP (default INBOX)"),
    max_results: int = Query(20, ge=1, le=100),
):
    """Listează ultimele email-uri din inbox (sau alt label) via IMAP."""
    email_addr = await _get_config_key("gmail_email")
    app_password = await _get_config_key("gmail_app_password")
    if not email_addr or not app_password:
        raise HTTPException(400, "Gmail nu este configurat. Adaugă gmail_email și gmail_app_password în Setări AI.")

    try:
        messages = await asyncio.to_thread(
            imap_list_messages, email_addr, app_password, q, max_results, label
        )

        await log_activity(
            action="integrations.gmail.list",
            summary=f"Listat {len(messages)} email-uri (label: {label})",
        )

        return {"messages": messages, "total": len(messages), "label": label}

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

    try:
        result = await asyncio.to_thread(
            imap_read_message, email_addr, app_password, message_id
        )
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

    try:
        await asyncio.to_thread(smtp_send_email, email_addr, app_password, req)

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

    try:
        filename, content_type, payload = await asyncio.to_thread(
            imap_download_attachment, email_addr, app_password, message_id, attachment_index
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

@router.get("/drive/status")
async def drive_status():
    """Verifică dacă Google Drive este configurat."""
    cached = _cache_get("google_drive")
    if cached is not None:
        return cached

    result = await check_drive_status()
    result["cached_at"] = _time.time()
    return _cache_set("google_drive", result)


@router.get("/drive/files")
async def drive_list_files(
    query: str = Query("", description="Căutare în Drive"),
    folder_id: str = Query("", description="ID folder Drive"),
    max_results: int = Query(20, ge=1, le=100),
):
    """Listează fișierele din Google Drive."""
    headers = await get_drive_headers()

    try:
        files = await list_drive_files(headers, query, folder_id, max_results)

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
    headers = await get_drive_headers()

    file_name = file.filename or "untitled"
    mime_type = file.content_type or "application/octet-stream"

    try:
        file_content = await file.read()
        result = await upload_drive_file(headers, file_name, mime_type, file_content, folder_id)

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
    headers = await get_drive_headers()

    try:
        file_meta = await download_drive_file(headers, file_id)

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

@router.get("/calendar/status")
async def calendar_status():
    """Verifică dacă Google Calendar este configurat."""
    cached = _cache_get("google_calendar")
    if cached is not None:
        return cached

    result = await check_calendar_status()
    result["cached_at"] = _time.time()
    return _cache_set("google_calendar", result)


@router.get("/calendar/events")
async def calendar_list_events(
    days: int = Query(7, ge=1, le=90, description="Câte zile înainte"),
):
    """Listează evenimentele din calendarul principal pentru următoarele N zile."""
    headers = await get_calendar_headers()

    try:
        events = await list_calendar_events(headers, days)

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
    headers = await get_calendar_headers()

    try:
        created = await create_calendar_event(
            headers, req.summary, req.start, req.end, req.description
        )

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
    headers = await get_calendar_headers()

    try:
        await delete_calendar_event(headers, event_id)

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
    headers = await get_calendar_headers()

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
        updated = await update_calendar_event(headers, event_id, patch_body)
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

@router.get("/github/status")
async def github_status():
    """Verifică dacă GitHub este configurat."""
    cached = _cache_get("github")
    if cached is not None:
        return cached

    result = await check_github_status()
    result["cached_at"] = _time.time()
    return _cache_set("github", result)


@router.get("/github/repos")
async def github_list_repos(
    max_results: int = Query(30, ge=1, le=100),
):
    """Listează repo-urile utilizatorului GitHub."""
    headers = await get_github_headers()

    try:
        repos = await list_github_repos(headers, max_results)

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
    headers = await get_github_headers()

    try:
        commits = await list_github_commits(headers, owner, repo, max_results, branch)

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
    headers = await get_github_headers()

    try:
        created = await create_github_issue(
            headers, owner, repo, req.title, req.body, req.labels
        )

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


@router.post("/status/refresh")
async def integrations_status_refresh():
    """Golește cache-ul de status pentru toate integrările, forțând verificare proaspătă."""
    _cache_clear()
    await log_activity(
        action="integrations.status.refresh",
        summary="Cache status integrări golit manual",
    )
    return {"status": "ok", "message": "Cache status golit. Următoarea verificare va fi proaspătă."}
