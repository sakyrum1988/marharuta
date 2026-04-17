from __future__ import annotations

import json
import re
import sys
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import app  # noqa: E402


BAD_ENCODING_MARKERS = ("????", "Рџ", "Р“", "РЎ", "вЂ", "в†", "в”", "�")


def schema_types(html: str) -> list[str]:
    types: list[str] = []
    for raw in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, flags=re.S):
        data = json.loads(raw)
        if isinstance(data, list):
            types.extend(item.get("@type", "") for item in data if isinstance(item, dict))
        elif isinstance(data, dict):
            types.append(data.get("@type", ""))
    return [item for item in types if item]


def local_path(path: str) -> str:
    if path.startswith(app.SITE_URL):
        return path.removeprefix(app.SITE_URL) or "/"
    return path


def audit() -> int:
    client = app.app.test_client()
    failures: list[str] = []
    rows: list[tuple[str, int, int, int, list[str]]] = []

    for path, _changefreq in app.sitemap_paths():
        url_path = local_path(path)
        response = client.get(url_path)
        body = response.data.decode("utf-8", "ignore")
        canonical = re.search(r'<link rel="canonical" href="([^"]+)"', body)
        description = re.search(r'<meta name="description" content="([^"]*)"', body)
        alternates = re.findall(r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)"', body)
        h1_count = body.count("<h1")
        h2_count = body.count("<h2")
        types = schema_types(body)
        rows.append((url_path, h1_count, h2_count, body.count("<a "), types))

        if response.status_code != 200:
            failures.append(f"{url_path}: status {response.status_code}")
        if not canonical:
            failures.append(f"{url_path}: missing canonical")
        elif canonical.group(1).count("https://") > 1:
            failures.append(f"{url_path}: broken canonical {canonical.group(1)}")
        if not description or len(unescape(description.group(1)).strip()) < 70:
            failures.append(f"{url_path}: weak meta description")
        if h1_count != 1:
            failures.append(f"{url_path}: h1 count {h1_count}")
        if any(marker in body for marker in BAD_ENCODING_MARKERS):
            failures.append(f"{url_path}: encoding marker found")
        if (
            url_path.startswith("/blog/")
            and url_path != "/blog/"
            and "/page/" not in url_path
            and "?" not in url_path
            and "BlogPosting" not in types
        ):
            failures.append(f"{url_path}: missing BlogPosting schema")
        if (
            url_path.startswith("/ru/blog/")
            and url_path != "/ru/blog/"
            and "/page/" not in url_path
            and "?" not in url_path
            and "BlogPosting" not in types
        ):
            failures.append(f"{url_path}: missing BlogPosting schema")
        if url_path.startswith(("/blog/", "/ru/blog/")) and alternates:
            langs = {lang for lang, _href in alternates}
            if "x-default" not in langs:
                failures.append(f"{url_path}: missing x-default hreflang")

    print(f"Checked URLs: {len(rows)}")
    print("Top sample:")
    for path, h1, h2, links, types in rows[:12]:
        print(f"- {path}: h1={h1} h2={h2} links={links} schema={','.join(types)}")

    if failures:
        print("\nFailures:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("\nSEO audit passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(audit())
