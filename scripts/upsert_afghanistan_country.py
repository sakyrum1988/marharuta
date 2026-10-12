"""Add or refresh the Afghanistan destination without touching other country rows."""
from __future__ import annotations
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "content.db"
SLUG = "move-to-afghanistan"


def main() -> None:
    now = datetime.now(timezone.utc).isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        page = {
            "title": "Moving to Afghanistan in 2026: Visas, Work, Costs and Safety",
            "content": "<p>Afghanistan relocation guide. The rendered country page is generated from verified bilingual country data in app.py.</p>",
            "parent": "countries",
            "link": "/countries/move-to-afghanistan/",
        }
        if conn.execute("SELECT 1 FROM pages WHERE slug=?", (SLUG,)).fetchone():
            conn.execute("UPDATE pages SET title=?,content=?,parent=?,link=? WHERE slug=?", (page["title"], page["content"], page["parent"], page["link"], SLUG))
        else:
            conn.execute("INSERT INTO pages (slug,title,content,parent,link) VALUES (?,?,?,?,?)", (SLUG, page["title"], page["content"], page["parent"], page["link"]))
        facts = {
            "iso2": "AF", "name": "Afghanistan", "capital": "Kabul", "currency_code": "AFN",
            "currency_name": "Afghan afghani", "languages": "Dari, Pashto", "population": 43844111,
            "flag_svg": "https://flagcdn.com/af.svg", "timezone": "UTC+4:30", "region": "Southern Asia",
            "gdp_per_capita": 416.871146273728, "internet_pct": 16.09499931,
            "inflation": -6.60118564073725, "unemployment": 13.351, "life_expectancy": 66.289,
            "area": 652870.0, "wb_year": "2024-2025", "gdp_per_capita_year": "2024",
            "internet_pct_year": "2024", "inflation_year": "2024", "unemployment_year": "2025",
            "life_expectancy_year": "2024", "population_year": "2025", "area_year": "2024",
            "updated_at": now, "wb_checked_at": now,
        }
        if conn.execute("SELECT 1 FROM country_facts WHERE slug=?", (SLUG,)).fetchone():
            assignments = ", ".join(f"{key}=?" for key in facts)
            conn.execute(f"UPDATE country_facts SET {assignments} WHERE slug=?", (*facts.values(), SLUG))
        else:
            values = {"slug": SLUG, **facts}
            conn.execute(f"INSERT INTO country_facts ({', '.join(values)}) VALUES ({', '.join('?' for _ in values)})", tuple(values.values()))
        conn.commit()
    print("Afghanistan destination and facts are up to date.")


if __name__ == "__main__":
    main()
