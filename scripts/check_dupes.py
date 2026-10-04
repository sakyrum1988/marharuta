import sqlite3
c = sqlite3.connect(r"D:\python-sas\content.db")
c.row_factory = sqlite3.Row
r = c.execute("SELECT content FROM pages WHERE slug=? AND parent=?",
              ("ru-thailand-vs-malaysia", "ru-compare")).fetchone()
h = r["content"]
print("flags divs:", h.count('<div class="rucmp-flags">'))
print("toc divs:  ", h.count('<div class="rucmp-toc">'))
print("all-links: ", h.count("rucmp-all-link"))
print("style tags:", h.count("<style>"))
c.close()
