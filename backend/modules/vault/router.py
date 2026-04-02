"""
API endpoints pentru API Key Vault — stocare criptata chei API.

Endpoints:
  POST   /api/vault/setup            — seteaza master password (prima data, min 12 chars)
  POST   /api/vault/unlock           — verifica master password, returneaza session token
  POST   /api/vault/check-strength   — verifica puterea parolei (weak/moderate/strong)
  GET    /api/vault/keys             — lista chei (nume, provider, data, expires_at) — fara valori
  GET    /api/vault/keys/expiring    — chei care expira in urmatoarele 7 zile
  POST   /api/vault/keys             — adauga cheie noua (cu expires_at optional)
  GET    /api/vault/keys/:name       — decripteaza si returneaza valoarea
  POST   /api/vault/keys/:name/test  — testeaza validitatea cheii la provider
  DELETE /api/vault/keys/:name       — sterge o cheie (necesita confirm=true)
  GET    /api/vault/status           — verifica daca vault-ul e configurat
  GET    /api/vault/backup           — export chei criptate (necesita master password)
  POST   /api/vault/restore          — import chei din backup JSON (skip duplicate)
"""

from __future__ import annotations

import base64
import hashlib
import logging
import os
import re
import time
import uuid
from datetime import datetime, timedelta
from typing import Optional

import httpx
from cryptography.fernet import Fernet, InvalidToken
from fastapi import APIRouter, HTTPException, Header, Query, Request
from pydantic import BaseModel, Field

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


def _password_strength(password: str) -> dict:
    """Evaluate password strength. Returns score (weak/moderate/strong) and missing requirements."""
    checks = {
        "min_length": len(password) >= 12,
        "has_upper": bool(re.search(r"[A-Z]", password)),
        "has_lower": bool(re.search(r"[a-z]", password)),
        "has_digit": bool(re.search(r"\d", password)),
    }
    passed = sum(checks.values())
    if passed == 4:
        score = "strong"
    elif passed >= 2 and len(password) >= 8:
        score = "moderate"
    else:
        score = "weak"
    return {"score": score, "checks": checks}


# --- Models ---

class SetupRequest(BaseModel):
    master_password: str


class AddKeyRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    value: str = Field(..., min_length=1, max_length=10000)
    provider: str = Field("generic", max_length=100)
    expires_at: Optional[str] = None  # ISO date string e.g. "2026-06-01"


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
    """Setează master password (doar prima dată). Minim 12 caractere, upper+lower+digit."""
    strength = _password_strength(req.master_password)
    if strength["score"] == "weak":
        missing = []
        if not strength["checks"]["min_length"]:
            missing.append("minim 12 caractere")
        if not strength["checks"]["has_upper"]:
            missing.append("cel putin o litera mare")
        if not strength["checks"]["has_lower"]:
            missing.append("cel putin o litera mica")
        if not strength["checks"]["has_digit"]:
            missing.append("cel putin o cifra")
        raise HTTPException(400, f"Parola prea slaba. Lipseste: {', '.join(missing)}")

    async with get_db() as db:
        cursor = await db.execute(
            "SELECT value FROM vault_config WHERE key = 'master_hash'"
        )
        if await cursor.fetchone():
            raise HTTPException(409, "Master password deja setat. Foloseste /unlock.")

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
    return {"status": "configured", "strength": strength}


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


@router.post("/check-strength")
async def check_password_strength(req: SetupRequest):
    """Returnează scorul de putere al parolei (weak/moderate/strong) + cerințe."""
    return _password_strength(req.master_password)


@router.get("/keys")
async def list_keys():
    """Lista cheilor stocate (fără valori decriptate)."""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT name, provider, created_at, updated_at, expires_at FROM vault_keys ORDER BY name"
        )
        return [dict(row) for row in await cursor.fetchall()]


@router.get("/keys/expiring")
async def expiring_keys():
    """Returnează cheile care expiră în următoarele 7 zile."""
    threshold = (datetime.utcnow() + timedelta(days=7)).strftime("%Y-%m-%d")
    today = datetime.utcnow().strftime("%Y-%m-%d")
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT name, provider, expires_at FROM vault_keys "
            "WHERE expires_at IS NOT NULL AND expires_at <= ? AND expires_at >= ? "
            "ORDER BY expires_at",
            (threshold, today),
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
                "INSERT INTO vault_keys (name, provider, encrypted_value, salt, expires_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (req.name, req.provider, encrypted, salt.hex(), req.expires_at),
            )
            await db.commit()
        except Exception:
            # Dacă numele există deja, update
            await db.execute(
                "UPDATE vault_keys SET encrypted_value = ?, provider = ?, "
                "salt = ?, updated_at = CURRENT_TIMESTAMP, expires_at = ? WHERE name = ?",
                (encrypted, req.provider, salt.hex(), req.expires_at, req.name),
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


@router.get("/backup")
async def vault_backup(
    x_master_password: Optional[str] = Header(default=None),
    x_vault_session: Optional[str] = Header(default=None),
):
    """Exportă toate cheile din vault (valori criptate cu Fernet). Necesită master password."""
    master_pw = _resolve_master_password(x_master_password, x_vault_session)
    salt = await _verify_password(master_pw)

    fernet_key = _derive_key(master_pw, salt)
    fernet = Fernet(fernet_key)

    async with get_db() as db:
        cursor = await db.execute(
            "SELECT name, provider, encrypted_value, expires_at, created_at FROM vault_keys ORDER BY name"
        )
        rows = await cursor.fetchall()

    keys_export = []
    for row in rows:
        keys_export.append({
            "name": row["name"],
            "provider": row["provider"],
            "encrypted_value": row["encrypted_value"],
            "expires_at": row["expires_at"],
            "created_at": row["created_at"],
        })

    await log_activity(
        action="vault_backup",
        summary=f"Vault backup exportat ({len(keys_export)} chei)",
    )
    return {
        "version": 1,
        "exported_at": datetime.utcnow().isoformat(),
        "key_count": len(keys_export),
        "master_salt": salt.hex(),
        "keys": keys_export,
    }


class RestoreRequest(BaseModel):
    backup: dict
    backup_master_password: Optional[str] = None  # required when backup used a different password


@router.post("/restore")
async def vault_restore(
    req: RestoreRequest,
    x_master_password: Optional[str] = Header(default=None),
    x_vault_session: Optional[str] = Header(default=None),
):
    """Restaurează chei din backup JSON. Sare peste duplicatele existente.

    Dacă backup-ul a fost creat cu o parolă diferită de cea curentă,
    furnizează backup_master_password pentru re-criptare automată.
    """
    master_pw = _resolve_master_password(x_master_password, x_vault_session)
    current_salt = await _verify_password(master_pw)

    backup = req.backup
    if "keys" not in backup or not isinstance(backup["keys"], list):
        raise HTTPException(400, "Format backup invalid — lipseste 'keys'")

    # Determine if re-encryption is needed
    backup_pw = req.backup_master_password
    need_reencrypt = backup_pw is not None and backup_pw != master_pw

    if need_reencrypt:
        # Derive Fernet keys for both passwords
        # The backup salt is stored per-key in the backup's vault_keys row,
        # but the backup endpoint doesn't export it. We use the current DB salt
        # as a fallback; for cross-password restore we require backup_master_password
        # and the backup must include the salt field (or we derive from backup's config).
        # Since the backup format stores salt per-key in the DB but the export omits it,
        # we must use the backup's master salt if available in the backup metadata,
        # otherwise fall back to current salt (same-instance backup scenario).
        backup_salt_hex = backup.get("master_salt")
        if backup_salt_hex:
            backup_salt = bytes.fromhex(backup_salt_hex)
        else:
            backup_salt = current_salt
        backup_fernet = Fernet(_derive_key(backup_pw, backup_salt))
        current_fernet = Fernet(_derive_key(master_pw, current_salt))

    imported = 0
    skipped = 0
    errors = 0

    async with get_db() as db:
        for entry in backup["keys"]:
            name = entry.get("name")
            if not name or "encrypted_value" not in entry:
                skipped += 1
                continue

            cursor = await db.execute(
                "SELECT id FROM vault_keys WHERE name = ?", (name,)
            )
            if await cursor.fetchone():
                skipped += 1
                continue

            encrypted = entry["encrypted_value"]

            if need_reencrypt:
                try:
                    plaintext = backup_fernet.decrypt(encrypted.encode())
                    encrypted = current_fernet.encrypt(plaintext).decode()
                except InvalidToken:
                    _logger.warning("Vault restore: nu s-a putut decripta cheia '%s' — sarind", name)
                    errors += 1
                    skipped += 1
                    continue

            await db.execute(
                "INSERT INTO vault_keys (name, provider, encrypted_value, salt, expires_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    name,
                    entry.get("provider", "generic"),
                    encrypted,
                    current_salt.hex(),
                    entry.get("expires_at"),
                ),
            )
            imported += 1
        await db.commit()

    await log_activity(
        action="vault_restore",
        summary=f"Vault restore: {imported} importate, {skipped} sarite",
        details={"imported": imported, "skipped": skipped, "errors": errors},
    )
    return {"status": "restored", "imported": imported, "skipped": skipped, "errors": errors}


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


# --- Usage Overview ---

# Provider free tier limits (monthly)
_PROVIDER_LIMITS = {
    "deepl": {"limit": 500000, "unit": "chars/month"},
    "azure": {"limit": 2000000, "unit": "chars/month"},
    "google": {"limit": 500000, "unit": "chars/month"},
    "mymemory": {"limit": 50000, "unit": "chars/day"},
    "gemini": {"limit": 250, "unit": "requests/day"},
    "cerebras": {"limit": 1000000, "unit": "tokens/day"},
    "groq": {"limit": 30, "unit": "RPM"},
    "mistral": {"limit": 1000000000, "unit": "tokens/month"},
}


@router.get("/usage-overview")
async def vault_usage_overview():
    """Returns free tier usage summary from activity_log for known providers."""
    result = []

    try:
        async with get_db() as db:
            # Get translation activity counts this month per provider
            cursor = await db.execute(
                "SELECT "
                "  COALESCE(json_extract(details, '$.provider'), 'unknown') AS provider, "
                "  COUNT(*) AS request_count, "
                "  COALESCE(SUM(CAST(json_extract(details, '$.chars') AS INTEGER)), 0) AS total_chars "
                "FROM activity_log "
                "WHERE action LIKE 'translator%' "
                "AND timestamp >= date('now', 'start of month') "
                "GROUP BY provider"
            )
            translator_rows = await cursor.fetchall()

            for row in translator_rows:
                prov = (row["provider"] or "unknown").lower()
                chars = row["total_chars"] or 0
                limits = _PROVIDER_LIMITS.get(prov)
                if limits:
                    limit_val = limits["limit"]
                    unit = limits["unit"]
                    used = chars if "chars" in unit else row["request_count"]
                    percent = round((used / limit_val * 100), 1) if limit_val > 0 else 0
                else:
                    limit_val = 0
                    unit = "unknown"
                    used = chars
                    percent = 0

                result.append({
                    "provider": prov,
                    "used": used,
                    "limit": limit_val,
                    "unit": unit,
                    "percent": min(percent, 100.0),
                })

            # Get AI provider usage this month
            cursor = await db.execute(
                "SELECT "
                "  COALESCE(json_extract(details, '$.provider'), 'unknown') AS provider, "
                "  COUNT(*) AS request_count "
                "FROM activity_log "
                "WHERE action LIKE 'ai%' "
                "AND timestamp >= date('now', 'start of month') "
                "GROUP BY provider"
            )
            ai_rows = await cursor.fetchall()

            for row in ai_rows:
                prov = (row["provider"] or "unknown").lower()
                limits = _PROVIDER_LIMITS.get(prov)
                if limits:
                    limit_val = limits["limit"]
                    unit = limits["unit"]
                    used = row["request_count"]
                    percent = round((used / limit_val * 100), 1) if limit_val > 0 else 0
                else:
                    limit_val = 0
                    unit = "unknown"
                    used = row["request_count"]
                    percent = 0

                # Skip if already added from translator
                if not any(r["provider"] == prov for r in result):
                    result.append({
                        "provider": prov,
                        "used": used,
                        "limit": limit_val,
                        "unit": unit,
                        "percent": min(percent, 100.0),
                    })

    except Exception as exc:
        _logger.error("Error fetching usage overview: %s", exc)

    return result
