"""
Invoice AI Extraction sub-router:
  - POST /api/invoice/scan            — OCR + AI extract received invoice data
  - POST /api/invoice/generate-from-calc — Pre-fill invoice from existing calculation
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import date, datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core.activity_log import log_activity
from app.db.database import get_db

from .router import GenerateFromCalcRequest, SCANNED_DIR

logger = logging.getLogger(__name__)

ai_router = APIRouter(prefix="/api/invoice", tags=["Invoice AI"])


# ═══════════════════════════════════════════
# Helper: safe text extraction from file
# ═══════════════════════════════════════════

def _extract_text_safe(filepath: str, max_chars: int = 2000) -> str:
    """Extract text from file (PDF, DOCX, text). Returns empty string on error."""
    try:
        p = filepath.lower()
        if p.endswith(".pdf"):
            import fitz
            doc = fitz.open(filepath)
            text = "\n".join(page.get_text() for page in doc)
            doc.close()
            return text[:max_chars].strip()
        elif p.endswith(".docx"):
            from docx import Document as DocxDocument
            doc = DocxDocument(filepath)
            text = "\n".join(para.text for para in doc.paragraphs)
            return text[:max_chars].strip()
        elif p.endswith((".txt", ".md", ".csv")):
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                return f.read(max_chars).strip()
    except Exception as exc:
        logger.warning("Text extraction failed for %s: %s", filepath, exc)
    return ""


async def _extract_client_with_ai(filepath: str) -> dict[str, Any]:
    """
    Foloseste AI (Gemini Flash) pentru a extrage informatii client din document.
    Returneaza dict cu campuri: name, cui, address, email, phone (ce gaseste).
    """
    from modules.ai.providers import ai_generate

    text = await asyncio.to_thread(_extract_text_safe, filepath, 2000)
    if not text:
        return {}

    prompt = f"""Analizeaza textul urmator si extrage informatii despre client/beneficiar.
Returneaza un JSON valid cu campurile (pune null daca nu gasesti cu certitudine):
- name: numele companiei sau persoanei (string sau null)
- cui: codul unic de inregistrare (string sau null)
- address: adresa (string sau null)
- email: adresa de email (string sau null)
- phone: numar de telefon (string sau null)
- confidence: cat de sigur esti pe datele extrase (0-100)

REGULI: Returneaza DOAR JSON valid, fara explicatii, fara markdown.
NU inventa date care nu sunt in text. Daca nu gasesti, pune null.
Daca textul nu contine informatii despre client, returneaza: {{"confidence": 0}}

Text document:
{text}"""

    system_prompt = (
        "Esti un asistent specializat in extragerea datelor din documente romanesti. "
        "Raspunzi EXCLUSIV cu JSON valid. NU inventa date care nu exista in text."
    )

    try:
        result = await ai_generate(prompt, system_prompt=system_prompt)
        response_text = result.get("text", "").strip()

        if response_text.startswith("```"):
            lines = response_text.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            response_text = "\n".join(lines).strip()

        parsed = json.loads(response_text)
        if isinstance(parsed, dict):
            allowed = {"name", "cui", "address", "email", "phone"}
            return {k: v for k, v in parsed.items() if k in allowed and v}
    except (json.JSONDecodeError, RuntimeError) as exc:
        logger.warning("AI client extraction parse error: %s", exc)

    return {}


# ═══════════════════════════════════════════
# Scanner facturi primite (OCR + AI)
# ═══════════════════════════════════════════

@ai_router.post("/scan")
async def scan_received_invoice(file: UploadFile = File(...)):
    """
    Upload factura primita (imagine/PDF), OCR + AI extrage:
    furnizor, suma, data, numar factura. Salveaza in received_invoices.
    """
    filename = file.filename or "scan_unknown"
    safe_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
    file_path = SCANNED_DIR / safe_name

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    raw_text = ""
    fname_lower = filename.lower()

    try:
        if fname_lower.endswith(".pdf"):
            import fitz
            doc = fitz.open(str(file_path))
            for page in doc:
                page_text = page.get_text()
                raw_text += page_text
                if not page_text.strip():
                    pix = page.get_pixmap(dpi=300)
                    img_path = str(file_path) + f"_page.png"
                    pix.save(img_path)
                    try:
                        import pytesseract
                        from PIL import Image
                        img = Image.open(img_path)
                        raw_text += pytesseract.image_to_string(img, lang="ron+eng")
                    except ImportError:
                        raw_text += "[pytesseract indisponibil]"
                    finally:
                        if os.path.exists(img_path):
                            os.unlink(img_path)
            doc.close()
        elif fname_lower.endswith((".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp")):
            try:
                import pytesseract
                from PIL import Image
                img = Image.open(str(file_path))
                raw_text = pytesseract.image_to_string(img, lang="ron+eng")
            except ImportError:
                raise HTTPException(500, "pytesseract nu e instalat")
        else:
            raise HTTPException(
                400,
                "Format nesuportat. Acceptate: PDF, PNG, JPG, TIFF, BMP, WEBP",
            )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Eroare OCR: %s", exc)
        raise HTTPException(500, f"Eroare la procesarea fisierului: {exc}")

    if not raw_text.strip():
        async with get_db() as db:
            cursor = await db.execute(
                """INSERT INTO received_invoices (file_path, raw_text, extracted_data)
                   VALUES (?, ?, ?)""",
                (str(file_path), "", "{}"),
            )
            await db.commit()
            scan_id = cursor.lastrowid

        return {
            "id": scan_id,
            "message": "Nu s-a detectat text in document.",
            "raw_text": "",
            "extracted": {},
        }

    extracted = {}
    try:
        from modules.ai.providers import ai_generate

        prompt = f"""Analizeaza textul urmator extras dintr-o factura primita si extrage urmatoarele informatii.
Returneaza un JSON valid cu EXACT aceste campuri (pune null daca nu gasesti cu certitudine):
- supplier_name: numele furnizorului/emitentului (string sau null)
- supplier_cui: CUI furnizor (string sau null)
- invoice_number: numarul facturii (string sau null)
- invoice_date: data facturii (format YYYY-MM-DD sau null)
- amount: suma fara TVA (number sau null)
- vat: suma TVA (number sau null)
- total: total de plata (number sau null)
- currency: moneda (RON, EUR, USD, sau null)
- confidence: cat de sigur esti pe datele extrase (0-100)

REGULI STRICTE:
- Returneaza DOAR JSON valid, fara explicatii, fara markdown.
- NU inventa date care nu sunt in text. Daca nu esti sigur, pune null.
- Daca textul nu contine o factura, returneaza: {{"confidence": 0}}

Exemplu output:
{{"supplier_name": "SC Exemplu SRL", "supplier_cui": "12345678", "invoice_number": "F-001", "invoice_date": "2026-01-15", "amount": 1000.00, "vat": 190.00, "total": 1190.00, "currency": "RON", "confidence": 85}}

Text factura:
{raw_text[:3000]}"""

        system_prompt = (
            "Esti un asistent specializat in extragerea datelor din facturi romanesti. "
            "Raspunzi EXCLUSIV cu JSON valid. NU inventa date care nu exista in text. "
            "Pune null pentru campurile pe care nu le gasesti cu certitudine."
        )
        result = await ai_generate(prompt, system_prompt=system_prompt)
        response_text = result.get("text", "").strip()

        if response_text.startswith("```"):
            lines = response_text.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            response_text = "\n".join(lines).strip()

        parsed = json.loads(response_text)
        if isinstance(parsed, dict):
            allowed = {"supplier_name", "supplier_cui", "invoice_number", "invoice_date",
                       "amount", "vat", "total", "currency"}
            extracted = {k: v for k, v in parsed.items() if k in allowed and v is not None}
    except (json.JSONDecodeError, RuntimeError, Exception) as exc:
        logger.warning("AI extraction pentru factura scanata a esuat: %s", exc)

    async with get_db() as db:
        cursor = await db.execute(
            """INSERT INTO received_invoices
               (supplier_name, supplier_cui, invoice_number, invoice_date,
                amount, vat, total, currency, file_path, raw_text, extracted_data)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                extracted.get("supplier_name"),
                extracted.get("supplier_cui"),
                extracted.get("invoice_number"),
                extracted.get("invoice_date"),
                float(extracted["amount"]) if extracted.get("amount") else 0,
                float(extracted["vat"]) if extracted.get("vat") else 0,
                float(extracted["total"]) if extracted.get("total") else 0,
                extracted.get("currency", "RON"),
                str(file_path),
                raw_text,
                json.dumps(extracted, ensure_ascii=False),
            ),
        )
        await db.commit()
        scan_id = cursor.lastrowid

    await log_activity(
        action="invoice.scan",
        summary=f"Factura scanata: {extracted.get('supplier_name', 'necunoscut')} — {extracted.get('total', '?')} {extracted.get('currency', 'RON')}",
        details={
            "scan_id": scan_id,
            "filename": filename,
            "extracted": extracted,
        },
    )

    return {
        "id": scan_id,
        "message": "Factura scanata si procesata cu succes.",
        "raw_text": raw_text.strip()[:2000],
        "extracted": extracted,
    }


# ═══════════════════════════════════════════
# AI-assisted: generate from calculation
# ═══════════════════════════════════════════

@ai_router.post("/generate-from-calc")
async def generate_from_calc(data: GenerateFromCalcRequest):
    """
    Pre-fill date factura din calculul de pret existent.

    Citeste din uploads + calculations, foloseste AI (Gemini Flash)
    pentru a extrage informatii client din document (daca e disponibil).
    Returneaza date pre-completate — NU salveaza in DB.
    """
    async with get_db() as db:
        cursor = await db.execute(
            """SELECT c.*, u.filename, u.original_name, u.filepath, u.file_type
               FROM calculations c
               JOIN uploads u ON c.upload_id = u.id
               WHERE c.id = ?""",
            (data.calculation_id,),
        )
        calc_row = await cursor.fetchone()

    if not calc_row:
        raise HTTPException(
            status_code=404,
            detail="Calculul nu a fost gasit sau nu are upload asociat.",
        )

    calc = dict(calc_row)
    final_price = calc.get("final_price", 0) or calc.get("estimated_price", 0) or 0
    doc_name = calc.get("original_name") or calc.get("filename") or "Document"
    filepath = calc.get("filepath", "")

    items = [{
        "description": f"Traducere document: {doc_name}",
        "quantity": 1,
        "unit_price": round(float(final_price), 2),
        "total": round(float(final_price), 2),
    }]

    client_suggestion: dict[str, Any] = {}
    if filepath and Path(filepath).exists():
        try:
            client_suggestion = await _extract_client_with_ai(filepath)
        except Exception as exc:
            logger.warning("AI client extraction failed: %s", exc)

    result = {
        "calculation_id": data.calculation_id,
        "suggested_client": client_suggestion,
        "items": items,
        "subtotal": items[0]["total"],
        "vat_percent": 0,
        "vat_amount": 0,
        "total": items[0]["total"],
        "date": date.today().isoformat(),
        "notes": f"Generat din calculul #{data.calculation_id} — {doc_name}",
        "source": "calculation",
    }

    await log_activity(
        action="invoice.generate_from_calc",
        summary=f"Pre-fill factura din calcul #{data.calculation_id}",
        details={"calculation_id": data.calculation_id, "total": result["total"]},
    )
    return result
