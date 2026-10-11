"""Add or refresh the Georgia destination without touching other country rows."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "content.db"
SLUG = "move-to-georgia"


def main() -> None:
    now = datetime.now(timezone.utc).isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute("SELECT id FROM pages WHERE slug = ?", (SLUG,)).fetchone()
        page = {
            "title": "Moving to Georgia in 2026: Visas, Costs, Work and Tax",
            "content": "<p>Georgia relocation guide. The rendered country page is generated from verified bilingual country data in app.py.</p>",
            "parent": "countries",
            "link": "/countries/move-to-georgia/",
        }
        if row:
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
            "iso2": "GE",
            "name": "Georgia",
            "capital": "Tbilisi",
            "currency_code": "GEL",
            "currency_name": "Georgian lari",
            "languages": "Georgian",
            "population": 3935766,
            "flag_svg": "https://flagcdn.com/ge.svg",
            "timezone": "UTC+4",
            "region": "Western Asia",
            "internet_pct": 83.8,
            "life_expectancy": 74.66,
            "area": 69700.0,
            "wb_year": "2024–2025",
            "internet_pct_year": "2024",
            "life_expectancy_year": "2024",
            "population_year": "2025",
            "area_year": "2023",
            "updated_at": now,
            "wb_checked_at": now,
        }
        existing = conn.execute("SELECT slug FROM country_facts WHERE slug = ?", (SLUG,)).fetchone()
        if existing:
            assignments = ", ".join(f"{key} = ?" for key in facts)
            conn.execute(
                f"UPDATE country_facts SET {assignments} WHERE slug = ?",
                (*facts.values(), SLUG),
            )
        else:
            values = {"slug": SLUG, **facts}
            conn.execute(
                f"INSERT INTO country_facts ({', '.join(values)}) VALUES ({', '.join('?' for _ in values)})",
                tuple(values.values()),
            )
        conn.commit()
    print("Georgia destination and facts are up to date.")


if __name__ == "__main__":
    main()
