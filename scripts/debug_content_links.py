import sqlite3, re
c = sqlite3.connect(r"D:\python-sas\content.db")
c.row_factory = sqlite3.Row
r = c.execute("SELECT content FROM posts WHERE slug=? AND lang=?",
              ("luchshie-strany-azii-dlya-ekspatov-2026","ru")).fetchone()
if r:
    links = re.findall(r'href="(/blog/[^"]+)"', r["content"])
    abs_links = re.findall(r'href="(https?://[^"]*blog[^"]+)"', r["content"])
    print("Relative /blog/ links:", links)
    print("Absolute blog links:", abs_links[:5])
    print("Total content length:", len(r["content"]))
c.close()
