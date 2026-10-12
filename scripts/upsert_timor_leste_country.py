"""Add or refresh the Timor-Leste destination without touching other country rows."""
from __future__ import annotations
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "content.db"
SLUG = "move-to-timor-leste"
def main() -> None:
    now = datetime.now(timezone.utc).isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        page={"title":"Timor-Leste in 2026: Visas, Work, Costs and Cities","content":"<p>Timor-Leste relocation guide. The rendered country page is generated from verified bilingual country data in app.py.</p>","parent":"countries","link":"/countries/move-to-timor-leste/"}
        if conn.execute("SELECT 1 FROM pages WHERE slug=?",(SLUG,)).fetchone(): conn.execute("UPDATE pages SET title=?,content=?,parent=?,link=? WHERE slug=?",(page["title"],page["content"],page["parent"],page["link"],SLUG))
        else: conn.execute("INSERT INTO pages (slug,title,content,parent,link) VALUES (?,?,?,?,?)",(SLUG,page["title"],page["content"],page["parent"],page["link"]))
        facts={"iso2":"TL","name":"Timor-Leste","capital":"Dili","currency_code":"USD","currency_name":"United States Dollar","languages":"Tetum, Portuguese","population":1418517,"flag_svg":"https://flagcdn.com/tl.svg","timezone":"UTC+9","region":"Southeastern Asia","gdp_per_capita":1341.0,"internet_pct":None,"inflation":0.4,"unemployment":1.6,"life_expectancy":68.0,"area":14987.0,"wb_year":"World Bank latest available","gdp_per_capita_year":"2025","internet_pct_year":None,"inflation_year":"2025","unemployment_year":"2025","life_expectancy_year":"2024","population_year":"2025","area_year":"2024","updated_at":now,"wb_checked_at":now}
        if conn.execute("SELECT 1 FROM country_facts WHERE slug=?",(SLUG,)).fetchone():
            assignments=", ".join(f"{key}=?" for key in facts); conn.execute(f"UPDATE country_facts SET {assignments} WHERE slug=?",(*facts.values(),SLUG))
        else:
            values={"slug":SLUG,**facts}; conn.execute(f"INSERT INTO country_facts ({', '.join(values)}) VALUES ({', '.join('?' for _ in values)})",tuple(values.values()))
        conn.commit()
    print("Timor-Leste destination and facts are up to date.")
if __name__ == "__main__": main()
