"""
API endpoints pentru API Key Vault — stocare criptată chei API.

Endpoints:
  POST   /api/vault/setup        — setează master password (prima dată)
  POST   /api/vault/unlock       — verifică master password
  GET    /api/vault/keys         — lista chei (nume, provider, dată) — fără valori
  POST   /api/vault/keys         — adaugă cheie nouă
  GET    /api/vault/keys/:name   — decriptează și returnează valoarea
  DELETE /api/vault/keys/:name   — șterge o cheie
  GET    /api/vault/status       — verifică dacă vault-ul e configurat
"""

from __future__ import annotations

import base64
import hashlib
import logging
import os
import re

from cryptography.fernet import Fernet, InvalidToken
from fastapi import APIRouter, HTTPException, Header
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
    """Setează master password (doar prima dată)."""
    if len(req.master_password) < 4:
        raise HTTPException(400, "Parola trebuie să aibă minim 4 caractere")

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
async def vault_unlock(req: SetupRequest):
    """Verifică master password."""
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
        raise HTTPException(401, "Parolă incorectă")

    return {"status": "unlocked"}


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
async def add_key(req: AddKeyRequest, x_master_password: str = Header()):
    """Adaugă o cheie criptată în vault."""
    salt = await _verify_password(x_master_password)

    fernet_key = _derive_key(x_master_password, salt)
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
async def get_key(name: str, x_master_password: str = Header()):
    """Decriptează și returnează valoarea unei chei."""
    salt = await _verify_password(x_master_password)

    async with get_db() as db:
        cursor = await db.execute(
            "SELECT encrypted_value FROM vault_keys WHERE name = ?", (name,)
        )
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(404, f"Cheia '{name}' nu există")

    fernet_key = _derive_key(x_master_password, salt)
    fernet = Fernet(fernet_key)

    try:
        decrypted = fernet.decrypt(row["encrypted_value"].encode()).decode()
    except InvalidToken:
        raise HTTPException(500, "Eroare decriptare — datele pot fi corupte")

    return {"name": name, "value": decrypted}


@router.delete("/keys/{name}")
async def delete_key(name: str, x_master_password: str = Header()):
    """Șterge o cheie din vault."""
    await _verify_password(x_master_password)

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
