"""Add or refresh the Türkiye destination without touching other country rows."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "content.db"
SLUG = "move-to-turkey"


def main() -> None:
    now = datetime.now(timezone.utc).isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        page = {
            "title": "Moving to Türkiye in 2026: Visas, Residence, Costs and Work",
            "content": "<p>Türkiye relocation guide. The rendered country page is generated from verified bilingual country data in app.py.</p>",
            "parent": "countries",
            "link": "/countries/move-to-turkey/",
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
            "iso2": "TR",
            "name": "Türkiye",
            "capital": "Ankara",
            "currency_code": "TRY",
            "currency_name": "Turkish lira",
            "languages": "Turkish",
            "population": 85878556,
            "flag_svg": "https://flagcdn.com/tr.svg",
            "timezone": "UTC+3",
            "region": "Western Asia",
            "gdp_per_capita": 18599.44,
            "internet_pct": 89.77,
            "inflation": 34.88,
            "unemployment": 8.52,
            "life_expectancy": 77.42,
            "area": 785350.0,
            "wb_year": "2024–2025",
            "gdp_per_capita_year": "2025",
            "internet_pct_year": "2025",
            "inflation_year": "2025",
            "unemployment_year": "2025",
            "life_expectancy_year": "2024",
            "population_year": "2025",
            "area_year": "2023",
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
    print("Turkey destination and facts are up to date.")


if __name__ == "__main__":
    main()
