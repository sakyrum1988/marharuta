"""Audit every rendered guide page in both site languages."""

from __future__ import annotations

import html
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    import sys

    sys.path.insert(0, str(ROOT))
    from app import app

    with sqlite3.connect(ROOT / "content.db") as connection:
        slugs = [
            row[0]
            for row in connection.execute(
                "SELECT slug FROM pages WHERE parent = 'guides' ORDER BY slug"
            )
        ]

    print("slug|lang|status|h1|visible_h1|wrapper|hero|sources|words|h2|tables|faq")
    client = app.test_client()
    for slug in slugs:
        for lang, path in (
            ("en", f"/guides/{slug}/"),
            ("ru", f"/ru/guides/{slug}/"),
        ):
            response = client.get(path)
            markup = response.get_data(as_text=True)
            h1s = re.findall(r"<h1\b([^>]*)>", markup, flags=re.I)
            visible_h1s = [attrs for attrs in h1s if "sr-only" not in attrs]
            wrapper_match = re.search(
                r'<div\s+class="([^"]*\brta-content\b[^"]*)"', markup, flags=re.I
            )
            classes = wrapper_match.group(1).split() if wrapper_match else []
            hero = re.search(
                r'class="[^"]*\b(?:guide-hero|ep-hero|article-hero|rta-post-header|rta-guides-hero)\b',
                markup,
                flags=re.I,
            )
            text = html.unescape(re.sub(r"<[^>]+>", " ", markup))
            text = re.sub(r"\s+", " ", text).strip()
            values = (
                slug,
                lang,
                response.status_code,
                len(h1s),
                len(visible_h1s),
                "rta-guide-detail-page" in classes,
                bool(hero),
                "rta-source-panel" in markup,
                len(text.split()),
                len(re.findall(r"<h2\b", markup, flags=re.I)),
                len(re.findall(r"<table\b", markup, flags=re.I)),
                len(re.findall(r'class="[^"]*\b(?:faq-item|rta-depth-faq-item)\b', markup, flags=re.I)),
            )
            print("|".join(str(value) for value in values))


if __name__ == "__main__":
    main()
