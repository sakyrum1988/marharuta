"""Add or refresh the Maldives destination without touching other country rows."""
from __future__ import annotations
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "content.db"
SLUG = "move-to-maldives"


def main() -> None:
    now = datetime.now(timezone.utc).isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        page = {"title": "Moving to the Maldives in 2026: Visas, Work, Costs and Island Life", "content": "<p>Maldives relocation guide. The rendered country page is generated from verified bilingual country data in app.py.</p>", "parent": "countries", "link": "/countries/move-to-maldives/"}
        if conn.execute("SELECT 1 FROM pages WHERE slug=?", (SLUG,)).fetchone():
            conn.execute("UPDATE pages SET title=?,content=?,parent=?,link=? WHERE slug=?", (page["title"], page["content"], page["parent"], page["link"], SLUG))
        else:
            conn.execute("INSERT INTO pages (slug,title,content,parent,link) VALUES (?,?,?,?,?)", (SLUG, page["title"], page["content"], page["parent"], page["link"]))
        facts = {
            "iso2": "MV", "name": "Maldives", "capital": "Malé", "currency_code": "MVR", "currency_name": "Maldivian Rufiyaa",
            "languages": "Dhivehi", "population": 529676, "flag_svg": "https://flagcdn.com/mv.svg", "timezone": "UTC+5", "region": "South Asia",
            "gdp_per_capita": 14614.7, "internet_pct": 85.0, "inflation": 4.0, "unemployment": 4.5,
            "life_expectancy": 81.285, "area": 300.0, "wb_year": "2024-2025",
            "gdp_per_capita_year": "2025", "internet_pct_year": "2024", "inflation_year": "2025", "unemployment_year": "2025",
            "life_expectancy_year": "2024", "population_year": "2025", "area_year": "2025", "updated_at": now, "wb_checked_at": now,
        }
        if conn.execute("SELECT 1 FROM country_facts WHERE slug=?", (SLUG,)).fetchone():
            assignments = ", ".join(f"{key}=?" for key in facts)
            conn.execute(f"UPDATE country_facts SET {assignments} WHERE slug=?", (*facts.values(), SLUG))
        else:
            values = {"slug": SLUG, **facts}
            conn.execute(f"INSERT INTO country_facts ({', '.join(values)}) VALUES ({', '.join('?' for _ in values)})", tuple(values.values()))
        conn.commit()
    print("Maldives destination and facts are up to date.")


if __name__ == "__main__":
    main()
