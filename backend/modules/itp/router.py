"""
API endpoints for ITP (Inspectie Tehnica Periodica) module.

Endpoints:
  GET    /api/itp/inspections                          — list all (paginated, searchable)
  POST   /api/itp/inspections                          — create new inspection
  GET    /api/itp/inspections/{id}                     — get single inspection
  PUT    /api/itp/inspections/{id}                     — update inspection
  DELETE /api/itp/inspections/{id}                     — delete inspection
  GET    /api/itp/vehicle/{plate}/history              — all inspections for a plate
  GET    /api/itp/rejection-reasons                    — standard ITP rejection reasons list
  POST   /api/itp/inspections/{id}/create-invoice      — pre-filled invoice data from inspection
  POST   /api/itp/import                               — import CSV/Excel file (with duplicate detection)
  GET    /api/itp/stats/overview                        — total, admis/respins, avg price, this month
  GET    /api/itp/stats/monthly                         — inspections per month (bar chart)
  GET    /api/itp/stats/brands                          — top brands (pie chart)
  GET    /api/itp/stats/revenue                         — monthly revenue (line chart)
  GET    /api/itp/stats/fuel-types                      — distribution by fuel type
  GET    /api/itp/stats/inspectors                      — stats per inspector
  GET    /api/itp/expiring                              — vehicles with ITP expiring soon
  GET    /api/itp/export/csv                            — export all as CSV
  GET    /api/itp/export/excel                          — export all as Excel
  GET    /api/itp/followup/due-soon                     — R4-24: vehicles due for re-inspection soon
  PUT    /api/itp/appointments/{id}/mark-showup         — R4-26: mark no-show / showed up
  GET    /api/itp/stats/noshow-rate                     — R4-26: no-show rate statistics
"""

from __future__ import annotations

import csv
import io
import json
import logging
from datetime import date, datetime, timedelta
from typing import Optional

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, model_validator

from app.core.activity_log import log_activity
from app.db.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/itp", tags=["itp"])


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


# ────────── CRUD ──────────

@router.get("/inspections")
async def list_inspections(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    search: str = Query("", description="Search by plate number or owner name"),
    page: Optional[int] = Query(None, ge=1, description="Page number (alternative to skip)"),
    per_page: Optional[int] = Query(None, ge=1, le=500, description="Items per page (alternative to limit)"),
):
    """List all inspections with pagination and optional search.

    Accepts either skip/limit or page/per_page. If page is provided,
    it takes precedence and calculates skip automatically.
    """
    # If page/per_page provided, convert to skip/limit
    if page is not None:
        per_page = per_page or limit
        skip = (page - 1) * per_page
        limit = per_page

    async with get_db() as db:
        if search:
            pattern = f"%{search}%"
            cursor = await db.execute(
                """SELECT COUNT(*) FROM itp_inspections
                   WHERE plate_number LIKE ? OR owner_name LIKE ?""",
                (pattern, pattern),
            )
            total = (await cursor.fetchone())[0]

            cursor = await db.execute(
                """SELECT * FROM itp_inspections
                   WHERE plate_number LIKE ? OR owner_name LIKE ?
                   ORDER BY inspection_date DESC
                   LIMIT ? OFFSET ?""",
                (pattern, pattern, limit, skip),
            )
        else:
            cursor = await db.execute("SELECT COUNT(*) FROM itp_inspections")
            total = (await cursor.fetchone())[0]

            cursor = await db.execute(
                """SELECT * FROM itp_inspections
                   ORDER BY inspection_date DESC
                   LIMIT ? OFFSET ?""",
                (limit, skip),
            )

        rows = await cursor.fetchall()
        items = [dict(row) for row in rows]

    total_pages = (total + limit - 1) // limit if limit > 0 else 1
    current_page = (skip // limit) + 1 if limit > 0 else 1

    return {
        "items": items,
        "total": total,
        "skip": skip,
        "limit": limit,
        "total_pages": total_pages,
        "page": current_page,
    }


@router.post("/inspections")
async def create_inspection(data: InspectionCreate):
    """Create a new ITP inspection record."""
    async with get_db() as db:
        cursor = await db.execute(
            """INSERT INTO itp_inspections
               (plate_number, vin, brand, model, year, fuel_type,
                owner_name, owner_phone, inspection_date, expiry_date,
                result, rejection_reasons, price, inspector_name, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                data.plate_number.upper().strip(),
                data.vin,
                data.brand,
                data.model,
                data.year,
                data.fuel_type,
                data.owner_name,
                data.owner_phone,
                data.inspection_date,
                data.expiry_date,
                data.result,
                data.rejection_reasons,
                data.price,
                data.inspector_name,
                data.notes,
            ),
        )
        await db.commit()
        new_id = cursor.lastrowid

        # 3-strike rule: count previous rejections for this plate
        blocked = False
        if data.result == "Respins":
            plate_upper = data.plate_number.upper().strip()
            cnt_cursor = await db.execute(
                "SELECT COUNT(*) FROM itp_inspections WHERE UPPER(plate_number) = ? AND result = 'Respins'",
                (plate_upper,),
            )
            cnt_row = await cnt_cursor.fetchone()
            rejection_count = cnt_row[0] if cnt_row else 0
            if rejection_count >= 3:
                blocked = True
                logger.warning(
                    "3-STRIKE BLOCK: plate %s has %d rejections (including current)",
                    plate_upper, rejection_count,
                )

    await log_activity(
        action="itp.create",
        summary=f"ITP creat: {data.plate_number} — {data.result}",
        details={"id": new_id, "plate": data.plate_number, "result": data.result},
    )
    response = {"id": new_id, "message": "Inspectie creata cu succes"}
    if blocked:
        response["blocked"] = True
        response["blocked_message"] = (
            f"ATENTIE: {data.plate_number.upper().strip()} a acumulat 3 sau mai multe respingeri. "
            "Verificati vehiculul cu atentie inainte de urmatoarea inspectie."
        )
    return response


@router.get("/inspections/{inspection_id}")
async def get_inspection(inspection_id: int):
    """Get a single inspection by ID."""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM itp_inspections WHERE id = ?", (inspection_id,)
        )
        row = await cursor.fetchone()

    if not row:
        raise HTTPException(404, "Inspectia nu a fost gasita")
    return dict(row)


@router.put("/inspections/{inspection_id}")
async def update_inspection(inspection_id: int, data: InspectionUpdate):
    """Update an existing inspection."""
    # Build dynamic update
    fields = []
    values = []
    update_data = data.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(400, "Niciun camp de actualizat")

    for key, value in update_data.items():
        if key == "plate_number" and value:
            value = value.upper().strip()
        fields.append(f"{key} = ?")
        values.append(value)

    values.append(inspection_id)

    async with get_db() as db:
        cursor = await db.execute(
            f"UPDATE itp_inspections SET {', '.join(fields)} WHERE id = ?",
            values,
        )
        await db.commit()

        if cursor.rowcount == 0:
            raise HTTPException(404, "Inspectia nu a fost gasita")

    await log_activity(
        action="itp.update",
        summary=f"ITP actualizat: ID {inspection_id}",
        details={"id": inspection_id, "fields": list(update_data.keys())},
    )
    return {"message": "Inspectie actualizata cu succes"}


@router.delete("/inspections/{inspection_id}")
async def delete_inspection(inspection_id: int):
    """Delete an inspection."""
    async with get_db() as db:
        cursor = await db.execute(
            "DELETE FROM itp_inspections WHERE id = ?", (inspection_id,)
        )
        await db.commit()

        if cursor.rowcount == 0:
            raise HTTPException(404, "Inspectia nu a fost gasita")

    await log_activity(
        action="itp.delete",
        summary=f"ITP sters: ID {inspection_id}",
        details={"id": inspection_id},
    )
    return {"message": "Inspectie stearsa cu succes"}


# ────────── Vehicle History ──────────

@router.get("/vehicle/{plate}/history")
async def vehicle_history(plate: str):
    """All inspections for a specific plate number, ordered by date DESC."""
    plate_upper = plate.strip().upper()
    if not plate_upper:
        raise HTTPException(400, "Numarul de inmatriculare este obligatoriu")

    async with get_db() as db:
        cursor = await db.execute(
            """SELECT * FROM itp_inspections
               WHERE UPPER(plate_number) = ?
               ORDER BY inspection_date DESC""",
            (plate_upper,),
        )
        rows = await cursor.fetchall()

    items = [dict(row) for row in rows]
    total = len(items)
    admis = sum(1 for item in items if item.get("result") == "admis")
    respins = sum(1 for item in items if item.get("result") == "respins")
    pass_rate = round((admis / total * 100), 1) if total > 0 else 0

    return {
        "plate_number": plate_upper,
        "total": total,
        "admis": admis,
        "respins": respins,
        "pass_rate": pass_rate,
        "inspections": items,
    }


# ────────── Rejection Reasons ──────────

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


@router.get("/rejection-reasons")
async def get_rejection_reasons():
    """Standard ITP rejection reasons list."""
    return STANDARD_REJECTION_REASONS


# ────────── Generate Invoice from Inspection ──────────

@router.post("/inspections/{inspection_id}/create-invoice")
async def create_invoice_from_inspection(inspection_id: int):
    """Return pre-filled invoice data from an inspection record.

    Also stores the link back: updates the inspection with linked_invoice_id
    so the relationship is bidirectional (ITP -> Invoice).
    """
    async with get_db() as db:
        # Ensure linked_invoice_id column exists (ALTER TABLE IF NOT EXISTS pattern)
        try:
            await db.execute(
                "ALTER TABLE itp_inspections ADD COLUMN linked_invoice_id INTEGER"
            )
            await db.commit()
        except Exception:
            pass  # Column already exists

        cursor = await db.execute(
            "SELECT * FROM itp_inspections WHERE id = ?", (inspection_id,)
        )
        row = await cursor.fetchone()

    if not row:
        raise HTTPException(404, "Inspectia nu a fost gasita")

    inspection = dict(row)
    plate = inspection.get("plate_number", "")
    owner = inspection.get("owner_name", "")
    price = inspection.get("price", 0) or 0
    result = inspection.get("result", "")
    insp_date = inspection.get("inspection_date", "")

    invoice_data = {
        "client_name": owner or f"Proprietar {plate}",
        "client_phone": inspection.get("owner_phone", ""),
        "date": insp_date,
        "items": [
            {
                "description": f"Inspectie ITP - {plate} ({result})",
                "quantity": 1,
                "unit": "buc",
                "price": price,
                "total": price,
            }
        ],
        "total": price,
        "notes": f"Vehicul: {inspection.get('brand', '')} {inspection.get('model', '')} ({inspection.get('year', '')}) - {plate}",
        "source": "itp",
        "source_id": inspection_id,
        "linked_inspection_id": inspection_id,
    }

    await log_activity(
        action="itp.create_invoice",
        summary=f"Generare factura din ITP: {plate} — {price} RON",
        details={"inspection_id": inspection_id, "plate": plate, "price": price},
    )

    return invoice_data


@router.put("/inspections/{inspection_id}/link-invoice")
async def link_invoice_to_inspection(inspection_id: int, invoice_id: int):
    """Store the bidirectional link: set linked_invoice_id on the ITP inspection.

    Called after the invoice is actually created from the pre-filled data,
    so the inspection record knows which invoice was generated from it.
    """
    async with get_db() as db:
        # Ensure column exists
        try:
            await db.execute(
                "ALTER TABLE itp_inspections ADD COLUMN linked_invoice_id INTEGER"
            )
            await db.commit()
        except Exception:
            pass  # Column already exists

        cursor = await db.execute(
            "SELECT id FROM itp_inspections WHERE id = ?", (inspection_id,)
        )
        if not await cursor.fetchone():
            raise HTTPException(404, "Inspectia nu a fost gasita")

        await db.execute(
            "UPDATE itp_inspections SET linked_invoice_id = ? WHERE id = ?",
            (invoice_id, inspection_id),
        )
        await db.commit()

    await log_activity(
        action="itp.link_invoice",
        summary=f"ITP #{inspection_id} linkuit la factura #{invoice_id}",
        details={"inspection_id": inspection_id, "invoice_id": invoice_id},
    )
    return {
        "message": f"Inspectia #{inspection_id} linkuita la factura #{invoice_id}.",
        "inspection_id": inspection_id,
        "invoice_id": invoice_id,
    }


# ────────── Import CSV/Excel ──────────

@router.post("/import")
async def import_inspections(file: UploadFile = File(...)):
    """Import inspections from CSV or Excel file."""
    filename = (file.filename or "").lower()
    content = await file.read()

    try:
        if filename.endswith((".xlsx", ".xls")):
            rows = _parse_excel(content)
        elif filename.endswith(".csv") or "csv" in (file.content_type or ""):
            rows = _parse_csv(content)
        else:
            raise HTTPException(
                400,
                "Format nesuportat. Acceptate: CSV, XLSX",
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, f"Eroare la parsarea fisierului: {e}")

    imported = 0
    skipped = 0
    duplicates = []
    errors = []

    async with get_db() as db:
        for i, row in enumerate(rows, 1):
            try:
                plate = (row.get("plate_number") or "").strip().upper()
                if not plate:
                    skipped += 1
                    continue

                insp_date = row.get("inspection_date", "")
                exp_date = row.get("expiry_date", "")
                result = (row.get("result") or "admis").strip().lower()

                if result not in ("admis", "respins"):
                    result = "admis"

                price = 0
                try:
                    price = float(row.get("price", 0) or 0)
                except (ValueError, TypeError):
                    price = 0

                year = None
                try:
                    year = int(row.get("year", 0) or 0)
                    if year < 1900:
                        year = None
                except (ValueError, TypeError):
                    year = None

                # Duplicate detection: same plate + same date
                if insp_date:
                    dup_cursor = await db.execute(
                        """SELECT id FROM itp_inspections
                           WHERE UPPER(plate_number) = ? AND inspection_date = ?
                           LIMIT 1""",
                        (plate, insp_date),
                    )
                    existing = await dup_cursor.fetchone()
                    if existing:
                        duplicates.append({
                            "row": i,
                            "plate_number": plate,
                            "inspection_date": insp_date,
                            "existing_id": existing[0],
                        })
                        continue

                await db.execute(
                    """INSERT INTO itp_inspections
                       (plate_number, brand, model, year, fuel_type,
                        owner_name, inspection_date, expiry_date,
                        result, price)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        plate,
                        row.get("brand", ""),
                        row.get("model", ""),
                        year,
                        row.get("fuel_type", ""),
                        row.get("owner_name", ""),
                        insp_date,
                        exp_date,
                        result,
                        price,
                    ),
                )
                imported += 1
            except Exception as e:
                errors.append(f"Rand {i}: {e}")

        await db.commit()

    await log_activity(
        action="itp.import",
        summary=f"Import ITP: {imported} importate, {len(duplicates)} duplicate, {skipped} sarite, {len(errors)} erori",
        details={
            "file": file.filename,
            "imported": imported,
            "duplicates": len(duplicates),
            "skipped": skipped,
        },
    )

    return {
        "imported": imported,
        "skipped": skipped,
        "duplicates": duplicates[:50],  # Limit duplicate list
        "errors": errors[:20],  # Limit error list
        "message": f"{imported} inspectii importate cu succes"
        + (f", {len(duplicates)} duplicate sarite" if duplicates else ""),
    }


def _parse_csv(content: bytes) -> list[dict]:
    """Parse CSV content into list of dicts."""
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    return list(reader)


def _parse_excel(content: bytes) -> list[dict]:
    """Parse Excel content into list of dicts."""
    from openpyxl import load_workbook

    wb = load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    ws = wb.active
    rows_iter = ws.iter_rows(values_only=True)

    # First row = headers
    headers_raw = next(rows_iter, None)
    if not headers_raw:
        return []

    headers = [str(h).strip().lower().replace(" ", "_") if h else f"col_{i}"
               for i, h in enumerate(headers_raw)]

    result = []
    for row in rows_iter:
        obj = {}
        for i, val in enumerate(row):
            key = headers[i] if i < len(headers) else f"col_{i}"
            if val is not None:
                obj[key] = str(val) if hasattr(val, "isoformat") else val
            else:
                obj[key] = ""
        result.append(obj)

    wb.close()
    return result


# ────────── Combined Statistics (for frontend) ──────────

@router.get("/statistics")
async def get_statistics_combined():
    """Combined statistics for frontend — calls individual stat queries in one endpoint."""
    async with get_db() as db:
        # Monthly inspection counts
        cursor = await db.execute(
            "SELECT strftime('%Y-%m', inspection_date) as month, COUNT(*) as count "
            "FROM itp_inspections GROUP BY month ORDER BY month"
        )
        monthly = [{"month": r[0], "count": r[1]} for r in await cursor.fetchall()]

        # Brand distribution (top 10)
        cursor = await db.execute(
            "SELECT brand, COUNT(*) as count FROM itp_inspections "
            "WHERE brand IS NOT NULL AND brand != '' "
            "GROUP BY brand ORDER BY count DESC LIMIT 10"
        )
        brands = [{"brand": r[0], "count": r[1]} for r in await cursor.fetchall()]

        # Monthly revenue
        cursor = await db.execute(
            "SELECT strftime('%Y-%m', inspection_date) as month, "
            "COALESCE(SUM(price), 0) as revenue "
            "FROM itp_inspections GROUP BY month ORDER BY month"
        )
        revenue = [{"month": r[0], "revenue": r[1]} for r in await cursor.fetchall()]

        # Fuel type distribution
        cursor = await db.execute(
            "SELECT fuel_type, COUNT(*) as count FROM itp_inspections "
            "WHERE fuel_type IS NOT NULL AND fuel_type != '' "
            "GROUP BY fuel_type ORDER BY count DESC"
        )
        fuel = [{"fuel_type": r[0], "count": r[1]} for r in await cursor.fetchall()]

    return {
        "monthly_inspections": monthly,
        "top_brands": brands,
        "monthly_revenue": revenue,
        "fuel_distribution": fuel,
    }


# ────────── Statistics ──────────


@router.get("/statistics")
async def statistics_combined():
    """Combined statistics endpoint for frontend dashboard.

    Returns monthly_inspections, top_brands, monthly_revenue, fuel_distribution
    in a single request (called by ITPPage StatsTab).
    """
    year = datetime.now().year
    month_names = [
        "", "Ian", "Feb", "Mar", "Apr", "Mai", "Iun",
        "Iul", "Aug", "Sep", "Oct", "Nov", "Dec",
    ]

    async with get_db() as db:
        # Monthly inspections
        cursor = await db.execute(
            """SELECT CAST(strftime('%%m', inspection_date) AS INTEGER) as month,
                      COUNT(*) as count
               FROM itp_inspections
               WHERE strftime('%%Y', inspection_date) = ?
               GROUP BY month ORDER BY month""",
            (str(year),),
        )
        monthly_raw = {r[0]: r[1] for r in await cursor.fetchall()}
        monthly_inspections = [
            {"month": month_names[i], "count": monthly_raw.get(i, 0)}
            for i in range(1, 13)
        ]

        # Top brands
        cursor = await db.execute(
            """SELECT brand, COUNT(*) as count FROM itp_inspections
               WHERE brand IS NOT NULL AND brand != ''
               GROUP BY brand ORDER BY count DESC LIMIT 10""",
        )
        top_brands = [{"brand": r[0], "count": r[1]} for r in await cursor.fetchall()]

        # Monthly revenue
        cursor = await db.execute(
            """SELECT CAST(strftime('%%m', inspection_date) AS INTEGER) as month,
                      SUM(price) as revenue
               FROM itp_inspections
               WHERE strftime('%%Y', inspection_date) = ?
               GROUP BY month ORDER BY month""",
            (str(year),),
        )
        revenue_raw = {r[0]: round(r[1] or 0, 2) for r in await cursor.fetchall()}
        monthly_revenue = [
            {"month": month_names[i], "revenue": revenue_raw.get(i, 0)}
            for i in range(1, 13)
        ]

        # Fuel distribution
        cursor = await db.execute(
            """SELECT fuel_type, COUNT(*) as count FROM itp_inspections
               WHERE fuel_type IS NOT NULL AND fuel_type != ''
               GROUP BY fuel_type ORDER BY count DESC""",
        )
        fuel_distribution = [{"fuel_type": r[0], "count": r[1]} for r in await cursor.fetchall()]

    return {
        "monthly_inspections": monthly_inspections,
        "top_brands": top_brands,
        "monthly_revenue": monthly_revenue,
        "fuel_distribution": fuel_distribution,
    }


@router.get("/stats/overview")
async def stats_overview():
    """Overview statistics: total, admis/respins ratio, avg price, this month."""
    async with get_db() as db:
        cursor = await db.execute("SELECT COUNT(*) FROM itp_inspections")
        total = (await cursor.fetchone())[0]

        cursor = await db.execute(
            "SELECT COUNT(*) FROM itp_inspections WHERE result = 'admis'"
        )
        admis = (await cursor.fetchone())[0]

        cursor = await db.execute(
            "SELECT COUNT(*) FROM itp_inspections WHERE result = 'respins'"
        )
        respins = (await cursor.fetchone())[0]

        cursor = await db.execute(
            "SELECT AVG(price) FROM itp_inspections WHERE price > 0"
        )
        avg_row = await cursor.fetchone()
        avg_price = round(avg_row[0], 2) if avg_row[0] else 0

        # This month
        now = datetime.now()
        month_start = now.strftime("%Y-%m-01")
        month_end = now.strftime("%Y-%m-31")
        cursor = await db.execute(
            """SELECT COUNT(*) FROM itp_inspections
               WHERE inspection_date >= ? AND inspection_date <= ?""",
            (month_start, month_end),
        )
        this_month = (await cursor.fetchone())[0]

    admis_rate = round((admis / total * 100), 1) if total > 0 else 0

    return {
        "total": total,
        "admis": admis,
        "respins": respins,
        "admis_rate": admis_rate,
        "avg_price": avg_price,
        "this_month": this_month,
    }


@router.get("/stats/monthly")
async def stats_monthly(year: int = Query(default=None)):
    """Inspections per month for a given year (default: current year)."""
    if year is None:
        year = datetime.now().year

    async with get_db() as db:
        cursor = await db.execute(
            """SELECT
                 CAST(strftime('%%m', inspection_date) AS INTEGER) as month,
                 COUNT(*) as count,
                 SUM(CASE WHEN result = 'admis' THEN 1 ELSE 0 END) as admis,
                 SUM(CASE WHEN result = 'respins' THEN 1 ELSE 0 END) as respins
               FROM itp_inspections
               WHERE strftime('%%Y', inspection_date) = ?
               GROUP BY month
               ORDER BY month""",
            (str(year),),
        )
        rows = await cursor.fetchall()

    # Fill all 12 months
    months_data = {i: {"month": i, "count": 0, "admis": 0, "respins": 0} for i in range(1, 13)}
    for row in rows:
        m = row[0]  # month as integer
        if m in months_data:
            months_data[m] = {
                "month": m,
                "count": row[1],
                "admis": row[2],
                "respins": row[3],
            }

    month_names = [
        "", "Ian", "Feb", "Mar", "Apr", "Mai", "Iun",
        "Iul", "Aug", "Sep", "Oct", "Nov", "Dec",
    ]
    result = []
    for i in range(1, 13):
        d = months_data[i]
        d["name"] = month_names[i]
        result.append(d)

    return {"year": year, "data": result}


@router.get("/stats/brands")
async def stats_brands():
    """Top car brands by inspection count."""
    async with get_db() as db:
        cursor = await db.execute(
            """SELECT brand, COUNT(*) as count
               FROM itp_inspections
               WHERE brand IS NOT NULL AND brand != ''
               GROUP BY brand
               ORDER BY count DESC
               LIMIT 15""",
        )
        rows = await cursor.fetchall()

    return [{"brand": row[0], "count": row[1]} for row in rows]


@router.get("/stats/revenue")
async def stats_revenue(year: int = Query(default=None)):
    """Monthly revenue for a given year."""
    if year is None:
        year = datetime.now().year

    async with get_db() as db:
        cursor = await db.execute(
            """SELECT
                 CAST(strftime('%%m', inspection_date) AS INTEGER) as month,
                 SUM(price) as revenue,
                 COUNT(*) as count
               FROM itp_inspections
               WHERE strftime('%%Y', inspection_date) = ?
               GROUP BY month
               ORDER BY month""",
            (str(year),),
        )
        rows = await cursor.fetchall()

    months_data = {i: {"month": i, "revenue": 0, "count": 0} for i in range(1, 13)}
    for row in rows:
        m = row[0]
        if m in months_data:
            months_data[m] = {
                "month": m,
                "revenue": round(row[1] or 0, 2),
                "count": row[2],
            }

    month_names = [
        "", "Ian", "Feb", "Mar", "Apr", "Mai", "Iun",
        "Iul", "Aug", "Sep", "Oct", "Nov", "Dec",
    ]
    result = []
    for i in range(1, 13):
        d = months_data[i]
        d["name"] = month_names[i]
        result.append(d)

    return {"year": year, "data": result}


@router.get("/stats/fuel-types")
async def stats_fuel_types():
    """Distribution by fuel type."""
    async with get_db() as db:
        cursor = await db.execute(
            """SELECT fuel_type, COUNT(*) as count
               FROM itp_inspections
               WHERE fuel_type IS NOT NULL AND fuel_type != ''
               GROUP BY fuel_type
               ORDER BY count DESC""",
        )
        rows = await cursor.fetchall()

    return [{"fuel_type": row[0], "count": row[1]} for row in rows]


@router.get("/stats/inspectors")
async def stats_inspectors():
    """Statistics per inspector: total, admis, respins, rate, revenue."""
    async with get_db() as db:
        cursor = await db.execute(
            """SELECT
                 inspector_name,
                 COUNT(*) as total,
                 SUM(CASE WHEN result = 'admis' THEN 1 ELSE 0 END) as admis,
                 SUM(CASE WHEN result = 'respins' THEN 1 ELSE 0 END) as respins,
                 SUM(price) as revenue
               FROM itp_inspections
               WHERE inspector_name IS NOT NULL AND inspector_name != ''
               GROUP BY inspector_name
               ORDER BY total DESC""",
        )
        rows = await cursor.fetchall()

    result = []
    for row in rows:
        total = row[1]
        admis = row[2]
        result.append({
            "inspector_name": row[0],
            "total": total,
            "admis": admis,
            "respins": row[3],
            "admis_rate": round((admis / total * 100), 1) if total > 0 else 0,
            "revenue": round(row[4] or 0, 2),
        })

    return result


# ────────── Expiring ──────────

@router.get("/expiring")
async def expiring_inspections(days: int = Query(30, ge=1, le=365)):
    """List vehicles with ITP expiring within N days."""
    today = date.today().isoformat()
    future = (date.today() + timedelta(days=days)).isoformat()

    async with get_db() as db:
        cursor = await db.execute(
            """SELECT id, plate_number, brand, model, owner_name, owner_phone,
                      expiry_date, inspection_date
               FROM itp_inspections
               WHERE expiry_date >= ? AND expiry_date <= ?
               ORDER BY expiry_date ASC""",
            (today, future),
        )
        rows = await cursor.fetchall()

    result = []
    today_date = date.today()
    for row in rows:
        item = dict(row)
        try:
            exp = date.fromisoformat(item["expiry_date"])
            item["days_remaining"] = (exp - today_date).days
        except (ValueError, TypeError):
            item["days_remaining"] = None
        result.append(item)

    return result


# ────────── Export ──────────

@router.get("/export/csv")
async def export_csv():
    """Export all inspections as CSV."""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM itp_inspections ORDER BY inspection_date DESC"
        )
        rows = await cursor.fetchall()
        items = [dict(row) for row in rows]

    if not items:
        raise HTTPException(404, "Nu exista inspectii de exportat")

    output = io.StringIO()
    headers = [
        "id", "plate_number", "vin", "brand", "model", "year", "fuel_type",
        "owner_name", "owner_phone", "inspection_date", "expiry_date",
        "result", "rejection_reasons", "price", "inspector_name", "notes",
        "created_at",
    ]
    writer = csv.DictWriter(output, fieldnames=headers, extrasaction="ignore")
    writer.writeheader()
    for item in items:
        writer.writerow(item)

    csv_bytes = output.getvalue().encode("utf-8-sig")

    await log_activity(
        action="itp.export",
        summary=f"Export CSV: {len(items)} inspectii",
        details={"format": "csv", "count": len(items)},
    )

    return StreamingResponse(
        io.BytesIO(csv_bytes),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="itp_inspectii.csv"'},
    )


@router.get("/export/excel")
async def export_excel():
    """Export all inspections as Excel (XLSX)."""
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill

    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM itp_inspections ORDER BY inspection_date DESC"
        )
        rows = await cursor.fetchall()
        items = [dict(row) for row in rows]

    if not items:
        raise HTTPException(404, "Nu exista inspectii de exportat")

    wb = Workbook()
    ws = wb.active
    ws.title = "Inspectii ITP"

    headers = [
        "ID", "Nr. Inmatriculare", "VIN", "Marca", "Model", "An", "Combustibil",
        "Proprietar", "Telefon", "Data ITP", "Data Expirare",
        "Rezultat", "Motiv Respingere", "Pret (RON)", "Inspector", "Note",
        "Data Creare",
    ]
    header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True)

    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.fill = header_fill
        cell.font = header_font

    field_keys = [
        "id", "plate_number", "vin", "brand", "model", "year", "fuel_type",
        "owner_name", "owner_phone", "inspection_date", "expiry_date",
        "result", "rejection_reasons", "price", "inspector_name", "notes",
        "created_at",
    ]
    admis_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
    respins_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")

    for row_idx, item in enumerate(items, 2):
        for col_idx, key in enumerate(field_keys, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=item.get(key, ""))
            # Color-code result column
            if key == "result":
                if item.get("result") == "admis":
                    cell.fill = admis_fill
                elif item.get("result") == "respins":
                    cell.fill = respins_fill

    # Auto-width columns
    for col in ws.columns:
        max_length = 0
        col_letter = col[0].column_letter
        for cell in col:
            try:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            except Exception:
                pass
        ws.column_dimensions[col_letter].width = min(max_length + 2, 40)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)

    await log_activity(
        action="itp.export",
        summary=f"Export Excel: {len(items)} inspectii",
        details={"format": "xlsx", "count": len(items)},
    )

    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="itp_inspectii.xlsx"'},
    )


# ────────── F5: Appointments / Calendar ──────────

# Allowed appointment status transitions (state machine)
_APPOINTMENT_TRANSITIONS: dict[str, list[str]] = {
    "scheduled":  ["confirmed", "cancelled"],
    "confirmed":  ["checked_in", "cancelled"],
    "checked_in": ["completed", "no_show", "cancelled"],
    "completed":  [],   # terminal state
    "cancelled":  [],   # terminal state
    "no_show":    [],   # terminal state
}


def _validate_appointment_transition(current: str, new: str) -> None:
    """Raise HTTP 400 if the status transition is not allowed."""
    allowed = _APPOINTMENT_TRANSITIONS.get(current, [])
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

@router.get("/appointments")
async def list_appointments(
    date_from: str = Query(None),
    date_to: str = Query(None),
    status: str = Query(None),
):
    """List appointments with optional date range and status filter."""
    conditions = []
    params = []
    if date_from:
        conditions.append("scheduled_date >= ?")
        params.append(date_from)
    if date_to:
        conditions.append("scheduled_date <= ?")
        params.append(date_to)
    if status:
        conditions.append("status = ?")
        params.append(status)
    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    async with get_db() as db:
        cursor = await db.execute(
            f"SELECT * FROM itp_appointments {where} ORDER BY scheduled_date ASC, scheduled_time ASC",
            params,
        )
        rows = await cursor.fetchall()
    return [dict(r) for r in rows]


@router.post("/appointments", status_code=201)
async def create_appointment(data: AppointmentCreate, force: bool = Query(False)):
    """Create a new ITP appointment. Checks for time conflicts unless force=True."""
    plate_upper = data.plate_number.upper().strip()
    conflict = None

    async with get_db() as db:
        # Check for overlapping appointments on the same date
        cursor = await db.execute(
            """SELECT id, plate_number, scheduled_time, duration_min
               FROM itp_appointments
               WHERE scheduled_date = ? AND status != 'cancelled'""",
            (data.scheduled_date,),
        )
        existing_appts = await cursor.fetchall()

        # Parse new appointment time range
        try:
            new_start_parts = data.scheduled_time.split(":")
            new_start_min = int(new_start_parts[0]) * 60 + int(new_start_parts[1])
            new_end_min = new_start_min + data.duration_min
        except (ValueError, IndexError):
            new_start_min = 0
            new_end_min = data.duration_min

        for appt in existing_appts:
            appt_dict = dict(appt)
            try:
                ex_parts = appt_dict["scheduled_time"].split(":")
                ex_start = int(ex_parts[0]) * 60 + int(ex_parts[1])
                ex_end = ex_start + (appt_dict["duration_min"] or 30)
            except (ValueError, IndexError):
                continue

            # Overlap check: two intervals [a,b) and [c,d) overlap if a < d and c < b
            if new_start_min < ex_end and ex_start < new_end_min:
                conflict = {
                    "existing_id": appt_dict["id"],
                    "existing_plate": appt_dict["plate_number"],
                    "existing_time": appt_dict["scheduled_time"],
                    "existing_duration": appt_dict["duration_min"],
                }
                break

        if conflict and not force:
            return {
                "warning": "Conflict de programare detectat",
                "conflict": conflict,
                "message": f"Exista deja o programare la {conflict['existing_time']} "
                           f"({conflict['existing_plate']}) in aceeasi zi. "
                           f"Folositi force=true pentru a crea oricum.",
                "created": False,
            }

        cursor = await db.execute(
            """INSERT INTO itp_appointments
               (plate_number, owner_name, owner_phone, scheduled_date, scheduled_time, duration_min, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (plate_upper, data.owner_name, data.owner_phone,
             data.scheduled_date, data.scheduled_time, data.duration_min, data.notes),
        )
        await db.commit()
        appt_id = cursor.lastrowid

    await log_activity(
        action="itp.appointment_create",
        summary=f"Programare ITP: {plate_upper} pe {data.scheduled_date} la {data.scheduled_time}"
                + (" (conflict fortat)" if conflict else ""),
        details={"id": appt_id, "plate": plate_upper, "date": data.scheduled_date,
                 "conflict": conflict},
    )

    result = {"id": appt_id, "message": "Programare creata cu succes.", "created": True}
    if conflict:
        result["warning"] = "Programare creata cu conflict de timp"
        result["conflict"] = conflict
    return result


@router.put("/appointments/{appt_id}")
async def update_appointment(appt_id: int, data: AppointmentUpdate):
    """Update an appointment."""
    updates = data.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(400, "Niciun camp de actualizat")
    if "plate_number" in updates and updates["plate_number"]:
        updates["plate_number"] = updates["plate_number"].upper().strip()
    async with get_db() as db:
        # Validate status transition if status is being changed
        if "status" in updates:
            row = await db.execute(
                "SELECT status FROM itp_appointments WHERE id = ?", (appt_id,)
            )
            existing = await row.fetchone()
            if existing is None:
                raise HTTPException(404, "Programarea nu a fost gasita")
            _validate_appointment_transition(existing["status"], updates["status"])
        fields = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [appt_id]
        cursor = await db.execute(
            f"UPDATE itp_appointments SET {fields} WHERE id = ?", values
        )
        await db.commit()
        if cursor.rowcount == 0:
            raise HTTPException(404, "Programarea nu a fost gasita")
    return {"message": "Programare actualizata cu succes."}


@router.delete("/appointments/{appt_id}")
async def delete_appointment(appt_id: int):
    """Delete an appointment."""
    async with get_db() as db:
        cursor = await db.execute(
            "DELETE FROM itp_appointments WHERE id = ?", (appt_id,)
        )
        await db.commit()
        if cursor.rowcount == 0:
            raise HTTPException(404, "Programarea nu a fost gasita")
    return {"message": "Programare stearsa cu succes."}


@router.put("/appointments/{appt_id}/complete")
async def complete_appointment(appt_id: int, inspection_id: int = None):
    """Mark appointment as completed, optionally linking to an inspection."""
    async with get_db() as db:
        row = await db.execute(
            "SELECT status FROM itp_appointments WHERE id = ?", (appt_id,)
        )
        existing = await row.fetchone()
        if existing is None:
            raise HTTPException(404, "Programarea nu a fost gasita")
        _validate_appointment_transition(existing["status"], "completed")
        cursor = await db.execute(
            "UPDATE itp_appointments SET status = 'completed', inspection_id = ? WHERE id = ?",
            (inspection_id, appt_id),
        )
        await db.commit()
        if cursor.rowcount == 0:
            raise HTTPException(404, "Programarea nu a fost gasita")
    return {"message": "Programare finalizata cu succes."}


# ────────── R4-24: Follow-up Alerts (next inspection due) ──────────

def _next_inspection_date(last_date_str: str, vehicle_type: str = "car") -> date | None:
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


@router.get("/followup/due-soon")
async def followup_due_soon(days: int = Query(30, ge=1, le=365)):
    """Vehicles with next inspection due within N days based on last inspection + 12 months.

    Returns list sorted by next_due_date ascending (most urgent first).
    Color coding: red (<7 days), yellow (7-14), green (14-30).
    """
    today_date = date.today()
    future_date = today_date + timedelta(days=days)

    async with get_db() as db:
        # Get the latest inspection per plate (most recent inspection_date)
        cursor = await db.execute(
            """SELECT plate_number, owner_name, MAX(inspection_date) as last_inspection_date,
                      brand, model, fuel_type
               FROM itp_inspections
               WHERE result = 'admis'
               GROUP BY UPPER(plate_number)
               ORDER BY last_inspection_date ASC"""
        )
        rows = await cursor.fetchall()

    result = []
    for row in rows:
        item = dict(row)
        last_date_str = item.get("last_inspection_date")
        if not last_date_str:
            continue
        next_due = _next_inspection_date(last_date_str)
        if next_due is None:
            continue
        # Only include if due within the requested window
        if next_due > future_date:
            continue
        days_remaining = (next_due - today_date).days
        result.append({
            "plate": item["plate_number"],
            "owner_name": item.get("owner_name") or "",
            "brand": item.get("brand") or "",
            "model": item.get("model") or "",
            "last_inspection_date": last_date_str,
            "next_due_date": next_due.isoformat(),
            "days_remaining": days_remaining,
        })

    # Sort by days_remaining ascending (most urgent first)
    result.sort(key=lambda x: x["days_remaining"])

    return result


# ────────── R4-26: No-show Tracking ──────────

class MarkShowupRequest(BaseModel):
    showed_up: bool


@router.put("/appointments/{appt_id}/mark-showup")
async def mark_appointment_showup(appt_id: int, data: MarkShowupRequest):
    """Mark whether a client showed up for their appointment."""
    async with get_db() as db:
        # Ensure showed_up column exists
        try:
            await db.execute(
                "ALTER TABLE itp_appointments ADD COLUMN showed_up INTEGER"
            )
            await db.commit()
        except Exception:
            pass  # Column already exists

        row = await db.execute(
            "SELECT status FROM itp_appointments WHERE id = ?", (appt_id,)
        )
        existing = await row.fetchone()
        if existing is None:
            raise HTTPException(404, "Programarea nu a fost gasita")
        new_status = "completed" if data.showed_up else "no_show"
        _validate_appointment_transition(existing["status"], new_status)

        cursor = await db.execute(
            "UPDATE itp_appointments SET showed_up = ?, status = ? WHERE id = ?",
            (1 if data.showed_up else 0, new_status, appt_id),
        )
        await db.commit()
        if cursor.rowcount == 0:
            raise HTTPException(404, "Programarea nu a fost gasita")

    label = "prezent" if data.showed_up else "neprezentare"
    await log_activity(
        action="itp.appointment_showup",
        summary=f"Programare #{appt_id}: {label}",
        details={"id": appt_id, "showed_up": data.showed_up},
    )
    return {"message": f"Programare marcata ca {label}."}


@router.get("/stats/noshow-rate")
async def stats_noshow_rate():
    """No-show statistics for appointments."""
    async with get_db() as db:
        # Ensure showed_up column exists
        try:
            await db.execute(
                "ALTER TABLE itp_appointments ADD COLUMN showed_up INTEGER"
            )
            await db.commit()
        except Exception:
            pass

        cursor = await db.execute("SELECT COUNT(*) FROM itp_appointments")
        total = (await cursor.fetchone())[0]

        cursor = await db.execute(
            "SELECT COUNT(*) FROM itp_appointments WHERE showed_up = 1"
        )
        showed_up = (await cursor.fetchone())[0]

        cursor = await db.execute(
            "SELECT COUNT(*) FROM itp_appointments WHERE showed_up = 0 AND showed_up IS NOT NULL"
        )
        no_shows = (await cursor.fetchone())[0]

    no_show_rate = round((no_shows / total * 100), 1) if total > 0 else 0

    return {
        "total_appointments": total,
        "showed_up": showed_up,
        "no_shows": no_shows,
        "no_show_rate_percent": no_show_rate,
    }
