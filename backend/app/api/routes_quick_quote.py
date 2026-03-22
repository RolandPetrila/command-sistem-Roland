"""
Rute extinse calculator: quick-quote, generare factura, templates, coeficienti limba.

POST   /api/calculator/quick-quote                    -- Estimare pret fara upload
POST   /api/calculator/create-invoice-from-calculation -- Pre-fill date factura din calcul
GET    /api/calculator/templates                       -- Lista template-uri salvate
POST   /api/calculator/templates                       -- Salvare template nou
DELETE /api/calculator/templates/{id}                   -- Stergere template
GET    /api/calculator/language-coefficients            -- Coeficienti pret per limba
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.config import settings
from app.core.activity_log import log_activity
from app.core.calibration_cache import load_calibration_data
from app.core.pricing.ensemble import calculate_ensemble_price
from app.core.self_learning import get_all_references
from app.core.validation import validate_price
from app.db.database import get_db, get_setting

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/calculator", tags=["calculator-extended"])


# ---------------------------------------------------------------------------
# Language coefficients — pret diferit per limba
# ---------------------------------------------------------------------------

LANGUAGE_COEFFICIENTS: dict[str, float] = {
    "de": 1.15,   # Germana — complexitate gramaticala ridicata
    "fr": 1.10,   # Franceza
    "it": 1.10,   # Italiana
    "es": 1.05,   # Spaniola
    "en": 1.0,    # Engleza — limba de baza
    "ro": 1.0,    # Romana — limba de baza
    "nl": 1.10,   # Olandeza
    "pt": 1.05,   # Portugheza
    "pl": 1.10,   # Poloneza
    "hu": 1.15,   # Maghiara — complexitate ridicata
    "ja": 1.25,   # Japoneza — limbi asiatice
    "zh": 1.25,   # Chineza
    "ko": 1.20,   # Coreeana
    "ar": 1.20,   # Araba — RTL + complexitate
    "ru": 1.10,   # Rusa
}


def get_language_coefficient(source_lang: str, target_lang: str) -> dict[str, Any]:
    """
    Calculeaza coeficientul de limba pe baza perechii source/target.

    Se aplica coeficientul maxim dintre cele doua limbi.
    Daca ambele sunt 1.0, nu se aplica nicio majorare.
    """
    src = source_lang.lower().strip()[:2]
    tgt = target_lang.lower().strip()[:2]

    src_coef = LANGUAGE_COEFFICIENTS.get(src, 1.0)
    tgt_coef = LANGUAGE_COEFFICIENTS.get(tgt, 1.0)

    # Se aplica coeficientul maxim (nu se cumuleaza)
    effective_coef = max(src_coef, tgt_coef)

    return {
        "source_lang": src,
        "target_lang": tgt,
        "source_coefficient": src_coef,
        "target_coefficient": tgt_coef,
        "effective_coefficient": effective_coef,
        "applied": effective_coef > 1.0,
    }


# ---------------------------------------------------------------------------
# Complexity presets — mapping document_type + complexity to features
# ---------------------------------------------------------------------------

DOCUMENT_TYPE_DEFAULTS: dict[str, dict[str, Any]] = {
    "general": {
        "layout_complexity": 1,
        "image_count": 0,
        "table_count": 0,
        "has_complex_tables": False,
        "has_diagrams": False,
        "chart_count": 0,
        "is_scanned": False,
        "text_density": 0.9,
    },
    "technical": {
        "layout_complexity": 3,
        "image_count": 2,
        "table_count": 2,
        "has_complex_tables": True,
        "has_diagrams": True,
        "chart_count": 1,
        "is_scanned": False,
        "text_density": 0.7,
    },
    "legal": {
        "layout_complexity": 2,
        "image_count": 0,
        "table_count": 1,
        "has_complex_tables": False,
        "has_diagrams": False,
        "chart_count": 0,
        "is_scanned": False,
        "text_density": 0.95,
    },
    "medical": {
        "layout_complexity": 3,
        "image_count": 1,
        "table_count": 3,
        "has_complex_tables": True,
        "has_diagrams": True,
        "chart_count": 0,
        "is_scanned": False,
        "text_density": 0.75,
    },
    "marketing": {
        "layout_complexity": 4,
        "image_count": 5,
        "table_count": 0,
        "has_complex_tables": False,
        "has_diagrams": False,
        "chart_count": 0,
        "is_scanned": False,
        "text_density": 0.5,
    },
    "certificate": {
        "layout_complexity": 2,
        "image_count": 1,
        "table_count": 0,
        "has_complex_tables": False,
        "has_diagrams": False,
        "chart_count": 0,
        "is_scanned": False,
        "text_density": 0.6,
    },
    "financial": {
        "layout_complexity": 3,
        "image_count": 0,
        "table_count": 5,
        "has_complex_tables": True,
        "has_diagrams": False,
        "chart_count": 2,
        "is_scanned": False,
        "text_density": 0.65,
    },
}

COMPLEXITY_LAYOUT_MAP: dict[str, int] = {
    "low": 1,
    "medium": 2,
    "high": 4,
}


# ---------------------------------------------------------------------------
# Helpers — shared with routes_price.py
# ---------------------------------------------------------------------------

def _load_reference_data() -> list[dict[str, Any]]:
    """Incarca toate datele de referinta (originale + invatate)."""
    try:
        return get_all_references(include_learned=True)
    except Exception:
        return []


def _load_calibration_data() -> dict[str, Any] | None:
    """Shared calibration loader — delegates to calibration_cache module."""
    return load_calibration_data()


async def _get_invoice_percent() -> float:
    """Obtine procentul de facturare din setarile bazei de date."""
    try:
        value = await get_setting("invoice_percent")
        if value:
            return float(value)
    except Exception:
        pass
    return settings.default_invoice_percent


def _build_synthetic_features(
    word_count: int,
    document_type: str,
    complexity: str,
) -> dict[str, Any]:
    """
    Construieste un dict de features sintetic pe baza word_count,
    document_type si complexity — fara sa fie nevoie de fisier uploadat.
    """
    words_per_page = 250  # medie standard
    page_count = max(1, round(word_count / words_per_page))

    # Ia defaults per document type
    type_defaults = DOCUMENT_TYPE_DEFAULTS.get(
        document_type.lower(),
        DOCUMENT_TYPE_DEFAULTS["general"],
    )

    # Ajusteaza layout_complexity pe baza complexity
    complexity_layout = COMPLEXITY_LAYOUT_MAP.get(complexity.lower(), 2)
    base_layout = type_defaults["layout_complexity"]
    # Folosim maximul intre tipul documentului si complexitatea specificata
    effective_layout = max(base_layout, complexity_layout)

    features: dict[str, Any] = {
        "page_count": page_count,
        "word_count": word_count,
        "words_per_page": words_per_page,
        # R2-4: image_count from defaults is per-page estimate; scale
        # proportionally but cap to avoid overpricing on long documents
        "image_count": type_defaults["image_count"] * min(page_count, 5),
        "table_count": type_defaults["table_count"],
        "has_complex_tables": type_defaults["has_complex_tables"],
        "chart_count": type_defaults["chart_count"],
        "has_diagrams": type_defaults["has_diagrams"],
        "layout_complexity": effective_layout,
        "is_scanned": type_defaults["is_scanned"],
        "text_density": type_defaults["text_density"],
    }

    return features


# ---------------------------------------------------------------------------
# 1. Quick Quote — estimare pret fara upload
# ---------------------------------------------------------------------------

class QuickQuoteRequest(BaseModel):
    """Schema pentru cererea de estimare rapida."""
    word_count: int = Field(..., gt=0, description="Numarul de cuvinte")
    document_type: str = Field(
        "general",
        description="Tipul documentului: general, technical, legal, medical, marketing, certificate, financial",
    )
    complexity: str = Field(
        "medium",
        description="Complexitate: low, medium, high",
    )
    source_lang: str = Field("en", description="Limba sursa (cod ISO 2 litere)")
    target_lang: str = Field("ro", description="Limba tinta (cod ISO 2 litere)")
    invoice_percent: float | None = Field(
        None,
        gt=0,
        le=100,
        description="Procentul de facturare (implicit din setari, 0-100%)",
    )


class QuickQuoteResponse(BaseModel):
    """Schema raspunsului de estimare rapida."""
    market_price: float
    market_price_with_lang: float
    invoice_price: float
    invoice_percent: float
    currency: str = "RON"
    word_count: int
    page_count_estimated: int
    document_type: str
    complexity: str
    language_info: dict[str, Any]
    dtp: dict[str, Any] | None = None
    method_prices: dict[str, float]
    weights_used: dict[str, float]
    features_used: dict[str, Any]


@router.post("/quick-quote", response_model=QuickQuoteResponse)
async def quick_quote(request: QuickQuoteRequest):
    """
    Estimare rapida de pret fara upload de fisier.

    Construieste features sintetice pe baza word_count, document_type
    si complexity, apoi ruleaza pricing engine-ul ensemble standard.
    Aplica coeficientul de limba daca e cazul.
    """
    # Validare document_type
    valid_types = list(DOCUMENT_TYPE_DEFAULTS.keys())
    doc_type = request.document_type.lower()
    if doc_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Tip document invalid: '{request.document_type}'. Tipuri valide: {', '.join(valid_types)}",
        )

    # Validare complexity
    valid_complexities = list(COMPLEXITY_LAYOUT_MAP.keys())
    complexity = request.complexity.lower()
    if complexity not in valid_complexities:
        raise HTTPException(
            status_code=400,
            detail=f"Complexitate invalida: '{request.complexity}'. Valori valide: {', '.join(valid_complexities)}",
        )

    # Construieste features sintetice
    features = _build_synthetic_features(
        word_count=request.word_count,
        document_type=doc_type,
        complexity=complexity,
    )

    # Incarca referinte si calibrare
    reference_data = _load_reference_data()
    calibration = _load_calibration_data()

    # Calcul pret ensemble
    price_result = calculate_ensemble_price(
        features=features,
        reference_data=reference_data,
        calibration=calibration,
    )

    market_price = price_result["market_price"]

    # Aplica coeficient limba
    lang_info = get_language_coefficient(request.source_lang, request.target_lang)
    market_price_with_lang = round(market_price * lang_info["effective_coefficient"], 2)

    # Pret facturat
    invoice_percent = request.invoice_percent
    if invoice_percent is None:
        invoice_percent = await _get_invoice_percent()

    invoice_price = round(market_price_with_lang * (invoice_percent / 100.0), 2)

    # Log activitate
    await log_activity(
        action="calculator.quick_quote",
        summary=(
            f"Quick quote: {request.word_count} cuvinte, {doc_type}, "
            f"{request.source_lang}->{request.target_lang} = {market_price_with_lang} RON"
        ),
        details={
            "word_count": request.word_count,
            "document_type": doc_type,
            "complexity": complexity,
            "source_lang": request.source_lang,
            "target_lang": request.target_lang,
            "market_price": market_price,
            "market_price_with_lang": market_price_with_lang,
            "invoice_price": invoice_price,
            "lang_coefficient": lang_info["effective_coefficient"],
        },
    )

    return QuickQuoteResponse(
        market_price=market_price,
        market_price_with_lang=market_price_with_lang,
        invoice_price=invoice_price,
        invoice_percent=invoice_percent,
        word_count=request.word_count,
        page_count_estimated=features["page_count"],
        document_type=doc_type,
        complexity=complexity,
        language_info=lang_info,
        dtp=price_result.get("dtp"),
        method_prices=price_result.get("method_prices", {}),
        weights_used=price_result.get("weights_used", {}),
        features_used=features,
    )


# ---------------------------------------------------------------------------
# 2. Generare factura din calcul
# ---------------------------------------------------------------------------

class CreateInvoiceFromCalcRequest(BaseModel):
    """Schema pentru generarea de date factura din rezultat calcul."""
    client_name: str = Field("", description="Numele clientului (optional)")
    document_type: str = Field("general", description="Tipul documentului")
    source_lang: str = Field("en", description="Limba sursa")
    target_lang: str = Field("ro", description="Limba tinta")
    word_count: int = Field(..., gt=0, description="Numarul de cuvinte")
    calculated_price: float = Field(..., gt=0, description="Pretul calculat (RON)")
    notes: str = Field("", description="Note suplimentare")


class InvoiceItemData(BaseModel):
    """Un articol de factura."""
    description: str
    quantity: float = 1.0
    unit_price: float
    unit: str = "buc"


class CreateInvoiceFromCalcResponse(BaseModel):
    """Raspuns cu datele pre-completate pentru factura."""
    client_name: str
    items: list[InvoiceItemData]
    total: float
    currency: str = "RON"
    notes: str


@router.post("/create-invoice-from-calculation", response_model=CreateInvoiceFromCalcResponse)
async def create_invoice_from_calculation(request: CreateInvoiceFromCalcRequest):
    """
    Genereaza date pre-completate pentru o factura pe baza unui calcul de pret.

    Nu creaza factura efectiv in DB — returneaza datele gata de trimis
    catre endpoint-ul de creare factura (/api/invoices).
    """
    # Construieste descrierea articolului
    doc_type_labels = {
        "general": "document general",
        "technical": "document tehnic",
        "legal": "document juridic",
        "medical": "document medical",
        "marketing": "material marketing",
        "certificate": "certificat/atestat",
        "financial": "document financiar",
    }
    type_label = doc_type_labels.get(
        request.document_type.lower(), request.document_type
    )

    src = request.source_lang.upper()
    tgt = request.target_lang.upper()

    description = (
        f"Traducere {type_label} {src} -> {tgt} "
        f"({request.word_count:,} cuvinte)"
    )

    items = [
        InvoiceItemData(
            description=description,
            quantity=1.0,
            unit_price=request.calculated_price,
            unit="buc",
        )
    ]

    notes = request.notes
    if not notes:
        notes = f"Pret calculat automat pentru {request.word_count:,} cuvinte."

    await log_activity(
        action="calculator.create_invoice_data",
        summary=f"Generat date factura: {description} = {request.calculated_price} RON",
        details={
            "client_name": request.client_name,
            "word_count": request.word_count,
            "price": request.calculated_price,
            "source_lang": request.source_lang,
            "target_lang": request.target_lang,
        },
    )

    return CreateInvoiceFromCalcResponse(
        client_name=request.client_name,
        items=items,
        total=request.calculated_price,
        notes=notes,
    )


# ---------------------------------------------------------------------------
# 3. Salvare oferta ca template
# ---------------------------------------------------------------------------

class TemplateCreateRequest(BaseModel):
    """Schema pentru salvarea unui template."""
    name: str = Field(..., min_length=1, max_length=200, description="Numele template-ului")
    word_count: int = Field(..., gt=0, description="Numarul de cuvinte")
    document_type: str = Field("general", description="Tipul documentului")
    complexity: str = Field("medium", description="Complexitate: low, medium, high")
    source_lang: str = Field("en", description="Limba sursa")
    target_lang: str = Field("ro", description="Limba tinta")
    price: float = Field(..., gt=0, description="Pretul calculat (RON)")
    notes: str = Field("", max_length=500, description="Note optionale")


class TemplateResponse(BaseModel):
    """Schema raspunsului pentru un template."""
    id: int
    name: str
    word_count: int
    document_type: str
    complexity: str
    source_lang: str
    target_lang: str
    price: float
    notes: str
    created_at: str


class TemplateListResponse(BaseModel):
    """Lista de template-uri."""
    templates: list[TemplateResponse]
    total: int


async def _ensure_templates_table() -> None:
    """Creeaza tabela calculation_templates daca nu exista."""
    async with get_db() as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS calculation_templates (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                name           TEXT NOT NULL,
                word_count     INTEGER NOT NULL,
                document_type  TEXT NOT NULL DEFAULT 'general',
                complexity     TEXT NOT NULL DEFAULT 'medium',
                source_lang    TEXT NOT NULL DEFAULT 'en',
                target_lang    TEXT NOT NULL DEFAULT 'ro',
                price          REAL NOT NULL,
                notes          TEXT DEFAULT '',
                created_at     TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()


@router.get("/templates", response_model=TemplateListResponse)
async def list_templates():
    """Returneaza toate template-urile salvate, ordonate descrescator dupa data."""
    await _ensure_templates_table()

    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM calculation_templates ORDER BY created_at DESC"
        )
        rows = await cursor.fetchall()

    templates = [
        TemplateResponse(
            id=row["id"],
            name=row["name"],
            word_count=row["word_count"],
            document_type=row["document_type"],
            complexity=row["complexity"],
            source_lang=row["source_lang"],
            target_lang=row["target_lang"],
            price=row["price"],
            notes=row["notes"] or "",
            created_at=row["created_at"] or "",
        )
        for row in rows
    ]

    return TemplateListResponse(templates=templates, total=len(templates))


@router.post("/templates", response_model=TemplateResponse, status_code=201)
async def create_template(request: TemplateCreateRequest):
    """Salveaza un calcul ca template reutilizabil."""
    await _ensure_templates_table()

    # Validare document_type
    valid_types = list(DOCUMENT_TYPE_DEFAULTS.keys())
    if request.document_type.lower() not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Tip document invalid: '{request.document_type}'. Tipuri valide: {', '.join(valid_types)}",
        )

    # Validare complexity
    valid_complexities = list(COMPLEXITY_LAYOUT_MAP.keys())
    if request.complexity.lower() not in valid_complexities:
        raise HTTPException(
            status_code=400,
            detail=f"Complexitate invalida: '{request.complexity}'. Valori valide: {', '.join(valid_complexities)}",
        )

    now = datetime.now(timezone.utc).isoformat()

    async with get_db() as db:
        cursor = await db.execute(
            """
            INSERT INTO calculation_templates
                (name, word_count, document_type, complexity, source_lang, target_lang, price, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                request.name.strip(),
                request.word_count,
                request.document_type.lower(),
                request.complexity.lower(),
                request.source_lang.lower().strip()[:2],
                request.target_lang.lower().strip()[:2],
                request.price,
                request.notes.strip(),
                now,
            ),
        )
        await db.commit()
        template_id = cursor.lastrowid

    await log_activity(
        action="calculator.template_create",
        summary=f"Template salvat: '{request.name}' ({request.word_count} cuvinte, {request.price} RON)",
        details={
            "template_id": template_id,
            "name": request.name,
            "word_count": request.word_count,
            "document_type": request.document_type,
            "price": request.price,
        },
    )

    return TemplateResponse(
        id=template_id,
        name=request.name.strip(),
        word_count=request.word_count,
        document_type=request.document_type.lower(),
        complexity=request.complexity.lower(),
        source_lang=request.source_lang.lower().strip()[:2],
        target_lang=request.target_lang.lower().strip()[:2],
        price=request.price,
        notes=request.notes.strip(),
        created_at=now,
    )


@router.delete("/templates/{template_id}")
async def delete_template(template_id: int):
    """Sterge un template dupa ID."""
    await _ensure_templates_table()

    async with get_db() as db:
        cursor = await db.execute(
            "SELECT id, name FROM calculation_templates WHERE id = ?",
            (template_id,),
        )
        row = await cursor.fetchone()

        if not row:
            raise HTTPException(
                status_code=404,
                detail=f"Template-ul cu ID {template_id} nu a fost gasit.",
            )

        template_name = row["name"]

        await db.execute(
            "DELETE FROM calculation_templates WHERE id = ?",
            (template_id,),
        )
        await db.commit()

    await log_activity(
        action="calculator.template_delete",
        summary=f"Template sters: '{template_name}' (ID {template_id})",
        details={"template_id": template_id, "name": template_name},
    )

    return {
        "message": f"Template-ul '{template_name}' a fost sters.",
        "deleted_id": template_id,
    }


# ---------------------------------------------------------------------------
# 4. Coeficienti limba — endpoint informativ
# ---------------------------------------------------------------------------

@router.get("/language-coefficients")
async def list_language_coefficients():
    """
    Returneaza toti coeficientii de pret per limba.

    Folosit de frontend pentru a afisa informatii despre majorari
    si pentru selectoarele de limba.
    """
    coefficients = [
        {
            "code": code,
            "coefficient": coef,
            "surcharge_percent": round((coef - 1.0) * 100, 1) if coef > 1.0 else 0,
        }
        for code, coef in sorted(LANGUAGE_COEFFICIENTS.items())
    ]

    return {
        "coefficients": coefficients,
        "total_languages": len(coefficients),
        "note": "Coeficientul se aplica pe pretul final. Se foloseste maximul dintre limba sursa si tinta.",
    }
