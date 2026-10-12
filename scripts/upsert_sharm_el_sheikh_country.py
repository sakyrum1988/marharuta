"""Add or refresh the Sharm el-Sheikh destination without touching other rows."""
from __future__ import annotations
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "content.db"
SLUG = "move-to-sharm-el-sheikh"
def main() -> None:
    now = datetime.now(timezone.utc).isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        page={"title":"Sharm el-Sheikh in 2026: Visas, Work, Costs and Areas","content":"<p>Sharm el-Sheikh relocation guide. The rendered destination page is generated from verified bilingual data in app.py.</p>","parent":"countries","link":"/countries/move-to-sharm-el-sheikh/"}
        if conn.execute("SELECT 1 FROM pages WHERE slug=?",(SLUG,)).fetchone(): conn.execute("UPDATE pages SET title=?,content=?,parent=?,link=? WHERE slug=?",(page["title"],page["content"],page["parent"],page["link"],SLUG))
        else: conn.execute("INSERT INTO pages (slug,title,content,parent,link) VALUES (?,?,?,?,?)",(SLUG,page["title"],page["content"],page["parent"],page["link"]))
        facts={"iso2":"EG","name":"Sharm el-Sheikh, Egypt","capital":"Cairo","currency_code":"EGP","currency_name":"Egyptian Pound","languages":"Arabic","population":118365995,"flag_svg":"https://flagcdn.com/eg.svg","timezone":"UTC+2","region":"Western Asia (South Sinai)","gdp_per_capita":3085.8,"internet_pct":None,"inflation":14.1,"unemployment":6.8,"life_expectancy":72.0,"area":1001450.0,"wb_year":"Egypt-wide World Bank latest available","gdp_per_capita_year":"2025","internet_pct_year":None,"inflation_year":"2025","unemployment_year":"2025","life_expectancy_year":"2024","population_year":"2025","area_year":"latest available","updated_at":now,"wb_checked_at":now}
        if conn.execute("SELECT 1 FROM country_facts WHERE slug=?",(SLUG,)).fetchone():
            assignments=", ".join(f"{key}=?" for key in facts); conn.execute(f"UPDATE country_facts SET {assignments} WHERE slug=?",(*facts.values(),SLUG))
        else:
            values={"slug":SLUG,**facts}; conn.execute(f"INSERT INTO country_facts ({', '.join(values)}) VALUES ({', '.join('?' for _ in values)})",tuple(values.values()))
        conn.commit()
    print("Sharm el-Sheikh destination and Egypt-wide facts are up to date.")
if __name__ == "__main__": main()
