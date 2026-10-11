"""Add or refresh the Yemen destination without touching other country rows."""
from __future__ import annotations
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; DB_PATH=ROOT/"content.db"; SLUG="move-to-yemen"
def main():
 now=datetime.now(timezone.utc).isoformat()
 with sqlite3.connect(DB_PATH) as conn:
  page={"title":"Moving to Yemen in 2026: Visas, Work, Costs and Residence","content":"<p>Yemen relocation guide. The rendered country page is generated from verified bilingual country data in app.py.</p>","parent":"countries","link":"/countries/move-to-yemen/"}
  if conn.execute("SELECT 1 FROM pages WHERE slug=?",(SLUG,)).fetchone(): conn.execute("UPDATE pages SET title=?,content=?,parent=?,link=? WHERE slug=?",(page["title"],page["content"],page["parent"],page["link"],SLUG))
  else: conn.execute("INSERT INTO pages (slug,title,content,parent,link) VALUES (?,?,?,?,?)",(SLUG,page["title"],page["content"],page["parent"],page["link"]))
  facts={"iso2":"YE","name":"Yemen","capital":"Sana'a","currency_code":"YER","currency_name":"Yemeni rial","languages":"Arabic","population":41773878,"flag_svg":"https://flagcdn.com/ye.svg","timezone":"UTC+3","region":"Western Asia","gdp_per_capita":633.887,"internet_pct":17.0,"inflation":8.1,"unemployment":17.3,"life_expectancy":69.439,"area":527970.0,"wb_year":"2014–2025","gdp_per_capita_year":"2018","internet_pct_year":"2019","inflation_year":"2014","unemployment_year":"2025","life_expectancy_year":"2024","population_year":"2025","area_year":"2024","updated_at":now,"wb_checked_at":now}
  if conn.execute("SELECT 1 FROM country_facts WHERE slug=?",(SLUG,)).fetchone():
   assignments=", ".join(f"{k}=?" for k in facts); conn.execute(f"UPDATE country_facts SET {assignments} WHERE slug=?",(*facts.values(),SLUG))
  else:
   values={"slug":SLUG,**facts}; conn.execute(f"INSERT INTO country_facts ({', '.join(values)}) VALUES ({', '.join('?' for _ in values)})",tuple(values.values()))
  conn.commit()
 print("Yemen destination and facts are up to date.")
if __name__=="__main__": main()
