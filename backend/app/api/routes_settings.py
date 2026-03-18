"""
Rute pentru gestionarea setărilor aplicației.

GET /api/settings — returnează toate setările
PUT /api/settings — actualizează setări
"""

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.activity_log import log_activity, get_activity_log
from app.db.database import get_db, get_setting, update_setting

router = APIRouter(prefix="/api", tags=["settings"])


class SettingsUpdate(BaseModel):
    """Schema pentru actualizarea setărilor."""
    invoice_percent: float | None = Field(
        None, ge=1, le=100,
        description="Procentul de facturare (1-100%)",
    )
    confidence_threshold: float | None = Field(
        None, ge=0, le=100,
        description="Pragul minim de încredere (0-100%)",
    )
    min_price: float | None = Field(
        None, ge=0,
        description="Prețul minim per document (RON)",
    )
    currency: str | None = Field(
        None, min_length=3, max_length=3,
        description="Moneda (cod ISO 3 litere)",
    )
    language: str | None = Field(
        None, min_length=2, max_length=5,
        description="Limba interfeței (ex: ro, en)",
    )


@router.get("/settings")
async def get_all_settings():
    """Returnează toate setările curente din baza de date."""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT key, value, updated_at FROM settings ORDER BY key"
        )
        rows = await cursor.fetchall()

    if not rows:
        # Returnează valorile implicite dacă tabelul e gol
        return {
            "settings": {
                "invoice_percent": 75.0,
                "confidence_threshold": 70.0,
                "min_price": 25.0,
                "currency": "RON",
                "language": "ro",
            },
            "message": "Setări implicite (baza de date nu conține valori).",
        }

    settings_dict: dict[str, Any] = {}
    metadata: dict[str, str] = {}
    for row in rows:
        key = row["key"]
        value = row["value"]
        # Conversie tipuri numerice
        if key in ("invoice_percent", "confidence_threshold", "min_price"):
            try:
                settings_dict[key] = float(value)
            except (ValueError, TypeError):
                settings_dict[key] = value
        else:
            settings_dict[key] = value
        metadata[key] = row["updated_at"]

    return {
        "settings": settings_dict,
        "last_updated": metadata,
    }


@router.put("/settings")
async def update_all_settings(updates: SettingsUpdate):
    """
    Actualizează una sau mai multe setări.

    Doar câmpurile furnizate (non-None) sunt actualizate.
    """
    update_data = updates.model_dump(exclude_none=True)

    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="Nu a fost furnizată nicio setare de actualizat.",
        )

    updated_keys = []
    for key, value in update_data.items():
        await update_setting(key, str(value))
        updated_keys.append(key)

    await log_activity(
        action="update_settings",
        summary=f"Setări modificate: {', '.join(updated_keys)}",
        details={"updated_keys": updated_keys, "updated_values": update_data},
    )

    return {
        "message": f"Setări actualizate: {', '.join(updated_keys)}.",
        "updated_keys": updated_keys,
        "updated_values": update_data,
    }


@router.get("/activity-log")
async def get_activity_log_endpoint(
    limit: int = Query(50, ge=1, le=1000, description="Numărul maxim de intrări"),
    action: str | None = Query(None, description="Filtrare după tip acțiune"),
):
    """
    Returnează logul de activitate al platformei (cele mai recente primele).

    Acțiuni posibile: upload, calculate, validate_price, calibrate,
    calibrate_revert, calibrate_reset, delete_history, update_settings.
    """
    entries = await get_activity_log(limit=limit, action_filter=action)
    return {
        "entries": entries,
        "total": len(entries),
        "limit": limit,
        "action_filter": action,
    }
