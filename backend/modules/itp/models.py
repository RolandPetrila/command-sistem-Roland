"""
Pydantic models, constants, and shared helpers for the ITP module.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Optional

from fastapi import HTTPException
from pydantic import BaseModel, model_validator


# ────────── Constants ──────────

# Directory for ITP inspection photos
ITP_PHOTOS_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "itp_photos"
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_PHOTO_SIZE = 5 * 1024 * 1024  # 5 MB
MAX_PHOTOS_PER_INSPECTION = 5

STANDARD_REJECTION_REASONS = [
    {"id": 1, "code": "EMISII", "description": "Emisii peste limita"},
    {"id": 2, "code": "FRANARE", "description": "Sistem de franare defect"},
    {"id": 3, "code": "DIRECTIE", "description": "Directie cu joc excesiv"},
    {"id": 4, "code": "SUSPENSIE", "description": "Suspensie deteriorata"},
    {"id": 5, "code": "ANVELOPE", "description": "Anvelope uzate/neconforme"},
    {"id": 6, "code": "LUMINI", "description": "Faruri/lumini defecte"},
    {"id": 7, "code": "CAROSERIE", "description": "Caroserie corodata"},
    {"id": 8, "code": "SCURGERI", "description": "Scurgeri ulei/lichid frana"},
    {"id": 9, "code": "OGLINZI", "description": "Oglinzi lipsa/deteriorate"},
    {"id": 10, "code": "CENTURI", "description": "Centuri de siguranta defecte"},
]

# Allowed appointment status transitions (state machine)
APPOINTMENT_TRANSITIONS: dict[str, list[str]] = {
    "scheduled":  ["confirmed", "cancelled"],
    "confirmed":  ["checked_in", "cancelled"],
    "checked_in": ["completed", "no_show", "cancelled"],
    "completed":  [],   # terminal state
    "cancelled":  [],   # terminal state
    "no_show":    [],   # terminal state
}

MONTH_NAMES = [
    "", "Ian", "Feb", "Mar", "Apr", "Mai", "Iun",
    "Iul", "Aug", "Sep", "Oct", "Nov", "Dec",
]


# ────────── Pydantic Models ──────────

class InspectionCreate(BaseModel):
    plate_number: str
    vin: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    fuel_type: Optional[str] = None
    owner_name: Optional[str] = None
    owner_phone: Optional[str] = None
    inspection_date: str
    expiry_date: str
    result: str  # admis / respins
    rejection_reasons: Optional[str] = None  # JSON array string
    price: float = 0
    inspector_name: Optional[str] = None
    notes: Optional[str] = None

    @model_validator(mode="after")
    def validate_rejection_reasons(self):
        """If result is 'Respins', rejection_reasons must be non-empty."""
        result_lower = (self.result or "").strip().lower()
        if result_lower == "respins":
            rr = self.rejection_reasons
            if not rr or rr in ("[]", "null", ""):
                raise ValueError(
                    "Motivele de respingere sunt obligatorii cand rezultatul este 'Respins'"
                )
            # Also validate if it's a JSON array
            try:
                parsed = json.loads(rr) if isinstance(rr, str) else rr
                if isinstance(parsed, list) and len(parsed) == 0:
                    raise ValueError(
                        "Motivele de respingere sunt obligatorii cand rezultatul este 'Respins'"
                    )
            except (json.JSONDecodeError, TypeError):
                pass  # Not JSON — treat as plain text, already non-empty
        return self


class InspectionUpdate(BaseModel):
    plate_number: Optional[str] = None
    vin: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    fuel_type: Optional[str] = None
    owner_name: Optional[str] = None
    owner_phone: Optional[str] = None
    inspection_date: Optional[str] = None
    expiry_date: Optional[str] = None
    result: Optional[str] = None
    rejection_reasons: Optional[str] = None
    price: Optional[float] = None
    inspector_name: Optional[str] = None
    notes: Optional[str] = None


class AppointmentCreate(BaseModel):
    plate_number: str
    owner_name: Optional[str] = None
    owner_phone: Optional[str] = None
    scheduled_date: str
    scheduled_time: str = "08:00"
    duration_min: int = 30
    notes: Optional[str] = None


class AppointmentUpdate(BaseModel):
    plate_number: Optional[str] = None
    owner_name: Optional[str] = None
    owner_phone: Optional[str] = None
    scheduled_date: Optional[str] = None
    scheduled_time: Optional[str] = None
    duration_min: Optional[int] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class MarkShowupRequest(BaseModel):
    showed_up: bool


# ────────── Shared Helpers ──────────

def row_dict(row) -> dict:
    """Convert an aiosqlite Row to a plain dict."""
    return dict(row)


def validate_appointment_transition(current: str, new: str) -> None:
    """Raise HTTP 400 if the status transition is not allowed."""
    allowed = APPOINTMENT_TRANSITIONS.get(current, [])
    if new not in allowed:
        if allowed:
            allowed_str = ", ".join(f"'{s}'" for s in allowed)
            raise HTTPException(
                400,
                f"Tranzitie invalida: '{current}' → '{new}'. "
                f"Din starea '{current}' sunt permise doar: {allowed_str}.",
            )
        else:
            raise HTTPException(
                400,
                f"Programarea este in starea finala '{current}' si nu mai poate fi modificata.",
            )


def next_inspection_date(last_date_str: str, vehicle_type: str = "car") -> date | None:
    """Calculate next inspection date from last inspection.

    Cars: 12 months, Commercial vehicles: 6 months.
    """
    try:
        last = date.fromisoformat(last_date_str)
    except (ValueError, TypeError):
        return None
    months = 6 if vehicle_type == "commercial" else 12
    # Add months: handle year/month overflow
    year = last.year + (last.month + months - 1) // 12
    month = (last.month + months - 1) % 12 + 1
    day = min(last.day, 28)  # Safe day for all months
    return date(year, month, day)
