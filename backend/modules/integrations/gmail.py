"""
Gmail/IMAP integration logic — pure functions, no route decorators.

All blocking IMAP/SMTP operations run via asyncio.to_thread.
"""

from __future__ import annotations

import email
import imaplib
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from .models import EmailSendRequest, _decode_mime_header, _extract_email_body


# ---------------------------------------------------------------------------
# IMAP helpers (blocking — call via asyncio.to_thread)
# ---------------------------------------------------------------------------

def imap_list_labels(addr: str, pwd: str) -> list[dict]:
    """Blocking IMAP LIST — returns list of labels/folders."""
    imap = None
    try:
        imap = imaplib.IMAP4_SSL("imap.gmail.com")
        imap.login(addr, pwd)
        status, data = imap.list()
        if status != "OK":
            return []
        labels = []
        for item in data:
            decoded = item.decode("utf-8", errors="replace") if isinstance(item, bytes) else str(item)
            # Format: '(\\HasNoChildren) "/" "INBOX"'
            match = re.search(r'"([^"]*)"$', decoded)
            if match:
                name = match.group(1)
            else:
                parts = decoded.rsplit(" ", 1)
                name = parts[-1].strip('"') if parts else decoded
            labels.append({"name": name, "raw": decoded})
        return labels
    finally:
        if imap:
            try:
                imap.logout()
            except Exception:
                pass


def imap_list_messages(addr: str, pwd: str, search_q: str, limit: int, mailbox: str) -> list[dict]:
    """Blocking IMAP fetch — returns list of message headers."""
    imap = None
    try:
        imap = imaplib.IMAP4_SSL("imap.gmail.com")
        imap.login(addr, pwd)
        # Use provided label/folder instead of hardcoded INBOX
        status, _ = imap.select(f'"{mailbox}"', readonly=True)
        if status != "OK":
            # Fallback to INBOX if label not found
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


def imap_read_message(addr: str, pwd: str, mid: str) -> dict | None:
    """Blocking IMAP read — returns full message dict or None."""
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


def imap_download_attachment(addr: str, pwd: str, mid: str, att_idx: int) -> tuple[str, str, bytes]:
    """Blocking IMAP attachment fetch.
    Returns (filename, content_type, payload) or raises ValueError."""
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


# ---------------------------------------------------------------------------
# SMTP helper (blocking — call via asyncio.to_thread)
# ---------------------------------------------------------------------------

def smtp_send_email(addr: str, pwd: str, request: EmailSendRequest) -> None:
    """Blocking SMTP send via Gmail."""
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
