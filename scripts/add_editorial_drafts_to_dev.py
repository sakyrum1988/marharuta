"""Add the reviewed editorial drafts to the local development database.

This script is intentionally local-only: it writes ``content.db``, creates a
recoverable backup first, and refuses to overwrite an existing post that has
different content.
"""
import argparse
from contextlib import closing
from datetime import datetime
import json
from pathlib import Path
import shutil
import sqlite3


ROOT = Path(__file__).resolve().parents[1]
DRAFTS = ROOT / "content" / "drafts"
REVIEWS = ROOT / "docs" / "content-reviews"
DATABASE = ROOT / "content.db"

SOURCES = (
    "traditional-kyoto-culture-guide-en.json",
    "traditsionnyy-kioto-kultura-ru.json",
    "what-is-an-expat-en.json",
    "kto-takoy-ekspat-ru.json",
    "best-places-to-retire-in-the-world-en.json",
    "luchshie-strany-dlya-pensionerov-ru.json",
    "cost-of-living-in-thailand-en.json",
    "stoimost-zhizni-v-tailande-ru.json",
    "cheapest-places-to-live-abroad-en.json",
    "samye-deshevye-strany-dlya-zhizni-ru.json",
)

COLUMNS = (
    "slug",
    "title",
    "content",
    "excerpt",
    "date",
    "lang",
    "link",
    "seo_title",
    "meta_description",
)


def load_article(filename: str) -> dict[str, str]:
    source = DRAFTS / filename
    item = json.loads(source.read_text(encoding="utf-8"))
    if item.get("status") != "draft":
        raise ValueError(f"{filename}: expected reviewed draft status")
    if item.get("lang") not in {"en", "ru"}:
        raise ValueError(f"{filename}: unsupported language")
    review = REVIEWS / f"{item['slug']}-{item['lang']}.md"
    if not review.exists():
        raise FileNotFoundError(f"Missing editorial review: {review.name}")

    content = (DRAFTS / item["content_file"]).read_text(encoding="utf-8").strip()
    lowered = content.lower()
    if any(marker in lowered for marker in ("<h1", "<script", "<style")):
        raise ValueError(f"{filename}: article body contains forbidden markup")

    item["content"] = content
    item["date"] = item.get("date") or item["research_date"]
    prefix = "/ru/blog" if item["lang"] == "ru" else "/blog"
    item["link"] = f"{prefix}/{item['slug']}/"
    return item


def add_to_dev(database: Path = DATABASE, *, refresh: bool = False) -> tuple[list[str], list[str], list[str]]:
    articles = [load_article(filename) for filename in SOURCES]
    inserted: list[str] = []
    unchanged: list[str] = []
    updated: list[str] = []

    with closing(sqlite3.connect(database)) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        available = {row[1] for row in connection.execute("PRAGMA table_info(posts)")}
        missing = set(COLUMNS) - available
        if missing:
            raise RuntimeError(f"posts table is missing columns: {sorted(missing)}")

        for item in articles:
            values = tuple(item[column] for column in COLUMNS)
            existing = connection.execute(
                f"SELECT {','.join(COLUMNS)} FROM posts WHERE slug=? AND lang=?",
                (item["slug"], item["lang"]),
            ).fetchone()
            identity = f"{item['lang']}:{item['slug']}"
            if existing:
                if tuple(existing) != values and not refresh:
                    raise RuntimeError(f"Refusing to overwrite different post: {identity}")
                if tuple(existing) != values:
                    assignments = ",".join(f"{column}=?" for column in COLUMNS)
                    connection.execute(
                        f"UPDATE posts SET {assignments} WHERE slug=? AND lang=?",
                        (*values, item["slug"], item["lang"]),
                    )
                    updated.append(identity)
                    continue
                unchanged.append(identity)
                continue
            connection.execute(
                f"INSERT INTO posts ({','.join(COLUMNS)}) "
                f"VALUES ({','.join('?' for _ in COLUMNS)})",
                values,
            )
            inserted.append(identity)
    return inserted, unchanged, updated


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Refresh only the allow-listed dev posts from their reviewed draft files.",
    )
    args = parser.parse_args()
    backups = ROOT / ".backups"
    backups.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    backup = backups / f"before-editorial-drafts-dev-{stamp}.db"
    shutil.copy2(DATABASE, backup)
    inserted, unchanged, updated = add_to_dev(refresh=args.refresh)
    print(f"Backup: {backup.name}")
    print(f"Inserted: {len(inserted)}")
    for identity in inserted:
        print(f"+ {identity}")
    print(f"Updated: {len(updated)}")
    for identity in updated:
        print(f"~ {identity}")
    for identity in unchanged:
        print(f"= {identity}")


if __name__ == "__main__":
    main()
