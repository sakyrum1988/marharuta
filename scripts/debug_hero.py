import sqlite3
c = sqlite3.connect(r"D:\python-sas\content.db")
c.row_factory = sqlite3.Row
r = c.execute("SELECT content FROM pages WHERE slug=? AND parent=?",
              ("ru-thailand-vs-malaysia", "ru-compare")).fetchone()
html = r["content"]
start = html.find('<div class="rucmp-hero">')
print("Hero start:", start)
# write to file instead
open("C:/Users/user/Desktop/hero_debug.txt", "w", encoding="utf-8").write(html[start:start+1000])
c.close()
