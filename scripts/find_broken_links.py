import sqlite3, re
c = sqlite3.connect(r"D:\python-sas\content.db")
c.row_factory = sqlite3.Row

# Find all posts/pages that link to the broken URLs
targets = [
    "best-countries-in-asia-for-expats-2026",
    "best-asian-countries-with-easy",
    "best-asian-countries-for-",
]

print("=== Posts with links to broken URLs ===")
posts = c.execute("SELECT slug, lang, content FROM posts").fetchall()
for post in posts:
    content = post["content"] or ""
    for t in targets:
        if f"/ru/blog/{t}" in content or f"/ru/guides/{t}" in content:
            print(f"  POST {post['lang']}:{post['slug']} links to /ru/*{t}")
            break

print("=== Pages with links to broken URLs ===")
pages = c.execute("SELECT slug, content FROM pages").fetchall()
for page in pages:
    content = page["content"] or ""
    for t in targets:
        if f"/ru/blog/{t}" in content or f"/ru/guides/{t}" in content:
            print(f"  PAGE {page['slug']} links to /ru/*{t}")
            break

# Also check EN post for its ru link
en = c.execute("SELECT content FROM posts WHERE slug=? AND lang=?",
               ("best-countries-in-asia-for-expats-2026","en")).fetchone()
if en:
    ru_links = re.findall(r'/ru/blog/([^"\'>\s]+)', en["content"])
    print(f"\nEN post ru-blog links: {ru_links[:5]}")

c.close()
