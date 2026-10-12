"""Add or refresh the Palestine destination without touching other country rows."""
from __future__ import annotations
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "content.db"
SLUG = "move-to-palestine"
def main() -> None:
    now = datetime.now(timezone.utc).isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        page={"title":"Palestine in 2026: West Bank Entry, Work and Safety","content":"<p>Palestine relocation guide. The rendered country page is generated from verified bilingual country data in app.py.</p>","parent":"countries","link":"/countries/move-to-palestine/"}
        if conn.execute("SELECT 1 FROM pages WHERE slug=?",(SLUG,)).fetchone(): conn.execute("UPDATE pages SET title=?,content=?,parent=?,link=? WHERE slug=?",(page["title"],page["content"],page["parent"],page["link"],SLUG))
        else: conn.execute("INSERT INTO pages (slug,title,content,parent,link) VALUES (?,?,?,?,?)",(SLUG,page["title"],page["content"],page["parent"],page["link"]))
        facts={"iso2":"PS","name":"Palestine","capital":"Ramallah (administrative centre)","currency_code":"ILS","currency_name":"Israeli New Shekel (widely used)","languages":"Arabic","population":5413596,"flag_svg":"https://flagcdn.com/ps.svg","timezone":"UTC+2 / UTC+3 DST","region":"Western Asia","gdp_per_capita":3171.108,"internet_pct":None,"inflation":9.8,"unemployment":24.4,"life_expectancy":69.213,"area":6020.0,"wb_year":"World Bank latest available","gdp_per_capita_year":"2025","internet_pct_year":None,"inflation_year":"2025","unemployment_year":"2022","life_expectancy_year":"2024","population_year":"2025","area_year":"2024","updated_at":now,"wb_checked_at":now}
        if conn.execute("SELECT 1 FROM country_facts WHERE slug=?",(SLUG,)).fetchone():
            assignments=", ".join(f"{key}=?" for key in facts); conn.execute(f"UPDATE country_facts SET {assignments} WHERE slug=?",(*facts.values(),SLUG))
        else:
            values={"slug":SLUG,**facts}; conn.execute(f"INSERT INTO country_facts ({', '.join(values)}) VALUES ({', '.join('?' for _ in values)})",tuple(values.values()))
        conn.commit()
    print("Palestine destination and facts are up to date.")
if __name__ == "__main__": main()
