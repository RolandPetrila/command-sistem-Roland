"""
Invoice Reports sub-router:
  - GET /api/invoice/reports/monthly  — Monthly revenue report
  - GET /api/invoice/reports/summary  — Total revenue summary + top clients
"""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter

from app.db.database import get_db

reports_router = APIRouter(prefix="/api/invoice", tags=["Invoice Reports"])


@reports_router.get("/reports/monthly")
async def monthly_report(year: int = None):
    """Raport lunar venituri — suma per luna, pentru grafice."""
    if year is None:
        year = date.today().year

    async with get_db() as db:
        cursor = await db.execute(
            """SELECT
                 strftime('%m', date) as luna,
                 COUNT(*) as nr_facturi,
                 COALESCE(SUM(total), 0) as total_venituri,
                 COALESCE(SUM(CASE WHEN status = 'paid' THEN total ELSE 0 END), 0) as total_incasat
               FROM invoices
               WHERE strftime('%Y', date) = ?
               GROUP BY strftime('%m', date)
               ORDER BY luna ASC""",
            (str(year),),
        )
        rows = await cursor.fetchall()

    month_names = [
        "Ianuarie", "Februarie", "Martie", "Aprilie",
        "Mai", "Iunie", "Iulie", "August",
        "Septembrie", "Octombrie", "Noiembrie", "Decembrie",
    ]
    data_by_month = {row["luna"]: dict(row) for row in rows}

    months = []
    for i in range(1, 13):
        key = f"{i:02d}"
        entry = data_by_month.get(key, {})
        months.append({
            "luna": i,
            "luna_nume": month_names[i - 1],
            "nr_facturi": entry.get("nr_facturi", 0),
            "total_venituri": round(entry.get("total_venituri", 0), 2),
            "total_incasat": round(entry.get("total_incasat", 0), 2),
        })

    return {
        "year": year,
        "months": months,
        "total_anual": round(sum(m["total_venituri"] for m in months), 2),
        "total_incasat_anual": round(sum(m["total_incasat"] for m in months), 2),
    }


@reports_router.get("/reports/summary")
async def reports_summary():
    """Sumar total: venituri, medie factura, top clienti, status breakdown."""
    async with get_db() as db:
        cursor = await db.execute(
            """SELECT
                 COUNT(*) as total_facturi,
                 COALESCE(SUM(total), 0) as total_venituri,
                 COALESCE(AVG(total), 0) as medie_factura,
                 COALESCE(MIN(total), 0) as min_factura,
                 COALESCE(MAX(total), 0) as max_factura,
                 COALESCE(SUM(CASE WHEN status = 'paid' THEN total ELSE 0 END), 0) as total_incasat
               FROM invoices"""
        )
        totals = await cursor.fetchone()

        cursor = await db.execute(
            """SELECT status, COUNT(*) as count, COALESCE(SUM(total), 0) as total
               FROM invoices
               GROUP BY status
               ORDER BY count DESC"""
        )
        status_rows = await cursor.fetchall()

        cursor = await db.execute(
            """SELECT c.id, c.name, c.cui,
                      COUNT(i.id) as nr_facturi,
                      COALESCE(SUM(i.total), 0) as total_valoare
               FROM clients c
               LEFT JOIN invoices i ON c.id = i.client_id
               GROUP BY c.id
               HAVING nr_facturi > 0
               ORDER BY total_valoare DESC
               LIMIT 10"""
        )
        top_clients = await cursor.fetchall()

        cursor = await db.execute(
            """SELECT i.id, i.invoice_number, i.date, i.total, i.status,
                      c.name as client_name
               FROM invoices i
               LEFT JOIN clients c ON i.client_id = c.id
               ORDER BY i.date DESC, i.id DESC
               LIMIT 5"""
        )
        recent = await cursor.fetchall()

    return {
        "totals": {
            "total_facturi": totals["total_facturi"],
            "total_venituri": round(totals["total_venituri"], 2),
            "medie_factura": round(totals["medie_factura"], 2),
            "min_factura": round(totals["min_factura"], 2),
            "max_factura": round(totals["max_factura"], 2),
            "total_incasat": round(totals["total_incasat"], 2),
        },
        "status_breakdown": [
            {"status": row["status"], "count": row["count"], "total": round(row["total"], 2)}
            for row in status_rows
        ],
        "top_clients": [
            {
                "id": row["id"],
                "name": row["name"],
                "cui": row["cui"],
                "nr_facturi": row["nr_facturi"],
                "total_valoare": round(row["total_valoare"], 2),
            }
            for row in top_clients
        ],
        "recent_invoices": [dict(row) for row in recent],
    }
