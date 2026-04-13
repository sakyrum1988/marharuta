from __future__ import annotations

import re
import sqlite3
from pathlib import Path

from flask import Flask, abort, render_template, request

APP_DIR = Path(__file__).resolve().parent
DB_PATH = APP_DIR / "content.db"

app = Flask(__name__)

SITE_NAME = "Relocate to Asia"
SITE_URL = "http://127.0.0.1:5000"


@app.before_request
def redirect_to_www():
    """Redirect marharuta.online → www.marharuta.online (301)."""
    host = request.host.split(":")[0]  # strip port if any
    if host == "marharuta.online":
        url = request.url.replace("://marharuta.online", "://www.marharuta.online", 1)
        from flask import redirect
        return redirect(url, 301)
DEFAULT_AUTHOR = "Relocate to Asia"
DEFAULT_DESCRIPTION = (
    "Relocate to Asia helps expats compare countries, cities, visas and real-world "
    "moving costs across Asia."
)


def strip_html(value: str | None) -> str:
    if not value:
        return ""
    text = re.sub(r"<style\b[^>]*>.*?</style>", " ", value, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<script\b[^>]*>.*?</script>", " ", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def trim_text(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    trimmed = value[: limit - 1].rsplit(" ", 1)[0].strip()
    return f"{trimmed}..."


def seo_payload(
    *,
    title: str,
    description: str = "",
    author: str = DEFAULT_AUTHOR,
    lang: str = "en",
) -> dict[str, str]:
    clean_title = strip_html(title) or SITE_NAME
    description = strip_html(description) or DEFAULT_DESCRIPTION
    short_title = trim_text(clean_title, 52)
    return {
        "page_title": f"{short_title} | {SITE_NAME}" if short_title != SITE_NAME else SITE_NAME,
        "meta_title": clean_title,
        "meta_description": trim_text(description, 160),
        "meta_keywords": ", ".join(
            [
                clean_title,
                "Asia relocation",
                "expat visas",
                "cost of living Asia",
                "move to Asia",
            ]
        ),
        "canonical_url": f"{SITE_URL}{request.path}",
        "meta_robots": "index,follow,max-image-preview:large",
        "meta_author": author,
        "meta_publisher": SITE_NAME,
        "html_lang": lang,
    }

def _flag_emojis_to_img(text: str) -> str:
    """Replace flag emoji pairs (regional indicator chars) with flagcdn.com <img> tags."""
    result: list[str] = []
    i = 0
    while i < len(text):
        cp = ord(text[i])
        if 0x1F1E6 <= cp <= 0x1F1FF and i + 1 < len(text):
            cp2 = ord(text[i + 1])
            if 0x1F1E6 <= cp2 <= 0x1F1FF:
                code = (
                    chr(cp  - 0x1F1E6 + ord('a'))
                    + chr(cp2 - 0x1F1E6 + ord('a'))
                )
                result.append(
                    f'<img src="https://flagcdn.com/w40/{code}.png"'
                    f' width="28" height="20" alt="{code.upper()}"'
                    f' style="vertical-align:middle;border-radius:2px;margin:0 2px">'
                )
                i += 2
                continue
        result.append(text[i])
        i += 1
    return "".join(result)


@app.template_filter("wp_clean")
def wp_clean(content: str | None) -> str:
    if not content:
        return ""

    cleaned = content
    fixes = [
        (r"<p>\s*(<!--.*?-->)\s*</p>", r"\1"),
        (r"(<a\b[^>]*>)\s*</p>", r"\1"),
        (r"<p>\s*(</a>)\s*(?:<br\s*/?>)?", r"\1"),
        (r"<p>\s*(<span\b[^>]*>.*?</span>)\s*</p>", r"\1"),
        (r"(<span\b[^>]*>.*?</span>)\s*</p>", r"\1"),
        (r"<p>\s*(<script\b.*?</script>)\s*</p>", r"\1"),
    ]
    for pattern, replacement in fixes:
        cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE | re.DOTALL)

    cleaned = _flag_emojis_to_img(cleaned)
    return cleaned



# ── DB helpers ────────────────────────────────────────────────────────────────

def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def one(sql: str, args: tuple = ()) -> sqlite3.Row | None:
    with _conn() as c:
        return c.execute(sql, args).fetchone()


def many(sql: str, args: tuple = ()) -> list[sqlite3.Row]:
    with _conn() as c:
        return c.execute(sql, args).fetchall()


def page_or_404(slug: str, parent: str | None = None) -> sqlite3.Row:
    if parent is None:
        row = one("SELECT * FROM pages WHERE slug = ?", (slug,))
    else:
        row = one("SELECT * FROM pages WHERE slug = ? AND parent = ?", (slug, parent))
    if not row:
        abort(404)
    return row


# ── Routes ────────────────────────────────────────────────────────────────────

def render_page_row(row: sqlite3.Row, **kwargs):
    seo = seo_payload(
        title=row["title"],
        description=row["excerpt"] if "excerpt" in row.keys() else row["content"],
    )
    return render_template("page.html", page=row, seo=seo, **kwargs)


def render_post_row(row: sqlite3.Row, *, lang: str):
    seo = seo_payload(
        title=row["title"],
        description=row["excerpt"] or row["content"],
        lang=lang,
    )
    return render_template("post.html", post=row, seo=seo, lang_code=lang)


@app.route("/")
def home():
    row = page_or_404("__home__")
    return render_page_row(row, breadcrumbs=[])


@app.route("/countries/")
def countries_index():
    row = page_or_404("countries")
    return render_page_row(row, breadcrumbs=[])


@app.route("/countries/<slug>/")
def country(slug: str):
    row = page_or_404(slug, parent="countries")
    facts = one("SELECT * FROM country_facts WHERE slug = ?", (slug,))
    seo = seo_payload(
        title=row["title"],
        description=row["excerpt"] if "excerpt" in row.keys() else row["content"],
    )
    return render_template(
        "country.html",
        page=row,
        facts=facts,
        seo=seo,
        breadcrumbs=[("Countries", "/countries/")],
    )


@app.route("/tools/")
def tools_index():
    row = page_or_404("tools")
    return render_page_row(row, breadcrumbs=[])


@app.route("/tools/<slug>/")
def tool(slug: str):
    row = page_or_404(slug, parent="tools")
    return render_page_row(row,
                           breadcrumbs=[("Tools", "/tools/")])


@app.route("/compare/")
def compare_index():
    row = page_or_404("compare")
    return render_page_row(row, breadcrumbs=[])


@app.route("/compare/<slug>/")
def compare(slug: str):
    row = page_or_404(slug, parent="compare")
    return render_page_row(row,
                           breadcrumbs=[("Compare", "/compare/")])


@app.route("/compare-cities/")
def compare_cities():
    row = page_or_404("compare-cities")
    return render_page_row(row, breadcrumbs=[],
                           extra_js="compare_cities")


@app.route("/visas/")
def visas():
    row = page_or_404("visas")
    return render_page_row(row, breadcrumbs=[])


@app.route("/best-countries-in-asia-to-move/")
def best_countries():
    row = page_or_404("best-countries-in-asia-to-move")
    return render_page_row(row, breadcrumbs=[])


@app.route("/cheapest-countries-in-asia/")
def cheapest_countries():
    row = page_or_404("cheapest-countries-in-asia")
    return render_page_row(row, breadcrumbs=[])


@app.route("/blog/")
def blog():
    posts = many(
        "SELECT id, slug, title, excerpt, date FROM posts"
        " WHERE lang = 'en' ORDER BY date DESC"
    )
    return render_template("blog.html", posts=posts, seo=seo_payload(title="Asia Relocation Blog", description="Guides, comparisons and practical relocation advice for expats moving across Asia."))


@app.route("/blog/<slug>/")
def post(slug: str):
    row = one("SELECT * FROM posts WHERE slug = ? AND lang = 'en'", (slug,))
    if not row:
        abort(404)
    return render_post_row(row, lang="en")


@app.route("/ru/blog/<slug>/")
def post_ru(slug: str):
    row = one("SELECT * FROM posts WHERE slug = ? AND lang = 'ru'", (slug,))
    if not row:
        abort(404)
    return render_post_row(row, lang="ru")


@app.errorhandler(404)
def not_found(error):
    seo = seo_payload(
        title="Page Not Found",
        description="The page could not be found. Use Relocate to Asia navigation to browse countries, visas, comparisons, tools and relocation guides.",
    )
    seo["meta_robots"] = "noindex,follow"
    return render_template("404.html", seo=seo), 404


if __name__ == "__main__":
    app.run(debug=True)
