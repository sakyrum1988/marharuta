import sqlite3
c = sqlite3.connect(r"D:\python-sas\content.db")
c.row_factory = sqlite3.Row
r = c.execute("SELECT content FROM pages WHERE slug=? AND parent=?",
              ("ru-thailand-vs-malaysia", "ru-compare")).fetchone()
html = r["content"]
# Find first 200 chars after style block (the actual HTML structure)
style_end = html.find("</style>") + 8
outer = html[style_end:style_end+400]
open("C:/Users/user/Desktop/outer_debug.txt", "w", encoding="utf-8").write(outer)
# Count all closing divs before first <section class="rucmp-section">
first_section = html.find('<section class="rucmp-section"')
header_region = html[style_end:first_section]
open("C:/Users/user/Desktop/header_region.txt", "w", encoding="utf-8").write(header_region)
print("header_region length:", len(header_region))
print("done")
c.close()
