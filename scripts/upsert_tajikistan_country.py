"""Add or refresh the Tajikistan destination without touching other country rows."""
from __future__ import annotations
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "content.db"
SLUG = "move-to-tajikistan"
def main() -> None:
    now = datetime.now(timezone.utc).isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        page={"title":"Tajikistan in 2026: Visas, Work, Costs and Cities","content":"<p>Tajikistan relocation guide. The rendered country page is generated from verified bilingual country data in app.py.</p>","parent":"countries","link":"/countries/move-to-tajikistan/"}
        if conn.execute("SELECT 1 FROM pages WHERE slug=?",(SLUG,)).fetchone(): conn.execute("UPDATE pages SET title=?,content=?,parent=?,link=? WHERE slug=?",(page["title"],page["content"],page["parent"],page["link"],SLUG))
        else: conn.execute("INSERT INTO pages (slug,title,content,parent,link) VALUES (?,?,?,?,?)",(SLUG,page["title"],page["content"],page["parent"],page["link"]))
        facts={"iso2":"TJ","name":"Tajikistan","capital":"Dushanbe","currency_code":"TJS","currency_name":"Tajikistani Somoni","languages":"Tajik, Russian","population":10786734,"flag_svg":"https://flagcdn.com/tj.svg","timezone":"UTC+5","region":"Central Asia","gdp_per_capita":1637.3,"internet_pct":56.0,"inflation":None,"unemployment":6.9,"life_expectancy":72.0,"area":141400.0,"wb_year":"World Bank latest available","gdp_per_capita_year":"2025","internet_pct_year":"2024","inflation_year":None,"unemployment_year":"2025","life_expectancy_year":"2024","population_year":"2025","area_year":"2024","updated_at":now,"wb_checked_at":now}
        if conn.execute("SELECT 1 FROM country_facts WHERE slug=?",(SLUG,)).fetchone():
            assignments=", ".join(f"{key}=?" for key in facts); conn.execute(f"UPDATE country_facts SET {assignments} WHERE slug=?",(*facts.values(),SLUG))
        else:
            values={"slug":SLUG,**facts}; conn.execute(f"INSERT INTO country_facts ({', '.join(values)}) VALUES ({', '.join('?' for _ in values)})",tuple(values.values()))
        conn.commit()
    print("Tajikistan destination and facts are up to date.")
if __name__ == "__main__": main()
