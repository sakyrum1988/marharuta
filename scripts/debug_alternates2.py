import sqlite3
c = sqlite3.connect(r"D:\python-sas\content.db")
c.row_factory = sqlite3.Row

slug = "luchshie-strany-azii-dlya-ekspatov-2026"
pattern1 = f'%/ru/blog/{slug}/%'
pattern2 = f'%ru/blog/{slug}/%'
print(f"P1: {pattern1}")
print(f"P2: {pattern2}")

r = c.execute(
    "SELECT slug FROM posts WHERE lang = 'en' AND (content LIKE ? OR content LIKE ?)",
    (pattern1, pattern2)
).fetchone()
print("Found:", r["slug"] if r else "NONE")

# Manual check
en = c.execute("SELECT content FROM posts WHERE slug=? AND lang=?",
               ("best-countries-in-asia-for-expats-2026","en")).fetchone()
if en:
    needle = f'/ru/blog/{slug}/'
    print(f"Manual check: '{needle}' in content: {needle in en['content']}")
    print(f"Content snippet around luchshie:", en["content"][en["content"].find("luchshie")-10:en["content"].find("luchshie")+60])
c.close()
