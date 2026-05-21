"""
e-Factura XML generator — UBL 2.1 / RO_CIUS format.

Generates valid XML per ANAF RO_CIUS standard for electronic invoicing.
Used by the invoice CRUD endpoint to export invoices as e-Factura XML.
"""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from datetime import date
from typing import Any

logger = logging.getLogger(__name__)

# UBL 2.1 namespaces
NS_INVOICE = "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
NS_CAC = "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
NS_CBC = "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"

CUSTOMIZATION_ID = (
    "urn:cen.eu:en16931:2017#compliant#urn:efactura.mfinante.ro:CIUS-RO:1.0.1"
)


def _el(parent: ET.Element, tag: str, text: str | None = None, attrib: dict | None = None) -> ET.Element:
    """Create a sub-element with optional text and attributes."""
    elem = ET.SubElement(parent, tag, attrib or {})
    if text is not None:
        elem.text = str(text)
    return elem


def _add_party(parent: ET.Element, role_tag: str, name: str, cui: str,
               address: str | None = None, iban: str | None = None) -> None:
    """Add AccountingSupplierParty or AccountingCustomerParty block."""
    party_wrapper = _el(parent, f"{{{NS_CAC}}}{role_tag}")
    party = _el(party_wrapper, f"{{{NS_CAC}}}Party")

    # PartyName
    party_name = _el(party, f"{{{NS_CAC}}}PartyName")
    _el(party_name, f"{{{NS_CBC}}}Name", name)

    # PostalAddress
    postal = _el(party, f"{{{NS_CAC}}}PostalAddress")
    if address:
        _el(postal, f"{{{NS_CBC}}}StreetName", address)
    _el(_el(postal, f"{{{NS_CAC}}}Country"), f"{{{NS_CBC}}}IdentificationCode", "RO")

    # PartyTaxScheme (CUI)
    tax_scheme = _el(party, f"{{{NS_CAC}}}PartyTaxScheme")
    # Prefix RO if numeric CUI without prefix
    cui_clean = cui.strip() if cui else ""
    if cui_clean and not cui_clean.upper().startswith("RO"):
        cui_clean = f"RO{cui_clean}"
    _el(tax_scheme, f"{{{NS_CBC}}}CompanyID", cui_clean)
    _el(_el(tax_scheme, f"{{{NS_CAC}}}TaxScheme"), f"{{{NS_CBC}}}ID", "VAT")

    # PartyLegalEntity
    legal = _el(party, f"{{{NS_CAC}}}PartyLegalEntity")
    _el(legal, f"{{{NS_CBC}}}RegistrationName", name)
    _el(legal, f"{{{NS_CBC}}}CompanyID", cui_clean)

    # Financial account (IBAN) — only for supplier
    if iban and role_tag == "AccountingSupplierParty":
        fin_account = _el(party_wrapper, f"{{{NS_CAC}}}FinancialAccount")
        _el(fin_account, f"{{{NS_CBC}}}ID", iban.strip())


def generate_efactura_xml(
    invoice: dict[str, Any],
    client: dict[str, Any],
    company: dict[str, Any],
    items: list[dict[str, Any]],
) -> str:
    """
    Generate e-Factura XML in UBL 2.1 / RO_CIUS format.

    Args:
        invoice: Dict with keys: invoice_number, date, due_date, currency,
                 subtotal, vat_percent, vat_amount, total, notes
        client:  Dict with keys: name, cui, address
        company: Dict with keys: name, cui, address, iban
        items:   List of dicts with keys: description, quantity, unit_price

    Returns:
        XML string with xml declaration.
    """
    # Register namespaces for clean output
    ET.register_namespace("", NS_INVOICE)
    ET.register_namespace("cac", NS_CAC)
    ET.register_namespace("cbc", NS_CBC)

    root = ET.Element(f"{{{NS_INVOICE}}}Invoice")

    # --- Header ---
    _el(root, f"{{{NS_CBC}}}CustomizationID", CUSTOMIZATION_ID)
    _el(root, f"{{{NS_CBC}}}ID", invoice.get("invoice_number", ""))
    _el(root, f"{{{NS_CBC}}}IssueDate", invoice.get("date", date.today().isoformat()))

    due_date = invoice.get("due_date")
    if due_date:
        _el(root, f"{{{NS_CBC}}}DueDate", due_date)

    _el(root, f"{{{NS_CBC}}}InvoiceTypeCode", "380")

    notes = invoice.get("notes")
    if notes:
        _el(root, f"{{{NS_CBC}}}Note", notes)

    currency = invoice.get("currency", "RON")
    _el(root, f"{{{NS_CBC}}}DocumentCurrencyCode", currency)

    # --- Supplier (company) ---
    _add_party(
        root,
        "AccountingSupplierParty",
        name=company.get("name", ""),
        cui=company.get("cui", ""),
        address=company.get("address"),
        iban=company.get("iban"),
    )

    # --- Customer (client) ---
    _add_party(
        root,
        "AccountingCustomerParty",
        name=client.get("name", ""),
        cui=client.get("cui", ""),
        address=client.get("address"),
    )

    # --- Tax Total ---
    vat_percent = float(invoice.get("vat_percent", 0))
    vat_amount = float(invoice.get("vat_amount", 0))
    subtotal = float(invoice.get("subtotal", 0))
    total = float(invoice.get("total", 0))

    tax_total = _el(root, f"{{{NS_CAC}}}TaxTotal")
    _el(tax_total, f"{{{NS_CBC}}}TaxAmount", f"{vat_amount:.2f}",
        {"currencyID": currency})

    tax_subtotal = _el(tax_total, f"{{{NS_CAC}}}TaxSubtotal")
    _el(tax_subtotal, f"{{{NS_CBC}}}TaxableAmount", f"{subtotal:.2f}",
        {"currencyID": currency})
    _el(tax_subtotal, f"{{{NS_CBC}}}TaxAmount", f"{vat_amount:.2f}",
        {"currencyID": currency})

    tax_category = _el(tax_subtotal, f"{{{NS_CAC}}}TaxCategory")
    _el(tax_category, f"{{{NS_CBC}}}ID", "S" if vat_percent > 0 else "O")
    _el(tax_category, f"{{{NS_CBC}}}Percent", f"{vat_percent:.2f}")
    tax_scheme = _el(tax_category, f"{{{NS_CAC}}}TaxScheme")
    _el(tax_scheme, f"{{{NS_CBC}}}ID", "VAT")

    # --- Legal Monetary Total ---
    monetary = _el(root, f"{{{NS_CAC}}}LegalMonetaryTotal")
    _el(monetary, f"{{{NS_CBC}}}LineExtensionAmount", f"{subtotal:.2f}",
        {"currencyID": currency})
    _el(monetary, f"{{{NS_CBC}}}TaxExclusiveAmount", f"{subtotal:.2f}",
        {"currencyID": currency})
    _el(monetary, f"{{{NS_CBC}}}TaxInclusiveAmount", f"{total:.2f}",
        {"currencyID": currency})
    _el(monetary, f"{{{NS_CBC}}}PayableAmount", f"{total:.2f}",
        {"currencyID": currency})

    # --- Invoice Lines ---
    for idx, item in enumerate(items, start=1):
        qty = float(item.get("quantity", 1))
        unit_price = float(item.get("unit_price", 0))
        line_total = round(qty * unit_price, 2)

        line = _el(root, f"{{{NS_CAC}}}InvoiceLine")
        _el(line, f"{{{NS_CBC}}}ID", str(idx))
        _el(line, f"{{{NS_CBC}}}InvoicedQuantity", f"{qty:.2f}",
            {"unitCode": "EA"})
        _el(line, f"{{{NS_CBC}}}LineExtensionAmount", f"{line_total:.2f}",
            {"currencyID": currency})

        # Item details
        inv_item = _el(line, f"{{{NS_CAC}}}Item")
        _el(inv_item, f"{{{NS_CBC}}}Name", item.get("description", ""))

        # ClassifiedTaxCategory
        classified_tax = _el(inv_item, f"{{{NS_CAC}}}ClassifiedTaxCategory")
        _el(classified_tax, f"{{{NS_CBC}}}ID", "S" if vat_percent > 0 else "O")
        _el(classified_tax, f"{{{NS_CBC}}}Percent", f"{vat_percent:.2f}")
        cls_tax_scheme = _el(classified_tax, f"{{{NS_CAC}}}TaxScheme")
        _el(cls_tax_scheme, f"{{{NS_CBC}}}ID", "VAT")

        # Price
        price_el = _el(line, f"{{{NS_CAC}}}Price")
        _el(price_el, f"{{{NS_CBC}}}PriceAmount", f"{unit_price:.2f}",
            {"currencyID": currency})

    # Serialize to string
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")

    from io import StringIO
    buf = StringIO()
    tree.write(buf, xml_declaration=True, encoding="unicode")
    return buf.getvalue()
