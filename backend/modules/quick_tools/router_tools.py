"""
API endpoints pentru Quick Tools — BNR curs valutar, ANAF CUI, convertor numere.

Endpoints:
  GET  /api/quick-tools/exchange-rate              — curs BNR curent (cache 1h)
  GET  /api/quick-tools/exchange-rate/convert      — conversie valuta
  GET  /api/quick-tools/company-check/{cui}        — verificare CUI la ANAF
  GET  /api/quick-tools/number-to-words            — numar in litere (romana)
"""

from __future__ import annotations

import logging
import time
import xml.etree.ElementTree as ET
from datetime import date

import httpx
from fastapi import APIRouter, HTTPException, Query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/quick-tools", tags=["quick_tools"])

# ---------------------------------------------------------------------------
# BNR Exchange Rate — cache in-memory 1 hour
# ---------------------------------------------------------------------------

_bnr_cache: dict = {"data": None, "ts": 0.0}
_BNR_URL = "https://www.bnr.ro/nbrfxrates.xml"
_BNR_NS = {"bnr": "http://www.bnr.ro/xsd"}
_BNR_CACHE_TTL = 3600  # 1 hour


async def _fetch_bnr_rates() -> dict:
    """Fetch and parse BNR XML, return structured rates dict."""
    now = time.time()
    if _bnr_cache["data"] and (now - _bnr_cache["ts"]) < _BNR_CACHE_TTL:
        return _bnr_cache["data"]

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(_BNR_URL)
        resp.raise_for_status()

    root = ET.fromstring(resp.text)

    # Extract date from <Cube date="YYYY-MM-DD">
    cube = root.find(".//bnr:Body/bnr:Cube", _BNR_NS)
    if cube is None:
        raise HTTPException(502, "BNR XML: nu s-a gasit elementul Cube")

    rate_date = cube.attrib.get("date", str(date.today()))

    rates: dict[str, float] = {}
    for rate_el in cube.findall("bnr:Rate", _BNR_NS):
        currency = rate_el.attrib.get("currency", "")
        multiplier = int(rate_el.attrib.get("multiplier", "1"))
        try:
            value = float(rate_el.text) / multiplier
        except (TypeError, ValueError):
            continue
        rates[currency] = round(value, 6)

    key_currencies = ["EUR", "USD", "GBP", "CHF", "HUF"]
    key_rates = {k: rates[k] for k in key_currencies if k in rates}

    result = {
        "date": rate_date,
        "base": "RON",
        "rates": rates,
        "key_rates": key_rates,
    }

    _bnr_cache["data"] = result
    _bnr_cache["ts"] = now
    return result


@router.get("/exchange-rate")
async def get_exchange_rate():
    """Curs valutar BNR curent (cache 1 ora)."""
    try:
        return await _fetch_bnr_rates()
    except httpx.HTTPError as exc:
        logger.error("BNR fetch error: %s", exc)
        raise HTTPException(502, f"Nu s-a putut accesa BNR: {exc}") from exc


@router.get("/exchange-rate/convert")
async def convert_currency(
    amount: float = Query(..., description="Suma de convertit"),
    from_currency: str = Query(..., alias="from", description="Moneda sursa (ex: EUR)"),
    to_currency: str = Query(..., alias="to", description="Moneda destinatie (ex: RON)"),
):
    """Conversie valuta folosind cursul BNR."""
    try:
        data = await _fetch_bnr_rates()
    except httpx.HTTPError as exc:
        logger.error("BNR fetch error: %s", exc)
        raise HTTPException(502, f"Nu s-a putut accesa BNR: {exc}") from exc

    rates = data["rates"]
    fr = from_currency.upper().strip()
    to = to_currency.upper().strip()

    # Convert to RON first, then to target
    if fr == "RON":
        amount_ron = amount
    elif fr in rates:
        amount_ron = amount * rates[fr]
    else:
        raise HTTPException(400, f"Moneda sursa necunoscuta: {fr}")

    if to == "RON":
        result = amount_ron
    elif to in rates:
        result = amount_ron / rates[to]
    else:
        raise HTTPException(400, f"Moneda destinatie necunoscuta: {to}")

    return {
        "amount": amount,
        "from": fr,
        "to": to,
        "rate_date": data["date"],
        "result": round(result, 2),
    }


# ---------------------------------------------------------------------------
# ANAF CUI Verification
# ---------------------------------------------------------------------------

_ANAF_URL = "https://webservicesp.anaf.ro/api/PlatitorTvaRest/api/v8/ws/tva"
_anaf_cache: dict = {}  # {cui_int: {"data": ..., "ts": float}}
_ANAF_CACHE_TTL = 86400  # 24 hours


@router.get("/company-check/{cui}")
async def check_company(cui: str):
    """Verificare firma dupa CUI la ANAF."""
    # Clean CUI: strip whitespace, uppercase, remove RO prefix
    clean = cui.strip().upper()
    if clean.startswith("RO"):
        clean = clean[2:]
    clean = clean.strip()

    try:
        cui_int = int(clean)
    except ValueError:
        raise HTTPException(400, f"CUI invalid: '{cui}'. Trebuie sa fie numeric.")

    # Check cache (24h TTL)
    cached = _anaf_cache.get(cui_int)
    if cached and (time.time() - cached["ts"]) < _ANAF_CACHE_TTL:
        return cached["data"]

    today_str = date.today().strftime("%Y-%m-%d")
    payload = [{"cui": cui_int, "data": today_str}]

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(_ANAF_URL, json=payload)
            resp.raise_for_status()
    except httpx.HTTPError as exc:
        logger.error("ANAF request error: %s", exc)
        raise HTTPException(
            502,
            "Serviciul ANAF nu este disponibil momentan. "
            "Incercati din nou mai tarziu.",
        ) from exc

    try:
        body = resp.json()
    except Exception:
        raise HTTPException(502, "Raspuns invalid de la ANAF (nu este JSON).")

    found_list = body.get("found", [])
    if not found_list:
        result = {
            "found": False,
            "cui": cui_int,
            "denumire": None,
            "adresa": None,
            "telefon": None,
            "cod_postal": None,
            "stare": None,
            "tva": None,
            "data_verificare": today_str,
        }
    else:
        item = found_list[0]
        general = item.get("date_generale", {})
        tva_info = item.get("inregistrare_scop_Tva", {})

        result = {
            "found": True,
            "cui": cui_int,
            "denumire": general.get("denumire"),
            "adresa": general.get("adresa"),
            "telefon": general.get("telefon"),
            "cod_postal": general.get("cod_postal"),
            "stare": general.get("stare_inregistrare"),
            "tva": tva_info.get("scpTVA", False),
            "data_verificare": today_str,
        }

    _anaf_cache[cui_int] = {"data": result, "ts": time.time()}
    return result


# ---------------------------------------------------------------------------
# Number to Romanian Words
# ---------------------------------------------------------------------------

_UNITS = [
    "", "unu", "doi", "trei", "patru", "cinci",
    "sase", "sapte", "opt", "noua",
]

_UNITS_FEM = [
    "", "una", "doua", "trei", "patru", "cinci",
    "sase", "sapte", "opt", "noua",
]

_TEENS = [
    "zece", "unsprezece", "doisprezece", "treisprezece",
    "paisprezece", "cincisprezece", "saisprezece",
    "saptesprezece", "optsprezece", "nouasprezece",
]

_TENS = [
    "", "zece", "douazeci", "treizeci", "patruzeci", "cincizeci",
    "saizeci", "saptezeci", "optzeci", "nouazeci",
]

_HUNDREDS = [
    "", "o suta", "doua sute", "trei sute", "patru sute", "cinci sute",
    "sase sute", "sapte sute", "opt sute", "noua sute",
]


def _chunk_under_1000(n: int, feminine: bool = False) -> str:
    """Convert 0-999 to Romanian words. feminine=True for mii/bani."""
    if n == 0:
        return ""

    parts: list[str] = []

    h = n // 100
    remainder = n % 100

    if h > 0:
        parts.append(_HUNDREDS[h])

    if remainder == 0:
        pass
    elif remainder < 10:
        units = _UNITS_FEM if feminine else _UNITS
        parts.append(units[remainder])
    elif remainder < 20:
        parts.append(_TEENS[remainder - 10])
    else:
        t = remainder // 10
        u = remainder % 10
        if u == 0:
            parts.append(_TENS[t])
        else:
            units = _UNITS_FEM if feminine else _UNITS
            parts.append(f"{_TENS[t]} si {units[u]}")

    return " ".join(parts)


def _number_to_words_int(n: int) -> str:
    """Convert integer to Romanian words (up to 999,999,999)."""
    if n == 0:
        return "zero"

    if n < 0:
        return f"minus {_number_to_words_int(-n)}"

    parts: list[str] = []

    # Millions (1,000,000 - 999,999,999)
    millions = n // 1_000_000
    n %= 1_000_000
    if millions > 0:
        if millions == 1:
            parts.append("un milion")
        elif millions == 2:
            parts.append("doua milioane")
        else:
            parts.append(f"{_chunk_under_1000(millions, feminine=False)} milioane")

    # Thousands (1,000 - 999,999)
    thousands = n // 1_000
    n %= 1_000
    if thousands > 0:
        if thousands == 1:
            parts.append("o mie")
        elif thousands == 2:
            parts.append("doua mii")
        else:
            # Thousands use feminine forms (doua mii, trei mii, etc.)
            chunk = _chunk_under_1000(thousands, feminine=True)
            if thousands < 20:
                parts.append(f"{chunk} mii")
            elif thousands >= 100:
                parts.append(f"{chunk} mii")
            else:
                parts.append(f"{chunk} mii")

    # Units (0 - 999)
    if n > 0:
        parts.append(_chunk_under_1000(n, feminine=False))

    return " ".join(parts)


def number_to_romanian(value: float) -> str:
    """Full conversion: number to RON words with lei + bani."""
    # Split into integer and decimal parts
    negative = value < 0
    value = abs(value)

    integer_part = int(value)
    # Round to 2 decimals to avoid float precision issues
    decimal_part = round((value - integer_part) * 100)
    if decimal_part >= 100:
        integer_part += 1
        decimal_part = 0

    if negative:
        integer_part_text = f"minus {_number_to_words_int(integer_part)}"
    else:
        integer_part_text = _number_to_words_int(integer_part)

    # "lei" forms: 1 = "un leu", rest = "lei"
    if integer_part == 1:
        lei_text = f"{integer_part_text} leu"
    elif integer_part == 0:
        lei_text = "zero lei"
    else:
        lei_text = f"{integer_part_text} lei"

    if decimal_part == 0:
        return lei_text

    # "bani" forms: always "bani" (even for 1 ban in practice we use "bani")
    bani_text = _chunk_under_1000(decimal_part, feminine=False)
    if decimal_part == 1:
        return f"{lei_text} si {bani_text} ban"
    else:
        return f"{lei_text} si {bani_text} bani"


@router.get("/number-to-words")
async def get_number_to_words(
    number: float = Query(..., description="Numarul de convertit in litere"),
):
    """Converteste un numar in cuvinte romanesti (cu lei si bani)."""
    if abs(number) > 999_999_999.99:
        raise HTTPException(400, "Numarul trebuie sa fie intre -999999999.99 si 999999999.99")

    text = number_to_romanian(number)
    return {
        "number": number,
        "words": text,
    }
