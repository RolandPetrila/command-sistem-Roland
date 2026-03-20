"""
API endpoints pentru Quick Tools Extra:
  - Calculator avansat (expresii matematice, safe parsing)
  - Generator parole securizate
  - Generator coduri de bare (Code128, EAN-13, Code39, QR)
"""

from __future__ import annotations

import ast
import io
import logging
import math
import operator
import secrets
import string
from collections import deque
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tools", tags=["quick_tools_extra"])

# ---------------------------------------------------------------------------
# 1. CALCULATOR AVANSAT — safe expression parser (NO eval)
# ---------------------------------------------------------------------------

# Operatori binari permisi
_BINARY_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

# Operatori unari permisi
_UNARY_OPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

# Functii matematice permise
_SAFE_FUNCTIONS = {
    "sqrt": math.sqrt,
    "pow": math.pow,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "asin": math.asin,
    "acos": math.acos,
    "atan": math.atan,
    "log": math.log,
    "log10": math.log10,
    "log2": math.log2,
    "abs": abs,
    "round": round,
    "ceil": math.ceil,
    "floor": math.floor,
    "factorial": math.factorial,
    "radians": math.radians,
    "degrees": math.degrees,
}

# Constante permise
_SAFE_CONSTANTS = {
    "pi": math.pi,
    "e": math.e,
    "tau": math.tau,
}


def _safe_eval_node(node: ast.AST) -> float:
    """
    Evalueaza recursiv un nod AST cu operatii matematice permise.
    NU foloseste eval() — parseaza manual arborele AST.
    """
    # Numar literal (int sau float)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)

    # Operatie unara: -x, +x
    if isinstance(node, ast.UnaryOp):
        op_func = _UNARY_OPS.get(type(node.op))
        if op_func is None:
            raise ValueError(f"Operator unar nepermis: {type(node.op).__name__}")
        return op_func(_safe_eval_node(node.operand))

    # Operatie binara: x + y, x * y, etc.
    if isinstance(node, ast.BinOp):
        op_func = _BINARY_OPS.get(type(node.op))
        if op_func is None:
            raise ValueError(f"Operator nepermis: {type(node.op).__name__}")
        left = _safe_eval_node(node.left)
        right = _safe_eval_node(node.right)
        if isinstance(node.op, ast.Div) and right == 0:
            raise ValueError("Impartire la zero")
        if isinstance(node.op, ast.Pow) and abs(right) > 1000:
            raise ValueError("Exponentul este prea mare (max 1000)")
        return op_func(left, right)

    # Apel de functie: sqrt(x), sin(x), pow(x, y)
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise ValueError("Apeluri de functii complexe nu sunt permise")
        func_name = node.func.id.lower()
        func = _SAFE_FUNCTIONS.get(func_name)
        if func is None:
            raise ValueError(f"Functie necunoscuta: {func_name}")
        args = [_safe_eval_node(arg) for arg in node.args]
        if not args:
            raise ValueError(f"Functia {func_name} necesita cel putin un argument")
        return float(func(*args))

    # Variabila (constanta): pi, e
    if isinstance(node, ast.Name):
        name = node.id.lower()
        if name in _SAFE_CONSTANTS:
            return _SAFE_CONSTANTS[name]
        # Poate fi o functie fara paranteze — eroare descriptiva
        if name in _SAFE_FUNCTIONS:
            raise ValueError(f"'{node.id}' este o functie — foloseste {node.id}(...)")
        raise ValueError(f"Variabila necunoscuta: {node.id}")

    raise ValueError(f"Expresie nepermisa: {ast.dump(node)}")


def _preprocess_expression(expr: str) -> str:
    """Pre-proceseaza expresia: suporta procente, inlocuiri."""
    # Inlocuieste x si X cu * pentru multiplicare
    import re

    # 50% din 200 -> 50/100*200
    expr = re.sub(r"(\d+(?:\.\d+)?)\s*%\s*(?:din|of|from)\s*(\d+(?:\.\d+)?)", r"(\1/100*\2)", expr, flags=re.IGNORECASE)

    # 50% standalone -> 50/100
    expr = re.sub(r"(\d+(?:\.\d+)?)\s*%", r"(\1/100)", expr)

    # Inmultire implicita: 2pi -> 2*pi, 3sqrt -> 3*sqrt
    expr = re.sub(r"(\d)([a-zA-Z])", r"\1*\2", expr)

    return expr


def _safe_calculate(expression: str) -> float:
    """
    Parseaza si evalueaza o expresie matematica in mod sigur.
    Foloseste ast.parse() + evaluare recursiva, NU eval().
    """
    processed = _preprocess_expression(expression)

    try:
        tree = ast.parse(processed, mode="eval")
    except SyntaxError as exc:
        raise ValueError(f"Sintaxa invalida: {exc.msg}") from exc

    return _safe_eval_node(tree.body)


# Istoric calcule in memorie (ultimele 20)
_calc_history: deque[dict] = deque(maxlen=20)


class CalcRequest(BaseModel):
    expression: str = Field(..., min_length=1, max_length=500, description="Expresia matematica de evaluat")


class CalcResponse(BaseModel):
    expression: str
    processed: str
    result: float
    formatted: str
    timestamp: str


@router.post("/calculate", response_model=CalcResponse)
async def calculate(req: CalcRequest):
    """
    Evalueaza o expresie matematica in mod sigur (fara eval).
    Suporta: +, -, *, /, **, %, sqrt, pow, sin, cos, tan, log, pi, e, paranteze.
    """
    expression = req.expression.strip()
    processed = _preprocess_expression(expression)

    try:
        result = _safe_calculate(expression)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except (OverflowError, ZeroDivisionError) as exc:
        raise HTTPException(status_code=400, detail=f"Eroare de calcul: {exc}")

    # Formatare rezultat: intreg daca e posibil, altfel 10 decimale semnificative
    if result == float("inf") or result == float("-inf") or math.isnan(result):
        raise HTTPException(status_code=400, detail="Rezultat invalid (infinit sau NaN)")

    if result == int(result) and abs(result) < 1e15:
        formatted = str(int(result))
    else:
        formatted = f"{result:.10g}"

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = {
        "expression": expression,
        "processed": processed,
        "result": result,
        "formatted": formatted,
        "timestamp": timestamp,
    }
    _calc_history.appendleft(entry)

    logger.info("Calculator: %s = %s", expression, formatted)
    return CalcResponse(**entry)


@router.get("/calc-history")
async def get_calc_history():
    """Returneaza istoricul ultimelor 20 de calcule."""
    return {"history": list(_calc_history)}


@router.delete("/calc-history")
async def clear_calc_history():
    """Sterge istoricul de calcule."""
    _calc_history.clear()
    return {"status": "ok", "message": "Istoric sters"}


# ---------------------------------------------------------------------------
# 2. GENERATOR PAROLE
# ---------------------------------------------------------------------------

class PasswordRequest(BaseModel):
    length: int = Field(16, ge=8, le=128, description="Lungime parola (8-128)")
    uppercase: bool = Field(True, description="Include litere mari (A-Z)")
    lowercase: bool = Field(True, description="Include litere mici (a-z)")
    digits: bool = Field(True, description="Include cifre (0-9)")
    symbols: bool = Field(True, description="Include simboluri (!@#$...)")
    exclude_ambiguous: bool = Field(False, description="Exclude caractere ambigue (0O, 1lI)")


class PasswordResponse(BaseModel):
    password: str
    length: int
    strength: dict
    character_sets: list[str]


class StrengthRequest(BaseModel):
    password: str = Field(..., min_length=1, max_length=500)


class StrengthResponse(BaseModel):
    score: int  # 0-4
    label: str  # Foarte slaba, Slaba, Medie, Puternica, Foarte puternica
    feedback: list[str]
    entropy_bits: float
    crack_time_display: str


def _check_password_strength(password: str) -> dict:
    """Analizeaza forta unei parole si returneaza scor + feedback."""
    feedback = []
    score = 0
    length = len(password)

    # Lungime
    if length >= 8:
        score += 1
    if length >= 12:
        score += 1
    if length >= 16:
        score += 1

    if length < 8:
        feedback.append("Parola este prea scurta (minim 8 caractere)")

    # Varietate caractere
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_symbol = any(c in string.punctuation for c in password)

    char_types = sum([has_upper, has_lower, has_digit, has_symbol])
    if char_types >= 3:
        score += 1
    if char_types == 4:
        score += 1

    if not has_upper:
        feedback.append("Adauga litere mari (A-Z)")
    if not has_lower:
        feedback.append("Adauga litere mici (a-z)")
    if not has_digit:
        feedback.append("Adauga cifre (0-9)")
    if not has_symbol:
        feedback.append("Adauga simboluri (!@#$...)")

    # Penalizari
    # Caractere repetitive
    if length > 0:
        unique_ratio = len(set(password)) / length
        if unique_ratio < 0.5:
            score = max(0, score - 1)
            feedback.append("Prea multe caractere repetate")

    # Secvente comune
    common_patterns = ["123456", "password", "qwerty", "abcdef", "111111", "000000"]
    lower_pw = password.lower()
    for pattern in common_patterns:
        if pattern in lower_pw:
            score = max(0, score - 1)
            feedback.append("Contine un pattern comun usor de ghicit")
            break

    # Normalizeaza scorul la 0-4
    score = max(0, min(4, score))

    # Calcul entropie
    pool_size = 0
    if has_upper:
        pool_size += 26
    if has_lower:
        pool_size += 26
    if has_digit:
        pool_size += 10
    if has_symbol:
        pool_size += 32
    if pool_size == 0:
        pool_size = 26  # fallback

    entropy = length * math.log2(pool_size)

    # Estimare timp de spargere (10 miliarde incercari/sec)
    guesses_per_sec = 1e10
    total_combos = pool_size ** length
    seconds = total_combos / guesses_per_sec

    if seconds < 1:
        crack_time = "Instant"
    elif seconds < 60:
        crack_time = f"{seconds:.0f} secunde"
    elif seconds < 3600:
        crack_time = f"{seconds / 60:.0f} minute"
    elif seconds < 86400:
        crack_time = f"{seconds / 3600:.0f} ore"
    elif seconds < 86400 * 365:
        crack_time = f"{seconds / 86400:.0f} zile"
    elif seconds < 86400 * 365 * 1000:
        crack_time = f"{seconds / (86400 * 365):.0f} ani"
    elif seconds < 86400 * 365 * 1e6:
        crack_time = f"{seconds / (86400 * 365 * 1000):.0f} mii de ani"
    else:
        crack_time = "Milioane+ de ani"

    labels = ["Foarte slaba", "Slaba", "Medie", "Puternica", "Foarte puternica"]

    if not feedback:
        feedback.append("Parola excelenta!")

    return {
        "score": score,
        "label": labels[score],
        "feedback": feedback,
        "entropy_bits": round(entropy, 1),
        "crack_time_display": crack_time,
    }


@router.post("/generate-password", response_model=PasswordResponse)
async def generate_password(req: PasswordRequest):
    """Genereaza o parola securizata cu parametri configurabili."""
    charset = ""
    char_sets_used = []

    ambiguous = "0O1lI|" if req.exclude_ambiguous else ""

    if req.uppercase:
        chars = string.ascii_uppercase
        if req.exclude_ambiguous:
            chars = "".join(c for c in chars if c not in ambiguous)
        charset += chars
        char_sets_used.append("Litere mari (A-Z)")
    if req.lowercase:
        chars = string.ascii_lowercase
        if req.exclude_ambiguous:
            chars = "".join(c for c in chars if c not in ambiguous)
        charset += chars
        char_sets_used.append("Litere mici (a-z)")
    if req.digits:
        chars = string.digits
        if req.exclude_ambiguous:
            chars = "".join(c for c in chars if c not in ambiguous)
        charset += chars
        char_sets_used.append("Cifre (0-9)")
    if req.symbols:
        charset += "!@#$%^&*()-_=+[]{}|;:,.<>?"
        char_sets_used.append("Simboluri (!@#$...)")

    if not charset:
        raise HTTPException(
            status_code=400,
            detail="Selecteaza cel putin un tip de caractere",
        )

    # Genereaza parola cu secrets (criptografic sigur)
    password = "".join(secrets.choice(charset) for _ in range(req.length))

    # Asigura ca fiecare tip selectat e prezent (daca lungimea permite)
    if req.length >= len(char_sets_used):
        attempts = 0
        while attempts < 100:
            ok = True
            if req.uppercase and not any(c.isupper() for c in password):
                ok = False
            if req.lowercase and not any(c.islower() for c in password):
                ok = False
            if req.digits and not any(c.isdigit() for c in password):
                ok = False
            if req.symbols and not any(c in "!@#$%^&*()-_=+[]{}|;:,.<>?" for c in password):
                ok = False
            if ok:
                break
            password = "".join(secrets.choice(charset) for _ in range(req.length))
            attempts += 1

    strength = _check_password_strength(password)

    logger.info("Password generated: length=%d, sets=%d", req.length, len(char_sets_used))
    return PasswordResponse(
        password=password,
        length=len(password),
        strength=strength,
        character_sets=char_sets_used,
    )


@router.post("/check-password-strength", response_model=StrengthResponse)
async def check_password_strength(req: StrengthRequest):
    """Verifica forta unei parole existente."""
    result = _check_password_strength(req.password)
    return StrengthResponse(**result)


# ---------------------------------------------------------------------------
# 3. GENERATOR CODURI DE BARE
# ---------------------------------------------------------------------------

class BarcodeRequest(BaseModel):
    data: str = Field(..., min_length=1, max_length=500, description="Textul/codul de encodat")
    barcode_type: str = Field("code128", description="Tipul: code128, ean13, code39, qr")
    width: Optional[float] = Field(None, ge=0.1, le=5.0, description="Latimea barelor (mm)")
    height: Optional[float] = Field(None, ge=5.0, le=100.0, description="Inaltimea (mm)")
    show_text: bool = Field(True, description="Afiseaza textul sub cod")


_BARCODE_TYPES = {
    "code128": "code128",
    "ean13": "ean13",
    "ean-13": "ean13",
    "code39": "code39",
    "qr": "qr",
}


@router.post("/generate-barcode")
async def generate_barcode(req: BarcodeRequest):
    """
    Genereaza un cod de bare ca imagine PNG.
    Tipuri suportate: Code128, EAN-13, Code39, QR.
    """
    barcode_key = req.barcode_type.lower().strip()
    barcode_name = _BARCODE_TYPES.get(barcode_key)

    if barcode_name is None:
        raise HTTPException(
            status_code=400,
            detail=f"Tip necunoscut: '{req.barcode_type}'. Tipuri valide: {', '.join(_BARCODE_TYPES.keys())}",
        )

    # QR code — folosim qrcode library daca exista, altfel eroare descriptiva
    if barcode_name == "qr":
        try:
            import qrcode
        except ImportError:
            raise HTTPException(
                status_code=400,
                detail="Foloseste pagina QR Generator dedicata pentru coduri QR (/qr). "
                       "Selecteaza Code128, EAN-13 sau Code39 pentru coduri de bare.",
            )

        img = qrcode.make(req.data)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

        return StreamingResponse(
            buf,
            media_type="image/png",
            headers={"Content-Disposition": f'inline; filename="qr_{req.data[:20]}.png"'},
        )

    # Coduri de bare standard via python-barcode
    try:
        import barcode
        from barcode.writer import ImageWriter
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="Biblioteca python-barcode nu este instalata pe server.",
        )

    # Validare EAN-13: exact 12 sau 13 cifre
    if barcode_name == "ean13":
        digits_only = req.data.strip()
        if not digits_only.isdigit() or len(digits_only) not in (12, 13):
            raise HTTPException(
                status_code=400,
                detail="EAN-13 necesita exact 12 cifre (checksum se calculeaza automat) sau 13 cifre.",
            )

    try:
        barcode_class = barcode.get_barcode_class(barcode_name)
    except barcode.errors.BarcodeNotFoundError:
        raise HTTPException(status_code=400, detail=f"Tip de cod de bare indisponibil: {barcode_name}")

    # Configurare writer
    writer_options = {}
    if req.width is not None:
        writer_options["module_width"] = req.width
    if req.height is not None:
        writer_options["module_height"] = req.height
    writer_options["write_text"] = req.show_text
    writer_options["quiet_zone"] = 6.5

    try:
        code = barcode_class(req.data, writer=ImageWriter())
        buf = io.BytesIO()
        code.write(buf, options=writer_options)
        buf.seek(0)
    except Exception as exc:
        logger.error("Eroare generare barcode: %s", exc)
        raise HTTPException(
            status_code=400,
            detail=f"Eroare la generare: {exc}. Verifica datele de intrare.",
        )

    safe_name = "".join(c if c.isalnum() else "_" for c in req.data[:20])
    filename = f"barcode_{barcode_name}_{safe_name}.png"

    logger.info("Barcode generat: type=%s, data=%s", barcode_name, req.data[:30])
    return StreamingResponse(
        buf,
        media_type="image/png",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )


@router.get("/barcode-types")
async def list_barcode_types():
    """Returneaza tipurile de coduri de bare disponibile."""
    return {
        "types": [
            {"id": "code128", "name": "Code 128", "description": "Alfanumeric universal — cel mai folosit", "input": "Orice text"},
            {"id": "ean13", "name": "EAN-13", "description": "Cod de bare European (produse magazin)", "input": "12-13 cifre"},
            {"id": "code39", "name": "Code 39", "description": "Alfanumeric industrial", "input": "Litere mari, cifre, spatii"},
            {"id": "qr", "name": "QR Code", "description": "Cod 2D scanabil cu telefonul", "input": "Orice text sau URL"},
        ]
    }
