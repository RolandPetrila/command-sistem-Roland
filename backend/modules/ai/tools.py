"""
AI module — Utility/tool endpoints.

Endpoints:
  POST   /api/ai/explain-price        — AI explanation for a price calculation
  GET    /api/ai/context-data         — DB stats for context-aware chat
  POST   /api/ai/notepad/{action}     — AI actions on notepad text (improve/summarize/translate)
  GET    /api/ai/dashboard-insights   — AI-generated insights from DB stats
  POST   /api/ai/compare-price        — Compare price vs competitors
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.activity_log import log_activity
from app.db.database import get_db
from .providers import ai_generate
from .token_tracker import track_usage

logger = logging.getLogger(__name__)
router_tools = APIRouter(prefix="/api/ai", tags=["AI Tools"])

# Path to Competitori.md
COMPETITORI_PATH = Path(__file__).resolve().parent.parent.parent.parent / "99_Roland_Work_Place" / "Competitori.md"


# --- Pydantic models ---

class ExplainPriceRequest(BaseModel):
    calculation_id: int | None = None
    features: dict | None = None
    price: float | None = None
    confidence: float | None = None


class NotepadActionRequest(BaseModel):
    text: str


class ComparePriceRequest(BaseModel):
    price: float
    pages: int = 1
    words: int = 0
    doc_type: str = "general"


# ==========================================
# 15B.2 — PRICE EXPLANATION
# ==========================================

@router_tools.post("/explain-price")
async def explain_price(req: ExplainPriceRequest):
    """
    Generează o explicație AI a prețului calculat, în limbaj accesibil clientului.
    Acceptă fie calculation_id (preia din DB), fie features + price direct.
    """
    features = req.features
    price = req.price
    confidence = req.confidence

    # If calculation_id provided, load from DB
    if req.calculation_id:
        async with get_db() as db:
            cursor = await db.execute(
                "SELECT c.market_price, c.invoice_price, c.confidence, c.features, "
                "       c.method_details, u.filename, u.file_type "
                "FROM calculations c "
                "JOIN uploads u ON u.id = c.upload_id "
                "WHERE c.id = ?",
                (req.calculation_id,),
            )
            row = await cursor.fetchone()
            if not row:
                raise HTTPException(404, "Calculul nu a fost găsit")

            row = dict(row)
            features = json.loads(row["features"]) if isinstance(row["features"], str) else row["features"]
            price = row["market_price"]
            confidence = row["confidence"]

            # Get similar recent calculations for context
            cursor = await db.execute(
                "SELECT c.market_price, c.features, u.filename "
                "FROM calculations c JOIN uploads u ON u.id = c.upload_id "
                "ORDER BY c.created_at DESC LIMIT 5"
            )
            recent = [dict(r) for r in await cursor.fetchall()]
    else:
        if not features or price is None:
            raise HTTPException(400, "Trimite calculation_id sau features + price")
        recent = []

    # Build prompt
    features_desc = json.dumps(features, ensure_ascii=False, indent=2) if features else "N/A"
    recent_desc = ""
    if recent:
        recent_lines = []
        for r in recent[:3]:
            feat = json.loads(r["features"]) if isinstance(r["features"], str) else r["features"]
            pg = feat.get("pages", "?")
            wc = feat.get("total_words", "?")
            recent_lines.append(f"  - {r['filename']}: {pg} pag, {wc} cuv → {r['market_price']} RON")
        recent_desc = "\nCalcule recente similare:\n" + "\n".join(recent_lines)

    system = (
        "Ești un asistent de preț pentru un birou de traduceri tehnice EN↔RO. "
        "Generează o explicație scurtă (3-4 propoziții) a prețului, în limba română, "
        "într-un limbaj accesibil clientului (fără jargon tehnic). "
        "Menționează factorii principali care influențează prețul: "
        "volum (pagini/cuvinte), complexitate (imagini, tabele), tip document. "
        "NU inventa date, bazează-te strict pe informațiile primite."
    )
    prompt = (
        f"Caracteristici document:\n{features_desc}\n\n"
        f"Preț calculat: {price} RON\n"
        f"Încredere model: {confidence}%\n"
        f"{recent_desc}\n\n"
        f"Generează o explicație scurtă și clară a acestui preț pentru client."
    )

    result = await ai_generate(prompt, system)
    await track_usage(result["provider"], chars=len(prompt) + len(result["text"]))

    await log_activity(
        action="ai.explain_price",
        summary=f"Explicație preț generată: {price} RON",
        details={"price": price, "provider": result["provider"]},
    )
    return {"explanation": result["text"], "provider": result["provider"]}


# ==========================================
# 15B.4 — CONTEXT-AWARE CHAT DATA
# ==========================================

@router_tools.get("/context-data")
async def get_context_data():
    """
    Returnează statistici din DB pentru injectare în system prompt (context_mode=true).
    Include: calculatii, fișiere, activitate recentă, note.
    """
    data = {}

    async with get_db() as db:
        # Calculations stats
        cursor = await db.execute("SELECT COUNT(*) AS cnt, SUM(market_price) AS total FROM calculations")
        row = await cursor.fetchone()
        data["calculations"] = {
            "total_count": row["cnt"] or 0,
            "total_value": round(row["total"] or 0, 2),
        }

        # Recent 5 calculations
        cursor = await db.execute(
            "SELECT c.market_price, c.confidence, c.features, u.filename, c.created_at "
            "FROM calculations c JOIN uploads u ON u.id = c.upload_id "
            "ORDER BY c.created_at DESC LIMIT 5"
        )
        recent_calcs = []
        for r in await cursor.fetchall():
            r = dict(r)
            feat = json.loads(r["features"]) if isinstance(r["features"], str) else r["features"]
            recent_calcs.append({
                "filename": r["filename"],
                "price": r["market_price"],
                "confidence": r["confidence"],
                "pages": feat.get("pages", 0),
                "words": feat.get("total_words", 0),
                "date": r["created_at"],
            })
        data["recent_calculations"] = recent_calcs

        # Files uploaded
        cursor = await db.execute("SELECT COUNT(*) AS cnt FROM uploads")
        row = await cursor.fetchone()
        data["total_files_uploaded"] = row["cnt"] or 0

        # Recent activity (5 items)
        cursor = await db.execute(
            "SELECT action, summary, timestamp FROM activity_log "
            "ORDER BY timestamp DESC LIMIT 5"
        )
        data["recent_activity"] = [dict(r) for r in await cursor.fetchall()]

        # Notes count
        try:
            cursor = await db.execute("SELECT COUNT(*) AS cnt FROM notes")
            row = await cursor.fetchone()
            data["notes_count"] = row["cnt"] or 0

            # Recent notepad content
            cursor = await db.execute(
                "SELECT title, substr(content, 1, 200) AS preview, updated_at "
                "FROM notes ORDER BY updated_at DESC LIMIT 3"
            )
            data["recent_notes"] = [dict(r) for r in await cursor.fetchall()]
        except Exception:
            data["notes_count"] = 0
            data["recent_notes"] = []

        # Translations count
        try:
            cursor = await db.execute("SELECT COUNT(*) AS cnt FROM translations")
            row = await cursor.fetchone()
            data["translations_count"] = row["cnt"] or 0
        except Exception:
            data["translations_count"] = 0

    return data


# ==========================================
# 15B.6 — NOTEPAD AI ACTIONS
# ==========================================

@router_tools.post("/notepad/{action}")
async def notepad_ai_action(action: str, req: NotepadActionRequest):
    """
    Acțiuni AI pe text din notepad: improve, summarize, translate.
    """
    valid_actions = {"improve", "summarize", "translate"}
    if action not in valid_actions:
        raise HTTPException(400, f"Acțiune invalidă. Opțiuni: {', '.join(valid_actions)}")

    if not req.text.strip():
        raise HTTPException(400, "Textul este gol")

    if action == "improve":
        system = (
            "Ești un editor de text profesionist. "
            "Corectează gramatica, îmbunătățește formularea și claritatea textului. "
            "Păstrează sensul original și stilul (formal/informal). "
            "Limba: română. Returnează DOAR textul îmbunătățit, fără explicații."
        )
        prompt = f"Îmbunătățește acest text:\n\n{req.text}"

    elif action == "summarize":
        system = (
            "Ești un specialist în sintetizare. "
            "Creează un rezumat concis în 3-5 bullet points. "
            "Fiecare punct: o propoziție clară cu ideea principală. "
            "Limba: română. Format: punct pe linie nouă, prefixat cu •"
        )
        prompt = f"Rezumă acest text:\n\n{req.text}"

    else:  # translate
        # Detect source language
        system = (
            "Ești un traducător profesionist EN↔RO. "
            "Detectează automat limba textului. "
            "Dacă e în română → traduce în engleză. "
            "Dacă e în engleză → traduce în română. "
            "Dacă e altă limbă → traduce în română. "
            "Returnează DOAR traducerea, fără explicații sau note. "
            "Păstrează formatarea originală (paragrafe, liste, bold)."
        )
        prompt = f"Traduce acest text:\n\n{req.text}"

    result = await ai_generate(prompt, system)
    await track_usage(result["provider"], chars=len(prompt) + len(result["text"]))

    await log_activity(
        action=f"ai.notepad_{action}",
        summary=f"Notepad AI: {action} ({len(req.text)} caractere)",
        details={"action": action, "input_len": len(req.text), "provider": result["provider"]},
    )

    return {
        "result": result["text"],
        "action": action,
        "provider": result["provider"],
    }


# ==========================================
# 15B.8 — DASHBOARD INSIGHTS
# ==========================================

@router_tools.get("/dashboard-insights")
async def get_dashboard_insights():
    """
    Generează insights AI din datele din DB.
    Folosește cache de 1 oră (ai_insights_cache).
    """
    cache_key = "dashboard_insights"

    # Check cache
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT content, generated_at FROM ai_insights_cache "
            "WHERE cache_key = ? AND expires_at > CURRENT_TIMESTAMP",
            (cache_key,),
        )
        cached = await cursor.fetchone()
        if cached:
            insights = json.loads(cached["content"])
            return {
                "insights": insights,
                "generated_at": cached["generated_at"],
                "cached": True,
            }

    # Gather DB stats for prompt
    stats = {}
    async with get_db() as db:
        # Total calculations and value
        cursor = await db.execute(
            "SELECT COUNT(*) AS cnt, "
            "  COALESCE(SUM(market_price), 0) AS total_value, "
            "  COALESCE(AVG(market_price), 0) AS avg_price, "
            "  COALESCE(AVG(confidence), 0) AS avg_confidence "
            "FROM calculations"
        )
        row = await cursor.fetchone()
        stats["calculations"] = {
            "count": row["cnt"],
            "total_value": round(row["total_value"], 2),
            "avg_price": round(row["avg_price"], 2),
            "avg_confidence": round(row["avg_confidence"], 1),
        }

        # This week vs last week
        cursor = await db.execute(
            "SELECT COUNT(*) AS cnt, COALESCE(SUM(market_price), 0) AS val "
            "FROM calculations WHERE created_at >= date('now', '-7 days')"
        )
        row = await cursor.fetchone()
        stats["this_week"] = {"count": row["cnt"], "value": round(row["val"], 2)}

        cursor = await db.execute(
            "SELECT COUNT(*) AS cnt, COALESCE(SUM(market_price), 0) AS val "
            "FROM calculations WHERE created_at >= date('now', '-14 days') "
            "AND created_at < date('now', '-7 days')"
        )
        row = await cursor.fetchone()
        stats["last_week"] = {"count": row["cnt"], "value": round(row["val"], 2)}

        # Files uploaded
        cursor = await db.execute("SELECT COUNT(*) AS cnt FROM uploads")
        row = await cursor.fetchone()
        stats["files_uploaded"] = row["cnt"]

        # Most common file types
        cursor = await db.execute(
            "SELECT file_type, COUNT(*) AS cnt FROM uploads GROUP BY file_type ORDER BY cnt DESC"
        )
        stats["file_types"] = [dict(r) for r in await cursor.fetchall()]

        # Translations count
        try:
            cursor = await db.execute(
                "SELECT COUNT(*) AS cnt, COALESCE(SUM(chars_count), 0) AS chars "
                "FROM translations"
            )
            row = await cursor.fetchone()
            stats["translations"] = {"count": row["cnt"], "total_chars": row["chars"]}
        except Exception:
            stats["translations"] = {"count": 0, "total_chars": 0}

        # AI usage today
        try:
            cursor = await db.execute(
                "SELECT provider, requests_count FROM ai_token_usage WHERE date = date('now')"
            )
            stats["ai_today"] = [dict(r) for r in await cursor.fetchall()]
        except Exception:
            stats["ai_today"] = []

        # Notes count
        try:
            cursor = await db.execute("SELECT COUNT(*) AS cnt FROM notes")
            row = await cursor.fetchone()
            stats["notes_count"] = row["cnt"]
        except Exception:
            stats["notes_count"] = 0

    # Build AI prompt
    system = (
        "Ești un analist de date pentru un birou de traduceri tehnice (CIP Inspection SRL). "
        "Analizează statisticile și generează 4-5 insight-uri scurte și utile. "
        "Fiecare insight: o propoziție clară cu valoare acționabilă. "
        "Limba: română. Format: JSON array de stringuri.\n"
        'Exemplu: ["Volumul de traduceri a crescut cu 20% față de săptămâna trecută.", "..."]'
    )
    prompt = f"Statistici birou traduceri:\n{json.dumps(stats, ensure_ascii=False, indent=2)}"

    try:
        result = await ai_generate(prompt, system)
        await track_usage(result["provider"], chars=len(prompt) + len(result["text"]))

        # Parse insights from AI response
        resp_text = result["text"]
        if "```" in resp_text:
            resp_text = resp_text.split("```")[1]
            if resp_text.startswith("json"):
                resp_text = resp_text[4:]

        try:
            insights = json.loads(resp_text.strip())
            if not isinstance(insights, list):
                insights = [resp_text.strip()]
        except json.JSONDecodeError:
            # Split by newlines/bullets if not valid JSON
            lines = [
                line.strip().lstrip("•-*0123456789.) ")
                for line in resp_text.strip().split("\n")
                if line.strip() and len(line.strip()) > 10
            ]
            insights = lines if lines else [resp_text.strip()]

        # Cache for 1 hour
        now = datetime.utcnow()
        expires = now + timedelta(hours=1)
        async with get_db() as db:
            await db.execute(
                "INSERT INTO ai_insights_cache (cache_key, content, generated_at, expires_at) "
                "VALUES (?, ?, ?, ?) "
                "ON CONFLICT(cache_key) DO UPDATE SET "
                "  content = excluded.content, "
                "  generated_at = excluded.generated_at, "
                "  expires_at = excluded.expires_at",
                (cache_key, json.dumps(insights, ensure_ascii=False), now.isoformat(), expires.isoformat()),
            )
            await db.commit()

        await log_activity(
            action="ai.dashboard_insights",
            summary=f"Dashboard insights generate ({len(insights)} items)",
            details={"provider": result["provider"]},
        )

        return {
            "insights": insights,
            "generated_at": now.isoformat(),
            "cached": False,
            "provider": result["provider"],
        }

    except RuntimeError as e:
        # No AI providers available — return fallback insights
        return {
            "insights": [
                f"Total calculații: {stats['calculations']['count']}, "
                f"valoare totală: {stats['calculations']['total_value']} RON.",
                f"Fișiere încărcate: {stats['files_uploaded']}.",
                f"Traduceri efectuate: {stats['translations']['count']}.",
            ],
            "generated_at": datetime.utcnow().isoformat(),
            "cached": False,
            "provider": "fallback",
            "note": str(e),
        }


@router_tools.post("/insights/refresh")
async def refresh_insights():
    """
    Invalidează cache-ul de insights și forțează regenerare.
    Șterge intrarea din ai_insights_cache și apelează get_dashboard_insights.
    """
    async with get_db() as db:
        cursor = await db.execute(
            "DELETE FROM ai_insights_cache WHERE cache_key = 'dashboard_insights'"
        )
        deleted = cursor.rowcount
        await db.commit()

    await log_activity(
        action="ai.insights_refresh",
        summary=f"Cache insights invalidat ({deleted} intrări șterse)",
    )

    # Regenerate fresh insights
    fresh = await get_dashboard_insights()
    fresh["cache_cleared"] = True
    return fresh


# ==========================================
# 15B.10 — COMPETITOR PRICE COMPARISON
# ==========================================

def _parse_competitors_md() -> list[dict]:
    """Parse Competitori.md to extract competitor pricing data."""
    if not COMPETITORI_PATH.exists():
        return []

    content = COMPETITORI_PATH.read_text(encoding="utf-8", errors="ignore")

    competitors = []
    # Find the table in "Tabel Comparativ Competitori"
    in_table = False
    for line in content.split("\n"):
        line = line.strip()
        if line.startswith("| #"):
            in_table = True
            continue
        if in_table and line.startswith("|---"):
            continue
        if in_table and line.startswith("|"):
            parts = [p.strip() for p in line.split("|")]
            # parts: ['', '#', 'Competitor', 'Locatie', 'Tarif EN↔RO', 'Tarif Tehnic', 'Urgenta', 'Obs', '']
            if len(parts) >= 7:
                name = re.sub(r"\*+", "", parts[2]).strip()
                tarif_general = parts[4]
                tarif_tehnic = parts[5]

                # Extract numeric values
                gen_nums = re.findall(r"(\d+)", tarif_general)
                tech_nums = re.findall(r"(\d+)", tarif_tehnic)

                gen_price = float(gen_nums[-1]) if gen_nums else None
                tech_price = float(tech_nums[-1]) if tech_nums else None

                if name and (gen_price or tech_price):
                    competitors.append({
                        "name": name,
                        "general_price": gen_price,
                        "technical_price": tech_price,
                        "location": re.sub(r"\*+", "", parts[3]).strip(),
                        "notes": re.sub(r"\*+", "", parts[7]).strip() if len(parts) > 7 else "",
                    })
        elif in_table and not line.startswith("|"):
            in_table = False

    return competitors


@router_tools.post("/compare-price")
async def compare_price(req: ComparePriceRequest):
    """
    Compară prețul calculat cu competitorii din Competitori.md.
    AI analizează poziția pe piață.
    """
    competitors = _parse_competitors_md()

    if not competitors:
        raise HTTPException(
            404,
            "Nu s-au găsit date despre competitori. Verifică 99_Roland_Work_Place/Competitori.md"
        )

    price_per_page = req.price / max(req.pages, 1)

    # Get relevant prices based on doc_type
    price_field = "technical_price" if req.doc_type in ("tehnic", "technical", "auto", "ITP") else "general_price"
    valid_competitors = [
        c for c in competitors if c.get(price_field) is not None
    ]

    if not valid_competitors:
        # Fallback to any available prices
        valid_competitors = [c for c in competitors if c.get("general_price") is not None]
        price_field = "general_price"

    market_prices = [c[price_field] for c in valid_competitors]
    avg_market = sum(market_prices) / len(market_prices) if market_prices else 30
    min_market = min(market_prices) if market_prices else 22
    max_market = max(market_prices) if market_prices else 45

    # Calculate percentile position
    cheaper_count = sum(1 for p in market_prices if p > price_per_page)
    position_percentile = round((cheaper_count / len(market_prices)) * 100) if market_prices else 50

    # Build AI prompt
    comp_list = "\n".join(
        f"  - {c['name']} ({c['location']}): {c[price_field]} RON/pag"
        for c in valid_competitors[:12]
    )

    system = (
        "Ești un analist de piață pentru traduceri tehnice EN↔RO în România. "
        "Analizează poziția prețului față de competitori. "
        "Răspunde concis: 2-3 propoziții cu poziționarea pe piață + o recomandare. "
        "Limba: română. Fii obiectiv și bazat pe date."
    )
    prompt = (
        f"Prețul nostru: {price_per_page:.0f} RON/pagină ({req.price:.0f} RON total, {req.pages} pagini)\n"
        f"Tip document: {req.doc_type}\n\n"
        f"Competitori:\n{comp_list}\n\n"
        f"Medie piață: {avg_market:.0f} RON/pag | "
        f"Interval: {min_market:.0f}-{max_market:.0f} RON/pag\n"
        f"Poziție: mai ieftin decât {position_percentile}% din competitori\n\n"
        f"Analizează poziția noastră pe piață."
    )

    result = await ai_generate(prompt, system)
    await track_usage(result["provider"], chars=len(prompt) + len(result["text"]))

    # Build competitor comparison list
    comp_data = [
        {
            "name": c["name"],
            "estimated_price": c[price_field],
            "location": c["location"],
        }
        for c in valid_competitors
    ]

    await log_activity(
        action="ai.compare_price",
        summary=f"Comparare preț: {price_per_page:.0f} RON/pag vs {len(valid_competitors)} competitori",
        details={"price": req.price, "price_per_page": price_per_page, "provider": result["provider"]},
    )

    return {
        "analysis": result["text"],
        "competitors": comp_data,
        "position_percentile": position_percentile,
        "suggestion": f"{'Sub media pieței' if price_per_page < avg_market else 'Peste media pieței'} "
                       f"({price_per_page:.0f} vs {avg_market:.0f} RON/pag)",
        "market_stats": {
            "average": round(avg_market, 1),
            "min": min_market,
            "max": max_market,
        },
        "provider": result["provider"],
    }
