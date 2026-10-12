"""Add or refresh the North Korea destination without touching other country rows."""
from __future__ import annotations
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "content.db"
SLUG = "move-to-north-korea"
def main() -> None:
    now = datetime.now(timezone.utc).isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        page={"title":"North Korea in 2026: Entry, Sponsored Assignments and Safety","content":"<p>North Korea assignment guide. The rendered country page is generated from verified bilingual country data in app.py.</p>","parent":"countries","link":"/countries/move-to-north-korea/"}
        if conn.execute("SELECT 1 FROM pages WHERE slug=?",(SLUG,)).fetchone(): conn.execute("UPDATE pages SET title=?,content=?,parent=?,link=? WHERE slug=?",(page["title"],page["content"],page["parent"],page["link"],SLUG))
        else: conn.execute("INSERT INTO pages (slug,title,content,parent,link) VALUES (?,?,?,?,?)",(SLUG,page["title"],page["content"],page["parent"],page["link"]))
        facts={"iso2":"KP","name":"North Korea","capital":"Pyongyang","currency_code":"KPW","currency_name":"North Korean Won","languages":"Korean","population":26571000,"flag_svg":"https://flagcdn.com/kp.svg","timezone":"UTC+9","region":"Eastern Asia","gdp_per_capita":640.0,"internet_pct":None,"inflation":None,"unemployment":None,"life_expectancy":73.85,"area":120538.0,"wb_year":"UN 2023-2025 estimates","gdp_per_capita_year":"2023","internet_pct_year":None,"inflation_year":None,"unemployment_year":None,"life_expectancy_year":"2025","population_year":"2025","area_year":"2023","updated_at":now,"wb_checked_at":now}
        if conn.execute("SELECT 1 FROM country_facts WHERE slug=?",(SLUG,)).fetchone():
            assignments=", ".join(f"{key}=?" for key in facts); conn.execute(f"UPDATE country_facts SET {assignments} WHERE slug=?",(*facts.values(),SLUG))
        else:
            values={"slug":SLUG,**facts}; conn.execute(f"INSERT INTO country_facts ({', '.join(values)}) VALUES ({', '.join('?' for _ in values)})",tuple(values.values()))
        conn.commit()
    print("North Korea destination and facts are up to date.")
if __name__ == "__main__": main()
