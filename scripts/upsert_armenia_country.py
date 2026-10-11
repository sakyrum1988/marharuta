"""Add or refresh the Armenia destination without touching other country rows."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "content.db"
SLUG = "move-to-armenia"


def main() -> None:
    now = datetime.now(timezone.utc).isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        page = {
            "title": "Moving to Armenia in 2026: Visas, Residence, Costs and Work",
            "content": "<p>Armenia relocation guide. The rendered country page is generated from verified bilingual country data in app.py.</p>",
            "parent": "countries",
            "link": "/countries/move-to-armenia/",
        }
        if conn.execute("SELECT 1 FROM pages WHERE slug = ?", (SLUG,)).fetchone():
            conn.execute(
                "UPDATE pages SET title = ?, content = ?, parent = ?, link = ? WHERE slug = ?",
                (page["title"], page["content"], page["parent"], page["link"], SLUG),
            )
        else:
            conn.execute(
                "INSERT INTO pages (slug, title, content, parent, link) VALUES (?, ?, ?, ?, ?)",
                (SLUG, page["title"], page["content"], page["parent"], page["link"]),
            )

        facts = {
            "iso2": "AM",
            "name": "Armenia",
            "capital": "Yerevan",
            "currency_code": "AMD",
            "currency_name": "Armenian dram",
            "languages": "Armenian",
            "population": 3086700,
            "flag_svg": "https://flagcdn.com/am.svg",
            "timezone": "UTC+4",
            "region": "Western Asia",
            "gdp_per_capita": 9474.02,
            "internet_pct": 81.0,
            "inflation": 3.3,
            "unemployment": 12.9,
            "life_expectancy": 78.32,
            "area": 29740.0,
            "wb_year": "2024–2025",
            "gdp_per_capita_year": "2025",
            "internet_pct_year": "2024",
            "inflation_year": "2025",
            "unemployment_year": "2025",
            "life_expectancy_year": "2024",
            "population_year": "2025",
            "area_year": "2024",
            "updated_at": now,
            "wb_checked_at": now,
        }
        if conn.execute("SELECT 1 FROM country_facts WHERE slug = ?", (SLUG,)).fetchone():
            assignments = ", ".join(f"{key} = ?" for key in facts)
            conn.execute(f"UPDATE country_facts SET {assignments} WHERE slug = ?", (*facts.values(), SLUG))
        else:
            values = {"slug": SLUG, **facts}
            conn.execute(
                f"INSERT INTO country_facts ({', '.join(values)}) VALUES ({', '.join('?' for _ in values)})",
                tuple(values.values()),
            )
        conn.commit()
    print("Armenia destination and facts are up to date.")


if __name__ == "__main__":
    main()
