"""Add or refresh the Syria destination without touching other country rows."""
from __future__ import annotations
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; DB_PATH=ROOT/"content.db"; SLUG="move-to-syria"
def main():
 now=datetime.now(timezone.utc).isoformat()
 with sqlite3.connect(DB_PATH) as conn:
  page={"title":"Moving to Syria in 2026: Visas, Work, Costs and Residence","content":"<p>Syria relocation guide. The rendered country page is generated from verified bilingual country data in app.py.</p>","parent":"countries","link":"/countries/move-to-syria/"}
  if conn.execute("SELECT 1 FROM pages WHERE slug=?",(SLUG,)).fetchone(): conn.execute("UPDATE pages SET title=?,content=?,parent=?,link=? WHERE slug=?",(page["title"],page["content"],page["parent"],page["link"],SLUG))
  else: conn.execute("INSERT INTO pages (slug,title,content,parent,link) VALUES (?,?,?,?,?)",(SLUG,page["title"],page["content"],page["parent"],page["link"]))
  facts={"iso2":"SY","name":"Syrian Arab Republic","capital":"Damascus","currency_code":"SYP","currency_name":"Syrian pound","languages":"Arabic","population":25620427,"flag_svg":"https://flagcdn.com/sy.svg","timezone":"UTC+3","region":"Western Asia","gdp_per_capita":1056.783,"internet_pct":34.0,"inflation":11.5,"unemployment":13.6,"life_expectancy":72.56,"area":185180.0,"wb_year":"2018–2025","gdp_per_capita_year":"2022","internet_pct_year":"2018","inflation_year":"2025","unemployment_year":"2025","life_expectancy_year":"2024","population_year":"2025","area_year":"2024","updated_at":now,"wb_checked_at":now}
  if conn.execute("SELECT 1 FROM country_facts WHERE slug=?",(SLUG,)).fetchone():
   assignments=", ".join(f"{k}=?" for k in facts); conn.execute(f"UPDATE country_facts SET {assignments} WHERE slug=?",(*facts.values(),SLUG))
  else:
   values={"slug":SLUG,**facts}; conn.execute(f"INSERT INTO country_facts ({', '.join(values)}) VALUES ({', '.join('?' for _ in values)})",tuple(values.values()))
  conn.commit()
 print("Syria destination and facts are up to date.")
if __name__=="__main__": main()
