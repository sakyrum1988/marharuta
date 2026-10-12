"""Add or refresh the Turkmenistan destination without touching other country rows."""
from __future__ import annotations
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "content.db"
SLUG = "move-to-turkmenistan"
def main() -> None:
    now = datetime.now(timezone.utc).isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        page={"title":"Turkmenistan in 2026: Visas, Work, Costs and Cities","content":"<p>Turkmenistan relocation guide. The rendered country page is generated from verified bilingual country data in app.py.</p>","parent":"countries","link":"/countries/move-to-turkmenistan/"}
        if conn.execute("SELECT 1 FROM pages WHERE slug=?",(SLUG,)).fetchone(): conn.execute("UPDATE pages SET title=?,content=?,parent=?,link=? WHERE slug=?",(page["title"],page["content"],page["parent"],page["link"],SLUG))
        else: conn.execute("INSERT INTO pages (slug,title,content,parent,link) VALUES (?,?,?,?,?)",(SLUG,page["title"],page["content"],page["parent"],page["link"]))
        facts={"iso2":"TM","name":"Turkmenistan","capital":"Ashgabat","currency_code":"TMT","currency_name":"Turkmenistani Manat","languages":"Turkmen","population":7495000,"flag_svg":"https://flagcdn.com/tm.svg","timezone":"UTC+5","region":"Central Asia","gdp_per_capita":9166.0,"internet_pct":None,"inflation":None,"unemployment":None,"life_expectancy":69.1,"area":488100.0,"wb_year":"World Bank country overview","gdp_per_capita_year":"2024","internet_pct_year":None,"inflation_year":None,"unemployment_year":None,"life_expectancy_year":"2021 WHO via World Bank","population_year":"2024 UNFPA via World Bank","area_year":"latest available","updated_at":now,"wb_checked_at":now}
        if conn.execute("SELECT 1 FROM country_facts WHERE slug=?",(SLUG,)).fetchone():
            assignments=", ".join(f"{key}=?" for key in facts); conn.execute(f"UPDATE country_facts SET {assignments} WHERE slug=?",(*facts.values(),SLUG))
        else:
            values={"slug":SLUG,**facts}; conn.execute(f"INSERT INTO country_facts ({', '.join(values)}) VALUES ({', '.join('?' for _ in values)})",tuple(values.values()))
        conn.commit()
    print("Turkmenistan destination and facts are up to date.")
if __name__ == "__main__": main()
