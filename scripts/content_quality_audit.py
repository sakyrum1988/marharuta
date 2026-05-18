from __future__ import annotations

import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import app as site_app  # noqa: E402


ARTICLE_PREFIXES = (
    "/blog/",
    "/ru/blog/",
    "/guides/",
    "/ru/guides/",
    "/compare/",
    "/ru/compare/",
    "/countries/",
    "/ru/countries/",
)

ARTICLE_PATHS = {
    "/cost-of-living-asia/",
    "/ru/cost-of-living-asia/",
    "/best-countries-in-asia-to-move/",
    "/ru/best-countries-in-asia-to-move/",
    "/cheapest-countries-in-asia/",
    "/ru/cheapest-countries-in-asia/",
    "/digital-nomad-visas-asia/",
    "/ru/digital-nomad-visas-asia/",
    "/retire-in-asia/",
    "/ru/retire-in-asia/",
}

SKIP_SOURCE_PANEL = {
    "/blog/",
    "/ru/blog/",
}

BROKEN_TEXT_MARKERS = (
    "????",
    "????????",
    "РЎ",
    "Рџ",
    "Ð",
    "Ñ",
)


def visible_words(markup: str) -> int:
    text = re.sub(r"<script.*?</script>", " ", markup, flags=re.S | re.I)
    text = re.sub(r"<style.*?</style>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(re.sub(r"\s+", " ", text)).strip()
    return len(text.split())


def is_article_path(path: str) -> bool:
    if "/page/" in path:
        return False
    return path.startswith(ARTICLE_PREFIXES) or path in ARTICLE_PATHS


def main() -> int:
    client = site_app.app.test_client()
    failures: list[str] = []
    checked = 0

    for path, _changefreq in site_app.sitemap_paths():
        if not is_article_path(path):
            continue
        response = client.get(path)
        body = response.data.decode("utf-8", "ignore")
        checked += 1
        words = visible_words(body)
        source_panels = body.count('class="rta-source-panel"')
        h1_count = body.count("<h1")
        has_title = bool(re.search(r"<title>[^<]{20,}</title>", body, flags=re.I))
        has_description = bool(re.search(r'<meta\s+name="description"\s+content="[^"]{80,}"', body, flags=re.I))
        has_canonical = bool(re.search(r'<link\s+rel="canonical"\s+href="https://www\.marharuta\.online/[^"]+"', body, flags=re.I))

        if response.status_code != 200:
            failures.append(f"{path}: status {response.status_code}")
        if h1_count != 1:
            failures.append(f"{path}: h1 count {h1_count}")
        if path not in SKIP_SOURCE_PANEL and source_panels < 1:
            failures.append(f"{path}: missing visible source panel")
        if path not in SKIP_SOURCE_PANEL and words < 1200:
            failures.append(f"{path}: thin rendered content ({words} words)")
        if any(marker in body for marker in BROKEN_TEXT_MARKERS):
            failures.append(f"{path}: broken encoding or placeholder markers found")
        if not has_title:
            failures.append(f"{path}: missing or weak title tag")
        if not has_description:
            failures.append(f"{path}: missing or weak meta description")
        if not has_canonical:
            failures.append(f"{path}: missing canonical URL")

    print(f"Checked article-like URLs: {checked}")
    if failures:
        print("Failures:")
        for item in failures:
            print(f"- {item}")
        return 1
    print("Content quality audit passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
