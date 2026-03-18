"""
Rute pentru istoricul calculelor.

GET    /api/history      — listare cu paginare, sortare, filtrare
GET    /api/history/{id} — detalii unui calcul
DELETE /api/history/{id} — ștergere calcul
"""

import json
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.core.activity_log import log_activity
from app.db.database import get_db

router = APIRouter(prefix="/api", tags=["history"])

# Coloane permise pentru sortare (din view-ul history)
ALLOWED_SORT_COLUMNS = {
    "calculation_id", "filename", "market_price", "invoice_price",
    "confidence", "calculated_at", "upload_date", "file_type",
}


@router.get("/history")
async def list_history(
    page: int = Query(1, ge=1, description="Numărul paginii"),
    per_page: int = Query(20, ge=1, le=100, description="Rezultate per pagină"),
    sort_by: str = Query("calculated_at", description="Coloană de sortare"),
    sort_order: str = Query("desc", description="Direcție sortare: asc sau desc"),
    search: str | None = Query(None, description="Căutare în numele fișierului"),
    file_type: str | None = Query(None, description="Filtrare după tip: pdf sau docx"),
    min_confidence: float | None = Query(None, ge=0, le=100, description="Încredere minimă"),
):
    """
    Returnează istoricul calculelor cu paginare, sortare și filtrare.

    Folosește view-ul `history` care combină tabelele uploads + calculations.
    """
    # --- Validare sortare ---
    if sort_by not in ALLOWED_SORT_COLUMNS:
        sort_by = "calculated_at"
    if sort_order.lower() not in ("asc", "desc"):
        sort_order = "desc"

    # --- Construire query ---
    where_clauses: list[str] = []
    params: list[Any] = []

    if search:
        where_clauses.append("filename LIKE ?")
        params.append(f"%{search}%")

    if file_type:
        where_clauses.append("file_type = ?")
        params.append(file_type.lower())

    if min_confidence is not None:
        where_clauses.append("confidence >= ?")
        params.append(min_confidence)

    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)

    offset = (page - 1) * per_page

    async with get_db() as db:
        # --- Total ---
        count_cursor = await db.execute(
            f"SELECT COUNT(*) as total FROM history {where_sql}",
            params,
        )
        count_row = await count_cursor.fetchone()
        total = count_row["total"] if count_row else 0

        # --- Date ---
        query = f"""
            SELECT calculation_id, upload_id, filename, file_type, file_size,
                   upload_date, market_price, invoice_price, invoice_percent,
                   confidence, calculated_at
            FROM history
            {where_sql}
            ORDER BY {sort_by} {sort_order}
            LIMIT ? OFFSET ?
        """
        cursor = await db.execute(query, params + [per_page, offset])
        rows = await cursor.fetchall()

    items = [
        {
            "id": row["calculation_id"],
            "upload_id": row["upload_id"],
            "filename": row["filename"],
            "file_type": row["file_type"],
            "file_size": row["file_size"],
            "upload_date": row["upload_date"],
            "market_price": row["market_price"],
            "invoice_price": row["invoice_price"],
            "invoice_percent": row["invoice_percent"],
            "confidence": row["confidence"],
            "calculated_at": row["calculated_at"],
        }
        for row in rows
    ]

    total_pages = (total + per_page - 1) // per_page if per_page > 0 else 0

    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
    }


@router.get("/history/{calculation_id}")
async def get_calculation(calculation_id: int):
    """Returnează detaliile complete ale unui calcul."""
    async with get_db() as db:
        cursor = await db.execute(
            """
            SELECT calculation_id, upload_id, filename, file_type, file_size,
                   upload_date, market_price, invoice_price, invoice_percent,
                   confidence, method_details, features, warnings,
                   validated_price, validated_at, calculated_at
            FROM history
            WHERE calculation_id = ?
            """,
            (calculation_id,),
        )
        row = await cursor.fetchone()

    if not row:
        raise HTTPException(
            status_code=404,
            detail=f"Calculul cu ID {calculation_id} nu a fost găsit.",
        )

    return {
        "id": row["calculation_id"],
        "upload_id": row["upload_id"],
        "filename": row["filename"],
        "file_type": row["file_type"],
        "file_size": row["file_size"],
        "upload_date": row["upload_date"],
        "market_price": row["market_price"],
        "invoice_price": row["invoice_price"],
        "invoice_percent": row["invoice_percent"],
        "confidence": row["confidence"],
        "features": json.loads(row["features"]) if row["features"] else {},
        "method_details": json.loads(row["method_details"]) if row["method_details"] else [],
        "warnings": json.loads(row["warnings"]) if row["warnings"] else [],
        "validated_price": row["validated_price"],
        "validated_at": row["validated_at"],
        "calculated_at": row["calculated_at"],
    }


@router.delete("/history/{calculation_id}")
async def delete_calculation(calculation_id: int):
    """Șterge un calcul din istoric (și upload-ul asociat dacă nu mai are calcule)."""
    async with get_db() as db:
        # Verifică existența
        cursor = await db.execute(
            "SELECT id, upload_id FROM calculations WHERE id = ?",
            (calculation_id,),
        )
        row = await cursor.fetchone()

        if not row:
            raise HTTPException(
                status_code=404,
                detail=f"Calculul cu ID {calculation_id} nu a fost găsit.",
            )

        upload_id = row["upload_id"]

        # Șterge calculul
        await db.execute(
            "DELETE FROM calculations WHERE id = ?",
            (calculation_id,),
        )

        # Verifică dacă upload-ul mai are alte calcule; dacă nu, șterge-l
        cursor = await db.execute(
            "SELECT COUNT(*) as cnt FROM calculations WHERE upload_id = ?",
            (upload_id,),
        )
        cnt_row = await cursor.fetchone()
        if cnt_row and cnt_row["cnt"] == 0:
            await db.execute(
                "DELETE FROM uploads WHERE id = ?",
                (upload_id,),
            )

        await db.commit()

    await log_activity(
        action="delete_history",
        summary=f"Calculul #{calculation_id} șters din istoric",
        details={"calculation_id": calculation_id, "upload_id": upload_id},
    )

    return {
        "message": f"Calculul #{calculation_id} a fost șters.",
        "deleted_id": calculation_id,
    }
