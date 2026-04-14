from __future__ import annotations

import re
import sqlite3
import json
from pathlib import Path

from flask import Flask, Response, abort, render_template, request

APP_DIR = Path(__file__).resolve().parent
DB_PATH = APP_DIR / "content.db"

app = Flask(__name__)

SITE_NAME = "Relocate to Asia"
SITE_URL = "https://www.marharuta.online"
DEFAULT_OG_IMAGE = "/static/img/og-default.png"


@app.before_request
def redirect_to_www():
    """Redirect marharuta.online → www.marharuta.online (301)."""
    host = request.host.split(":")[0]  # strip port if any
    if host == "marharuta.online":
        url = request.url.replace("://marharuta.online", "://www.marharuta.online", 1)
        from flask import redirect
        return redirect(url, 301)
DEFAULT_AUTHOR = "Relocate to Asia Editorial Team"
DEFAULT_DESCRIPTION = (
    "Relocate to Asia helps expats compare countries, cities, visas and real-world "
    "moving costs across Asia."
)
PAGE_SEO_DESCRIPTIONS = {
    "compare": (
        "Compare Asian countries in 2026 by cost of living, visas, safety, healthcare, "
        "climate, English level and digital nomad practicality."
    ),
    "move-to-asia": (
        "Plan a move to Asia in 2026 with country guides, visa routes, cost tools, "
        "comparison pages and practical relocation trade-offs."
    ),
    "digital-nomad-visas-asia": (
        "Compare digital nomad visas in Asia for 2026, including Japan, Taiwan, "
        "Indonesia, Thailand, South Korea and UAE remote work routes."
    ),
    "retire-in-asia": (
        "Compare retirement options in Asia for 2026, including long-stay visas, "
        "healthcare, deposits, costs and practical country trade-offs."
    ),
    "cost-of-living-asia": (
        "Compare cost of living in Asia for 2026 with budget tools, cheap country "
        "guides and relocation planning links."
    ),
    "japan-vs-taiwan": "Compare Japan vs Taiwan for expats in 2026 by visa route, cost pressure, professional fit, lifestyle and long-stay practicality.",
    "thailand-vs-vietnam": "Compare Thailand vs Vietnam for expats in 2026 by cost, visas, city life, infrastructure and practical long-stay trade-offs.",
    "malaysia-vs-vietnam": "Compare Malaysia vs Vietnam for expats in 2026 by English level, costs, visa planning, city comfort and relocation fit.",
    "singapore-vs-hong-kong": "Compare Singapore vs Hong Kong for expats in 2026 by career routes, cost pressure, talent visas, housing and regional access.",
    "uae-vs-qatar": "Compare UAE vs Qatar for expats in 2026 by entry routes, remote work options, cost profile, lifestyle and relocation fit.",
}


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
    canonical_path: str | None = None,
    alternates: list[dict[str, str]] | None = None,
    schema: list[dict] | dict | None = None,
    og_type: str = "website",
    og_image: str = DEFAULT_OG_IMAGE,
) -> dict:
    clean_title = strip_html(title) or SITE_NAME
    description = strip_html(description) or DEFAULT_DESCRIPTION
    short_title = trim_text(clean_title, 52)
    canonical_url = absolute_url(canonical_path or request.path)
    og_image_url = absolute_url(og_image) if "absolute_url" in globals() else f"{SITE_URL}{og_image}"
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
        "canonical_url": canonical_url,
        "meta_robots": "index,follow,max-image-preview:large",
        "meta_author": author,
        "meta_publisher": SITE_NAME,
        "html_lang": lang,
        "alternates": alternates or [],
        "schema_json": json.dumps(schema, ensure_ascii=False) if schema else "",
        "og_type": og_type,
        "og_image": og_image_url,
    }


def absolute_url(path: str) -> str:
    if path.startswith("http://") or path.startswith("https://"):
        return path
    if not path.startswith("/"):
        path = f"/{path}"
    return f"{SITE_URL}{path}"


def breadcrumb_schema(items: list[tuple[str, str]], current_title: str, current_path: str) -> dict:
    schema_items = [("Home", "/"), *items, (strip_html(current_title), current_path)]
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": index,
                "name": name,
                "item": absolute_url(url),
            }
            for index, (name, url) in enumerate(schema_items, start=1)
        ],
    }


def organization_schema() -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": SITE_NAME,
        "url": SITE_URL,
    }


def website_schema() -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": SITE_NAME,
        "url": SITE_URL,
        "inLanguage": ["en", "ru"],
    }


def faq_schema_from_html(content: str | None, *, lang: str) -> dict | None:
    if not content:
        return None
    items: list[tuple[str, str]] = []
    for question, answer in re.findall(
        r'<div class="faq-item">\s*<h3>(.*?)</h3>\s*<p>(.*?)</p>\s*</div>',
        content,
        flags=re.IGNORECASE | re.DOTALL,
    ):
        items.append((strip_html(question), strip_html(answer)))
    for question, answer in re.findall(
        r'<details>\s*<summary>(.*?)</summary>\s*<p>(.*?)</p>\s*</details>',
        content,
        flags=re.IGNORECASE | re.DOTALL,
    ):
        items.append((strip_html(question), strip_html(answer)))
    if not items:
        return None
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "inLanguage": lang,
        "mainEntity": [
            {
                "@type": "Question",
                "name": question,
                "acceptedAnswer": {"@type": "Answer", "text": answer},
            }
            for question, answer in items[:8]
            if question and answer
        ],
    }


def item_list_schema(name: str, links: list[dict[str, str]]) -> dict | None:
    if not links:
        return None
    return {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": name,
        "itemListElement": [
            {"@type": "ListItem", "position": index, "name": strip_html(link["title"]), "url": absolute_url(link["url"])}
            for index, link in enumerate(links, start=1)
        ],
    }


def web_application_schema(name: str, path: str, description: str) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "WebApplication",
        "name": strip_html(name),
        "url": absolute_url(path),
        "applicationCategory": "TravelApplication",
        "operatingSystem": "Web",
        "description": trim_text(strip_html(description), 200),
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
    }


def country_meta_description(row: sqlite3.Row, facts: sqlite3.Row | None) -> str:
    title = strip_html(row["title"]).replace("—", "-").replace(":", " -")
    if facts:
        details = []
        if facts["capital"]:
            details.append(f"capital {facts['capital']}")
        if facts["currency_code"]:
            details.append(f"currency {facts['currency_code']}")
        if facts["internet_pct"]:
            details.append(f"internet users {facts['internet_pct']:.1f}%")
        if details:
            return f"{title}: 2026 relocation guide with visa context, cost planning, cities and country facts including {', '.join(details)}."
    return f"{title}: 2026 relocation guide with visa context, cost planning, cities, country facts and practical trade-offs for expats."


def country_schema(row: sqlite3.Row, facts: sqlite3.Row | None, path: str) -> dict:
    name = facts["name"] if facts and facts["name"] else strip_html(row["title"])
    schema = {
        "@context": "https://schema.org",
        "@type": "Country",
        "name": name,
        "url": absolute_url(path),
    }
    if facts:
        if facts["capital"]:
            schema["containsPlace"] = {"@type": "City", "name": facts["capital"]}
        if facts["population"]:
            schema["additionalProperty"] = [
                {
                    "@type": "PropertyValue",
                    "name": "Population",
                    "value": facts["population"],
                }
            ]
        if facts["flag_svg"]:
            schema["image"] = facts["flag_svg"]
    return schema


def article_schema(row: sqlite3.Row, *, lang: str, canonical_path: str) -> dict:
    published = row["date"] or ""
    return {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": strip_html(row["title"]),
        "description": trim_text(strip_html(row["excerpt"] or row["content"]), 200),
        "datePublished": published,
        "dateModified": published,
        "author": {"@type": "Organization", "name": DEFAULT_AUTHOR},
        "publisher": {"@type": "Organization", "name": SITE_NAME, "url": SITE_URL},
        "mainEntityOfPage": absolute_url(canonical_path),
        "url": absolute_url(canonical_path),
        "inLanguage": lang,
        "image": [absolute_url(DEFAULT_OG_IMAGE)],
    }


def post_alternates(row: sqlite3.Row, *, lang: str, canonical_path: str) -> list[dict[str, str]]:
    alternates = [{"lang": lang, "url": absolute_url(canonical_path)}]
    content = row["content"] or ""
    if lang == "en":
        match = re.search(r'href="/ru/blog/([^"/]+)/"', content)
        if match:
            alternates.append({"lang": "ru", "url": absolute_url(f"/ru/blog/{match.group(1)}/")})
    elif lang == "ru":
        match = re.search(r'href="/blog/([^"/]+)/"', content)
        if match:
            alternates.append({"lang": "en", "url": absolute_url(f"/blog/{match.group(1)}/")})
    english = next((item for item in alternates if item["lang"] == "en"), alternates[0])
    alternates.append({"lang": "x-default", "url": english["url"]})
    return alternates


def post_path(row: sqlite3.Row) -> str:
    prefix = "/blog" if row["lang"] == "en" else "/ru/blog"
    return f"{prefix}/{row['slug']}/"


def related_posts(row: sqlite3.Row, *, limit: int = 3) -> list[sqlite3.Row]:
    title_words = [w.lower() for w in re.findall(r"[A-Za-zА-Яа-яЁё]{4,}", strip_html(row["title"]))]
    candidates = many(
        "SELECT id, slug, title, excerpt, date, lang FROM posts WHERE lang = ? AND id != ? ORDER BY date DESC",
        (row["lang"], row["id"]),
    )
    scored = []
    for candidate in candidates:
        haystack = f"{candidate['title']} {candidate['excerpt'] or ''}".lower()
        score = sum(1 for word in title_words if word in haystack)
        scored.append((score, candidate))
    scored.sort(key=lambda item: (item[0], item[1]["date"] or ""), reverse=True)
    return [candidate for _, candidate in scored[:limit]]


def collection_schema(title: str, description: str, path: str) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": strip_html(title),
        "description": trim_text(strip_html(description), 200),
        "url": absolute_url(path),
        "inLanguage": "ru" if path.startswith("/ru/") else "en",
    }


def post_pair_map() -> dict[str, list[dict[str, str]]]:
    rows = many("SELECT slug, lang, content FROM posts")
    path_to_alternates: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        path = post_path(row)
        alternates = post_alternates(row, lang=row["lang"], canonical_path=path)
        if len(alternates) > 2:
            path_to_alternates[path] = alternates
    return path_to_alternates

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

COUNTRY_INTERNAL_LINKS = [
    ("japan", "yaponiya", "Япони", "/countries/move-to-japan/", "Move to Japan", "Переезд в Японию"),
    ("taiwan", "Тайван", "/countries/move-to-taiwan/", "Move to Taiwan", "Переезд на Тайвань"),
    ("indonesia", "bali", "Бали", "Индонез", "/countries/move-to-bali/", "Move to Bali", "Переезд на Бали"),
    ("thailand", "tailand", "Таиланд", "/countries/move-to-thailand/", "Move to Thailand", "Переезд в Таиланд"),
    ("philippines", "Филиппин", "/countries/move-to-philippines/", "Move to Philippines", "Переезд на Филиппины"),
    ("south-korea", "korea", "Коре", "/countries/move-to-south-korea/", "Move to South Korea", "Переезд в Южную Корею"),
    ("singapore", "Сингапур", "/countries/move-to-singapore/", "Move to Singapore", "Переезд в Сингапур"),
    ("hong-kong", "Гонконг", "/countries/move-to-china/", "Move to China", "Переезд в Китай"),
    ("vietnam", "Вьетнам", "/countries/move-to-vietnam/", "Move to Vietnam", "Переезд во Вьетнам"),
    ("cambodia", "Камбодж", "/countries/move-to-cambodia/", "Move to Cambodia", "Переезд в Камбоджу"),
    ("sri-lanka", "Шри-Ланк", "/countries/move-to-sri-lanka/", "Move to Sri Lanka", "Переезд на Шри-Ланку"),
    ("india", "Инди", "/countries/move-to-india/", "Move to India", "Переезд в Индию"),
    ("qatar", "Катар", "/visas/", "Asia visa guide", "Гайд по визам Азии"),
    ("saudi", "Сауд", "/visas/", "Asia visa guide", "Гайд по визам Азии"),
    ("uae", "ОАЭ", "emirates", "/countries/move-to-uae/", "Move to UAE", "Переезд в ОАЭ"),
    ("malaysia", "Малайз", "/countries/move-to-malaysia/", "Move to Malaysia", "Переезд в Малайзию"),
]


def _link(title: str, url: str, description: str = "") -> dict[str, str]:
    return {"title": title, "url": url, "description": description}


def _dedupe_links(links: list[dict[str, str]], current_path: str = "", limit: int = 8) -> list[dict[str, str]]:
    seen: set[str] = set()
    clean: list[dict[str, str]] = []
    current_paths = {current_path}
    if current_path.startswith(SITE_URL):
        current_paths.add(current_path.removeprefix(SITE_URL))
    elif current_path.startswith("/"):
        current_paths.add(absolute_url(current_path))
    for link in links:
        url = link["url"]
        if not url or url in current_paths or url in seen:
            continue
        seen.add(url)
        clean.append(link)
        if len(clean) >= limit:
            break
    return clean


def _matched_country_links(text: str, lang: str) -> list[dict[str, str]]:
    haystack = text.lower()
    links: list[dict[str, str]] = []
    for *keys, url, en_title, ru_title in COUNTRY_INTERNAL_LINKS:
        if any(str(key).lower() in haystack for key in keys):
            links.append(_link(
                ru_title if lang == "ru" else en_title,
                url,
                (
                    "Базовая страница страны: расходы, города, визовая логика и практические компромиссы."
                    if lang == "ru"
                    else "Country hub: costs, cities, visa logic and practical trade-offs."
                ),
            ))
    return links


def internal_links_for_post(row: sqlite3.Row, *, lang: str) -> list[dict[str, str]]:
    current_path = post_path(row)
    title_text = strip_html(f"{row['title']} {row['excerpt'] or ''} {row['slug']}")
    links = _matched_country_links(title_text, lang)
    if lang == "ru":
        links.extend([
            _link("Все статьи на русском", "/ru/blog/", "Свежие русскоязычные материалы по визам, странам и релокации."),
            _link("Гайд по визам Азии", "/visas/", "Главная страница для сравнения визовых маршрутов."),
            _link("Сравнить страны", "/compare/", "Быстрое сравнение стран для переезда в Азию."),
            _link("Калькулятор стоимости жизни", "/tools/cost-calculator/", "Проверка бюджета перед выбором страны."),
            _link("Планировщик бюджета", "/tools/budget-planner/", "Разложить переезд по основным расходам."),
        ])
    else:
        links.extend([
            _link("All relocation articles", "/blog/", "Fresh guides on visas, countries and relocation planning."),
            _link("Asia visa guide", "/visas/", "Start here when comparing visa routes across Asia."),
            _link("Compare Asian countries", "/compare/", "Compare relocation options side by side."),
            _link("Cost of living calculator", "/tools/cost-calculator/", "Check the monthly budget before choosing a country."),
            _link("Budget planner", "/tools/budget-planner/", "Turn a relocation idea into a rough expense plan."),
        ])
    for related in related_posts(row, limit=4):
        links.append(_link(strip_html(related["title"]), post_path(related), trim_text(strip_html(related["excerpt"] or ""), 110)))
    return _dedupe_links(links, current_path=current_path, limit=9)


def internal_links_for_page(row: sqlite3.Row | dict, *, current_path: str) -> list[dict[str, str]]:
    text = strip_html(f"{row['title']} {row['content']} {current_path}")
    links = _matched_country_links(text, "en")
    links.extend([
        _link("Countries hub", "/countries/", "Start with country pages if you are still choosing a destination."),
        _link("Asia visa guide", "/visas/", "Compare visa routes before planning housing or flights."),
        _link("Compare countries", "/compare/", "Side-by-side country comparison for relocation decisions."),
        _link("Compare Asian cities", "/compare-cities/", "Check city-level trade-offs before choosing a base."),
        _link("Free relocation tools", "/tools/", "Cost calculator and budget planner for early planning."),
        _link("Relocation blog", "/blog/", "Fresh visa and country guides based on official sources."),
    ])
    haystack = text.lower()
    for *keys, _url, _en_title, _ru_title in COUNTRY_INTERNAL_LINKS:
        if not any(str(key).lower() in haystack for key in keys):
            continue
        for key in keys:
            if str(key).startswith("/") or len(str(key)) < 4:
                continue
            topic_posts = many(
                """
                SELECT slug, title, excerpt, lang
                FROM posts
                WHERE lang = 'en'
                  AND (lower(slug) LIKE ? OR lower(title) LIKE ? OR lower(excerpt) LIKE ?)
                ORDER BY date DESC, id DESC
                LIMIT 3
                """,
                (f"%{str(key).lower()}%", f"%{str(key).lower()}%", f"%{str(key).lower()}%"),
            )
            for post in topic_posts:
                links.append(_link(strip_html(post["title"]), post_path(post), trim_text(strip_html(post["excerpt"] or ""), 110)))
            if topic_posts:
                break
    latest_posts = many("SELECT slug, title, excerpt, lang FROM posts WHERE lang = 'en' ORDER BY date DESC, id DESC LIMIT 4")
    for post in latest_posts:
        links.append(_link(strip_html(post["title"]), post_path(post), trim_text(strip_html(post["excerpt"] or ""), 110)))
    return _dedupe_links(links, current_path=current_path, limit=8)


def internal_links_for_blog(lang: str) -> list[dict[str, str]]:
    if lang == "ru":
        return [
            _link("Гайд по странам", "/countries/", "Страницы стран: стоимость жизни, города, визовая логика и практические компромиссы."),
            _link("Гайд по визам Азии", "/visas/", "Сравнение визовых маршрутов до выбора страны."),
            _link("Сравнить страны", "/compare/", "Быстрое сравнение направлений для переезда."),
            _link("Калькулятор стоимости жизни", "/tools/cost-calculator/", "Проверка бюджета перед планированием переезда."),
            _link("Планировщик бюджета", "/tools/budget-planner/", "Разложить расходы на переезд по категориям."),
            _link("Compare Cities", "/compare-cities/", "Сравнение городов по практическим метрикам."),
        ]
    return [
        _link("Countries hub", "/countries/", "Country pages for costs, cities, visa logic and trade-offs."),
        _link("Asia visa guide", "/visas/", "Compare visa routes before choosing a destination."),
        _link("Compare countries", "/compare/", "Side-by-side comparison for relocation decisions."),
        _link("Cost of living calculator", "/tools/cost-calculator/", "Check the monthly budget before planning a move."),
        _link("Budget planner", "/tools/budget-planner/", "Break relocation expenses into practical categories."),
        _link("Compare Asian cities", "/compare-cities/", "City-level comparison for choosing a base."),
    ]


def render_page_row(row: sqlite3.Row | dict, **kwargs):
    breadcrumbs = kwargs.get("breadcrumbs", [])
    path = row["link"] if "link" in row.keys() and row["link"] else request.path
    slug = row["slug"] if "slug" in row.keys() else request.path.strip("/")
    schema = [
        breadcrumb_schema(breadcrumbs, row["title"], path),
        organization_schema(),
        website_schema(),
    ]
    internal_links = internal_links_for_page(row, current_path=path)
    faq_schema = faq_schema_from_html(row["content"], lang="en")
    if faq_schema:
        schema.append(faq_schema)
    item_list = item_list_schema(f"Internal links for {strip_html(row['title'])}", internal_links)
    if item_list:
        schema.append(item_list)
    if path in {"/compare/", "/compare-cities/", "/tools/cost-calculator/", "/tools/budget-planner/"}:
        schema.append(web_application_schema(row["title"], path, row["content"]))
    seo = seo_payload(
        title=row["title"],
        description=PAGE_SEO_DESCRIPTIONS.get(slug, row["excerpt"] if "excerpt" in row.keys() else row["content"]),
        canonical_path=path,
        schema=schema,
    )
    return render_template(
        "page.html",
        page=row,
        seo=seo,
        internal_links=internal_links,
        **kwargs,
    )


def render_post_row(row: sqlite3.Row, *, lang: str):
    canonical_path = f"/blog/{row['slug']}/" if lang == "en" else f"/ru/blog/{row['slug']}/"
    alternates = post_alternates(row, lang=lang, canonical_path=canonical_path)
    schema = [
        article_schema(row, lang=lang, canonical_path=canonical_path),
        breadcrumb_schema([("Blog", "/blog/")], row["title"], canonical_path),
        organization_schema(),
    ]
    faq_schema = faq_schema_from_html(row["content"], lang=lang)
    if faq_schema:
        schema.append(faq_schema)
    internal_links = internal_links_for_post(row, lang=lang)
    item_list = item_list_schema(f"Internal links for {strip_html(row['title'])}", internal_links)
    if item_list:
        schema.append(item_list)
    seo = seo_payload(
        title=row["title"],
        description=row["excerpt"] or row["content"],
        lang=lang,
        canonical_path=canonical_path,
        alternates=alternates,
        schema=schema,
        og_type="article",
    )
    return render_template(
        "post.html",
        post=row,
        seo=seo,
        lang_code=lang,
        related_posts=related_posts(row),
        internal_links=internal_links,
    )


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
    path = row["link"] or request.path
    internal_links = internal_links_for_page(row, current_path=path)
    schema = [
        breadcrumb_schema([("Countries", "/countries/")], row["title"], path),
        organization_schema(),
        website_schema(),
        country_schema(row, facts, path),
    ]
    item_list = item_list_schema(f"Internal links for {strip_html(row['title'])}", internal_links)
    if item_list:
        schema.append(item_list)
    seo = seo_payload(
        title=row["title"],
        description=country_meta_description(row, facts),
        canonical_path=path,
        schema=schema,
    )
    return render_template(
        "country.html",
        page=row,
        facts=facts,
        seo=seo,
        breadcrumbs=[("Countries", "/countries/")],
        internal_links=internal_links,
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


@app.route("/move-to-asia/")
def move_to_asia():
    row = page_or_404("move-to-asia")
    return render_page_row(row, breadcrumbs=[])


@app.route("/digital-nomad-visas-asia/")
def digital_nomad_visas_asia():
    row = page_or_404("digital-nomad-visas-asia")
    return render_page_row(row, breadcrumbs=[])


@app.route("/retire-in-asia/")
def retire_in_asia():
    row = page_or_404("retire-in-asia")
    return render_page_row(row, breadcrumbs=[])


@app.route("/cost-of-living-asia/")
def cost_of_living_asia():
    row = page_or_404("cost-of-living-asia")
    return render_page_row(row, breadcrumbs=[])


def render_blog_index(*, lang: str):
    is_ru = lang == "ru"
    path = "/ru/blog/" if is_ru else "/blog/"
    title = "Блог о релокации в Азию" if is_ru else "Asia Relocation Blog"
    description = (
        "Русскоязычные гайды по визам, странам и релокации в Азию на основе официальных источников."
        if is_ru else
        "Guides, comparisons and practical relocation advice for expats moving across Asia."
    )
    posts = many(
        "SELECT id, slug, title, excerpt, date, lang FROM posts WHERE lang = ? ORDER BY date DESC",
        (lang,),
    )
    alternates = [
        {"lang": "en", "url": absolute_url("/blog/")},
        {"lang": "ru", "url": absolute_url("/ru/blog/")},
        {"lang": "x-default", "url": absolute_url("/blog/")},
    ]
    seo = seo_payload(
        title=title,
        description=description,
        lang=lang,
        canonical_path=path,
        alternates=alternates,
        schema=[breadcrumb_schema([], title, path), collection_schema(title, description, path), organization_schema(), website_schema()],
    )
    return render_template(
        "blog.html",
        posts=posts,
        seo=seo,
        blog_lang=lang,
        blog_url_prefix="/ru/blog" if is_ru else "/blog",
        blog_title=title,
        blog_intro=description,
        internal_links=internal_links_for_blog(lang),
        read_more="Читать" if is_ru else "Read more",
    )


@app.route("/blog/")
def blog():
    return render_blog_index(lang="en")


@app.route("/ru/blog/")
def blog_ru():
    return render_blog_index(lang="ru")


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




TRUST_PAGES = {
    "about": {
        "title": "About Relocate to Asia",
        "description": "Who publishes Relocate to Asia and how the site helps readers compare Asian countries, visas and relocation costs.",
        "content": """
<section class="rta-trust-page">
  <h1>About Relocate to Asia</h1>
  <p>Relocate to Asia is an editorial relocation resource for readers comparing Asian countries, cities, visas and practical moving costs. The site focuses on decision support: official visa facts, country comparisons, cost context and clear trade-offs.</p>
  <p>Our editorial goal is to help readers filter options before they spend money on applications, flights, housing or professional advice. We do not sell visas, and we do not present editorial planning guides as legal advice.</p>
  <h2>What We Cover</h2>
  <ul>
    <li>Country and city comparisons for expats and remote workers.</li>
    <li>Visa and long-stay guides based on official public sources.</li>
    <li>Cost and lifestyle trade-offs for moving across Asia.</li>
    <li>English and Russian versions where a translated guide is useful.</li>
  </ul>
</section>
""",
    },
    "editorial-policy": {
        "title": "Editorial Policy",
        "description": "How Relocate to Asia researches, writes and updates relocation and visa guides.",
        "content": """
<section class="rta-trust-page">
  <h1>Editorial Policy</h1>
  <p>Relocate to Asia publishes practical relocation guides for planning, not legal instructions. Visa articles prioritize official government, consular or program pages. Secondary sources may be used for context, but they should not override the authority that publishes the rule.</p>
  <h2>Our Standards</h2>
  <ul>
    <li>Use official sources for visa limits, eligibility, stay duration and application rules.</li>
    <li>Separate confirmed facts from editorial interpretation.</li>
    <li>Show the month and year when a guide was checked whenever possible.</li>
    <li>Use nofollow links for external official references.</li>
    <li>Update or rewrite pages when rules change or a better official source becomes available.</li>
  </ul>
  <p>Readers should always verify the official source before applying. Immigration rules can change without notice.</p>
</section>
""",
    },
    "how-we-verify-data": {
        "title": "How We Verify Data",
        "description": "The verification process used for Relocate to Asia visa, country and comparison content.",
        "content": """
<section class="rta-trust-page">
  <h1>How We Verify Data</h1>
  <p>For visa and long-stay guides, the visible source block should point to official public pages such as immigration departments, ministries, consulates or government program websites. We quote short official phrases for key numbers, then explain what those facts mean for planning.</p>
  <h2>Verification Checklist</h2>
  <ul>
    <li>Identify the official authority for the visa or program.</li>
    <li>Confirm the core numbers: allowed stay, validity, income, fees or deposit when stated.</li>
    <li>Check whether local work, renewal, dependants or conversion are explicitly mentioned.</li>
    <li>Keep internal data tools out of public source blocks because they are editorial infrastructure, not reader-facing authority.</li>
    <li>Add a clear caution when a rule is not confirmed by the official source.</li>
  </ul>
</section>
""",
    },
}


@app.route("/about/")
def about():
    page = {"title": TRUST_PAGES["about"]["title"], "content": TRUST_PAGES["about"]["content"], "link": "/about/"}
    return render_page_row(page, breadcrumbs=[])


@app.route("/editorial-policy/")
def editorial_policy():
    page = {"title": TRUST_PAGES["editorial-policy"]["title"], "content": TRUST_PAGES["editorial-policy"]["content"], "link": "/editorial-policy/"}
    return render_page_row(page, breadcrumbs=[])


@app.route("/how-we-verify-data/")
def how_we_verify_data():
    page = {"title": TRUST_PAGES["how-we-verify-data"]["title"], "content": TRUST_PAGES["how-we-verify-data"]["content"], "link": "/how-we-verify-data/"}
    return render_page_row(page, breadcrumbs=[])


def sitemap_paths() -> list[tuple[str, str]]:
    paths: list[tuple[str, str]] = [
        ("/", "daily"),
        ("/countries/", "weekly"),
        ("/tools/", "monthly"),
        ("/compare/", "weekly"),
        ("/compare-cities/", "monthly"),
        ("/visas/", "weekly"),
        ("/best-countries-in-asia-to-move/", "monthly"),
        ("/cheapest-countries-in-asia/", "monthly"),
        ("/blog/", "daily"),
        ("/ru/blog/", "daily"),
        ("/about/", "monthly"),
        ("/editorial-policy/", "monthly"),
        ("/how-we-verify-data/", "monthly"),
    ]
    for row in many("SELECT link FROM pages WHERE link IS NOT NULL AND link != ''"):
        paths.append((row["link"], "monthly"))
    for row in many("SELECT slug, lang FROM posts ORDER BY date DESC"):
        prefix = "/blog" if row["lang"] == "en" else "/ru/blog"
        paths.append((f"{prefix}/{row['slug']}/", "weekly"))
    seen = set()
    unique: list[tuple[str, str]] = []
    for path, changefreq in paths:
        if path not in seen:
            seen.add(path)
            unique.append((path, changefreq))
    return unique


@app.route("/sitemap.xml")
def sitemap_xml():
    from html import escape

    alternate_map = post_pair_map()
    alternate_map["/blog/"] = [
        {"lang": "en", "url": absolute_url("/blog/")},
        {"lang": "ru", "url": absolute_url("/ru/blog/")},
        {"lang": "x-default", "url": absolute_url("/blog/")},
    ]
    alternate_map["/ru/blog/"] = alternate_map["/blog/"]
    urls = []
    for path, changefreq in sitemap_paths():
        links = "".join(
            f"<xhtml:link rel=\"alternate\" hreflang=\"{escape(item['lang'])}\" href=\"{escape(item['url'])}\" />"
            for item in alternate_map.get(path, [])
        )
        urls.append(
            "  <url>"
            f"<loc>{escape(absolute_url(path))}</loc>"
            f"{links}"
            f"<changefreq>{changefreq}</changefreq>"
            "</url>"
        )
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
    xml += "\n".join(urls)
    xml += "\n</urlset>\n"
    return Response(xml, mimetype="application/xml")

@app.route("/robots.txt")
def robots_txt():
    body = "\n".join([
        "User-agent: *",
        "Allow: /",
        f"Sitemap: {SITE_URL}/sitemap.xml",
        "",
    ])
    return Response(body, mimetype="text/plain")


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
