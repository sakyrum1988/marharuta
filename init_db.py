"""
Imports all content from marharuta.online WordPress site into content.db.
Run once before deploying, or as part of Render build command.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import requests

BASE_URL = "https://www.marharuta.online"
API = f"{BASE_URL}/wp-json/wp/v2"
DB_PATH = Path(__file__).resolve().parent / "content.db"


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS pages (
            id      INTEGER PRIMARY KEY,
            slug    TEXT NOT NULL UNIQUE,
            title   TEXT NOT NULL,
            content TEXT NOT NULL,
            parent  TEXT,
            link    TEXT
        );
        CREATE TABLE IF NOT EXISTS posts (
            id      INTEGER PRIMARY KEY,
            slug    TEXT NOT NULL,
            title   TEXT NOT NULL,
            content TEXT NOT NULL,
            excerpt TEXT,
            date    TEXT,
            lang    TEXT NOT NULL DEFAULT 'en',
            link    TEXT
        );
    """)


def parent_of(link: str, slug: str) -> str | None:
    """Derive parent category from URL structure."""
    if "/countries/move-to-" in link:
        return "countries"
    if "/tools/" in link and slug != "tools":
        return "tools"
    if "/compare/" in link and slug not in ("compare", "compare-asian-countries"):
        return "compare"
    return None


def fetch_all(endpoint: str, fields: str) -> list[dict]:
    items: list[dict] = []
    page = 1
    while True:
        r = requests.get(
            f"{API}/{endpoint}",
            params={"per_page": 100, "page": page, "_fields": fields},
            timeout=30,
        )
        if r.status_code != 200:
            break
        batch = r.json()
        if not batch:
            break
        items.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return items


def main() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        init_schema(conn)

        # ── Pages ────────────────────────────────────────────────────────────
        pages = fetch_all("pages", "id,slug,title,content,link")
        page_count = 0
        for p in pages:
            slug: str = p["slug"]
            link: str = p["link"]
            title: str = p["title"]["rendered"]
            content: str = p["content"]["rendered"]

            # Homepage detection
            if link.rstrip("/") == BASE_URL.rstrip("/"):
                slug = "__home__"
                parent = None
            else:
                parent = parent_of(link, slug)

            conn.execute(
                "INSERT OR REPLACE INTO pages (id, slug, title, content, parent, link)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (p["id"], slug, title, content, parent, link),
            )
            page_count += 1

        # ── Posts ────────────────────────────────────────────────────────────
        posts = fetch_all("posts", "id,slug,title,content,excerpt,date,link")
        post_count = 0
        for p in posts:
            slug = p["slug"]
            link = p["link"]
            lang = "ru" if "/ru/blog/" in link else "en"
            title = p["title"]["rendered"]
            content = p["content"]["rendered"]
            excerpt = p.get("excerpt", {}).get("rendered", "")
            date = p["date"]

            conn.execute(
                "INSERT OR REPLACE INTO posts"
                " (id, slug, title, content, excerpt, date, lang, link)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (p["id"], slug, title, content, excerpt, date, lang, link),
            )
            post_count += 1

        conn.commit()
        print(f"Imported {page_count} pages, {post_count} posts -> content.db")


if __name__ == "__main__":
    main()
