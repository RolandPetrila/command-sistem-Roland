"""
AI module endpoints: chat (streaming SSE), document analysis, diff, config.

Endpoints:
  POST   /api/ai/chat                — Chat message (streaming SSE response)
  GET    /api/ai/chat/sessions       — List chat sessions
  POST   /api/ai/chat/sessions       — Create new session
  GET    /api/ai/chat/sessions/:id   — Get session messages
  DELETE /api/ai/chat/sessions/:id   — Delete session
  POST   /api/ai/summarize           — Summarize document
  POST   /api/ai/qa                  — Q&A on document
  POST   /api/ai/classify            — Classify document type
  POST   /api/ai/extract             — Extract structured data
  POST   /api/ai/suggest-name        — Suggest filename
  POST   /api/ai/ocr-enhance         — OCR + AI post-processing
  POST   /api/ai/diff                — Compare two documents
  GET    /api/ai/providers           — List available providers
  GET    /api/ai/config              — Get AI config keys (no values)
  POST   /api/ai/config              — Set API key
  DELETE /api/ai/config/:key         — Remove API key
"""

from __future__ import annotations

import difflib
import json
import logging
import os
import tempfile
import uuid
from pathlib import Path

# fitz, docx — lazy imported inside functions to cut cold-start time
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.core.activity_log import log_activity
from app.db.database import get_db
from .providers import (
    ai_generate,
    ai_generate_stream,
    get_available_providers,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ai", tags=["AI"])


# --- Text extraction (shared) ---
from app.core.file_utils import extract_text as _extract_text


async def _save_upload(file: UploadFile) -> str:
    """Save UploadFile to temp and return path."""
    suffix = Path(file.filename or "file").suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir=tempfile.gettempdir()) as tmp:
        content = await file.read()
        tmp.write(content)
        return tmp.name


async def _extract_from_upload(file: UploadFile) -> str:
    """Extract text from an uploaded file."""
    import asyncio
    tmp_path = await _save_upload(file)
    try:
        return await asyncio.to_thread(_extract_text, tmp_path)
    finally:
        os.unlink(tmp_path)


def _truncate_text(text: str, max_chars: int = 60000) -> str:
    """Truncate text to fit within AI context window."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + f"\n\n[... truncat, {len(text) - max_chars} caractere omise]"


# --- Pydantic models ---

class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    document_context: str | None = None
    provider: str | None = None  # Specific provider name or None for auto chain
    context_mode: bool = False   # Inject DB stats into system prompt


class ConfigSetRequest(BaseModel):
    key: str
    value: str


# === CHAT ENDPOINTS ===

async def _build_context_data() -> str:
    """Build context string from DB stats for context-aware chat."""
    parts = []
    try:
        async with get_db() as db:
            cursor = await db.execute("SELECT COUNT(*) AS cnt, SUM(market_price) AS total FROM calculations")
            row = await cursor.fetchone()
            parts.append(f"Calculații preț: {row['cnt'] or 0} total, valoare totală {round(row['total'] or 0, 2)} RON")

            cursor = await db.execute(
                "SELECT c.market_price, u.filename FROM calculations c "
                "JOIN uploads u ON u.id = c.upload_id ORDER BY c.created_at DESC LIMIT 3"
            )
            recent = [dict(r) for r in await cursor.fetchall()]
            if recent:
                parts.append("Ultimele calculații: " + ", ".join(f"{r['filename']} ({r['market_price']} RON)" for r in recent))

            cursor = await db.execute("SELECT COUNT(*) AS cnt FROM uploads")
            row = await cursor.fetchone()
            parts.append(f"Fișiere încărcate: {row['cnt'] or 0}")

            cursor = await db.execute("SELECT action, summary FROM activity_log ORDER BY timestamp DESC LIMIT 5")
            activities = [dict(r) for r in await cursor.fetchall()]
            if activities:
                parts.append("Activitate recentă: " + "; ".join(a['summary'] for a in activities))

            try:
                cursor = await db.execute("SELECT COUNT(*) AS cnt FROM notes")
                row = await cursor.fetchone()
                parts.append(f"Note: {row['cnt'] or 0}")
            except Exception:
                pass
    except Exception as e:
        logger.warning(f"Context data build failed: {e}")

    return "\n".join(parts) if parts else ""


@router.post("/chat")
async def chat(req: ChatRequest):
    """Chat with AI — streaming SSE response with provider selection and context mode."""
    session_id = req.session_id or str(uuid.uuid4())

    # Ensure session exists
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT id FROM chat_sessions WHERE id = ?", (session_id,)
        )
        if not await cursor.fetchone():
            title = req.message[:50] + ("..." if len(req.message) > 50 else "")
            await db.execute(
                "INSERT INTO chat_sessions (id, title) VALUES (?, ?)",
                (session_id, title),
            )
            await db.commit()

        # Save user message
        await db.execute(
            "INSERT INTO chat_messages (session_id, role, content) VALUES (?, 'user', ?)",
            (session_id, req.message),
        )
        await db.commit()

        # Build context from session history (last 20 messages)
        cursor = await db.execute(
            "SELECT role, content FROM chat_messages WHERE session_id = ? "
            "ORDER BY created_at DESC LIMIT 20",
            (session_id,),
        )
        history = list(reversed([dict(r) for r in await cursor.fetchall()]))

    # Build system prompt
    system_prompt = (
        "Ești un asistent AI integrat în Roland Command Center. "
        "Răspunzi în limba română. Ești concis și util."
    )

    # Context mode: inject DB stats
    if req.context_mode:
        context_data = await _build_context_data()
        if context_data:
            system_prompt += (
                "\n\nDatele utilizatorului din sistem:\n"
                + context_data
                + "\n\nPoți folosi aceste date pentru a oferi răspunsuri relevante."
            )

    prompt_parts = []
    if req.document_context:
        prompt_parts.append(f"Context document:\n{_truncate_text(req.document_context)}\n\n---\n")

    for msg in history[:-1]:  # exclude last (current user message)
        role_label = "Utilizator" if msg["role"] == "user" else "Asistent"
        prompt_parts.append(f"{role_label}: {msg['content']}")
    prompt_parts.append(f"Utilizator: {req.message}")
    prompt_parts.append("Asistent:")

    full_prompt = "\n".join(prompt_parts)
    preferred_provider = req.provider

    async def event_stream():
        full_response = []
        provider_name = ""
        model_name = ""

        async for data in ai_generate_stream(full_prompt, system_prompt, preferred_provider):
            if "error" in data:
                yield f"data: {json.dumps(data)}\n\n"
                return
            if "chunk" in data:
                full_response.append(data["chunk"])
                provider_name = data.get("provider", "")
                model_name = data.get("model", "")
                yield f"data: {json.dumps({'chunk': data['chunk'], 'provider': provider_name})}\n\n"
            if data.get("done"):
                # Save assistant message
                assistant_text = "".join(full_response)
                try:
                    async with get_db() as db:
                        await db.execute(
                            "INSERT INTO chat_messages (session_id, role, content, provider, model) "
                            "VALUES (?, 'assistant', ?, ?, ?)",
                            (session_id, assistant_text, provider_name, model_name),
                        )
                        await db.execute(
                            "UPDATE chat_sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                            (session_id,),
                        )
                        await db.commit()
                except Exception as e:
                    logger.error(f"Failed to save assistant message: {e}")

                await log_activity(
                    action="ai.chat",
                    summary=f"Chat: {req.message[:80]}",
                    details={"session_id": session_id, "provider": provider_name, "model": model_name, "response_len": len(assistant_text)},
                )
                yield f"data: {json.dumps({'done': True, 'session_id': session_id, 'provider': provider_name, 'model': model_name})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/chat/sessions")
async def list_sessions():
    """List all chat sessions."""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT id, title, created_at, updated_at FROM chat_sessions "
            "ORDER BY updated_at DESC"
        )
        return [dict(r) for r in await cursor.fetchall()]


@router.post("/chat/sessions")
async def create_session():
    """Create a new empty chat session."""
    session_id = str(uuid.uuid4())
    async with get_db() as db:
        await db.execute(
            "INSERT INTO chat_sessions (id, title) VALUES (?, 'Chat nou')",
            (session_id,),
        )
        await db.commit()
    return {"id": session_id, "title": "Chat nou"}


@router.delete("/chat/sessions/all")
async def delete_all_sessions():
    """Delete ALL chat sessions and messages."""
    async with get_db() as db:
        await db.execute("DELETE FROM chat_messages")
        await db.execute("DELETE FROM chat_sessions")
        await db.commit()
    await log_activity(action="ai.delete_all_sessions", summary="Toate sesiunile chat șterse")
    return {"status": "deleted", "message": "Toate conversațiile au fost șterse."}


@router.get("/chat/sessions/{session_id}")
async def get_session(session_id: str):
    """Get all messages in a session."""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT id, title, created_at FROM chat_sessions WHERE id = ?",
            (session_id,),
        )
        session = await cursor.fetchone()
        if not session:
            raise HTTPException(404, "Sesiunea nu există")

        cursor = await db.execute(
            "SELECT id, role, content, provider, model, created_at "
            "FROM chat_messages WHERE session_id = ? ORDER BY created_at",
            (session_id,),
        )
        messages = [dict(r) for r in await cursor.fetchall()]

    return {"session": dict(session), "messages": messages}


@router.delete("/chat/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a chat session and all its messages."""
    async with get_db() as db:
        await db.execute("DELETE FROM chat_messages WHERE session_id = ?", (session_id,))
        await db.execute("DELETE FROM chat_sessions WHERE id = ?", (session_id,))
        await db.commit()
    await log_activity(action="ai.delete_session", summary=f"Sesiune chat ștearsă")
    return {"status": "deleted"}


# === DOCUMENT ANALYSIS ENDPOINTS ===

@router.post("/summarize")
async def summarize(file: UploadFile = File(...)):
    """Summarize a document."""
    text = await _extract_from_upload(file)
    if not text:
        raise HTTPException(400, "Nu s-a putut extrage text din fișier")

    system = (
        "Esti un asistent specializat in rezumarea documentelor. "
        "Creeaza un rezumat clar, structurat, in limba romana. "
        "Include punctele cheie si concluziile principale. "
        "NU inventa informatii care nu exista in document. "
        "Daca documentul e prea scurt sau neclar, spune explicit."
    )
    prompt = f"Rezuma urmatorul document:\n\n{_truncate_text(text)}"

    result = await ai_generate(prompt, system)
    await log_activity(
        action="ai.summarize",
        summary=f"Rezumat generat: {file.filename}",
        details={"filename": file.filename, "provider": result["provider"]},
    )
    return {**result, "filename": file.filename}


@router.post("/qa")
async def question_answer(
    file: UploadFile = File(...),
    question: str = Form(...),
):
    """Answer a question about a document."""
    text = await _extract_from_upload(file)
    if not text:
        raise HTTPException(400, "Nu s-a putut extrage text din fișier")

    system = (
        "Esti un asistent AI. Raspunzi la intrebari bazat STRICT pe continutul documentului furnizat. "
        "Daca raspunsul nu se gaseste in document, spune clar: 'Nu am gasit aceasta informatie in document.' "
        "NU inventa sau presupune informatii care nu exista in text. "
        "Citeaza sectiunile relevante. Raspunde in limba romana."
    )
    prompt = (
        f"Document ({file.filename}):\n{_truncate_text(text)}\n\n"
        f"---\nÎntrebare: {question}"
    )

    result = await ai_generate(prompt, system)
    await log_activity(
        action="ai.qa",
        summary=f"Q&A pe {file.filename}: {question[:50]}",
        details={"filename": file.filename, "question": question, "provider": result["provider"]},
    )
    return {**result, "filename": file.filename, "question": question}


@router.post("/classify")
async def classify(file: UploadFile = File(...)):
    """Classify document type."""
    text = await _extract_from_upload(file)
    if not text:
        raise HTTPException(400, "Nu s-a putut extrage text din fișier")

    system = (
        "Clasifica tipul documentului. Raspunde STRICT in format JSON valid, fara markdown:\n"
        '{"type": "tip document", "domain": "domeniu", "language": "limba", '
        '"confidence": 0-100, "description": "descriere scurta"}\n'
        "Tipuri posibile: factura, contract, certificat, raport, manual tehnic, "
        "scrisoare, proces verbal, oferta, comanda, alt document.\n"
        "Domenii posibile: automotive, constructii, IT, juridic, financiar, tehnic, medical, altul.\n"
        "NU inventa un tip daca documentul nu se potriveste niciunei categorii — foloseste 'alt document'."
    )
    prompt = f"Clasifică acest document:\n\n{_truncate_text(text, 10000)}"

    result = await ai_generate(prompt, system)

    # Try to parse JSON from response
    classification = result["text"]
    try:
        # Extract JSON from response (might be wrapped in markdown code block)
        json_str = classification
        if "```" in json_str:
            json_str = json_str.split("```")[1]
            if json_str.startswith("json"):
                json_str = json_str[4:]
        parsed = json.loads(json_str.strip())
        classification = parsed
    except (json.JSONDecodeError, IndexError):
        classification = {"raw": classification}

    await log_activity(
        action="ai.classify",
        summary=f"Document clasificat: {file.filename}",
        details={"filename": file.filename, "provider": result["provider"]},
    )
    return {"classification": classification, "provider": result["provider"], "filename": file.filename}


@router.post("/extract")
async def extract_data(file: UploadFile = File(...)):
    """Extract structured data from document (invoice, certificate, etc.)."""
    text = await _extract_from_upload(file)
    if not text:
        raise HTTPException(400, "Nu s-a putut extrage text din fișier")

    system = (
        "Extrage datele structurate din document. Raspunde STRICT in format JSON valid, fara markdown.\n"
        "Include un camp \"confidence\": 0-100 indicand cat de sigur esti pe datele extrase.\n"
        "Pune null pentru campurile pe care nu le gasesti cu certitudine. NU inventa date.\n"
        "Pentru facturi: {\"tip\": \"factura\", \"furnizor\": \"...\", \"cui_furnizor\": \"...\", "
        "\"numar\": \"...\", \"data\": \"YYYY-MM-DD\", \"suma_fara_tva\": 0, \"tva\": 0, \"total\": 0, "
        "\"moneda\": \"RON\", \"produse\": [...], \"confidence\": 85}\n"
        "Pentru certificate: {\"tip\": \"certificat\", \"emitent\": \"...\", \"numar\": \"...\", "
        "\"data_emitere\": \"YYYY-MM-DD\", \"valabil_pana\": \"YYYY-MM-DD\", \"subiect\": \"...\", \"confidence\": 90}\n"
        "Pentru alte documente: extrage campurile relevante + confidence."
    )
    prompt = f"Extrage datele structurate din:\n\n{_truncate_text(text, 30000)}"

    result = await ai_generate(prompt, system)

    extracted = result["text"]
    try:
        json_str = extracted
        if "```" in json_str:
            json_str = json_str.split("```")[1]
            if json_str.startswith("json"):
                json_str = json_str[4:]
        parsed = json.loads(json_str.strip())
        extracted = parsed
    except (json.JSONDecodeError, IndexError):
        extracted = {"raw": extracted}

    await log_activity(
        action="ai.extract",
        summary=f"Date extrase: {file.filename}",
        details={"filename": file.filename, "provider": result["provider"]},
    )
    return {"data": extracted, "provider": result["provider"], "filename": file.filename}


@router.post("/suggest-name")
async def suggest_name(file: UploadFile = File(...)):
    """Suggest a better filename based on content."""
    text = await _extract_from_upload(file)
    if not text:
        raise HTTPException(400, "Nu s-a putut extrage text din fișier")

    system = (
        "Analizează conținutul documentului și sugerează un nume descriptiv pentru fișier. "
        "Formatul: Tip_Document_Detaliu_Principal_Data.extensie\n"
        "Exemple: Factura_TechAuto_SRL_2026-03-15.pdf, Certificat_Conformitate_BMW_X5.pdf\n"
        "Răspunde cu UN SINGUR nume de fișier, fără explicații suplimentare. "
        "Folosește underscore, fără spații, fără diacritice."
    )
    original_ext = Path(file.filename or "file.pdf").suffix
    prompt = (
        f"Fișier original: {file.filename}\n"
        f"Extensie: {original_ext}\n\n"
        f"Conținut (primele 5000 caractere):\n{_truncate_text(text, 5000)}"
    )

    result = await ai_generate(prompt, system)
    suggested = result["text"].strip().strip('"').strip("'")

    # Ensure it has the right extension
    if not suggested.lower().endswith(original_ext.lower()):
        suggested = Path(suggested).stem + original_ext

    await log_activity(
        action="ai.suggest_name",
        summary=f"Sugestie redenumire: {file.filename} → {suggested}",
        details={"original": file.filename, "suggested": suggested, "provider": result["provider"]},
    )
    return {
        "original": file.filename,
        "suggested": suggested,
        "provider": result["provider"],
    }


@router.post("/ocr-enhance")
async def ocr_enhance(file: UploadFile = File(...)):
    """OCR image + AI post-processing to clean up text."""
    tmp_path = await _save_upload(file)
    try:
        # Step 1: OCR with pytesseract
        raw_text = ""
        fname = (file.filename or "").lower()
        if fname.endswith(".pdf"):
            import fitz  # PyMuPDF
            doc = fitz.open(tmp_path)
            for page in doc:
                raw_text += page.get_text()
                # If no text found, try OCR on page images
                if not page.get_text().strip():
                    pix = page.get_pixmap(dpi=300)
                    img_path = tmp_path + f"_page.png"
                    pix.save(img_path)
                    try:
                        import pytesseract
                        from PIL import Image
                        img = Image.open(img_path)
                        raw_text += pytesseract.image_to_string(img, lang="ron+eng")
                    except ImportError:
                        raw_text += "[pytesseract not available]"
                    finally:
                        if os.path.exists(img_path):
                            os.unlink(img_path)
            doc.close()
        elif fname.endswith((".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp")):
            try:
                import pytesseract
                from PIL import Image
                img = Image.open(tmp_path)
                raw_text = pytesseract.image_to_string(img, lang="ron+eng")
            except ImportError:
                raise HTTPException(500, "pytesseract nu e instalat")
        else:
            raise HTTPException(400, "Format nesuportat. Acceptate: PDF, PNG, JPG, TIFF, BMP, WEBP")

        if not raw_text.strip():
            return {"raw_text": "", "enhanced_text": "", "note": "Nu s-a detectat text"}

        # Step 2: AI enhancement
        system = (
            "Primești text extras prin OCR care poate conține erori. "
            "Corectează erorile OCR (litere confundate, spații lipsă, diacritice greșite). "
            "Păstrează structura originală (paragrafe, liste). "
            "Returnează DOAR textul corectat, fără explicații."
        )
        prompt = f"Corectează acest text OCR:\n\n{_truncate_text(raw_text)}"

        result = await ai_generate(prompt, system)

        await log_activity(
            action="ai.ocr_enhance",
            summary=f"OCR+ aplicat: {file.filename}",
            details={"filename": file.filename, "provider": result["provider"]},
        )
        return {
            "raw_text": raw_text.strip(),
            "enhanced_text": result["text"],
            "provider": result["provider"],
            "filename": file.filename,
        }
    finally:
        os.unlink(tmp_path)


# === DIFF ENDPOINT ===

@router.post("/diff")
async def diff_documents(
    file1: UploadFile = File(...),
    file2: UploadFile = File(...),
):
    """Compare two documents and return structured diff."""
    text1 = await _extract_from_upload(file1)
    text2 = await _extract_from_upload(file2)

    if not text1 or not text2:
        raise HTTPException(400, "Nu s-a putut extrage text din unul din fișiere")

    lines1 = text1.splitlines()
    lines2 = text2.splitlines()

    # Generate opcodes for structured diff
    matcher = difflib.SequenceMatcher(None, lines1, lines2)
    ops = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        ops.append({
            "tag": tag,
            "left_lines": lines1[i1:i2],
            "right_lines": lines2[j1:j2],
            "left_range": [i1, i2],
            "right_range": [j1, j2],
        })

    # Statistics
    ratio = matcher.ratio()
    added = sum(len(op["right_lines"]) for op in ops if op["tag"] == "insert")
    deleted = sum(len(op["left_lines"]) for op in ops if op["tag"] == "delete")
    changed = sum(len(op["left_lines"]) for op in ops if op["tag"] == "replace")

    await log_activity(
        action="ai.diff",
        summary=f"Comparare: {file1.filename} vs {file2.filename} ({ratio:.0%} similar)",
        details={
            "file1": file1.filename,
            "file2": file2.filename,
            "similarity": round(ratio, 3),
        },
    )

    return {
        "file1": file1.filename,
        "file2": file2.filename,
        "similarity": round(ratio * 100, 1),
        "stats": {"added": added, "deleted": deleted, "changed": changed},
        "ops": ops,
    }


# === CONFIG ENDPOINTS ===

@router.get("/providers")
async def list_providers():
    """List available AI providers and their status."""
    return await get_available_providers()


@router.get("/config")
async def get_config():
    """Get AI config keys (no values — only which keys are set)."""
    async with get_db() as db:
        cursor = await db.execute("SELECT key, updated_at FROM ai_config")
        rows = [dict(r) for r in await cursor.fetchall()]
    return rows


@router.post("/config")
async def set_config(req: ConfigSetRequest):
    """Set an AI config value (e.g., API key)."""
    async with get_db() as db:
        await db.execute(
            "INSERT INTO ai_config (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value, "
            "updated_at = CURRENT_TIMESTAMP",
            (req.key, req.value),
        )
        await db.commit()

    # Mask the value for logging
    masked = req.value[:4] + "****" + req.value[-4:] if len(req.value) > 8 else "****"
    await log_activity(
        action="ai.config_set",
        summary=f"Config AI setat: {req.key} = {masked}",
    )
    return {"status": "saved", "key": req.key}


@router.delete("/config/{key}")
async def delete_config(key: str):
    """Remove an AI config value."""
    async with get_db() as db:
        await db.execute("DELETE FROM ai_config WHERE key = ?", (key,))
        await db.commit()
    await log_activity(action="ai.config_delete", summary=f"Config AI șters: {key}")
    return {"status": "deleted", "key": key}


# === F2: PROMPT TEMPLATES ===

class PromptTemplateCreate(BaseModel):
    name: str
    description: str | None = None
    prompt_text: str
    variables: list[str] | None = None
    category: str = "general"


class PromptTemplateUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    prompt_text: str | None = None
    variables: list[str] | None = None
    category: str | None = None


@router.get("/templates")
async def list_templates(category: str = None):
    """List prompt templates, optionally filtered by category."""
    async with get_db() as db:
        if category:
            cursor = await db.execute(
                "SELECT * FROM ai_prompt_templates WHERE category = ? ORDER BY usage_count DESC",
                (category,),
            )
        else:
            cursor = await db.execute(
                "SELECT * FROM ai_prompt_templates ORDER BY usage_count DESC"
            )
        rows = await cursor.fetchall()
    result = []
    for r in rows:
        d = dict(r)
        d["variables"] = json.loads(d["variables"]) if d.get("variables") else []
        result.append(d)
    return result


@router.post("/templates", status_code=201)
async def create_template(data: PromptTemplateCreate):
    """Create a new prompt template."""
    async with get_db() as db:
        cursor = await db.execute(
            """INSERT INTO ai_prompt_templates (name, description, prompt_text, variables, category)
               VALUES (?, ?, ?, ?, ?)""",
            (data.name, data.description, data.prompt_text,
             json.dumps(data.variables or []), data.category),
        )
        await db.commit()
        template_id = cursor.lastrowid
    await log_activity(
        action="ai.template_create",
        summary=f"Template AI creat: {data.name}",
        details={"id": template_id, "category": data.category},
    )
    return {"id": template_id, "message": f"Template '{data.name}' creat cu succes."}


@router.put("/templates/{template_id}")
async def update_template(template_id: int, data: PromptTemplateUpdate):
    """Update a prompt template."""
    updates = data.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(400, "Niciun camp de actualizat")
    if "variables" in updates:
        updates["variables"] = json.dumps(updates["variables"] or [])
    fields = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [template_id]
    async with get_db() as db:
        cursor = await db.execute(
            f"UPDATE ai_prompt_templates SET {fields} WHERE id = ?", values
        )
        await db.commit()
        if cursor.rowcount == 0:
            raise HTTPException(404, "Template negasit")
    return {"message": "Template actualizat cu succes."}


@router.delete("/templates/{template_id}")
async def delete_template(template_id: int):
    """Delete a prompt template."""
    async with get_db() as db:
        cursor = await db.execute(
            "DELETE FROM ai_prompt_templates WHERE id = ?", (template_id,)
        )
        await db.commit()
        if cursor.rowcount == 0:
            raise HTTPException(404, "Template negasit")
    return {"message": "Template sters cu succes."}


@router.post("/templates/{template_id}/use")
async def use_template(template_id: int):
    """Increment usage count and return the template text."""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM ai_prompt_templates WHERE id = ?", (template_id,)
        )
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(404, "Template negasit")
        await db.execute(
            "UPDATE ai_prompt_templates SET usage_count = usage_count + 1 WHERE id = ?",
            (template_id,),
        )
        await db.commit()
    d = dict(row)
    d["variables"] = json.loads(d["variables"]) if d.get("variables") else []
    return d
