"""
Rute pentru calcularea prețului de traducere.

POST /api/calculate — analizează document, calculează preț, validează, salvează.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.config import settings
from app.core.activity_log import log_activity
from app.core.analyzer import extract_features
from app.core.pricing.ensemble import calculate_ensemble_price
from app.core.validation import validate_price
from app.core.self_learning import get_all_references, add_validated_price as sl_add_validated_price
from app.db.database import get_db, get_setting
from app.api.routes_quick_quote import get_language_coefficient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["price"])


class ValidatePriceRequest(BaseModel):
    """Schema pentru validarea unui preț de către utilizator."""
    upload_id: int = Field(..., description="ID-ul upload-ului")
    validated_price: float = Field(..., gt=0, description="Prețul validat de utilizator (RON)")


class ValidatePriceResponse(BaseModel):
    """Schema răspunsului la validarea prețului."""
    status: str
    action: str
    filename: str
    confirmed_price: float
    total_learned_references: int


class CalculateRequest(BaseModel):
    """Schema pentru cererea de calcul preț."""
    upload_id: int | None = Field(None, description="ID-ul din tabela uploads")
    file_path: str | None = Field(None, description="Calea directă către fișier")
    invoice_percent: float | None = Field(
        None,
        description="Procentul de facturare (implicit din setări)",
    )
    source_lang: str | None = Field(
        None,
        description="Limba sursă (cod ISO 2 litere) — pentru coeficient limbă",
    )
    target_lang: str | None = Field(
        None,
        description="Limba țintă (cod ISO 2 litere) — pentru coeficient limbă",
    )


class CalculateResponse(BaseModel):
    """Schema răspunsului de calcul preț."""
    calculation_id: int
    upload_id: int | None
    filename: str
    market_price: float
    base_price_before_dtp: float | None = None
    invoice_price: float
    invoice_percent: float
    currency: str
    confidence: float
    is_reliable: bool
    breakdown: dict[str, Any]
    dtp: dict[str, Any] | None = None
    method_details: list[dict[str, Any]]
    method_prices: dict[str, float]
    warnings: list[str]
    features: dict[str, Any]
    language_info: dict[str, Any] | None = None


@router.post("/calculate", response_model=CalculateResponse)
async def calculate_price(request: CalculateRequest):
    """
    Calculează prețul de traducere pentru un document.

    Pași:
    1. Localizează fișierul (prin upload_id sau file_path)
    2. Analizează documentul — extrage caracteristici
    3. Calculează prețul ensemble
    4. Validează rezultatul
    5. Salvează în baza de date
    6. Returnează rezultatul complet
    """
    # --- 1. Localizare fișier ---
    file_path, upload_id, filename = await _resolve_file(request)

    # --- Obține task_id pentru WebSocket ---
    task_id = str(upload_id) if upload_id else str(uuid.uuid4())

    # Importăm ws_manager aici pentru a evita circular imports
    from app.main import ws_manager

    # --- 2. Analiză document ---
    await ws_manager.send_progress(task_id, {
        "step": "analyzing",
        "progress": 20,
        "message": "Analizare document...",
    })

    try:
        features = extract_features(str(file_path))
    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Eroare la analiza documentului: {exc}",
        )

    # --- 3. Calcul preț ensemble ---
    await ws_manager.send_progress(task_id, {
        "step": "calculating",
        "progress": 50,
        "message": "Calcul preț...",
    })

    # Încarcă referințe și calibrare
    reference_data = _load_reference_data()
    calibration = _load_calibration_data()

    price_result = calculate_ensemble_price(
        features=features,
        reference_data=reference_data,
        calibration=calibration,
    )

    # --- 4. Validare ---
    await ws_manager.send_progress(task_id, {
        "step": "validating",
        "progress": 80,
        "message": "Validare rezultat...",
    })

    validation = validate_price(price_result, reference_data)

    # --- Coeficient limbă (dacă s-au specificat limbile) ---
    lang_info = None
    if request.source_lang and request.target_lang:
        lang_info = get_language_coefficient(request.source_lang, request.target_lang)

    # --- Calcul preț facturat ---
    invoice_percent = request.invoice_percent
    if invoice_percent is None:
        invoice_percent = await _get_invoice_percent()

    market_price = price_result["market_price"]

    # Aplică coeficient limbă dacă e cazul
    if lang_info and lang_info["applied"]:
        market_price = round(market_price * lang_info["effective_coefficient"], 2)

    invoice_price = round(market_price * (invoice_percent / 100.0), 2)

    confidence = validation.get("confidence", 0.0)
    is_reliable = confidence >= 70.0

    # --- 5. Salvare în DB ---
    if upload_id is None:
        # Dacă a fost furnizat file_path direct, creăm o intrare în uploads
        upload_id = await _create_upload_entry(file_path)

    calculation_id = await _save_calculation(
        upload_id=upload_id,
        market_price=market_price,
        invoice_price=invoice_price,
        invoice_percent=invoice_percent,
        confidence=confidence,
        features=features,
        method_details=price_result.get("methods", []),
        warnings=validation.get("warnings", []),
    )

    # --- 5b. Log activitate ---
    dtp_info = price_result.get("dtp")
    await log_activity(
        action="calculate",
        summary=f"{filename} → {market_price} RON (fact. {invoice_price} RON, {confidence}% încredere)",
        details={
            "filename": filename,
            "market_price": market_price,
            "invoice_price": invoice_price,
            "invoice_percent": invoice_percent,
            "confidence": confidence,
            "is_reliable": is_reliable,
            "dtp_level": dtp_info.get("level") if dtp_info else None,
            "dtp_factor": dtp_info.get("factor") if dtp_info else None,
            "method_prices": price_result.get("method_prices", {}),
            "warnings": validation.get("warnings", []),
            "features": {
                "page_count": features.get("page_count"),
                "word_count": features.get("word_count"),
                "image_count": features.get("image_count"),
                "table_count": features.get("table_count"),
            },
            "language_info": lang_info,
        },
    )

    # --- 6. Complet ---
    await ws_manager.send_progress(task_id, {
        "step": "complete",
        "progress": 100,
        "message": "Complet!",
    })

    return CalculateResponse(
        calculation_id=calculation_id,
        upload_id=upload_id,
        filename=filename,
        market_price=market_price,
        base_price_before_dtp=price_result.get("base_price_before_dtp"),
        invoice_price=invoice_price,
        invoice_percent=invoice_percent,
        currency="RON",
        confidence=confidence,
        is_reliable=is_reliable,
        breakdown=features,
        dtp=price_result.get("dtp"),
        method_details=price_result.get("methods", []),
        method_prices=price_result.get("method_prices", {}),
        warnings=validation.get("warnings", []),
        features=features,
        language_info=lang_info,
    )


@router.post("/validate-price", response_model=ValidatePriceResponse)
async def validate_price_endpoint(request: ValidatePriceRequest):
    """
    Salvează un preț validat de utilizator pentru auto-învățare.

    Caută upload-ul și ultimul calcul asociat, apoi transmite datele
    către modulul de self-learning.
    """
    # Obține detaliile upload-ului
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT id, filename, filepath FROM uploads WHERE id = ?",
            (request.upload_id,),
        )
        upload = await cursor.fetchone()

        if not upload:
            raise HTTPException(
                status_code=404,
                detail=f"Upload-ul cu ID {request.upload_id} nu a fost găsit.",
            )

        # Obține ultimul calcul pentru acest upload (pentru features și estimarea originală)
        cursor = await db.execute(
            "SELECT market_price, features FROM calculations WHERE upload_id = ? ORDER BY id DESC LIMIT 1",
            (request.upload_id,),
        )
        calc = await cursor.fetchone()

    features = {}
    original_estimate = None
    if calc:
        try:
            features = json.loads(calc["features"]) if calc["features"] else {}
        except (json.JSONDecodeError, TypeError):
            features = {}
        original_estimate = calc["market_price"]

    result = await asyncio.to_thread(
        sl_add_validated_price,
        filename=upload["filename"],
        features=features,
        confirmed_price=request.validated_price,
        original_estimate=original_estimate,
    )

    await log_activity(
        action="validate_price",
        summary=f"{upload['filename']} → validat la {request.validated_price} RON (estimare: {original_estimate})",
        details={
            "filename": upload["filename"],
            "validated_price": request.validated_price,
            "original_estimate": original_estimate,
            "error_percent": result.get("error_percent"),
            "total_learned": result["total_learned_references"],
        },
    )

    return ValidatePriceResponse(
        status=result["status"],
        action=result["action"],
        filename=result["filename"],
        confirmed_price=result["confirmed_price"],
        total_learned_references=result["total_learned_references"],
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _resolve_file(
    request: CalculateRequest,
) -> tuple[Path, int | None, str]:
    """
    Rezolvă calea completă către fișier din upload_id sau file_path.

    Returns:
        (file_path, upload_id, filename)
    """
    if request.upload_id:
        async with get_db() as db:
            cursor = await db.execute(
                "SELECT id, filename, filepath FROM uploads WHERE id = ?",
                (request.upload_id,),
            )
            row = await cursor.fetchone()

        if not row:
            raise HTTPException(
                status_code=404,
                detail=f"Upload-ul cu ID {request.upload_id} nu a fost găsit.",
            )

        path = Path(row["filepath"])
        if not path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Fișierul '{row['filename']}' nu mai există pe disc.",
            )
        return path, row["id"], row["filename"]

    if request.file_path:
        path = Path(request.file_path)
        if not path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Fișierul nu a fost găsit: {request.file_path}",
            )
        return path, None, path.name

    raise HTTPException(
        status_code=400,
        detail="Trebuie să furnizați upload_id sau file_path.",
    )


def _load_reference_data() -> list[dict[str, Any]]:
    """Încarcă toate datele de referință (originale + învățate)."""
    try:
        return get_all_references(include_learned=True)
    except Exception:
        return []


_calibration_cache: dict = {"data": None, "mtime": 0.0}


def _load_calibration_data() -> dict[str, Any] | None:
    """Încarcă datele de calibrare din fișierul JSON, dacă există. Cached until file changes."""
    cal_file = settings.calibration_file
    if not cal_file.exists():
        return None
    try:
        current_mtime = cal_file.stat().st_mtime
        if _calibration_cache["data"] is not None and current_mtime == _calibration_cache["mtime"]:
            return _calibration_cache["data"]
        with open(cal_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        result = data.get("calibration", data)
        _calibration_cache["data"] = result
        _calibration_cache["mtime"] = current_mtime
        return result
    except (json.JSONDecodeError, OSError):
        return None


async def _get_invoice_percent() -> float:
    """Obține procentul de facturare din setările bazei de date."""
    try:
        value = await get_setting("invoice_percent")
        if value:
            return float(value)
    except Exception:
        pass
    return settings.default_invoice_percent


async def _create_upload_entry(file_path: Path) -> int:
    """Creează o intrare în tabela uploads pentru un fișier dat direct prin cale."""
    ext = file_path.suffix.lower().lstrip(".")
    file_type = ext if ext in ("pdf", "docx") else "pdf"
    file_size = file_path.stat().st_size

    async with get_db() as db:
        cursor = await db.execute(
            """
            INSERT INTO uploads (filename, filepath, file_type, file_size)
            VALUES (?, ?, ?, ?)
            """,
            (file_path.name, str(file_path), file_type, file_size),
        )
        await db.commit()
        return cursor.lastrowid


async def _save_calculation(
    upload_id: int,
    market_price: float,
    invoice_price: float,
    invoice_percent: float,
    confidence: float,
    features: dict,
    method_details: list,
    warnings: list,
) -> int:
    """Salvează calculul în baza de date și returnează ID-ul."""
    async with get_db() as db:
        cursor = await db.execute(
            """
            INSERT INTO calculations
                (upload_id, market_price, invoice_price, invoice_percent,
                 confidence, features, method_details, warnings)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                upload_id,
                market_price,
                invoice_price,
                invoice_percent,
                confidence,
                json.dumps(features, ensure_ascii=False),
                json.dumps(method_details, ensure_ascii=False),
                json.dumps(warnings, ensure_ascii=False),
            ),
        )
        await db.commit()
        return cursor.lastrowid
