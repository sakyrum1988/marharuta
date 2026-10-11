"""Add or refresh the Israel destination without touching other country rows."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "content.db"
SLUG = "move-to-israel"

def main() -> None:
    now = datetime.now(timezone.utc).isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        page = {"title":"Moving to Israel in 2026: Visas, Aliyah, Work and Costs", "content":"<p>Israel relocation guide. The rendered country page is generated from verified bilingual country data in app.py.</p>", "parent":"countries", "link":"/countries/move-to-israel/"}
        if conn.execute("SELECT 1 FROM pages WHERE slug=?", (SLUG,)).fetchone():
            conn.execute("UPDATE pages SET title=?,content=?,parent=?,link=? WHERE slug=?", (page["title"], page["content"], page["parent"], page["link"], SLUG))
        else:
            conn.execute("INSERT INTO pages (slug,title,content,parent,link) VALUES (?,?,?,?,?)", (SLUG, page["title"], page["content"], page["parent"], page["link"]))
        facts = {
            "iso2":"IL", "name":"Israel", "capital":"Jerusalem", "currency_code":"ILS", "currency_name":"Israeli new shekel", "languages":"Hebrew, Arabic", "population":10122800,
            "flag_svg":"https://flagcdn.com/il.svg", "timezone":"UTC+2 / UTC+3 DST", "region":"Western Asia", "gdp_per_capita":60336.8477964194,
            "internet_pct":88.18242225, "inflation":3.04141321556539, "unemployment":3.489, "life_expectancy":83.1975609756098, "area":22070.0,
            "wb_year":"2024–2025", "gdp_per_capita_year":"2025", "internet_pct_year":"2024", "inflation_year":"2025", "unemployment_year":"2025",
            "life_expectancy_year":"2024", "population_year":"2025", "area_year":"2024", "updated_at":now, "wb_checked_at":now,
        }
        if conn.execute("SELECT 1 FROM country_facts WHERE slug=?", (SLUG,)).fetchone():
            assignments = ", ".join(f"{key}=?" for key in facts)
            conn.execute(f"UPDATE country_facts SET {assignments} WHERE slug=?", (*facts.values(), SLUG))
        else:
            values = {"slug":SLUG, **facts}
            conn.execute(f"INSERT INTO country_facts ({', '.join(values)}) VALUES ({', '.join('?' for _ in values)})", tuple(values.values()))
        conn.commit()
    print("Israel destination and facts are up to date.")

if __name__ == "__main__":
    main()
