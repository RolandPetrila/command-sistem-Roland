"""
Timeline & Export — activity timeline (paginated + stats) and full data export.

Endpoints:
  GET /api/reports/timeline
  GET /api/reports/timeline/stats
  GET /api/reports/export/full
"""

from __future__ import annotations

import json
import logging
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.core.activity_log import log_activity
from app.db.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/reports", tags=["Reports — Timeline"])


# ===========================================================================
# ACTIVITY TIMELINE
# ===========================================================================

@router.get("/timeline")
async def activity_timeline(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    date_from: str = Query("", description="Data inceput (YYYY-MM-DD)"),
    date_to: str = Query("", description="Data sfarsit (YYYY-MM-DD)"),
    action_filter: str = Query("", description="Filtreaza pe actiune"),
):
    """Timeline activitate din activity_log, paginat cu filtre pe data."""
    offset = (page - 1) * per_page

    conditions = []
    params: list[Any] = []

    if date_from:
        conditions.append("timestamp >= ?")
        params.append(date_from)
    if date_to:
        conditions.append("timestamp <= ?")
        params.append(date_to + "T23:59:59")
    if action_filter:
        conditions.append("action = ?")
        params.append(action_filter)

    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    try:
        async with get_db() as db:
            count_sql = f"SELECT COUNT(*) as cnt FROM activity_log {where_clause}"
            cursor = await db.execute(count_sql, tuple(params))
            count_row = await cursor.fetchone()
            total = count_row["cnt"] if count_row else 0

            data_sql = f"""
                SELECT * FROM activity_log {where_clause}
                ORDER BY timestamp DESC
                LIMIT ? OFFSET ?
            """
            cursor = await db.execute(data_sql, tuple(params) + (per_page, offset))
            rows = await cursor.fetchall()

            entries = []
            for row in rows:
                entry: dict[str, Any] = {
                    "id": row["id"] if "id" in row.keys() else None,
                    "timestamp": row["timestamp"],
                    "action": row["action"],
                    "status": row["status"],
                    "summary": row["summary"],
                }
                if row["details"]:
                    try:
                        entry["details"] = json.loads(row["details"])
                    except (json.JSONDecodeError, TypeError):
                        entry["details"] = row["details"]
                entries.append(entry)

        return {
            "entries": entries,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": max(1, (total + per_page - 1) // per_page),
        }

    except Exception as exc:
        logger.error("Eroare timeline: %s", exc)
        raise HTTPException(500, f"Eroare citire timeline: {exc}")


@router.get("/timeline/stats")
async def activity_timeline_stats(
    group_by: str = Query("day", description="Grupare: day, week, month"),
    days: int = Query(30, ge=1, le=365, description="Ultimele N zile"),
):
    """Agregare activitate pe zi/saptamana/luna."""
    try:
        async with get_db() as db:
            if group_by == "month":
                date_expr = "strftime('%Y-%m', timestamp)"
            elif group_by == "week":
                date_expr = "strftime('%Y-W%W', timestamp)"
            else:
                date_expr = "strftime('%Y-%m-%d', timestamp)"

            sql = f"""
                SELECT
                    {date_expr} as period,
                    COUNT(*) as count,
                    action,
                    status
                FROM activity_log
                WHERE timestamp >= date('now', '-' || ? || ' days')
                GROUP BY period, action, status
                ORDER BY period DESC
            """
            cursor = await db.execute(sql, (days,))
            rows = await cursor.fetchall()

            periods: dict[str, dict[str, Any]] = defaultdict(
                lambda: {"total": 0, "actions": defaultdict(int), "statuses": defaultdict(int)}
            )
            for row in rows:
                p = row["period"]
                cnt = row["count"]
                periods[p]["total"] += cnt
                periods[p]["actions"][row["action"]] += cnt
                periods[p]["statuses"][row["status"]] += cnt

            result = []
            for period, data in sorted(periods.items(), reverse=True):
                result.append({
                    "period": period,
                    "total": data["total"],
                    "actions": dict(data["actions"]),
                    "statuses": dict(data["statuses"]),
                })

        return {
            "stats": result,
            "group_by": group_by,
            "days": days,
            "total_periods": len(result),
        }

    except Exception as exc:
        logger.error("Eroare timeline stats: %s", exc)
        raise HTTPException(500, f"Eroare statistici timeline: {exc}")


# ===========================================================================
# FULL EXPORT
# ===========================================================================

@router.get("/export/full")
async def export_full():
    """Export complet al tuturor datelor ca JSON — clienti, facturi, activitate, jurnal, bookmark-uri."""
    export_data: dict[str, Any] = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "tables": {},
    }

    tables_to_export = [
        "activity_log",
        "uploads",
        "settings",
        "journal_entries",
        "bookmarks",
        "clients",
        "invoices",
        "invoice_items",
        "itp_inspections",
        "notepad_entries",
    ]

    try:
        async with get_db() as db:
            for table in tables_to_export:
                try:
                    cursor = await db.execute(f"SELECT * FROM {table}")
                    rows = await cursor.fetchall()
                    export_data["tables"][table] = [dict(row) for row in rows]
                except Exception:
                    export_data["tables"][table] = []

        total_records = sum(len(v) for v in export_data["tables"].values())
        export_data["stats"] = {
            "total_tables": len(export_data["tables"]),
            "total_records": total_records,
        }

        await log_activity(
            action="reports.export",
            summary=f"Export complet: {total_records} inregistrari din {len(export_data['tables'])} tabele",
        )

        return export_data

    except Exception as exc:
        logger.error("Eroare export: %s", exc)
        raise HTTPException(500, f"Eroare export date: {exc}")
