from __future__ import annotations

import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import app as site_app  # noqa: E402


GLOBAL_FORBIDDEN = (
    "YMYL",
    "Start Here",
    "Read more",
    "Quick Verdict",
    "Final Verdict",
    "Quick Comparison",
    "Retirement Planning Is Different",
    "A planning hub",
    "This section is",
    "Start with the legal",
    "Move To Asia In 2026",
    "Country Comparison Tool",
    "Built for Real Relocation Decisions",
    "Select two countries",
    "Compare costs",
    "The mistake is",
    "DTV is built",
    "Confirmed Facts From",
    "The key Japan question",
    "The primary appeal is",
    "All budgets below represent",
    "The USD is the de facto currency",
    "Find the right visa",
    "Get an instant personalised",
    "The best new pages here",
    "lifestyle",
    "expat-",
    "nomad-сред",
    "long-stay",
    "long stay",
    "remote work",
    "remote income",
    "premium stay",
    "high earners",
    "founders",
    "low-barrier",
    "With a cost of living",
    "offers a range of visa paths",
    "English widely spoken",
    "Humidity year-round",
    "Traffic in KL",
    "Limited nightlife",
    "World-Famous",
    "Whether you",
    "to live in",
    "Select your destination",
    "retirement-style",
    "Образ жизни-based",
    "Moving to Asia is one of the biggest",
)

COUNTRY_FORBIDDEN = (
    "Best Cities",
    "Best Visa",
    "Time Zone",
    "Generally safe",
    "Ready to Move",
    "Very low cost of living",
    "Beach lifestyle",
    "Urban hub",
    "world-class infrastructure",
    "Pros ",
    " Cons ",
)


def visible_text(markup: str) -> str:
    text = re.sub(r'<section[^>]+class=["\'][^"\']*rta-source-panel[^"\']*["\'][^>]*>.*?</section>', " ", markup, flags=re.S | re.I)
    text = re.sub(r"<script.*?</script>|<style.*?</style>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    return html.unescape(re.sub(r"\s+", " ", text)).strip()


def main() -> int:
    client = site_app.app.test_client()
    failures: list[str] = []

    paths = [path for path, _changefreq in site_app.sitemap_paths()]
    paths.extend(
        f"/ru/countries/{row['slug']}/"
        for row in site_app.many("SELECT slug FROM pages WHERE parent = 'countries'")
    )
    paths = sorted(set(paths))

    for path in paths:
        if not path.startswith("/ru/") or "/page/" in path:
            continue
        response = client.get(path)
        body = response.data.decode("utf-8", "ignore")
        text = visible_text(body)
        forbidden = list(GLOBAL_FORBIDDEN)
        if path.startswith("/ru/countries/"):
            forbidden.extend(COUNTRY_FORBIDDEN)
        hits = [phrase for phrase in forbidden if phrase in text]
        if hits:
            failures.append(f"{path}: {', '.join(hits[:8])}")

    if failures:
        print("RU localization failures:")
        for item in failures:
            print(f"- {item}")
        return 1
    print("RU localization audit passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
