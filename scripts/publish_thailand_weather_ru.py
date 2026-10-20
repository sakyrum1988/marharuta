"""Publish the approved weather article without overwriting existing content.

Adds nullable SEO columns used by render_post_row; legacy posts retain their
title/excerpt fallback. Re-running is a no-op only for an identical article.
"""
from contextlib import closing
from datetime import datetime
import json
from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "content/posts/sezon-dozhdey-v-tailande-ru.json"
COLUMNS = ("slug", "title", "content", "excerpt", "date", "lang", "link",
           "seo_title", "meta_description")


def article():
    item = json.loads(SOURCE.read_text(encoding="utf-8"))
    item["content"] = (SOURCE.parent / item["content_file"]).read_text(encoding="utf-8").strip()
    item["link"] = f"/ru/blog/{item['slug']}/"
    if item["status"] != "published" or not item["date"]:
        raise ValueError("Publication metadata must be explicitly approved.")
    if any(marker in item["content"].lower() for marker in ("<h1", "<script", "<style")):
        raise ValueError("Article body must not include a hero or executable markup.")
    return item


def publish(db_path):
    item = article()
    values = tuple(item[key] for key in COLUMNS)
    with closing(sqlite3.connect(db_path)) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        existing_columns = {row[1] for row in connection.execute("PRAGMA table_info(posts)")}
        for column in ("seo_title", "meta_description"):
            if column not in existing_columns:
                connection.execute(f"ALTER TABLE posts ADD COLUMN {column} TEXT")
        existing = connection.execute(
            f"SELECT {','.join(COLUMNS)} FROM posts WHERE slug=? AND lang=?",
            (item["slug"], item["lang"]),
        ).fetchall()
        if existing:
            if existing != [values]:
                raise RuntimeError("Existing post differs; refusing to overwrite it.")
            return False
        connection.execute(
            f"INSERT INTO posts ({','.join(COLUMNS)}) VALUES ({','.join('?' for _ in COLUMNS)})",
            values,
        )
    return True


if __name__ == "__main__":
    database = ROOT / "content.db"
    backups = ROOT / ".backups"
    backups.mkdir(exist_ok=True)
    backup = backups / f"before-weather-{datetime.now().strftime('%Y%m%d-%H%M%S-%f')}.db"
    with closing(sqlite3.connect(database)) as source, closing(sqlite3.connect(backup)) as target:
        source.backup(target)
    print(f"Backup: {backup.name}")
    print("Article inserted." if publish(database) else "Article already matches; no changes.")
