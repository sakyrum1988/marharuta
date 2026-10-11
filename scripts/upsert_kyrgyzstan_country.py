"""Add or refresh the Kyrgyzstan destination without touching other country rows."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "content.db"
SLUG = "move-to-kyrgyzstan"


def main() -> None:
    now = datetime.now(timezone.utc).isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        page = {
            "title": "Moving to Kyrgyzstan in 2026: Entry, Registration, Costs and Work",
            "content": "<p>Kyrgyzstan relocation guide. The rendered country page is generated from verified bilingual country data in app.py.</p>",
            "parent": "countries",
            "link": "/countries/move-to-kyrgyzstan/",
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
            "iso2": "KG",
            "name": "Kyrgyzstan",
            "capital": "Bishkek",
            "currency_code": "KGS",
            "currency_name": "Kyrgyzstani som",
            "languages": "Kyrgyz, Russian",
            "population": 7343064,
            "flag_svg": "https://flagcdn.com/kg.svg",
            "timezone": "UTC+6",
            "region": "Central Asia",
            "gdp_per_capita": 3080.97,
            "internet_pct": 92.03,
            "inflation": 8.21,
            "unemployment": 3.53,
            "life_expectancy": 72.4,
            "area": 199950.0,
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
    print("Kyrgyzstan destination and facts are up to date.")


if __name__ == "__main__":
    main()
