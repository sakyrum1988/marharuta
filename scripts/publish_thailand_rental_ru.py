"""Insert the reviewed Russian rental article; never overwrite another post.

Usage: python scripts/publish_thailand_rental_ru.py
Re-running is a no-op only when the stored article is identical.
"""
from contextlib import closing
import json
from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "content/posts/arenda-kvartiry-v-tailande-ru.json"


def article():
    item = json.loads(SOURCE.read_text(encoding="utf-8"))
    item["content"] = (SOURCE.parent / item["content_file"]).read_text(encoding="utf-8").strip()
    item["link"] = f"/ru/blog/{item['slug']}/"
    # The current DB uses title/excerpt for these SEO fields.
    if item["seo_title"] != item["title"] or item["meta_description"] != item["excerpt"]:
        raise ValueError("Separate SEO overrides need a schema migration; do not silently discard them.")
    if any(marker in item["content"].lower() for marker in ("<h1", "<script", "<style")):
        raise ValueError("Article body must not contain a duplicate hero or executable markup.")
    return item


def publish(db_path):
    item = article()
    columns = ("slug", "title", "content", "excerpt", "date", "lang", "link")
    values = tuple(item[key] for key in columns)
    with closing(sqlite3.connect(db_path)) as connection, connection:
        existing = connection.execute(
            "SELECT slug,title,content,excerpt,date,lang,link FROM posts WHERE slug=? AND lang=?",
            (item["slug"], item["lang"]),
        ).fetchall()
        if existing:
            if existing != [values]:
                raise RuntimeError("Existing post differs; refusing to overwrite it.")
            return False
        connection.execute(
            "INSERT INTO posts (slug,title,content,excerpt,date,lang,link) VALUES (?,?,?,?,?,?,?)",
            values,
        )
    return True


if __name__ == "__main__":
    changed = publish(ROOT / "content.db")
    print("Article inserted." if changed else "Article already matches; no changes.")
