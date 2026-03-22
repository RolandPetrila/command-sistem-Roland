"""
API endpoints pentru API Key Vault — stocare criptată chei API.

Endpoints:
  POST   /api/vault/setup            — setează master password (prima dată)
  POST   /api/vault/unlock           — verifică master password, returnează session token
  GET    /api/vault/keys             — lista chei (nume, provider, dată) — fără valori
  POST   /api/vault/keys             — adaugă cheie nouă
  GET    /api/vault/keys/:name       — decriptează și returnează valoarea
  POST   /api/vault/keys/:name/test  — testează validitatea cheii la provider
  DELETE /api/vault/keys/:name       — șterge o cheie (necesită confirm=true)
  GET    /api/vault/status           — verifică dacă vault-ul e configurat
"""

from __future__ import annotations

import base64
import hashlib
import logging
import os
import re
import time
import uuid
from typing import Optional

import httpx
from cryptography.fernet import Fernet, InvalidToken
from fastapi import APIRouter, HTTPException, Header, Query, Request
from pydantic import BaseModel

from app.core.activity_log import log_activity
from app.db.database import get_db

router = APIRouter(prefix="/api/vault", tags=["vault"])


# --- Helpers criptare ---

def _derive_key(password: str, salt: bytes) -> bytes:
    """Derivă cheie Fernet din password + salt (PBKDF2)."""
    key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
    return base64.urlsafe_b64encode(key)


def _hash_password(password: str, salt: bytes) -> str:
    """Hash password pentru verificare."""
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000).hex()


# --- Models ---

class SetupRequest(BaseModel):
    master_password: str


class AddKeyRequest(BaseModel):
    name: str
    value: str
    provider: str = "generic"


# S9.9 — Key format validation patterns per provider
_KEY_PATTERNS: dict[str, tuple[str, str]] = {
    "gemini": (r"^AIza[0-9A-Za-z_-]{35}$", "AIza... (39 caractere)"),
    "openai": (r"^sk-[a-zA-Z0-9_-]{20,}$", "sk-... (minim 23 caractere)"),
    "deepl": (r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}:fx$", "UUID:fx"),
    "groq": (r"^gsk_[a-zA-Z0-9]{20,}$", "gsk_... (minim 24 caractere)"),
    "azure": (r"^[0-9a-f]{32}$", "32 hex characters"),
    "cerebras": (r"^csk-[a-zA-Z0-9_-]{20,}$", "csk-... (minim 24 caractere)"),
    "mistral": (r"^[a-zA-Z0-9]{32}$", "32 alphanumeric characters"),
}

_logger = logging.getLogger(__name__)


# --- Rate limiter for /unlock (max 5 attempts per 60s per IP) ---

_unlock_attempts: dict[str, list[float]] = {}
_RATE_LIMIT_MAX = 5
_RATE_LIMIT_WINDOW = 60  # seconds


def _check_rate_limit(client_ip: str) -> None:
    """Verifică rate limit pe /unlock. Aruncă 429 dacă depășit."""
    now = time.time()
    if client_ip not in _unlock_attempts:
        _unlock_attempts[client_ip] = []

    # Remove expired entries
    _unlock_attempts[client_ip] = [
        t for t in _unlock_attempts[client_ip] if now - t < _RATE_LIMIT_WINDOW
    ]

    if len(_unlock_attempts[client_ip]) >= _RATE_LIMIT_MAX:
        raise HTTPException(
            429,
            f"Prea multe încercări de deblocare. Așteaptă {_RATE_LIMIT_WINDOW}s."
        )


def _record_attempt(client_ip: str) -> None:
    """Înregistrează o încercare de unlock."""
    if client_ip not in _unlock_attempts:
        _unlock_attempts[client_ip] = []
    _unlock_attempts[client_ip].append(time.time())


# --- Session management (30 min TTL) ---

_sessions: dict[str, dict] = {}  # token -> {"pw_hash": str, "pw_enc": bytes, "expires": float}
_SESSION_TTL = 30 * 60  # 30 minutes in seconds


def _hash_session_pw(master_password: str) -> str:
    """Hash master password for session validation (never store plaintext)."""
    return hashlib.sha256(master_password.encode()).hexdigest()


def _create_session(master_password: str) -> str:
    """Creează o sesiune nouă și returnează token-ul.

    Password is stored hashed (for validation) and encrypted with a
    per-session Fernet key (for crypto operations that need the original).
    Plaintext is never kept in the session dict.
    """
    _cleanup_expired_sessions()
    token = str(uuid.uuid4())
    # Encrypt password with a per-session key so plaintext is not in memory
    session_key = base64.urlsafe_b64encode(hashlib.sha256(token.encode()).digest())
    pw_enc = Fernet(session_key).encrypt(master_password.encode())
    _sessions[token] = {
        "pw_hash": _hash_session_pw(master_password),
        "pw_enc": pw_enc,
        "expires": time.time() + _SESSION_TTL,
    }
    return token


def _cleanup_expired_sessions() -> None:
    """Șterge sesiunile expirate."""
    now = time.time()
    expired = [t for t, s in _sessions.items() if s["expires"] < now]
    for t in expired:
        del _sessions[t]


def _resolve_master_password(
    x_master_password: Optional[str] = None,
    x_vault_session: Optional[str] = None,
) -> str:
    """Rezolvă master password din header direct sau din session token.

    Prioritate: X-Master-Password > X-Vault-Session.
    Session stores password hashed + encrypted (never plaintext).
    Aruncă HTTPException dacă niciuna nu e validă.
    """
    if x_master_password:
        return x_master_password

    if x_vault_session:
        _cleanup_expired_sessions()
        session = _sessions.get(x_vault_session)
        if session and session["expires"] > time.time():
            # Decrypt password from session using token-derived key
            session_key = base64.urlsafe_b64encode(
                hashlib.sha256(x_vault_session.encode()).digest()
            )
            try:
                decrypted = Fernet(session_key).decrypt(session["pw_enc"]).decode()
            except InvalidToken:
                raise HTTPException(401, "Sesiune coruptă. Deblochează din nou.")
            # Verify hash matches as extra safety check
            if _hash_session_pw(decrypted) != session["pw_hash"]:
                raise HTTPException(401, "Sesiune invalidă. Deblochează din nou.")
            return decrypted
        raise HTTPException(401, "Sesiune expirată sau invalidă. Deblochează din nou.")

    raise HTTPException(401, "Lipsește X-Master-Password sau X-Vault-Session header.")


# --- Key test URLs per provider ---

_KEY_TEST_URLS: dict[str, dict] = {
    "gemini": {
        "url": "https://generativelanguage.googleapis.com/v1beta/models",
        "auth_type": "query_param",
        "param_name": "key",
    },
    "openai": {
        "url": "https://api.openai.com/v1/models",
        "auth_type": "bearer",
    },
    "deepl": {
        "url": "https://api-free.deepl.com/v2/usage",
        "auth_type": "header",
        "header_name": "DeepL-Auth-Key",
    },
    "groq": {
        "url": "https://api.groq.com/openai/v1/models",
        "auth_type": "bearer",
    },
    "cerebras": {
        "url": "https://api.cerebras.ai/v1/models",
        "auth_type": "bearer",
    },
    "mistral": {
        "url": "https://api.mistral.ai/v1/models",
        "auth_type": "bearer",
    },
}


def _validate_key_format(provider: str, value: str) -> str | None:
    """Returns warning message if key format doesn't match expected pattern, None if OK."""
    provider_lower = provider.lower()
    for key, (pattern, expected) in _KEY_PATTERNS.items():
        if key in provider_lower:
            if not re.match(pattern, value.strip()):
                return f"Format key {provider} neașteptat. Așteptat: {expected}"
            return None
    return None  # unknown provider — no validation


# --- Endpoints ---

@router.get("/status")
async def vault_status():
    """Verifică dacă vault-ul are master password setat."""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT value FROM vault_config WHERE key = 'master_hash'"
        )
        row = await cursor.fetchone()
        return {"configured": row is not None}


@router.post("/setup")
async def vault_setup(req: SetupRequest):
    """Setează master password (doar prima dată). Minim 8 caractere."""
    if len(req.master_password) < 8:
        raise HTTPException(400, "Parola trebuie să aibă minim 8 caractere")

    async with get_db() as db:
        cursor = await db.execute(
            "SELECT value FROM vault_config WHERE key = 'master_hash'"
        )
        if await cursor.fetchone():
            raise HTTPException(409, "Master password deja setat. Folosește /unlock.")

        salt = os.urandom(16)
        pw_hash = _hash_password(req.master_password, salt)

        await db.execute(
            "INSERT INTO vault_config (key, value) VALUES (?, ?)",
            ("master_salt", salt.hex()),
        )
        await db.execute(
            "INSERT INTO vault_config (key, value) VALUES (?, ?)",
            ("master_hash", pw_hash),
        )
        await db.commit()

    await log_activity(
        action="vault_setup",
        summary="Vault configurat cu master password",
    )
    return {"status": "configured"}


@router.post("/unlock")
async def vault_unlock(req: SetupRequest, request: Request):
    """Verifică master password. Returnează session token (30 min TTL).

    Rate limited: max 5 încercări per minut per IP.
    """
    client_ip = request.client.host if request.client else "unknown"

    # Rate limit check BEFORE password verification
    _check_rate_limit(client_ip)

    async with get_db() as db:
        cursor = await db.execute(
            "SELECT key, value FROM vault_config WHERE key IN ('master_hash', 'master_salt')"
        )
        rows = {row["key"]: row["value"] for row in await cursor.fetchall()}

    if "master_hash" not in rows:
        raise HTTPException(404, "Vault nu e configurat. Folosește /setup.")

    salt = bytes.fromhex(rows["master_salt"])
    expected_hash = rows["master_hash"]

    if _hash_password(req.master_password, salt) != expected_hash:
        _record_attempt(client_ip)
        raise HTTPException(401, "Parolă incorectă")

    # Successful unlock — create session token
    token = _create_session(req.master_password)

    return {"status": "unlocked", "session_token": token, "ttl_minutes": 30}


async def _verify_password(master_password: str) -> bytes:
    """Verifică parola și returnează salt-ul. Aruncă HTTPException dacă greșită."""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT key, value FROM vault_config WHERE key IN ('master_hash', 'master_salt')"
        )
        rows = {row["key"]: row["value"] for row in await cursor.fetchall()}

    if "master_hash" not in rows:
        raise HTTPException(404, "Vault nu e configurat")

    salt = bytes.fromhex(rows["master_salt"])
    if _hash_password(master_password, salt) != rows["master_hash"]:
        raise HTTPException(401, "Parolă incorectă")

    return salt


@router.get("/keys")
async def list_keys():
    """Lista cheilor stocate (fără valori decriptate)."""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT name, provider, created_at, updated_at FROM vault_keys ORDER BY name"
        )
        return [dict(row) for row in await cursor.fetchall()]


@router.post("/keys")
async def add_key(
    req: AddKeyRequest,
    x_master_password: Optional[str] = Header(default=None),
    x_vault_session: Optional[str] = Header(default=None),
):
    """Adaugă o cheie criptată în vault. Autentificare prin parolă sau session token."""
    master_pw = _resolve_master_password(x_master_password, x_vault_session)
    salt = await _verify_password(master_pw)

    fernet_key = _derive_key(master_pw, salt)
    fernet = Fernet(fernet_key)
    encrypted = fernet.encrypt(req.value.encode()).decode()

    async with get_db() as db:
        try:
            await db.execute(
                "INSERT INTO vault_keys (name, provider, encrypted_value, salt) "
                "VALUES (?, ?, ?, ?)",
                (req.name, req.provider, encrypted, salt.hex()),
            )
            await db.commit()
        except Exception:
            # Dacă numele există deja, update
            await db.execute(
                "UPDATE vault_keys SET encrypted_value = ?, provider = ?, "
                "salt = ?, updated_at = CURRENT_TIMESTAMP WHERE name = ?",
                (encrypted, req.provider, salt.hex(), req.name),
            )
            await db.commit()

    warning = _validate_key_format(req.provider, req.value)

    await log_activity(
        action="vault_add_key",
        summary=f"Cheie API adăugată: {req.name} ({req.provider})",
        details={"name": req.name, "provider": req.provider},
    )
    result = {"status": "stored", "name": req.name}
    if warning:
        result["warning"] = warning
    return result


@router.get("/keys/{name}")
async def get_key(
    name: str,
    x_master_password: Optional[str] = Header(default=None),
    x_vault_session: Optional[str] = Header(default=None),
):
    """Decriptează și returnează valoarea unei chei. Autentificare prin parolă sau session token."""
    master_pw = _resolve_master_password(x_master_password, x_vault_session)
    salt = await _verify_password(master_pw)

    async with get_db() as db:
        cursor = await db.execute(
            "SELECT encrypted_value FROM vault_keys WHERE name = ?", (name,)
        )
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(404, f"Cheia '{name}' nu există")

    fernet_key = _derive_key(master_pw, salt)
    fernet = Fernet(fernet_key)

    try:
        decrypted = fernet.decrypt(row["encrypted_value"].encode()).decode()
    except InvalidToken:
        raise HTTPException(500, "Eroare decriptare — datele pot fi corupte")

    return {"name": name, "value": decrypted}


@router.delete("/keys/{name}")
async def delete_key(
    name: str,
    confirm: bool = Query(default=False, description="Trebuie True pentru confirmare ștergere"),
    x_master_password: Optional[str] = Header(default=None),
    x_vault_session: Optional[str] = Header(default=None),
):
    """Șterge o cheie din vault. Necesită confirm=true ca protecție la ștergeri accidentale."""
    if not confirm:
        raise HTTPException(
            400,
            "Ești sigur? Adaugă ?confirm=true pentru a confirma ștergerea cheii."
        )

    master_pw = _resolve_master_password(x_master_password, x_vault_session)
    await _verify_password(master_pw)

    async with get_db() as db:
        cursor = await db.execute(
            "SELECT id FROM vault_keys WHERE name = ?", (name,)
        )
        if not await cursor.fetchone():
            raise HTTPException(404, f"Cheia '{name}' nu există")

        await db.execute("DELETE FROM vault_keys WHERE name = ?", (name,))
        await db.commit()

    await log_activity(
        action="vault_delete_key",
        summary=f"Cheie API ștearsă: {name}",
        details={"name": name},
    )
    return {"status": "deleted", "name": name}


@router.post("/keys/{name}/test")
async def test_key(
    name: str,
    x_master_password: Optional[str] = Header(default=None),
    x_vault_session: Optional[str] = Header(default=None),
):
    """Testează validitatea unei chei API la provider-ul corespunzător.

    Decriptează cheia și face o cerere de test (ex: listare modele) la provider.
    Suportă: gemini, openai, deepl, groq, cerebras, mistral.
    Returnează {"valid": true/false, "message": "..."}.
    """
    master_pw = _resolve_master_password(x_master_password, x_vault_session)
    salt = await _verify_password(master_pw)

    # Fetch key details (encrypted_value + provider)
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT encrypted_value, provider FROM vault_keys WHERE name = ?", (name,)
        )
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(404, f"Cheia '{name}' nu există")

    # Decrypt the key
    fernet_key = _derive_key(master_pw, salt)
    fernet = Fernet(fernet_key)
    try:
        api_key = fernet.decrypt(row["encrypted_value"].encode()).decode()
    except InvalidToken:
        raise HTTPException(500, "Eroare decriptare — datele pot fi corupte")

    provider = row["provider"].lower()

    # Find matching test config
    test_config = None
    for key, config in _KEY_TEST_URLS.items():
        if key in provider:
            test_config = config
            break

    if not test_config:
        return {
            "valid": False,
            "message": f"Provider '{row['provider']}' nu are test configurabil. "
                       f"Suportați: {', '.join(_KEY_TEST_URLS.keys())}",
        }

    # Build request
    url = test_config["url"]
    headers: dict[str, str] = {}
    params: dict[str, str] = {}

    auth_type = test_config["auth_type"]
    if auth_type == "bearer":
        headers["Authorization"] = f"Bearer {api_key}"
    elif auth_type == "header":
        headers[test_config["header_name"]] = api_key
    elif auth_type == "query_param":
        params[test_config["param_name"]] = api_key

    # Make test request
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers=headers, params=params)

        if resp.status_code == 200:
            await log_activity(
                action="vault_test_key",
                summary=f"Cheie API testată OK: {name} ({row['provider']})",
                details={"name": name, "provider": row["provider"], "valid": True},
            )
            return {"valid": True, "message": f"Cheia '{name}' este validă ({row['provider']})."}
        elif resp.status_code in (401, 403):
            return {"valid": False, "message": f"Cheie invalidă sau expirată (HTTP {resp.status_code})."}
        else:
            return {
                "valid": False,
                "message": f"Răspuns neașteptat de la {row['provider']}: HTTP {resp.status_code}.",
            }
    except httpx.TimeoutException:
        return {"valid": False, "message": f"Timeout (10s) la testarea cheii cu {row['provider']}."}
    except httpx.RequestError as exc:
        return {"valid": False, "message": f"Eroare conexiune la {row['provider']}: {exc}"}
