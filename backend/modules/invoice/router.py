"""
Invoice module — shared models, helpers, and constants.

All endpoints are split into sub-routers:
  - crud.py          — Client CRUD, Invoice CRUD, series, overdue, email, ANAF
  - ai_extraction.py — OCR scan, AI extract, generate-from-calc
  - pdf_generation.py — PDF, offer PDF, export CSV/Excel, templates
  - reports.py        — Monthly report, summary report

This file exposes only Pydantic models, helper functions, and directory constants
used by the sub-routers above.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import date
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.config import settings
from app.db.database import get_db

logger = logging.getLogger(__name__)

# --- Directory constants ---
INVOICES_DIR = settings.data_dir / "invoices"
INVOICES_DIR.mkdir(parents=True, exist_ok=True)

TEMPLATES_DIR = settings.data_dir / "templates"
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

SCANNED_DIR = settings.data_dir / "scanned_invoices"
SCANNED_DIR.mkdir(parents=True, exist_ok=True)


# ═══════════════════════════════════════════
# Pydantic models
# ═══════════════════════════════════════════

class ClientCreate(BaseModel):
    name: str
    cui: Optional[str] = None
    reg_com: Optional[str] = None
    address: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    notes: Optional[str] = None
    default_payment_terms: Optional[str] = None  # net_15, net_30, net_45, immediate, or custom


class ClientUpdate(BaseModel):
    name: Optional[str] = None
    cui: Optional[str] = None
    reg_com: Optional[str] = None
    address: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    notes: Optional[str] = None
    default_payment_terms: Optional[str] = None


class InvoiceItem(BaseModel):
    description: str
    quantity: float = 1.0
    unit_price: float = 0.0
    total: float = 0.0


class InvoiceCreate(BaseModel):
    client_id: int
    items: list[InvoiceItem]
    series_prefix: Optional[str] = None
    date: str = Field(default_factory=lambda: date.today().isoformat())
    due_date: Optional[str] = None
    notes: Optional[str] = None
    vat_percent: float = 0.0


class OfferPdfRequest(BaseModel):
    client_name: str
    client_address: Optional[str] = None
    items: list[InvoiceItem]
    notes: Optional[str] = None
    validity_days: int = 30


class InvoiceUpdate(BaseModel):
    client_id: Optional[int] = None
    items: Optional[list[InvoiceItem]] = None
    date: Optional[str] = None
    due_date: Optional[str] = None
    notes: Optional[str] = None
    vat_percent: Optional[float] = None


class StatusUpdate(BaseModel):
    status: str  # draft, sent, paid, cancelled


class GenerateFromCalcRequest(BaseModel):
    calculation_id: int


class InvoiceSeriesCreate(BaseModel):
    prefix: str
    name: str
    description: str | None = None


class InvoiceSeriesUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    active: bool | None = None


class SendEmailRequest(BaseModel):
    to_email: str
    subject: Optional[str] = None
    body: Optional[str] = None


class TemplateGenerateRequest(BaseModel):
    template_name: str
    data: dict[str, Any]
    output_format: str = "docx"  # docx or pdf


class ItemPresetCreate(BaseModel):
    description: str
    unit_price: float = 0.0
    unit: str = "buc"
    category: str = "general"


class RecurringSet(BaseModel):
    frequency: str = "monthly"  # monthly, quarterly, yearly
    next_due: Optional[str] = None  # YYYY-MM-DD; auto-calculated if None


class PartialPayment(BaseModel):
    amount: float
    payment_date: str = Field(default_factory=lambda: date.today().isoformat())
    method: str = "transfer"  # transfer, cash, card
    notes: Optional[str] = None


class BatchPdfRequest(BaseModel):
    invoice_ids: Optional[list[int]] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    client_id: Optional[int] = None


class FromCalculationRequest(BaseModel):
    word_count: int
    price: float
    document_type: Optional[str] = None
    source_lang: str = "EN"
    target_lang: str = "RO"
    client_id: Optional[int] = None


# ═══════════════════════════════════════════
# Helper functions
# ═══════════════════════════════════════════

async def _next_invoice_number(series_prefix: str | None = None) -> str:
    """Generate next sequential invoice number using configurable series."""
    year = date.today().year
    async with get_db() as db:
        if not series_prefix:
            cursor = await db.execute(
                "SELECT prefix FROM invoice_series WHERE is_default = 1 AND active = 1 LIMIT 1"
            )
            row = await cursor.fetchone()
            series_prefix = row["prefix"] if row else "RCC"
        prefix = f"{series_prefix}-{year}-"
        cursor = await db.execute(
            "SELECT invoice_number FROM invoices WHERE invoice_number LIKE ? ORDER BY invoice_number DESC LIMIT 1",
            (f"{prefix}%",),
        )
        row = await cursor.fetchone()
    if row:
        try:
            last_num = int(row["invoice_number"].split("-")[-1])
        except (ValueError, IndexError):
            last_num = 0
        return f"{prefix}{last_num + 1:03d}"
    return f"{prefix}001"


def _calculate_totals(items: list[InvoiceItem], vat_percent: float) -> tuple[float, float, float]:
    """Calculate subtotal, VAT amount, and total from items."""
    subtotal = sum(item.quantity * item.unit_price for item in items)
    vat_amount = subtotal * vat_percent / 100.0
    total = subtotal + vat_amount
    return round(subtotal, 2), round(vat_amount, 2), round(total, 2)


def _items_to_json(items: list[InvoiceItem]) -> str:
    """Serialize items list to JSON string."""
    return json.dumps(
        [item.model_dump() for item in items],
        ensure_ascii=False,
    )


def _items_from_json(json_str: str) -> list[dict]:
    """Deserialize items JSON string."""
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return []


def _row_to_dict(row) -> dict:
    """Convert aiosqlite Row to dict, parsing items_json."""
    d = dict(row)
    if "items_json" in d:
        d["items"] = _items_from_json(d.pop("items_json"))
    return d


# ═══════════════════════════════════════════
# PDF builder (used by pdf_generation.py and crud.py)
# ═══════════════════════════════════════════

def _draw_watermark(canvas_obj, doc_obj, watermark_text: str) -> None:
    """
    Draw a large diagonal watermark on the PDF page.
    Used for DRAFT and ANULAT statuses.
    """
    from reportlab.lib.pagesizes import A4
    import math

    if not watermark_text:
        return

    width, height = A4
    canvas_obj.saveState()
    canvas_obj.setFont("Helvetica-Bold", 72)
    canvas_obj.setFillColorRGB(0.85, 0.2, 0.2, alpha=0.15)
    canvas_obj.translate(width / 2, height / 2)
    canvas_obj.rotate(45)
    canvas_obj.drawCentredString(0, 0, watermark_text)
    canvas_obj.restoreState()


def _build_invoice_pdf(invoice: dict, items: list[dict], output_path: str) -> None:
    """
    Genereaza PDF profesional pentru factura.

    Header: CIP Inspection SRL / CUI 43978110
    Continut: detalii client, tabel articole, totaluri
    Footer: detalii bancare placeholder
    Watermark: DRAFT (pentru draft) sau ANULAT (pentru cancelled)
    """
    import html as _html
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm, mm
    from reportlab.platypus import (
        SimpleDocTemplate,
        Table,
        TableStyle,
        Paragraph,
        Spacer,
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

    # Determine watermark text based on status
    status = invoice.get("status", "draft").lower()
    watermark_text = ""
    if status == "draft":
        watermark_text = "DRAFT"
    elif status == "cancelled":
        watermark_text = "ANULAT"

    def _page_callback(canvas_obj, doc_obj):
        """Called on every page to draw watermark if needed."""
        if watermark_text:
            _draw_watermark(canvas_obj, doc_obj, watermark_text)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        topMargin=1.5 * cm,
        bottomMargin=2 * cm,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
    )

    styles = getSampleStyleSheet()

    style_title = ParagraphStyle(
        "InvoiceTitle",
        parent=styles["Heading1"],
        fontSize=18,
        alignment=TA_CENTER,
        spaceAfter=6,
        textColor=colors.HexColor("#1a365d"),
    )
    style_company = ParagraphStyle(
        "Company",
        parent=styles["Normal"],
        fontSize=10,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#4a5568"),
    )
    style_section = ParagraphStyle(
        "Section",
        parent=styles["Heading2"],
        fontSize=11,
        spaceBefore=12,
        spaceAfter=4,
        textColor=colors.HexColor("#2d3748"),
    )
    style_normal = ParagraphStyle(
        "NormalCustom",
        parent=styles["Normal"],
        fontSize=9,
        leading=13,
    )
    style_right = ParagraphStyle(
        "RightAlign",
        parent=styles["Normal"],
        fontSize=9,
        alignment=TA_RIGHT,
    )
    style_footer = ParagraphStyle(
        "Footer",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.HexColor("#718096"),
        alignment=TA_CENTER,
    )

    elements = []

    # --- HEADER ---
    _co_name = os.environ.get("COMPANY_NAME", "CIP Inspection SRL")
    _co_cui = os.environ.get("COMPANY_CUI", "43978110")
    _co_addr = os.environ.get("COMPANY_ADDRESS", "")
    _co_reg = os.environ.get("COMPANY_REG", "J02/597/2021")
    elements.append(Paragraph("FACTURA", style_title))
    elements.append(Paragraph(_co_name, style_company))
    elements.append(Paragraph(f"CUI: {_co_cui} | {_co_reg}", style_company))
    if _co_addr:
        elements.append(Paragraph(_co_addr, style_company))
    elements.append(Spacer(1, 8 * mm))

    # --- Invoice meta info ---
    inv_number = invoice.get("invoice_number", "")
    inv_date = invoice.get("date", "")
    inv_due = invoice.get("due_date", "")
    inv_status = invoice.get("status", "draft").upper()

    meta_data = [
        [
            Paragraph(f"<b>Nr. factura:</b> {inv_number}", style_normal),
            Paragraph(f"<b>Data:</b> {inv_date}", style_normal),
        ],
        [
            Paragraph(f"<b>Status:</b> {inv_status}", style_normal),
            Paragraph(f"<b>Scadenta:</b> {inv_due or 'N/A'}", style_normal),
        ],
    ]
    meta_table = Table(meta_data, colWidths=[9 * cm, 8 * cm])
    meta_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 6 * mm))

    # --- CLIENT INFO ---
    elements.append(Paragraph("Date client", style_section))
    # Escape all user-provided strings before embedding in ReportLab XML/HTML
    # to prevent tag injection (e.g. <b>, <script>) from corrupting the PDF.
    client_name = _html.escape(invoice.get("client_name", "N/A"))
    client_cui = _html.escape(invoice.get("client_cui", "") or "")
    client_reg = _html.escape(invoice.get("client_reg_com", "") or "")
    client_addr = _html.escape(invoice.get("client_address", "") or "")
    client_email = _html.escape(invoice.get("client_email", "") or "")
    client_phone = _html.escape(invoice.get("client_phone", "") or "")

    client_lines = [f"<b>{client_name}</b>"]
    if client_cui:
        client_lines.append(f"CUI: {client_cui}")
    if client_reg:
        client_lines.append(f"Reg. Com.: {client_reg}")
    if client_addr:
        client_lines.append(f"Adresa: {client_addr}")
    if client_email:
        client_lines.append(f"Email: {client_email}")
    if client_phone:
        client_lines.append(f"Tel: {client_phone}")
    elements.append(Paragraph("<br/>".join(client_lines), style_normal))
    elements.append(Spacer(1, 6 * mm))

    # --- ITEMS TABLE ---
    elements.append(Paragraph("Articole", style_section))

    header_row = [
        Paragraph("<b>Nr.</b>", style_normal),
        Paragraph("<b>Descriere</b>", style_normal),
        Paragraph("<b>Cant.</b>", style_normal),
        Paragraph("<b>Pret unitar</b>", style_normal),
        Paragraph("<b>Total</b>", style_normal),
    ]

    table_data = [header_row]
    for idx, item in enumerate(items, 1):
        desc = _html.escape(item.get("description", ""))
        qty = item.get("quantity", 1)
        unit_price = item.get("unit_price", 0)
        item_total = item.get("total", qty * unit_price)
        table_data.append([
            Paragraph(str(idx), style_normal),
            Paragraph(desc, style_normal),
            Paragraph(f"{qty:.2f}", style_right),
            Paragraph(f"{unit_price:.2f} RON", style_right),
            Paragraph(f"{item_total:.2f} RON", style_right),
        ])

    items_table = Table(
        table_data,
        colWidths=[1.2 * cm, 8.5 * cm, 2 * cm, 2.8 * cm, 2.8 * cm],
        repeatRows=1,
    )
    items_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#edf2f7")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#2d3748")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e0")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7fafc")]),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 4 * mm))

    # --- TOTALS ---
    subtotal = invoice.get("subtotal", 0)
    vat_pct = invoice.get("vat_percent", 0)
    vat_amount = invoice.get("vat_amount", 0)
    total = invoice.get("total", 0)

    totals_data = [
        ["", Paragraph(f"<b>Subtotal:</b>", style_right), Paragraph(f"{subtotal:.2f} RON", style_right)],
    ]
    if vat_pct > 0:
        totals_data.append(
            ["", Paragraph(f"<b>TVA ({vat_pct:.0f}%):</b>", style_right), Paragraph(f"{vat_amount:.2f} RON", style_right)]
        )
    totals_data.append(
        ["", Paragraph(f"<b>TOTAL:</b>", style_right), Paragraph(f"<b>{total:.2f} RON</b>", style_right)]
    )

    totals_table = Table(totals_data, colWidths=[10 * cm, 4 * cm, 3.3 * cm])
    totals_table.setStyle(TableStyle([
        ("LINEABOVE", (1, -1), (-1, -1), 1, colors.HexColor("#2d3748")),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    elements.append(totals_table)

    # --- NOTES ---
    notes = invoice.get("notes", "")
    if notes:
        elements.append(Spacer(1, 6 * mm))
        elements.append(Paragraph("Observatii", style_section))
        elements.append(Paragraph(notes, style_normal))

    # --- FOOTER ---
    elements.append(Spacer(1, 12 * mm))
    elements.append(Paragraph("_" * 70, style_footer))
    elements.append(Spacer(1, 2 * mm))
    # Citeste date companie din env vars
    company_name = os.environ.get("COMPANY_NAME", "CIP Inspection SRL")
    company_cui = os.environ.get("COMPANY_CUI", "43978110")
    company_reg = os.environ.get("COMPANY_REG", "J02/597/2021")
    iban = invoice.get("company_iban") or os.environ.get("COMPANY_IBAN", "")
    bank = invoice.get("company_bank") or os.environ.get("COMPANY_BANK", "")
    company_addr = os.environ.get("COMPANY_ADDRESS", "")
    company_phone = os.environ.get("COMPANY_PHONE", "")
    company_email = os.environ.get("COMPANY_EMAIL", "")
    bank_info = ""
    if iban:
        bank_info = f" | IBAN: {iban}"
        if bank:
            bank_info += f" | Banca: {bank}"
    elements.append(Paragraph(
        f"{company_name} | CUI: {company_cui} | {company_reg}{bank_info}",
        style_footer,
    ))
    addr_parts = []
    if company_addr:
        addr_parts.append(company_addr)
    if company_phone:
        addr_parts.append(f"Tel: {company_phone}")
    if company_email:
        addr_parts.append(company_email)
    if addr_parts:
        elements.append(Paragraph(" | ".join(addr_parts), style_footer))
    elements.append(Paragraph(
        "Factura generata automat — Roland Command Center",
        style_footer,
    ))

    doc.build(elements, onFirstPage=_page_callback, onLaterPages=_page_callback)
