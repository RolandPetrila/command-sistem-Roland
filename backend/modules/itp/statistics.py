"""
Statistics/analytics helper functions for the ITP module.

Pure functions that run SQL queries and return structured data.
No route decorators — called by router.py endpoints.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

from app.db.database import get_db

from .models import MONTH_NAMES, next_inspection_date, row_dict


async def compute_statistics_combined(year: int | None = None) -> dict:
    """Combined statistics for frontend dashboard.

    Returns monthly_inspections, top_brands, monthly_revenue, fuel_distribution
    in a single result (called by ITPPage StatsTab).
    """
    if year is None:
        year = datetime.now().year

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
            {"month": MONTH_NAMES[i], "count": monthly_raw.get(i, 0)}
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
            {"month": MONTH_NAMES[i], "revenue": revenue_raw.get(i, 0)}
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


async def compute_stats_overview() -> dict:
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


async def compute_stats_monthly(year: int | None = None) -> dict:
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

    result = []
    for i in range(1, 13):
        d = months_data[i]
        d["name"] = MONTH_NAMES[i]
        result.append(d)

    return {"year": year, "data": result}


async def compute_stats_brands() -> list[dict]:
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


async def compute_stats_revenue(year: int | None = None) -> dict:
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

    result = []
    for i in range(1, 13):
        d = months_data[i]
        d["name"] = MONTH_NAMES[i]
        result.append(d)

    return {"year": year, "data": result}


async def compute_stats_fuel_types() -> list[dict]:
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


async def compute_stats_inspectors() -> list[dict]:
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


async def compute_followup_due_soon(days: int = 30) -> list[dict]:
    """Vehicles with next inspection due within N days based on last inspection + 12 months.

    Returns list sorted by next_due_date ascending (most urgent first).
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
        item = row_dict(row)
        last_date_str = item.get("last_inspection_date")
        if not last_date_str:
            continue
        next_due = next_inspection_date(last_date_str)
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


async def compute_noshow_rate() -> dict:
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
