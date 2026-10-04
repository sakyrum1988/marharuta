import sqlite3, re
c = sqlite3.connect(r"D:\python-sas\content.db")
c.row_factory = sqlite3.Row

en = c.execute("SELECT content FROM posts WHERE slug=? AND lang=?",
               ("best-countries-in-asia-for-expats-2026", "en")).fetchone()
if en:
    print("EN has /ru/blog/ link:", "/ru/blog/" in en["content"])
    print("EN has luchshie:", "luchshie" in en["content"])

ru = c.execute("SELECT content FROM posts WHERE slug=? AND lang=?",
               ("luchshie-strany-azii-dlya-ekspatov-2026", "ru")).fetchone()
if ru:
    links = re.findall(r'href="/blog/([^"]+)"', ru["content"])
    print("RU /blog/ links:", links[:5])
    print("RU has /best-countries:", "/best-countries" in ru["content"])

# Check all posts that might have wrong cross-links
rows = c.execute(
    "SELECT slug, lang FROM posts WHERE content LIKE ? OR content LIKE ?",
    ("%/ru/blog/best-countries-in-asia%", "%/blog/luchshie%")
).fetchall()
print("Posts with broken cross-links:", [(r["slug"], r["lang"]) for r in rows])
c.close()
