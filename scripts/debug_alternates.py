import sqlite3
c = sqlite3.connect(r"D:\python-sas\content.db")
c.row_factory = sqlite3.Row

slug = "luchshie-strany-azii-dlya-ekspatov-2026"
ru_link = f'/ru/blog/{slug}/'
pattern = f'%href="{ru_link}"%'
print(f"Searching for: {pattern}")

r = c.execute("SELECT slug FROM posts WHERE lang = 'en' AND content LIKE ?", (pattern,)).fetchone()
print("Found:", r["slug"] if r else "NONE")

# Check if EN post has the link with or without quotes
en = c.execute("SELECT content FROM posts WHERE slug=? AND lang=?",
               ("best-countries-in-asia-for-expats-2026","en")).fetchone()
if en:
    # Find the actual link pattern used
    import re
    links = re.findall(r'href=["\']([^"\']*luchshie[^"\']*)["\']', en["content"])
    print("Actual links with luchshie:", links)
c.close()
