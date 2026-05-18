from __future__ import annotations

import re
import sqlite3
import json
import html
from pathlib import Path

from flask import Flask, Response, abort, redirect, render_template, request

APP_DIR = Path(__file__).resolve().parent
DB_PATH = APP_DIR / "content.db"

app = Flask(__name__)

SITE_NAME = "Relocate to Asia"
SITE_URL = "https://www.marharuta.online"
DEFAULT_OG_IMAGE = "/static/img/og-default.png"
FAVICON_PATH = "/static/img/favicon.svg"
GOOGLE_SITE_VERIFICATION_FILE = "google0cbfacb558cd5e85.html"


@app.before_request
def redirect_to_www():
    """Redirect marharuta.online → www.marharuta.online (301)."""
    host = request.host.split(":")[0]  # strip port if any
    if host == "marharuta.online":
        url = request.url.replace("://marharuta.online", "://www.marharuta.online", 1)
        from flask import redirect
        return redirect(url, 301)


@app.route("/favicon.ico")
def favicon_ico():
    return redirect(FAVICON_PATH, 301)


@app.route(f"/{GOOGLE_SITE_VERIFICATION_FILE}")
def google_site_verification():
    verification_path = APP_DIR / GOOGLE_SITE_VERIFICATION_FILE
    if not verification_path.exists():
        abort(404)
    return Response(verification_path.read_text(encoding="utf-8"), mimetype="text/html")


DEFAULT_AUTHOR = "Relocate to Asia Editorial Team"
EDITORIAL_TEAM_URL = "/authors/editorial-team/"
CONTACT_EMAIL = "contact@marharuta.online"
LAST_REVIEWED_EN = "May 2026"
LAST_REVIEWED_RU = "май 2026"
DEFAULT_DESCRIPTION = (
    "Relocate to Asia helps expats compare countries, cities, visas and real-world "
    "moving costs across Asia."
)
PAGE_SEO_DESCRIPTIONS = {
    "compare": (
        "Compare Asian countries in 2026 by cost of living, visas, safety, healthcare, "
        "climate, English level and digital nomad practicality."
    ),
    "visas": (
        "Asia visa guide for 2026 covering digital nomad visas, long-stay routes, "
        "retirement options and official source checks."
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
    "guides": "Asia relocation guides for 2026 visa, budget, family, retirement and country comparison decisions before you spend money on a move.",
    "can-you-extend-japan-digital-nomad-visa": "Can you extend Japan Digital Nomad Visa in 2026? Clear answer, official limit and practical planning risk.",
    "japan-digital-nomad-visa-income-requirement": "Japan Digital Nomad Visa income requirement in 2026, what to verify and where applicants often misread the rule.",
    "thailand-dtv-vs-ltr-visa": "Thailand DTV vs LTR Visa in 2026 by stay logic, eligibility, documents and who should avoid each route.",
    "malaysia-de-rantau-vs-thailand-dtv": "Malaysia DE Rantau vs Thailand DTV in 2026 for remote workers comparing visa fit, location and practical limits.",
    "taiwan-gold-card-income-requirement": "Taiwan Gold Card income requirement and eligibility logic in 2026 for skilled professionals and remote workers.",
    "best-asian-countries-with-easy-long-stay-visas": "Best Asian countries with easier long-stay visa routes in 2026, with realistic limits and planning cautions.",
    "where-to-live-in-asia-on-1500-a-month": "Where to live in Asia on $1500 a month in 2026, with budget trade-offs and country fit.",
    "best-asian-countries-for-remote-workers-with-family": "Best Asian countries for remote workers with family in 2026 by visa practicality, schools, healthcare and cost.",
    "philippines-srrv-vs-thailand-retirement-visa": "Philippines SRRV vs Thailand Retirement Visa in 2026 by deposit logic, stay comfort and retirement planning risk.",
    "vietnam-evisa-vs-thailand-dtv": "Vietnam eVisa vs Thailand DTV in 2026 for long stays, remote workers and people testing Southeast Asia.",
}

RU_PAGE_SEO_DESCRIPTIONS = {
    "compare": (
        "Сравнение стран Азии в 2026 году по стоимости жизни, визам, инфраструктуре, "
        "медицине, безопасности и практичности для релокации."
    ),
    "bali-vs-thailand": (
        "Сравнение Бали и Таиланда для переезда в 2026 году: визовая логика, расходы, "
        "инфраструктура и кому какой вариант подходит лучше."
    ),
    "thailand-vs-malaysia": (
        "Сравнение Таиланда и Малайзии для релокации в 2026 году: долгосрочные визы, "
        "расходы, английский язык, медицина и семейный сценарий."
    ),
    "japan-vs-taiwan": (
        "Сравнение Японии и Тайваня для релокации в 2026 году: визовые маршруты, "
        "профессиональный профиль, стоимость жизни и практические ограничения."
    ),
    "thailand-vs-vietnam": (
        "Сравнение Таиланда и Вьетнама для релокации в 2026 году: стоимость, визы, "
        "городская инфраструктура и устойчивость долгого проживания."
    ),
    "malaysia-vs-vietnam": (
        "Сравнение Малайзии и Вьетнама для релокации в 2026 году: комфорт, бюджет, "
        "визовая логика и повседневная практичность."
    ),
    "singapore-vs-hong-kong": (
        "Сравнение Сингапура и Гонконга для релокации в 2026 году: карьерный профиль, "
        "дороговизна, визы для специалистов и реальные компромиссы."
    ),
    "uae-vs-qatar": (
        "Сравнение ОАЭ и Катара для релокации в 2026 году: рабочие маршруты, удаленная "
        "работа, расходы и ограничения для экспатов."
    ),
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


def local_path(path: str) -> str:
    if path.startswith(SITE_URL):
        return path.removeprefix(SITE_URL) or "/"
    return path


def page_meta_description(row: sqlite3.Row | dict, *, lang: str) -> str:
    slug = row["slug"] if "slug" in row.keys() else ""
    normalized_slug = slug.removeprefix("ru-")
    if lang == "ru":
        return RU_PAGE_SEO_DESCRIPTIONS.get(normalized_slug, row["content"])
    return PAGE_SEO_DESCRIPTIONS.get(normalized_slug, row["excerpt"] if "excerpt" in row.keys() else row["content"])


def localized_page_alternates(*, en_path: str, ru_path: str) -> list[dict[str, str]]:
    return [
        {"lang": "en", "url": absolute_url(en_path)},
        {"lang": "ru", "url": absolute_url(ru_path)},
        {"lang": "x-default", "url": absolute_url(en_path)},
    ]


def localized_compare_db_slug(slug: str) -> str:
    return f"ru-{slug}"


def localized_compare_index_content() -> str:
    row = page_or_404("compare")
    content = row["content"]
    replacements = [
        ('<span class="ct-badge">Free Tool</span>', '<span class="ct-badge">Бесплатный инструмент</span>'),
        ('<h1>Compare Asian Countries</h1>', '<h1>Сравните страны Азии</h1>'),
        ('Select two countries and get a real-time side-by-side comparison of cost, safety, climate and quality of life.', 'Выберите две страны и получите наглядное сравнение стоимости жизни, безопасности, климата и качества повседневной жизни.'),
        ('Country Comparison Tool', 'Инструмент сравнения стран'),
        ('>Home<', '>Главная<'),
        ('>Compare<', '>Сравнения<'),
        ('href="/compare/', 'href="/ru/compare/'),
        ("Country 1", "Страна 1"),
        ("Country 2", "Страна 2"),
        ("Compare Countries →", "Сравнить страны →"),
        ("Fetching real-time data&#8230;", "Загружаем актуальные данные&#8230;"),
        ("Compare Asian Countries Before You Choose Where To Move", "Сравните страны Азии до того, как выберете, куда переезжать"),
        ("Choosing a country in Asia is easier when the comparison is not built around one number. Cheap rent can hide weak visa options. A strong visa can sit in a city that is too expensive. A safe country can still be a poor fit if the internet, healthcare or family logistics do not match your life.", "Выбор страны в Азии становится проще, если не сводить всё к одной цифре. Дешёвая аренда может скрывать слабый визовый маршрут. Сильная виза может идти вместе со слишком дорогим городом. А безопасная страна всё равно может оказаться не вашей, если интернет, медицина или семейная логистика не совпадают с реальной жизнью."),
        ("This country comparison tool is meant for the first serious shortlist. Use it to compare cost of living, visa routes, safety, healthcare, climate, English level and digital nomad practicality before you go deeper into a full relocation guide.", "Этот инструмент нужен для первого серьёзного shortlist. Сравните стоимость жизни, визовые маршруты, безопасность, медицину, климат, уровень английского и практичность для удалённой работы до того, как уходить в длинные гайды."),
        ("Best Country Comparisons To Start With", "С каких сравнений лучше начать"),
        ("Thailand vs Malaysia", "Таиланд vs Малайзия"),
        ("Bali vs Thailand", "Бали vs Таиланд"),
        ("Compare Asian Cities", "Сравнить города Азии"),
        ("Compare two of Southeast Asia's most popular expat bases for visas, costs, healthcare and lifestyle.", "Сравнение двух самых популярных баз в Юго-Восточной Азии по визам, расходам, медицине и образу жизни."),
        ("Check the trade-off between Bali lifestyle and Thailand's broader city and visa options.", "Посмотрите, что для вас важнее: стиль жизни на Бали или более широкий выбор городов и виз в Таиланде."),
        ("Use city-level data when the country looks right but the base is still unclear.", "Подключите данные по городам, если страна уже подходит, а конкретная база всё ещё не ясна."),
        ("Best Countries In Asia To Move To", "Лучшие страны Азии для переезда"),
        ("Cheapest Countries In Asia", "Самые дешёвые страны Азии"),
        ("Asia Visa Guide", "Гид по визам Азии"),
        ("Start with the broader ranking if you do not yet know which countries belong on your shortlist.", "Начните с общего рейтинга, если ещё не ясно, какие страны стоит оставить в shortlist."),
        ("Focus on monthly budget, low-cost cities and realistic compromises for cheaper living.", "Сфокусируйтесь на месячном бюджете, недорогих городах и реальных компромиссах дешёвой жизни."),
        ("Check visa routes before planning housing, flights or a long stay.", "Проверьте визовые маршруты до жилья, билетов и long-stay плана."),
        ("What The Инструмент сравнения стран Checks", "Что проверяет инструмент сравнения стран"),
        ("Monthly budget: a practical starting estimate for solo expat planning.", "Месячный бюджет: стартовая оценка для одного человека."),
        ("Visa route: the main path people usually check before a move.", "Визовый маршрут: главный путь, который проверяют до переезда."),
        ("Monthly budget: practical starting estimate for expat planning.", "Месячный бюджет: практичная стартовая оценка для планирования."),
        ("the main path people usually check before move", "главный маршрут, который обычно проверяют до переезда"),
        ("Lifestyle country best which country fits this person this income this visa and this time horizon", "Главный вопрос — какая страна подходит этому человеку, этому доходу, этой визе и этому сроку"),
        ("Malaysia's cost, English level, long-stay options and city choices.", "Расходы, английский, long-stay варианты и города Малайзии."),
        ("Bali lifestyle, costs, practical limits and remote work considerations.", "Lifestyle на Бали, расходы, ограничения и удалённая работа."),
        ("Budget, cities and eVisa planning for Vietnam.", "Бюджет, города и eVisa-логика Вьетнама."),
        ("Move To Taiwan", "Переезд на Тайвань"),
        ("Move To Japan", "Переезд в Японию"),
        ("Quality of life, Gold Card logic and city trade-offs.", "Качество жизни, логика Gold Card и компромиссы по городам."),
        ("Japan's costs, visa limits and practical relocation questions.", "Расходы Японии, визовые ограничения и практические вопросы переезда."),
        ("How To Use The Comparison", "Как пользоваться сравнением"),
        ("Start with two countries you would genuinely consider. If one country wins on cost but loses on visa fit, do not treat the cheaper number as the final answer. If a country looks strong on safety and healthcare but weak on budget, check whether your income can absorb the difference.", "Начинайте с двух стран, которые вы реально рассматриваете. Если одна выигрывает по цене, но проигрывает по визе, не считайте дешёвую цифру финальным ответом. Если страна сильна по безопасности и медицине, но дорога, проверьте, выдерживает ли это ваш доход."),
        ("The useful decision is not “which", "Полезный вопрос не в том, какая"),
        ("After the tool narrows the shortlist, open the country guide and visa guide before making any paid commitment.", "После первого отбора откройте страновой гид и визовую страницу до любых платных решений."),
        ("Compare countries first if you are still checking visas, budgets and long-stay logic. Compare cities after the country already looks realistic.", "Сначала сравнивайте страны, если ещё проверяете визы, бюджет и long-stay логику. К городам переходите после того, как страна уже выглядит реалистично."),
        ("Is The Cheapest Country Always The Best Choice?", "Самая дешёвая страна — всегда лучший выбор?"),
        ("No. A cheaper country can still be a poor fit if the visa route is weak, healthcare is not enough for your needs, or the city does not match your work and family situation.", "Нет. Дешёвая страна может не подойти, если визовый маршрут слабый, медицина не закрывает ваши задачи или город не совпадает с работой и семейной логистикой."),
        ("Which Factors Matter Most For Digital Nomads?", "Какие факторы важнее всего для digital nomads?"),
        ("Visa rules, internet quality, cost of living, safety, English level and the local remote-work community usually matter more than a broad lifestyle score.", "Визы, интернет, стоимость жизни, безопасность, английский и локальное remote-work сообщество обычно важнее общего lifestyle-рейтинга."),
        ("Open the full country guide, check the visa page, run the cost calculator and compare cities. The tool is a shortlist step, not the final decision.", "Откройте полный гид по стране, проверьте визы, посчитайте бюджет и сравните города. Инструмент — это shortlist, а не финальное решение."),
        ("How To Use This Country Comparison Tool", "Как пользоваться этим инструментом"),
        ("Visa stability and stay logic:", "Визовая устойчивость и логика проживания:"),
        ("the first filter for long-term relocation.", "первый фильтр для долгосрочного переезда."),
        ("Monthly budget and housing pressure:", "Ежемесячный бюджет и давление по жилью:"),
        ("important for digital nomads, retirees and families.", "важно для удалёнщиков, пенсионных маршрутов и семей."),
        ("Safety and healthcare:", "Безопасность и медицина:"),
        ("useful filters for families, retirees and long-stay expats.", "важные фильтры для семьи, пенсии и долгого проживания."),
        ("Internet and English level:", "Интернет и уровень английского:"),
        ("important for remote workers and digital nomads.", "важно для удалённой работы и повседневной адаптации."),
        ("Climate and outdoors:", "Климат и повседневная среда:"),
        ("helpful when lifestyle is a real deciding factor.", "важно, если образ жизни действительно влияет на решение."),
        ("Quality of life:", "Качество жизни:"),
        ("a broad signal, not a replacement for reading the country guide.", "общий ориентир, а не замена полноценному страновому гайду."),
        ("Popular Country Pages", "Популярные страницы стран"),
        ("Move To Thailand", "Переезд в Таиланд"),
        ("Move To Malaysia", "Переезд в Малайзию"),
        ("Move To Bali", "Переезд на Бали"),
        ("Move To Vietnam", "Переезд во Вьетнам"),
        ("Costs, cities, visa logic and trade-offs for Thailand.", "Расходы, города, визовая логика и реальные компромиссы по Таиланду."),
        ("Costs, visas, English level and long-stay routes in Malaysia.", "Расходы, визы, английский язык и маршруты долгого проживания в Малайзии."),
        ("Lifestyle, costs, visa reality and trade-offs for Bali.", "Стиль жизни, расходы, визовая реальность и компромиссы на Бали."),
        ("Budget, cities, visas and infrastructure across Vietnam.", "Бюджет, города, визы и инфраструктура во Вьетнаме."),
        ("FAQ", "Частые вопросы"),
        ("What Is The Best Country In Asia For Expats?", "Какая страна в Азии лучше всего подходит для переезда?"),
        ("Should I Compare Countries Or Cities First?", "Что сравнивать сначала: страны или города?"),
        ("How Accurate Is This Country Comparison Tool?", "Насколько точен этот инструмент сравнения?"),
        ("What Should I Do After Comparing Two Countries?", "Что делать после сравнения двух стран?"),
        ("There is no single best country for every expat. Thailand and Malaysia are common starting points, Taiwan is strong for professionals, Vietnam can be attractive for budget planning, and Japan works better for people who can handle higher costs and stricter visa limits.", "Универсально лучшей страны для всех нет. Таиланд и Малайзия часто становятся первой точкой входа, Тайвань силён для специалистов, Вьетнам интересен по бюджету, а Япония подходит тем, кто выдерживает более высокие расходы и более жёсткие визовые рамки."),
        ("Compare countries first if you are still checking visa logic, healthcare and budget at a broad level. Compare cities once the country looks right but the daily base is still unclear.", "Сначала сравнивайте страны, если ещё проверяете визовую логику, медицину и бюджет на широком уровне. К городам лучше переходить тогда, когда страна уже подходит, но база для жизни всё ещё не выбрана."),
        ("The tool gives a useful first-pass comparison, not a final legal answer. Use it to narrow the shortlist, then verify visa details and read the matching country guide before making payments.", "Инструмент даёт хороший первый срез, но не заменяет финальную юридическую проверку. Используйте его, чтобы сузить shortlist, а затем отдельно проверяйте визовые детали и читайте страновой гайд."),
        ("After comparing, open the country guide and visa guide before making any paid commitment.", "После сравнения откройте страновой и визовый гид, а уже потом принимайте платные обязательства."),
        ("Please select two different countries.", "Выберите две разные страны."),
        ("Error fetching data: ", "Ошибка при загрузке данных: "),
        (". Please try again.", ". Попробуйте ещё раз."),
        ("Cost of Living Score", "Оценка стоимости жизни"),
        ("🛡️ Safety &amp; Health", "🛡️ Безопасность и медицина"),
        ("Safety Score", "Оценка безопасности"),
        ("Healthcare Score", "Оценка медицины"),
        ("🌤️ Climate", "🌤️ Климат"),
        ("Avg Temperature", "Средняя температура"),
        ("Rain / month", "Осадки / месяц"),
        ("Outdoors Score", "Оценка среды"),
        ("💼 Visa &amp; Work", "💼 Визы и работа"),
        ("Best Visa", "Основной визовый маршрут"),
        ("English Level", "Уровень английского"),
        ("Nomad Score", "Оценка для удалёнщиков"),
        ("📊 General", "📊 Общие показатели"),
        ("Population", "Население"),
        ("Area", "Площадь"),
        ("Ready to Choose?", "Готовы выбрать?"),
        ("Read the full relocation guides to make your final decision.", "Откройте полные гайды по странам, чтобы принять финальное решение."),
        ("Guide: ${d1.name} →", "Гайд: ${d1.name} →"),
        ("Guide: ${d2.name} →", "Гайд: ${d2.name} →"),
    ]
    for old, new in replacements:
        content = content.replace(old, new)
    content = content.replace(
        "Monthly budget: a practical starting estimate for solo expat planning.",
        "Месячный бюджет: стартовая оценка для одного человека.",
    )
    content = content.replace(
        "Visa route: the main path people usually check before a move.",
        "Визовый маршрут: главный путь, который проверяют до переезда.",
    )
    content = content.replace(
        "<li><strong>Monthly budget:</strong> a practical starting estimate for solo expat planning.</li>",
        "<li><strong>Месячный бюджет:</strong> стартовая оценка для одного человека.</li>",
    )
    content = content.replace(
        "<li><strong>Visa route:</strong> the main path people usually check before a move.</li>",
        "<li><strong>Визовый маршрут:</strong> главный путь, который проверяют до переезда.</li>",
    )
    content = re.sub(
        r"Полезный вопрос не в том, какая\s*country is best[”\"]\.\s*It is [“\"]which country fits this person, this income, this visa route and this time horizon[”\"]\.",
        "Полезный вопрос не в том, какая страна лучшая вообще, а какая страна подходит именно этому человеку, этому доходу, этой визе и этому сроку.",
        content,
    )
    content = re.sub(
        r"Полезный вопрос не в том, какая\s*country is best.{0,20}which country fits this person, this income, this visa route and this time horizon.{0,5}",
        "Полезный вопрос не в том, какая страна лучшая вообще, а какая страна подходит именно этому человеку, этому доходу, этой визе и этому сроку.",
        content,
    )
    return content


def ru_cheapest_countries_article() -> tuple[str, str]:
    countries = [
        {
            "id": "cambodia",
            "rank": 1,
            "tag": "самый дешёвый старт",
            "flag": "🇰🇭",
            "name": "Камбоджа",
            "ultra": "$550",
            "comfort": "$800",
            "plus": "$1,200",
            "currency": "USD / KHR",
            "city": "Пномпень",
            "text": [
                "Камбоджа часто оказывается самым мягким входом по деньгам. Пномпень даёт городскую базу с квартирами, кафе, интернетом и растущим сообществом экспатов. Сиемреап спокойнее и дешевле, но там меньше городской инфраструктуры.",
                "Практический смысл простой: Камбоджа хороша, если бюджет действительно главный фильтр. Но экономия не должна закрывать глаза на медицину, качество жилья и визовую логику. Для долгого проживания сначала считайте не аренду, а весь месяц вместе со страховкой и запасом.",
            ],
            "rows": [("Студия / 1BR", "$200-350"), ("Еда: местная + западная", "$150-250"), ("Транспорт", "$40-80"), ("Коммунальные услуги и интернет", "$50-80"), ("Досуг и прочее", "$80-150")],
            "pros": ["низкая аренда", "USD часто используют в быту", "простая бытовая логика для одного человека"],
            "cons": ["медицина слабее за пределами столицы", "инфраструктура неровная", "жара и сезонность могут утомлять"],
        },
        {
            "id": "laos",
            "rank": 2,
            "tag": "спокойно и недорого",
            "flag": "🇱🇦",
            "name": "Лаос",
            "ultra": "$600",
            "comfort": "$850",
            "plus": "$1,300",
            "currency": "LAK / USD",
            "city": "Вьентьян",
            "text": [
                "Лаос не про быстрый карьерный ритм и не про огромную среду экспатов. Его сила в другом: тише, дешевле, медленнее. Вьентьян подходит тем, кому нужна спокойная база, а Луангпхабанг чаще выбирают за атмосферу, природу и размеренный темп.",
                "На практике Лаос стоит рассматривать только если вы нормально переносите меньший выбор сервисов. Интернет и инфраструктура стали лучше, но это всё ещё не Бангкок и не Куала-Лумпур. Экономия реальная, но вместе с ней идут компромиссы.",
            ],
            "rows": [("Студия / 1BR", "$150-300"), ("Еда: местная + редкая западная", "$130-220"), ("Транспорт", "$30-70"), ("Коммунальные услуги и интернет", "$45-90"), ("Досуг и прочее", "$80-160")],
            "pros": ["очень спокойный ритм", "низкие базовые расходы", "мало туристической перегрузки"],
            "cons": ["меньше сервисов", "слабее медицина", "не всем подходит медленный темп"],
        },
        {
            "id": "nepal",
            "rank": 3,
            "tag": "горы и низкие расходы",
            "flag": "🇳🇵",
            "name": "Непал",
            "ultra": "$650",
            "comfort": "$900",
            "plus": "$1,300",
            "currency": "NPR",
            "city": "Катманду",
            "text": [
                "Непал может быть очень дешёвым, особенно если жить просто и не пытаться копировать западный городской комфорт. Катманду даёт больше сервисов, Покхара спокойнее и приятнее для части удалённых специалистов.",
                "Но Непал нельзя выбирать только по цене. Важны качество воздуха, медицина, электричество, интернет, район и сезон. Если работа требует стабильных звонков и предсказуемого дня, тестовый месяц здесь почти обязателен.",
            ],
            "rows": [("Студия / 1BR", "$180-350"), ("Еда", "$150-260"), ("Транспорт", "$25-60"), ("Интернет и коммунальные", "$50-90"), ("Досуг и поездки", "$100-180")],
            "pros": ["низкая стоимость жизни", "сильная природа", "много простых бытовых сценариев"],
            "cons": ["качество воздуха", "нестабильность инфраструктуры", "медицина требует осторожности"],
        },
        {
            "id": "vietnam",
            "rank": 4,
            "tag": "лучший бюджетный городский тест",
            "flag": "🇻🇳",
            "name": "Вьетнам",
            "ultra": "$700",
            "comfort": "$1,000",
            "plus": "$1,500",
            "currency": "VND",
            "city": "Дананг",
            "text": [
                "Вьетнам часто сильнее Лаоса и Камбоджи для удалённой работы: больше городов, лучше еда и кофе-сцена, больше жилья, выше динамика. Дананг удобен для теста, Ханой и Хошимин дают больше энергии, но и больше шума.",
                "Главный риск — принять дешёвый тест за готовую релокацию. Вьетнам может быть отличным первым шагом, но визовый ритм, медицина, банковские вопросы и долгий статус нужно проверять отдельно.",
            ],
            "rows": [("Студия / 1BR", "$250-500"), ("Еда", "$180-320"), ("Транспорт", "$40-100"), ("Связь и коммунальные", "$60-110"), ("Досуг", "$120-250")],
            "pros": ["очень хорошее соотношение цена / быт", "сильные города для теста", "быстрый повседневный ритм"],
            "cons": ["визовый горизонт требует проверки", "шум и трафик", "качество жилья сильно зависит от района"],
        },
        {
            "id": "india",
            "rank": 5,
            "tag": "дёшево, но не для всех",
            "flag": "🇮🇳",
            "name": "Индия",
            "ultra": "$700",
            "comfort": "$1,100",
            "plus": "$1,600",
            "currency": "INR",
            "city": "Гоа / Бангалор",
            "text": [
                "Индия может быть очень доступной, но разброс огромный. Гоа, Бангалор, Хайдарабад, Дели и маленькие города — это разные бюджеты и разный уровень стресса. Для tech-профилей Бангалор может быть логичнее, для спокойного теста часто смотрят Гоа.",
                "Сильная сторона Индии — цена и масштаб. Слабая — бытовая нагрузка. Если вы впервые едете в Азию, лучше не строить долгий план без короткого теста на месте.",
            ],
            "rows": [("Жильё", "$250-550"), ("Еда", "$150-300"), ("Транспорт", "$40-120"), ("Коммунальные и связь", "$50-120"), ("Досуг", "$120-250")],
            "pros": ["низкие расходы", "английский встречается часто", "много разных городских сценариев"],
            "cons": ["высокая бытовая нагрузка", "качество воздуха и шум", "город нужно выбирать очень внимательно"],
        },
        {
            "id": "philippines",
            "rank": 6,
            "tag": "английский и островной быт",
            "flag": "🇵🇭",
            "name": "Филиппины",
            "ultra": "$750",
            "comfort": "$1,150",
            "plus": "$1,700",
            "currency": "PHP",
            "city": "Себу",
            "text": [
                "Филиппины удобны тем, кому важен английский язык и более мягкая социальная адаптация. Себу, Давао и отдельные районы Манилы дают разные бюджеты. Островной сценарий может быть приятным, но не всегда дешёвым.",
                "Для пенсионеров Филиппины интересны отдельно из-за SRRV, но бюджетная статья не должна подменять визовую проверку. Медицину, страховку, город и расстояние до аэропорта нужно считать заранее.",
            ],
            "rows": [("Жильё", "$280-600"), ("Еда", "$200-350"), ("Транспорт", "$50-120"), ("Коммунальные и интернет", "$70-140"), ("Досуг", "$150-300")],
            "pros": ["английский в быту", "дружелюбная среда", "есть пенсионные сценарии"],
            "cons": ["островная логистика", "дороже хороший район", "погода и тайфуны"],
        },
        {
            "id": "indonesia",
            "rank": 7,
            "tag": "Бали дороже, чем кажется",
            "flag": "🇮🇩",
            "name": "Индонезия / Бали",
            "ultra": "$800",
            "comfort": "$1,300",
            "plus": "$2,000",
            "currency": "IDR",
            "city": "Бали",
            "text": [
                "Бали часто попадает в бюджетные списки, но это спорно. Да, можно жить относительно недорого, если выбрать простой район и умеренный ритм. Но Чангу, Семиньяк, частые кафе, байк, спорт, виза и хорошее жильё быстро поднимают бюджет.",
                "Индонезия подходит тем, кто честно считает образ жизни. Если вам нужен Бали как картинка из соцсетей, $800 почти наверняка будет мало. Если нужен спокойный быт вне дорогих районов, сценарий становится реалистичнее.",
            ],
            "rows": [("Жильё", "$350-800"), ("Еда", "$220-450"), ("Транспорт", "$60-150"), ("Связь и коммунальные", "$70-160"), ("Досуг", "$200-450")],
            "pros": ["сильное сообщество удалёнщиков", "много жилья и сервисов", "приятная среда при нормальном бюджете"],
            "cons": ["популярные районы дорогие", "трафик", "виза и страховка влияют на итог"],
        },
        {
            "id": "thailand",
            "rank": 8,
            "tag": "лучший баланс цены и инфраструктуры",
            "flag": "🇹🇭",
            "name": "Таиланд",
            "ultra": "$850",
            "comfort": "$1,400",
            "plus": "$2,200",
            "currency": "THB",
            "city": "Чиангмай / Бангкок",
            "text": [
                "Таиланд редко самый дешёвый, зато часто самый сбалансированный. Чиангмай может быть мягким по бюджету, Бангкок дороже, но даёт медицину, транспорт, сервисы и выбор районов. Острова быстро поднимают расходы.",
                "Если выбирать страну для долгого теста, Таиланд сильнее многих дешёвых альтернатив. Но визовый маршрут нельзя оставлять на потом: DTV, LTR, Elite и туристические варианты решают разные задачи.",
            ],
            "rows": [("Жильё", "$350-750"), ("Еда", "$220-400"), ("Транспорт", "$60-150"), ("Коммунальные и интернет", "$80-160"), ("Досуг", "$180-400")],
            "pros": ["сильная инфраструктура", "медицина в крупных городах", "много городов и районов"],
            "cons": ["не самый дешёвый вариант", "сложнее логика долгого проживания", "сезонное загрязнение воздуха"],
        },
        {
            "id": "malaysia",
            "rank": 9,
            "tag": "городской комфорт за разумные деньги",
            "flag": "🇲🇾",
            "name": "Малайзия",
            "ultra": "$900",
            "comfort": "$1,500",
            "plus": "$2,300",
            "currency": "MYR",
            "city": "Куала-Лумпур / Пенанг",
            "text": [
                "Малайзия не всегда выглядит самой дешёвой, но часто выигрывает по качеству за свои деньги. Куала-Лумпур даёт большие квартиры, английский, транспорт, торговые центры, медицину и перелёты. Пенанг спокойнее и может быть дешевле.",
                "Сильная сторона Малайзии — предсказуемость. Для семьи, долгого проживания или спокойного городского быта это может быть важнее, чем минимальная аренда в другой стране.",
            ],
            "rows": [("Жильё", "$400-850"), ("Еда", "$250-450"), ("Транспорт", "$70-160"), ("Коммунальные и интернет", "$80-170"), ("Досуг", "$200-450")],
            "pros": ["английский в быту", "хорошая городская инфраструктура", "сильная медицина"],
            "cons": ["Куала-Лумпур не всегда дешёвый", "виза зависит от профиля", "автомобильная логика вне центра"],
        },
        {
            "id": "sri-lanka",
            "rank": 10,
            "tag": "недорогой островной тест",
            "flag": "🇱🇰",
            "name": "Шри-Ланка",
            "ultra": "$900",
            "comfort": "$1,400",
            "plus": "$2,000",
            "currency": "LKR",
            "city": "Коломбо / Галле",
            "text": [
                "Шри-Ланка может быть недорогой, если не жить только в туристических местах и не строить премиальный пляжный быт. Коломбо практичнее, южное побережье приятнее, но сезон и район сильно меняют расходы.",
                "Для релокации Шри-Ланку лучше читать как тестовый вариант, а не как автоматический ответ для долгого проживания. Проверяйте ETA, продление, медицину и стабильность жилья до того, как считать страну дешёвой.",
            ],
            "rows": [("Жильё", "$350-750"), ("Еда", "$200-400"), ("Транспорт", "$50-130"), ("Коммунальные и интернет", "$70-150"), ("Досуг", "$180-400")],
            "pros": ["красивая среда", "можно жить недорого", "есть городские и пляжные сценарии"],
            "cons": ["сезонность", "инфраструктура неровная", "туристические районы дорожают"],
        },
    ]

    toc = "\n".join(
        f'<li><a href="#{item["id"]}">{item["name"]} — от {item["ultra"]}/мес.</a></li>'
        for item in countries
    )
    cards = []
    table_rows = []
    for item in countries:
        rows = "\n".join(f"<tr><td>{html.escape(label)}</td><td>{html.escape(value)}</td></tr>" for label, value in item["rows"])
        pros = "".join(f"<li>{html.escape(text)}</li>" for text in item["pros"])
        cons = "".join(f"<li>{html.escape(text)}</li>" for text in item["cons"])
        paragraphs = "\n".join(f"<p>{html.escape(text)}</p>" for text in item["text"])
        cards.append(f"""
<section class="cc-country" id="{item['id']}">
  <div class="cc-country-header">
    <div class="cc-rank-num">{item['rank']}</div>
    <div class="cc-country-info"><span class="tag">{html.escape(item['tag'])}</span><h2>{item['flag']} {html.escape(item['name'])}</h2></div>
  </div>
  <div class="cc-budget-grid">
    <div class="cc-budget-item"><span class="val">{item['ultra']}</span><span class="lbl">ультрабюджет</span></div>
    <div class="cc-budget-item"><span class="val">{item['comfort']}</span><span class="lbl">комфортно</span></div>
    <div class="cc-budget-item"><span class="val">{item['plus']}</span><span class="lbl">комфорт+</span></div>
    <div class="cc-budget-item"><span class="val">{item['currency']}</span><span class="lbl">валюта</span></div>
  </div>
  {paragraphs}
  <div class="cc-breakdown"><h4>Разбивка расходов за месяц — {html.escape(item['city'])} 2026</h4><table>{rows}</table></div>
  <div class="bcm-cols"><div class="bcm-pros"><h3>Плюсы</h3><ul>{pros}</ul></div><div class="bcm-cons"><h3>Минусы</h3><ul>{cons}</ul></div></div>
</section>
""")
        table_rows.append(
            f"<tr><td>{item['rank']}</td><td>{item['flag']} {html.escape(item['name'])}</td><td>{item['ultra']}-{item['comfort']}</td><td>{item['plus']}</td><td>{html.escape(item['city'])}</td></tr>"
        )

    title = "Самые дешёвые страны Азии для жизни в 2026 году"
    content = f"""
<div class="cc-page">
  <section class="cc-hero">
    <span class="badge">Проверено в марте 2026 · расходы, визы и бытовые риски</span>
    <h1>{title}</h1>
    <p>Дешёвая страна не всегда даёт дешёвую релокацию. Считать нужно не только аренду, а весь месяц: жильё, еду, транспорт, страховку, визовый ритм, интернет и запас на ошибку.</p>
    <div class="cc-stats"><div><strong>$550</strong><span>минимальный бюджет</span></div><div><strong>10</strong><span>стран в рейтинге</span></div><div><strong>2026</strong><span>обновлённые ориентиры</span></div></div>
  </section>
  <div class="guide-note"><strong>Короткий вывод:</strong> если нужен самый дешёвый старт, смотрите Камбоджу, Лаос, Непал и Вьетнам. Если нужен баланс цены, медицины, интернета и городской инфраструктуры, чаще сильнее Таиланд или Малайзия.</div>
  <section class="table-of-contents"><h2>Содержание</h2><ol>{toc}<li><a href="#table">Сводная таблица расходов</a></li><li><a href="#tips">Как не ошибиться с дешёвой страной</a></li><li><a href="#faq">FAQ</a></li></ol></section>
  {''.join(cards)}
  <section id="table" class="cc-country"><h2>Сводная таблица расходов</h2><p>Цифры ниже — рабочие диапазоны для одного человека. Семья, международная школа, премиальное жильё, частая медицина и островной быт быстро меняют итог.</p><table><tr><th>#</th><th>Страна</th><th>Базовый / комфортный месяц</th><th>Комфорт+</th><th>Город для первого теста</th></tr>{''.join(table_rows)}</table></section>
  <section id="tips" class="cc-country"><h2>Как не ошибиться с дешёвой страной</h2><p>Первый риск — сравнивать только аренду. Второй — забыть про визу. Третий — считать, что дешёвый туристический месяц равен нормальной жизни. Перед переездом проверьте срок пребывания, продление, страховку, медицину, интернет, район, депозит, перелёты и стоимость выхода из страны, если план не сработает.</p><p>Для одного человека с удалённой работой дешёвая страна может быть отличным фильтром. Для семьи, пенсионера или человека с регулярным лечением дешёвый вариант иногда становится дорогим именно из-за слабой инфраструктуры.</p></section>
  <section id="faq" class="cc-country"><h2>FAQ</h2><div class="faq-item"><h3>Какая страна Азии самая дешёвая для жизни?</h3><p>Чаще всего самый дешёвый старт даёт Камбоджа, но всё зависит от города, жилья, визового сценария и уровня комфорта.</p></div><div class="faq-item"><h3>Можно ли жить в Азии на $600 в месяц?</h3><p>Можно, но это ультрабюджетный сценарий для одного человека. В нём мало запаса на медицину, перелёты, плохое жильё или визовые расходы.</p></div><div class="faq-item"><h3>Какая страна лучше по балансу цены и качества?</h3><p>Для многих сильнее выглядят Вьетнам, Таиланд и Малайзия. Они не всегда самые дешёвые, зато дают больше инфраструктуры.</p></div><div class="faq-item"><h3>Бали входит в список дешёвых стран?</h3><p>Да, но с оговоркой. Бали может быть доступным вне дорогих районов, но популярный образ жизни быстро делает его заметно дороже.</p></div><div class="faq-item"><h3>Что проверить перед выбором?</h3><p>Визу, срок пребывания, продление, страховку, медицину, район, интернет, депозит и бюджет первого месяца.</p></div></section>
</div>
"""
    return title, content


def localized_compare_pair_content(slug: str, title: str, content: str) -> tuple[str, str]:
    content = localized_generic_content(content)
    common = [
        ("Updated March 2026 · Side-by-Side Comparison", "Обновлено в марте 2026 · подробное сравнение"),
        ("Side-by-Side Comparison", "подробное сравнение"),
        ("Digital Nomad Guide", "гайд для digital nomads"),
        ("Complete Comparison", "подробное сравнение"),
        ("for Expats 2026", "для релокации в 2026 году"),
        ("Which Is Better for Expats?", "что лучше для релокации?"),
        ("Two iconic expat destinations go head-to-head — compared across cost, visas, lifestyle, nomad scene, and long-term livability.", "Два популярных expat-направления рядом: расходы, визы, lifestyle, nomad-среда и долгосрочная практичность."),
        ("Two of Southeast Asia’s top relocation destinations — compared across cost, visas, lifestyle, healthcare, and more. Which is right for you?", "Два сильных направления Юго-Восточной Азии — по расходам, визам, быту, медицине и практичности."),
        ("Two of Southeast Asia&#8217;s top relocation destinations — compared across cost, visas, lifestyle, healthcare, and more. Which is right for you?", "Два сильных направления Юго-Восточной Азии — по расходам, визам, быту, медицине и практичности."),
        ("Quick Verdict", "Короткий вывод"),
        ("Quick Comparison", "Быстрое сравнение"),
        ("Category", "Категория"),
        ("Cheaper", "Дешевле"),
        ("More options", "Больше вариантов"),
        ("Moderate (complex)", "Средняя сложность"),
        ("World #1", "№1 в мире"),
        ("Top 5 globally", "топ-5 в мире"),
        ("Unmatched", "Очень сильный"),
        ("Good", "Хорошо"),
        ("Beautiful", "Красиво"),
        ("More variety", "Больше выбора"),
        ("Limited outside Denpasar", "ограничено вне Денпасара"),
        ("World-class", "Мировой уровень"),
        ("Cost of Living", "Стоимость жизни"),
        ("Visa Options", "Визовые маршруты"),
        ("Visas & Residency", "Визы и проживание"),
        ("Visas &amp; Residency", "Визы и проживание"),
        ("Digital Nomad Scene", "Digital nomad среда"),
        ("Lifestyle & Vibe", "Lifestyle и атмосфера"),
        ("Lifestyle &amp; Vibe", "Lifestyle и атмосфера"),
        ("Internet & Infrastructure", "Интернет и инфраструктура"),
        ("Internet &amp; Infrastructure", "Интернет и инфраструктура"),
        ("Long-Term Living", "Долгое проживание"),
        ("Lifestyle & Culture", "Lifestyle и культура"),
        ("Lifestyle &amp; Culture", "Lifestyle и культура"),
        ("Internet & Remote Work", "Интернет и удалённая работа"),
        ("Internet &amp; Remote Work", "Интернет и удалённая работа"),
        ("Safety & Crime", "Безопасность и преступность"),
        ("Safety &amp; Crime", "Безопасность и преступность"),
        ("Language & English", "Язык и английский"),
        ("Language &amp; English", "Язык и английский"),
        ("Family & Schools", "Семья и школы"),
        ("Family &amp; Schools", "Семья и школы"),
        ("Climate & Weather", "Климат и погода"),
        ("Climate &amp; Weather", "Климат и погода"),
        ("Quality of Life", "Качество жизни"),
        ("Healthcare", "Медицина"),
        ("Safety", "Безопасность"),
        ("Internet", "Интернет"),
        ("English Level", "Английский язык"),
        ("Best For", "Кому подходит"),
        ("Pros", "Плюсы"),
        ("Cons", "Минусы"),
        ("Winner", "Сильнее"),
        ("Monthly Budget", "Месячный бюджет"),
        ("Rent", "Аренда"),
        ("Food", "Еда"),
        ("Transport", "Транспорт"),
        ("Coworking", "Коворкинг"),
        ("Entertainment", "Досуг"),
        ("Total", "Итого"),
        ("Which is cheaper?", "Где дешевле?"),
        ("Which has better visas?", "Где сильнее визовые маршруты?"),
        ("Which is better for families?", "Что лучше для семьи?"),
        ("Which is better for digital nomads?", "Что лучше для digital nomads?"),
        ("Frequently Asked Questions", "FAQ"),
        ("Final Verdict", "Итог"),
        ("Compare Countries", "Сравнить страны"),
        ("Cost Calculator", "Калькулятор стоимости жизни"),
        ("Explore Next", "Что открыть дальше"),
        ("Read the full guide", "Открыть полный гид"),
        (">Thailand<", ">Таиланд<"),
        (">Malaysia<", ">Малайзия<"),
        (">Bali<", ">Бали<"),
        (">Indonesia<", ">Индонезия<"),
        ("Thailand vs Malaysia", "Таиланд vs Малайзия"),
        ("Bali vs Thailand", "Бали vs Таиланд"),
    ]
    pair_specific = {
        "bali-vs-thailand": [
            ("Bali vs Thailand for Expats 2026", "Бали или Таиланд для релокации в 2026 году"),
            ("Bali vs Таиланд 2026: what лучше для релокации?", "Бали или Таиланд в 2026 году: что лучше для релокации?"),
            ("Bali vs Таиланд 2026: Which Is Better for Expats?", "Бали или Таиланд в 2026 году: что лучше для релокации?"),
            ("Two of Southeast Asia’s top relocation destinations — compared across cost, visas, lifestyle, healthcare, and more. Which is right for you?", "Два популярных направления Юго-Восточной Азии — по расходам, визам, быту, медицине и реальным компромиссам."),
            ("Bali wins on lifestyle, community, and creative energy.", "Бали сильнее по lifestyle, сообществу и творческой среде."),
            ("Thailand wins on infrastructure, healthcare, city choice, and long-term stability.", "Таиланд сильнее по инфраструктуре, медицине, выбору городов и долгосрочной устойчивости."),
        ],
        "thailand-vs-malaysia": [
            ("Thailand vs Malaysia for Expats 2026", "Таиланд или Малайзия для релокации в 2026 году"),
            ("Таиланд vs Малайзия для релокации в 2026 году", "Таиланд или Малайзия для релокации в 2026 году"),
            ("Two of Southeast Asia’s top relocation destinations — compared across cost, visas, lifestyle, healthcare, and more. Which is right for you?", "Два сильных направления Юго-Восточной Азии — по расходам, визам, городскому комфорту, медицине и семейной практичности."),
            ("Thailand wins on lifestyle, tourism infrastructure, food, and city variety.", "Таиланд сильнее по lifestyle, туристической инфраструктуре, еде и выбору городов."),
            ("Malaysia wins on English, urban comfort, family logistics, and long-term predictability.", "Малайзия сильнее по английскому языку, городскому комфорту, семейной логистике и предсказуемости."),
        ],
    }
    content = replace_many(content, common)
    content = replace_many(content, pair_specific.get(slug, []))
    content = _localize_internal_links(content, lang="ru")
    return title, content


def normalize_ru_compare_content(content: str) -> str:
    replacements = [
        ("Все Сравнения На Русском", "Все сравнения на русском"),
        ("Все Сравнения", "Все сравнения"),
        ("Переезд На Бали", "Переезд на Бали"),
        ("Переезд В Таиланд", "Переезд в Таиланд"),
        ("Переезд В Малайзию", "Переезд в Малайзию"),
        ("Переезд Во Вьетнам", "Переезд во Вьетнам"),
        ("Гайд По Визам Азии", "Гайд по визам Азии"),
        ("Сравнить Страны", "Сравнить страны"),
        ("Калькулятор Стоимости Жизни", "Калькулятор стоимости жизни"),
        ("Планировщик Бюджета", "Планировщик бюджета"),
    ]
    return replace_many(content, replacements)


RU_STATIC_TITLES = {
    "__home__": "Переезд в Азию: страны, расходы и визы",
    "tools": "Бесплатные инструменты для релокации в Азию",
    "cost-calculator": "Калькулятор стоимости жизни в Азии — 2026",
    "budget-planner": "Планировщик бюджета на переезд в Азию — 2026",
    "visas": "Гид по визам Азии в 2026 году: long-stay, digital nomad и пенсия",
    "countries": "Страны Азии для релокации",
    "guides": "Гайды по релокации в Азию: визы, бюджет и выбор страны",
    "compare-cities": "Сравнение городов Азии для релокации",
    "best-countries-in-asia-to-move": "Лучшие страны Азии для переезда в 2026 году",
    "cheapest-countries-in-asia": "Самые дешёвые страны Азии для жизни в 2026 году",
    "move-to-asia": "Переезд в Азию в 2026 году: с чего начать",
    "digital-nomad-visas-asia": "Digital Nomad визы в Азии в 2026 году",
    "retire-in-asia": "Пенсия в Азии в 2026 году: визы, расходы и практичность",
    "cost-of-living-asia": "Стоимость жизни в Азии в 2026 году",
    "about": "О проекте Relocate to Asia",
    "editorial-policy": "Редакционная политика",
    "how-we-verify-data": "Как мы проверяем данные",
}


COUNTRY_FORMS_RU = {
    "move-to-thailand": ("Таиланд", "Таиланд", "Таиланде"),
    "move-to-malaysia": ("Малайзия", "Малайзию", "Малайзии"),
    "move-to-bali": ("Бали", "Бали", "Бали"),
    "move-to-vietnam": ("Вьетнам", "Вьетнам", "Вьетнаме"),
    "move-to-taiwan": ("Тайвань", "Тайвань", "Тайване"),
    "move-to-japan": ("Япония", "Японию", "Японии"),
    "move-to-china": ("Китай", "Китай", "Китае"),
    "move-to-singapore": ("Сингапур", "Сингапур", "Сингапуре"),
    "move-to-south-korea": ("Южная Корея", "Южную Корею", "Южной Корее"),
    "move-to-philippines": ("Филиппины", "Филиппины", "Филиппинах"),
    "move-to-uae": ("ОАЭ", "ОАЭ", "ОАЭ"),
    "move-to-cambodia": ("Камбоджа", "Камбоджу", "Камбодже"),
    "move-to-sri-lanka": ("Шри-Ланка", "Шри-Ланку", "Шри-Ланке"),
    "move-to-india": ("Индия", "Индию", "Индии"),
    "move-to-nepal": ("Непал", "Непал", "Непале"),
    "move-to-laos": ("Лаос", "Лаос", "Лаосе"),
    "move-to-kazakhstan": ("Казахстан", "Казахстан", "Казахстане"),
    "move-to-brunei": ("Бруней", "Бруней", "Брунее"),
    "move-to-myanmar": ("Мьянма", "Мьянму", "Мьянме"),
    "move-to-uzbekistan": ("Узбекистан", "Узбекистан", "Узбекистане"),
}

COUNTRY_EN_NAMES = {
    "move-to-thailand": "Thailand",
    "move-to-malaysia": "Malaysia",
    "move-to-bali": "Bali",
    "move-to-vietnam": "Vietnam",
    "move-to-taiwan": "Taiwan",
    "move-to-japan": "Japan",
    "move-to-china": "China",
    "move-to-singapore": "Singapore",
    "move-to-south-korea": "South Korea",
    "move-to-philippines": "Philippines",
    "move-to-uae": "UAE",
    "move-to-cambodia": "Cambodia",
    "move-to-sri-lanka": "Sri Lanka",
    "move-to-india": "India",
    "move-to-nepal": "Nepal",
    "move-to-laos": "Laos",
    "move-to-kazakhstan": "Kazakhstan",
    "move-to-brunei": "Brunei",
    "move-to-myanmar": "Myanmar",
    "move-to-uzbekistan": "Uzbekistan",
}


RU_GUIDE_TITLES = {
    "can-you-extend-japan-digital-nomad-visa": "Можно ли продлить визу digital nomad в Японии в 2026 году?",
    "japan-digital-nomad-visa-income-requirement": "Требование к доходу для Japan Digital Nomad Visa в 2026 году",
    "thailand-dtv-vs-ltr-visa": "Thailand DTV vs LTR Visa: какой маршрут лучше подходит в 2026 году",
    "malaysia-de-rantau-vs-thailand-dtv": "DE Rantau или Thailand DTV: что лучше для удалённой работы в 2026 году",
    "taiwan-gold-card-income-requirement": "Требование к доходу для Taiwan Gold Card в 2026 году",
    "best-asian-countries-with-easy-long-stay-visas": "В каких странах Азии проще long-stay виза в 2026 году",
    "where-to-live-in-asia-on-1500-a-month": "Где жить в Азии на $1500 в месяц в 2026 году",
    "best-asian-countries-for-remote-workers-with-family": "Лучшие страны Азии для удалёнщиков с семьёй в 2026 году",
    "philippines-srrv-vs-thailand-retirement-visa": "Philippines SRRV или пенсионная виза Таиланда: что выбрать в 2026 году",
    "vietnam-evisa-vs-thailand-dtv": "Vietnam eVisa или Thailand DTV: что выбрать в 2026 году",
}

def ru_country_display(slug: str) -> str:
    forms = COUNTRY_FORMS_RU.get(slug)
    return forms[0] if forms else COUNTRY_EN_NAMES.get(slug, slug.replace("move-to-", "").replace("-", " ").title())


def ru_country_accusative(slug: str) -> str:
    forms = COUNTRY_FORMS_RU.get(slug)
    return forms[1] if forms else ru_country_display(slug)


def ru_country_prep(slug: str) -> str:
    forms = COUNTRY_FORMS_RU.get(slug)
    return forms[2] if forms else ru_country_display(slug)


def compact_number(value) -> str:
    if value is None:
        return "нет данных"
    try:
        value = float(value)
    except (TypeError, ValueError):
        return str(value)
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f} млн".replace(".0", "")
    if value >= 1_000:
        return f"{value / 1_000:.0f} тыс."
    return f"{value:.0f}"


RU_COUNTRY_NOTES = {
    "move-to-thailand": ("Таиланд часто выбирают за быт, еду, медицину и выбор городов.", "Главный риск — не путать комфортный lifestyle с подходящим визовым маршрутом."),
    "move-to-malaysia": ("Малайзия сильна английским языком, инфраструктурой и понятной городской жизнью.", "Главный риск — заранее проверить конкретный long-stay маршрут и требования к доходу."),
    "move-to-bali": ("Бали подходит тем, кому важны сообщество, климат и гибкий ритм жизни.", "Главный риск — визовая логика Индонезии и зависимость качества жизни от района."),
    "move-to-vietnam": ("Вьетнам часто выигрывает по бюджету, еде и городскому темпу.", "Главный риск — не строить long-stay план только на туристической eVisa."),
    "move-to-taiwan": ("Тайвань силён безопасностью, медициной, интернетом и профессиональной средой.", "Главный риск — Gold Card и другие маршруты требуют реального соответствия профилю."),
    "move-to-japan": ("Япония даёт безопасность, транспорт и очень высокий бытовой стандарт.", "Главный риск — высокая стоимость жизни и более жёсткая визовая логика."),
    "move-to-south-korea": ("Южная Корея подходит тем, кому важны города, интернет и современная инфраструктура.", "Главный риск — требования к доходу, работе и документам могут быть строже, чем кажется."),
    "move-to-singapore": ("Сингапур силён как профессиональный и финансовый хаб.", "Главный риск — высокий бюджет и конкуренция за рабочие маршруты."),
    "move-to-philippines": ("Филиппины часто рассматривают из-за английского языка, островного быта и пенсионных маршрутов.", "Главный риск — качество инфраструктуры сильно зависит от города и района."),
    "move-to-cambodia": ("Камбоджа может быть бюджетной базой с мягким повседневным входом.", "Главный риск — медицина, инфраструктура и правовая стабильность важнее низкой аренды."),
    "move-to-sri-lanka": ("Шри-Ланка интересна природой, стоимостью жизни и спокойным ритмом.", "Главный риск — экономическая и визовая устойчивость должна проверяться перед планом."),
    "move-to-china": ("Китай подходит тем, кому важен большой рынок и крупные города.", "Главный риск — язык, цифровая среда и визовая логика требуют подготовки."),
    "move-to-uae": ("ОАЭ подходят для высокого дохода, налоговой логики и международной среды.", "Главный риск — бюджет, страховка и зависимость от статуса резидентства."),
}


def ru_country_article(slug: str, facts: sqlite3.Row | None) -> str:
    country = ru_country_display(slug)
    acc = ru_country_accusative(slug)
    capital = facts["capital"] if facts and facts["capital"] else "главный город"
    currency = facts["currency_code"] if facts and facts["currency_code"] else "местная валюта"
    languages = facts["languages"] if facts and facts["languages"] else "местные языки"
    population = compact_number(facts["population"] if facts else None)
    internet = f"{facts['internet_pct']:.1f}%" if facts and facts["internet_pct"] is not None else "нет данных"
    life = f"{facts['life_expectancy']:.1f} года" if facts and facts["life_expectancy"] is not None else "нет данных"
    year = facts["wb_year"] if facts and facts["wb_year"] else "последние доступные данные"
    note, risk = RU_COUNTRY_NOTES.get(
        slug,
        (
            f"{country} может быть рабочим направлением, если совпадают виза, бюджет и бытовая среда.",
            "Главный риск — выбирать страну по впечатлению, не проверив легальный срок stay, медицину и расходы.",
        ),
    )
    return f"""
<section class="rta-article">
  <div class="rta-hero-card">
    <span class="rta-pill">Гид по стране 2026</span>
    <h1>Переезд в {html.escape(acc)}: визы, расходы и реальная логика выбора</h1>
    <p>{html.escape(note)} Но решение лучше начинать не с картинки в голове, а с трёх вещей: легальный срок проживания, месячный бюджет и город, в котором вы реально сможете жить.</p>
  </div>
  <div class="rta-note"><strong>Короткий вывод:</strong> {html.escape(acc)} стоит держать в shortlist только если визовый маршрут совпадает с вашим доходом, сроком stay и семейной ситуацией. {html.escape(risk)}</div>
  <h2>Что проверить в первую очередь</h2>
  <p>Сначала проверьте право находиться в стране. Потом уже жильё, районы, кафе и пляжи. Это скучный порядок, зато он экономит деньги. Если виза подходит только для короткого stay, не стоит строить вокруг неё план долгой релокации.</p>
  <p>Второй фильтр — бюджет. Низкая аренда не означает дешёвый переезд: к ней добавляются страховка, депозиты, перелёты, визовые сборы, техника, школа для детей и запас на первые месяцы.</p>
  <h2>Факты о стране</h2>
  <div class="rta-fact-grid">
    <div><strong>Столица</strong><span>{html.escape(capital)}</span></div>
    <div><strong>Валюта</strong><span>{html.escape(currency)}</span></div>
    <div><strong>Языки</strong><span>{html.escape(languages)}</span></div>
    <div><strong>Население</strong><span>{population}</span></div>
    <div><strong>Интернет</strong><span>{internet}</span></div>
    <div><strong>Ожидаемая продолжительность жизни</strong><span>{life}</span></div>
  </div>
  <p class="rta-muted">Числа по населению, интернету и макропоказателям взяты из последнего доступного набора World Bank в базе сайта. Год данных: {html.escape(str(year))}.</p>
  <h2>Кому подойдёт {html.escape(country)}</h2>
  <p>{html.escape(country)} логичнее рассматривать тем, кто заранее понимает свой источник дохода, срок проживания и уровень бытового комфорта. Для solo remote worker решение обычно проще. Для семьи важнее dependants, школы, медицина и стабильность аренды.</p>
  <h2>Кому лучше быть осторожнее</h2>
  <p>Если вы ищете путь к постоянной резиденции, не путайте long-stay удобство с иммиграционной стратегией. Если бюджет плотный, закладывайте не только аренду, но и выход из страны, продление, страховку и emergency fund.</p>
  <h2>Следующий шаг</h2>
  <p>Сравните страну с соседними направлениями, затем откройте визовый гид и калькулятор стоимости жизни. Хороший выбор страны — это не самая красивая карточка, а совпадение правил, денег и повседневной реальности.</p>
</section>
"""


def ru_hub_content(slug: str) -> str | None:
    hubs = {
        "__home__": ("Переезд в Азию: страны, визы и расходы", "Главная задача сайта — помочь выбрать страну не по красивой картинке, а по реальным ограничениям: визе, бюджету, медицине, городу и сроку проживания.", [("Страны", "Сначала сузьте shortlist по бюджету и визовой логике."), ("Визы", "Проверьте stay, продление, доход и dependants до аренды."), ("Инструменты", "Посчитайте месячный бюджет и стартовые расходы до переезда.")]),
        "countries": ("Страны Азии для релокации", "Эта страница нужна не для вдохновения, а для первого отбора. Сравнивайте страны по визе, бюджету, медицине, интернету и тому, насколько городская жизнь совпадает с вашим сценарием.", [("Таиланд", "Сильный lifestyle и медицина, но визовый маршрут надо выбирать аккуратно."), ("Малайзия", "Английский, инфраструктура и понятные города для long-stay сценариев."), ("Вьетнам", "Сильный бюджетный вариант, но long-stay логику нельзя оставлять на потом.")]),
        "tools": ("Инструменты для планирования переезда в Азию", "Инструменты помогают быстро проверить грубые цифры: месячный бюджет, стартовые расходы и сравнение стран. Это не финальный ответ, но хороший фильтр до платных решений.", [("Калькулятор стоимости жизни", "Прикиньте месячные расходы по стране и стилю жизни."), ("Планировщик бюджета", "Сложите перелёты, визы, депозиты, первый месяц и emergency fund."), ("Сравнение стран", "Поставьте две страны рядом и проверьте, где сильнее компромиссы.")]),
        "guides": ("Гайды по релокации в Азию", "Здесь собраны короткие страницы под конкретные вопросы: продление визы, доход, семейный переезд, пенсионные маршруты и бюджет. Это слой между длинной статьёй и быстрым ответом.", [("Визовые вопросы", "Разбирайте срок stay, продление, доход и dependants до выбора города."), ("Бюджет", "Смотрите полный сценарий, а не только аренду."), ("Семья и пенсия", "Медицина, школы, страховка и банковская логика важнее красивого района.")]),
        "move-to-asia": ("Переезд в Азию в 2026 году: с чего начать", "Азия — не один рынок релокации. Япония, Таиланд, Малайзия, Тайвань, Вьетнам и ОАЭ решают разные задачи. Нельзя выбрать страну только по цене аренды или красивому lifestyle.", [("Сначала виза", "Проверьте срок stay, продление, доход, dependants и право на удалённую или местную работу."), ("Потом бюджет", "Считайте не только месяц жизни, но и перелёт, депозит, страховку, визы и финансовую подушку."), ("Потом город", "Одна и та же страна может быть дешёвой в одном городе и неудобной в другом.")]),
        "digital-nomad-visas-asia": ("Digital Nomad визы в Азии в 2026 году", "Digital nomad виза полезна только тогда, когда она совпадает с тем, как вы зарабатываете. Одни маршруты короткие, другие требуют сильного профиля, третьи ближе к профессиональным talent-pass программам.", [("Japan Digital Nomad Visa", "Короткий stay до 6 месяцев. Хорошо для временной базы, плохо для долгой релокации."), ("Taiwan Gold Card", "Профессиональный маршрут с work permit и residence логикой."), ("Thailand LTR / DTV", "Сначала сравните профиль, доход и цель stay. Это разные инструменты, а не две версии одной визы.")]),
        "retire-in-asia": ("Пенсия в Азии в 2026 году: визы, расходы и медицина", "Пенсионная релокация отличается от remote-work переезда. Здесь важнее медицина, страховка, банковская логика, валюта, dependants и стабильность long-stay маршрута. Ошибка обычно начинается там, где страну выбирают по пляжу или аренде, а депозит, больницы, страховое покрытие и срок статуса проверяют уже после решения. Для пенсионного сценария особенно важно считать не самый дешёвый месяц, а спокойный год: продление, лечение, перелёты домой, помощь на месте и запас на валютные колебания.", [("Philippines SRRV", "Пенсионный маршрут с депозитом и логикой indefinite stay. Подходит не всем, но его стоит сравнить."), ("Малайзия", "Сильна английским, городами и медициной. Важно проверять актуальные условия MM2H."), ("Таиланд", "Сильный lifestyle и медицина в крупных городах, но визовый маршрут нужно проверять отдельно.")]),
        "cost-of-living-asia": ("Стоимость жизни в Азии в 2026 году", "Дешёвая страна не всегда подходит для переезда. Низкая аренда может идти вместе со слабой визовой логикой, дорогой медициной или городом, который не подходит под работу и семью.", [("Считайте полный месяц", "Аренда, еда, транспорт, связь, страховка, coworking, медицина и непредвиденные расходы."), ("Отделяйте старт от жизни", "Депозит, перелёты, визы и первый месяц часто ломают красивый бюджет."), ("Сравнивайте города", "Бангкок и Чиангмай, Куала-Лумпур и Пенанг, Бали и Джакарта — это разные бюджеты.")]),
        "visas": ("Визы Азии в 2026 году: long-stay, digital nomad и пенсионные маршруты", "Страну лучше выбирать после проверки визы. Иначе можно влюбиться в направление, которое не совпадает с вашим доходом, сроком stay, семьёй или типом работы.", [("Удалённая работа", "Проверяйте, разрешена ли удалённая работа и где должен находиться работодатель."), ("Долгое проживание", "Смотрите срок, продление, доход, депозиты и dependants."), ("Пенсионный сценарий", "Медицина и стабильность часто важнее минимальной стоимости жизни.")]),
        "best-countries-in-asia-to-move": ("Лучшие страны Азии для переезда в 2026 году", "Лучшей страны для всех нет. Есть страна, которая совпадает с вашим бюджетом, визой, работой, семьёй и терпимостью к бытовым компромиссам.", [("Таиланд", "Сильный lifestyle, медицина и выбор городов. Визовый маршрут нужно подбирать аккуратно."), ("Малайзия", "Хороший английский, инфраструктура и long-stay логика для части профилей."), ("Тайвань", "Сильная безопасность, медицина и профессиональные маршруты.")]),
        "cheapest-countries-in-asia": ("Самые дешёвые страны Азии для жизни в 2026 году", "Дешевизна полезна только тогда, когда не ломает визу, медицину, интернет и качество жилья. Бюджет нужно считать вместе с рисками.", [("Вьетнам", "Часто силён по повседневным расходам, но long-stay логику нужно проверять отдельно."), ("Камбоджа", "Может быть бюджетной, но медицина и инфраструктура требуют осторожности."), ("Бали / Индонезия", "Бюджет зависит от района и lifestyle. Визовый маршрут нельзя оставлять на потом.")]),
    }
    data = hubs.get(slug)
    if not data:
        return None
    title, intro, cards = data
    card_html = "\n".join(f'<div class="rta-linkhub-card"><h3>{html.escape(card_title)}</h3><p>{html.escape(text)}</p></div>' for card_title, text in cards)
    default_copy = (
        "Смотрите на страницу как на первый фильтр, а не как на готовый ответ. Если визовый маршрут, бюджет и срок проживания не сходятся, красивое направление лучше убрать из shortlist до оплаты жилья и билетов.",
        "Как принимать решение",
        "Сначала проверьте легальный маршрут. Потом посчитайте полный бюджет: стартовые расходы, месячную жизнь, страховку, депозиты и emergency fund. Только после этого сравнивайте города, районы и бытовые компромиссы.",
        "Если маршрут не подходит по документам, лучше узнать это сразу. Хорошая страна с неподходящей визой всё равно не становится хорошим планом.",
        "Что открыть дальше",
        "Откройте страновые страницы, визовый гид, сравнение стран и калькулятор стоимости жизни. Они работают вместе: одна страница показывает правила, другая деньги, третья бытовые ограничения.",
    )
    hub_copy = {
        "__home__": (
            "Главная страница должна быстро сузить выбор. Не до одной страны навсегда, а до нормального списка из 2-3 направлений, которые выдерживают проверку по визе, бюджету, медицине и сроку жизни.",
            "Как двигаться по сайту",
            "Начните со стран, если вы ещё выбираете регион. Если уже есть 2 варианта, идите в сравнение. Если вопрос упирается в деньги, сначала откройте калькулятор и посчитайте не только аренду, но и первый месяц.",
            "Переезд в Азию редко ломается из-за одного фактора. Чаще проблема в связке: виза короткая, город дороже ожиданий, страховка не включена, а запас денег слишком тонкий.",
            "Следующий шаг",
            "Соберите короткий маршрут: страна → виза → бюджет → город. Если на одном шаге всё рассыпается, лучше сменить направление до того, как появятся платные обязательства.",
        ),
        "countries": (
            "Страны здесь не ранжируются как туристические места. Смысл другой: понять, где ваш доход, срок stay, семья и бытовые ожидания вообще совпадают с реальностью.",
            "Как выбирать страну",
            "Сначала уберите направления, где нет понятного legal stay. Потом сравните ежемесячный бюджет, медицину, интернет, язык, городскую инфраструктуру и стоимость первого месяца.",
            "Не выбирайте страну только потому, что она дешёвая или популярная у nomads. Дешевизна быстро теряет смысл, если виза короткая, медицина слабая или город не подходит под работу.",
            "Что открыть дальше",
            "Откройте 2-3 страновые страницы и сравните их попарно. Так проще увидеть не абстрактные плюсы, а реальные trade-offs.",
        ),
        "visas": (
            "Визовая страница — это не каталог красивых названий. Здесь главный вопрос жёстче: какой маршрут легально выдерживает ваш доход, работу, семью и желаемый срок проживания.",
            "Как читать визовые варианты",
            "Смотрите срок, продление, требования к доходу, страховку, dependants, разрешённую деятельность и работодателя. Если правило не подтверждено официально, не стройте на нём план.",
            "Самая дорогая ошибка — сначала выбрать страну, а потом пытаться подогнать под неё документы. Работает наоборот: сначала маршрут, потом страна и город.",
            "Что открыть дальше",
            "После визового обзора переходите к конкретному гайду или сравнению маршрутов. В вопросах виз, денег и медицины общие впечатления не заменяют официальный источник.",
        ),
        "tools": (
            "Инструменты нужны не для красивой точности до доллара. Их задача — быстро показать, где сценарий живой, а где бюджет держится только на идеальных условиях.",
            "Как использовать расчёты",
            "Считайте отдельно старт переезда и обычный месяц. Депозит, перелёты, страховка, визовые сборы и emergency fund часто важнее, чем разница в аренде на 100 долларов.",
            "Если результат выглядит комфортно только без запаса, это слабый план. Лучше увидеть это в калькуляторе, чем после подписания договора аренды.",
            "Что открыть дальше",
            "После расчёта откройте страну и визу. Цифра сама по себе ничего не решает, если legal stay не совпадает с вашим профилем.",
        ),
        "guides": (
            "Гайды отвечают на узкие вопросы: можно ли продлить визу, хватает ли дохода, какой маршрут меньше конфликтует с вашим профилем. Это не вдохновение, а проверка слабого места.",
            "Как читать гайд",
            "Сначала найдите ограничение: срок, доход, работодатель, семья, страховка, возраст или продление. Именно оно обычно решает, стоит ли продолжать.",
            "Если источник не обещает исключение, его нельзя считать доступным. Для визовых решений осторожная формулировка лучше, чем уверенный, но неподтверждённый совет.",
            "Что открыть дальше",
            "После гайда сравните альтернативный маршрут. Часто правильный ответ находится не внутри одной визы, а в сравнении двух похожих вариантов.",
        ),
        "retire-in-asia": (
            "Пенсионная релокация отличается от nomad-сценария. Тут важнее медицина, стабильность статуса, депозиты, dependants, валюта расходов и возможность жить спокойно несколько лет.",
            "Как оценивать retirement route",
            "Начинайте с визы и медицинского доступа. Потом считайте депозит, страховку, регулярный доход, город, близость больниц и бытовую поддержку на месте.",
            "Низкая стоимость жизни помогает, но не заменяет healthcare и понятный статус. Для пенсионного сценария дешёвая страна с хрупкой инфраструктурой может оказаться плохой экономией.",
            "Что открыть дальше",
            "Сравните пенсионные маршруты Филиппин, Таиланда и Малайзии, затем проверьте город и медицинскую инфраструктуру.",
        ),
        "digital-nomad-visas-asia": (
            "Digital nomad visa звучит просто, но правила у стран разные. Где-то важен иностранный работодатель, где-то доход, где-то срок короткий и не похож на релокацию.",
            "Как сравнивать nomad-визы",
            "Проверьте не только сумму дохода. Важно, откуда деньги, где зарегистрирован работодатель, можно ли брать семью, сколько длится stay и что написано про продление.",
            "Не называйте любую удобную туристическую визу digital nomad route. Если удалённая работа не разрешена или не описана, риск остаётся на заявителе.",
            "Что открыть дальше",
            "Откройте конкретные статьи по Японии, Малайзии, Таиланду, Корее, Индонезии и Тайваню. Там лучше видны ограничения, чем в общей таблице.",
        ),
        "cost-of-living-asia": (
            "Стоимость жизни — это не одна цифра. Для переезда важнее диапазон: базовый месяц, комфортный месяц, первый месяц и запас на ошибку.",
            "Как считать бюджет",
            "Разделите аренду, депозит, еду, транспорт, страховку, связь, коворкинг, визовые сборы и перелёты. Когда всё в одной строке, слабые места не видны.",
            "Дешёвый город может стать дорогим, если нужен частый выезд, частная медицина, международная школа или жильё в конкретном районе.",
            "Что открыть дальше",
            "После общей страницы используйте калькулятор, а затем откройте страну. Бюджет без визового маршрута — только половина ответа.",
        ),
        "best-countries-in-asia-to-move": (
            "Лучшие страны — это не универсальный рейтинг. Для одного человека выигрывает Таиланд, для другого Малайзия, для третьего Тайвань или Япония. Всё решает профиль.",
            "Как читать рейтинг",
            "Смотрите не только место в списке, а причину. Страна может быть сильной по медицине, но слабой по бюджету. Или дешёвой, но неудобной по долгому статусу.",
            "Если страна не совпадает с вашим доходом, сроком stay или семейной логистикой, её лучше не спасать красивыми плюсами.",
            "Что открыть дальше",
            "Выберите 2-3 страны из рейтинга и сравните их напрямую. Так быстрее видно, где плюс действительно важен, а где просто приятно звучит.",
        ),
        "cheapest-countries-in-asia": (
            "Дешёвые страны полезны только тогда, когда экономия не покупается за счёт визовой неопределённости, слабой медицины или плохой инфраструктуры.",
            "Как читать бюджетный список",
            "Смотрите не минимальную аренду, а реалистичный месяц: нормальный район, интернет, страховка, транспорт, еда, запас и стоимость визового ритма.",
            "Если страна дешёвая только при очень аскетичном сценарии, это не обязательно хороший вариант для семьи, пенсионера или человека с медицинскими требованиями.",
            "Что открыть дальше",
            "После списка откройте калькулятор и сравнение стран. Бюджетный shortlist должен выдерживать не только цену, но и legal stay.",
        ),
        "move-to-asia": (
            "Переезд в Азию лучше начинать не с выбора страны мечты, а с отсечения вариантов, которые не выдерживают документы, деньги или срок.",
            "Как начать без хаоса",
            "Сначала определите профиль: remote worker, семья, пенсионер, предприниматель, high-income specialist или человек с ограниченным бюджетом. Потом подберите 2-3 маршрута, а не 15 стран сразу.",
            "Если вы не можете объяснить, на какой визе будете жить через 6-12 месяцев, план ещё сырой. Это нормально. Лучше доработать его до аренды и перелётов.",
            "Что открыть дальше",
            "Начните со странового хаба, затем визы и бюджет. После этого уже имеет смысл выбирать город и район.",
        ),
    }.get(slug, default_copy)
    summary, decision_title, decision_one, decision_two, next_title, next_text = hub_copy
    return f"""
<section class="rta-article">
  <div class="rta-hero-card">
    <span class="rta-pill">Гид 2026</span>
    <h1>{html.escape(title)}</h1>
    <p>{html.escape(intro)}</p>
  </div>
  <h2>Короткий вывод</h2>
  <p>{html.escape(summary)}</p>
  <div class="rta-linkhub-grid">{card_html}</div>
  <h2>{html.escape(decision_title)}</h2>
  <p>{html.escape(decision_one)}</p>
  <p>{html.escape(decision_two)}</p>
  <h2>{html.escape(next_title)}</h2>
  <p>{html.escape(next_text)}</p>
</section>
"""


def ru_thailand_dtv_vs_ltr_article(title: str) -> str:
    return f"""
<article class="guide-page">
  <div class="guide-hero">
    <span class="badge">Обновлено в апреле 2026 · проверено по официальным источникам</span>
    <h1>{html.escape(title)}</h1>
    <p>Thailand DTV и LTR часто ставят рядом, но это не две версии одной визы. DTV больше похожа на гибкий маршрут для повторяющихся stay в Таиланде. LTR — на долгую структуру для людей, которые проходят жёсткий фильтр по доходу, страховке, работодателю, активам или профессиональному статусу.</p>
  </div>

  <div class="guide-note"><strong>Короткий ответ:</strong> если вы удалёнщик, фрилансер или хотите пожить в Таиланде с понятным среднесрочным горизонтом, сначала смотрите DTV. Если вам нужен долгий статус, меньше отчётности, возможный digital work permit и вы реально проходите требования BOI, тогда имеет смысл разбирать LTR. Но LTR не становится “лучше” просто потому, что срок больше. Она становится лучше только тогда, когда ваш профиль под неё подходит.</div>

  <h2>Thailand DTV vs LTR Visa: В Чём Разница На Практике</h2>
  <p>Главная ошибка — сравнивать только срок. На поверхности всё выглядит просто: у DTV срок действия визы 5 лет, у LTR заявлена 10-летняя логика. Но решение не в цифре на обложке. Решение в том, какую жизнь вы пытаетесь легализовать.</p>
  <p>По DTV официальная логика идёт через конкретные цели: workcation, digital nomad, remote worker, foreign talent, freelancer, Thai soft power activities, medical treatment и dependants. На правительственной странице Thailand.go.th прямо указано пребывание до 180 дней с возможностью продления ещё на 180 дней. На отдельной странице о типах DTV также указаны финансовые доказательства не менее 500 000 THB и срок действия 5 лет. Это хороший маршрут, но он не превращает человека в резидента в обычном смысле.</p>
  <p>LTR устроена иначе. BOI описывает Long-Term Resident Visa как программу для high-potential individuals. Категории там другие: Wealthy Global Citizen, Wealthy Pensioner, Work-From-Thailand Professional, Highly Skilled Professional и dependants. На сайте BOI указана 10-летняя renewable visa, но с важной деталью: сначала permission to stay даётся на 5 лет, затем возможны ещё 5 лет, если квалификация сохраняется.</p>

  <h2>Ключевые Факты По DTV И LTR</h2>
  <table class="guide-table">
    <tr><th>Пункт</th><th>DTV</th><th>LTR</th></tr>
    <tr><td>Базовая логика</td><td>Повторяющиеся medium-stay въезды под workcation, soft power, лечение или dependants.</td><td>Долгосрочный статус для профилей, которые проходят BOI-фильтр.</td></tr>
    <tr><td>Срок</td><td>До 180 дней за въезд; Thailand.go.th пишет про опцию продления ещё на 180 дней.</td><td>10-летняя логика, но BOI объясняет схему как 5 лет плюс ещё 5 лет при сохранении условий.</td></tr>
    <tr><td>Финансовый фильтр</td><td>Официальная DTV-страница указывает financial evidence не менее 500 000 THB.</td><td>Для Work-From-Thailand Professionals BOI указывает минимум USD 80 000 в год за последние два года или альтернативный путь при USD 40 000+ и дополнительных доказательствах.</td></tr>
    <tr><td>Работа</td><td>Маршрут подходит для удалённой работы на зарубежного работодателя или клиентов, если это соответствует категории подачи.</td><td>LTR может включать digital work permit для некоторых категорий, но BOI отдельно пишет, что Work-From-Thailand Professionals не получают work permit, потому что работают на иностранного работодателя из Таиланда.</td></tr>
    <tr><td>Семья</td><td>Официальные консульские страницы называют spouse и children under 20 как dependants DTV holder.</td><td>BOI пишет про spouse и children under 20, максимум 4 dependants на одного LTR holder.</td></tr>
    <tr><td>Риск</td><td>Не стоит считать DTV полноценной резидентской стратегией без проверки продления, налогов и повторных въездов.</td><td>Не стоит начинать LTR, если доход, страховка, работодатель или инвестиционные документы слабые.</td></tr>
  </table>

  <h2>Кому Подходит Thailand DTV</h2>
  <p>DTV подходит человеку, который хочет жить в Таиланде не как турист на две недели, но и не строит сразу тяжёлую резидентскую конструкцию. Например: удалённый сотрудник иностранной компании, фрилансер с понятным портфолио, человек на medical treatment, участник soft-power программы или семья, которая идёт как dependants основного держателя DTV.</p>
  <p>Что написано в правилах: DTV привязана к purpose of visit. Консульство в Лос-Анджелесе перечисляет workcation, Thai soft power и spouse/children under 20 of DTV visa holders. Там же в чеклисте есть bank statement с ending balance не менее 500 000 THB или эквивалентом в USD. Практический смысл простой: одной любви к Таиланду мало. Нужны документы, которые объясняют, почему вы попадаете именно в эту категорию.</p>
  <p>Где люди ошибаются: думают, что DTV автоматически закрывает любую удалённую работу, любое обучение, любую семью и любой срок. Нет. Смотрите конкретное консульство, страну подачи и документы. У разных посольств могут быть локальные форматы доказательств, а e-Visa всё равно не отменяет проверку eligibility.</p>

  <h2>Кому Подходит Thailand LTR Visa</h2>
  <p>LTR подходит не “тем, кто серьёзнее”, а тем, чей профиль реально проходит BOI. Это большая разница. Если у вас сильный доход, стабильный зарубежный работодатель, понятная карьера, медицинская страховка или финансовая база, LTR может быть намного спокойнее. Но если профиль пограничный, LTR быстро превращается в длинный список документов без гарантии результата.</p>
  <p>BOI пишет, что Work-From-Thailand Professionals должны быть remote workers working for well-established overseas companies. По доходу на главной странице LTR указан минимум USD 80 000 в год за последние два года. Если доход ниже, но не ниже USD 40 000, нужны дополнительные доказательства, например степень или другие квалификационные документы. Для пенсионеров BOI отдельно подчёркивает passive income. Зарплата или самозанятость для Wealthy Pensioner не читаются как такой доход.</p>
  <p>Практически это значит вот что: LTR не надо начинать с вопроса “нравится ли мне Таиланд?”. Начинать нужно с документов. Налоговые формы, подтверждение дохода, страховое покрытие, работодатель, категория, dependants. Если всё это не собирается в чистую историю, DTV или другой маршрут может быть разумнее.</p>

  <h2>Где DTV Сильнее LTR</h2>
  <p>DTV сильнее там, где нужна гибкость. Она понятнее для людей, которые хотят приехать, пожить, поработать удалённо, протестировать Бангкок, Чиангмай, Пхукет или другой город, но не готовы доказывать профиль уровня BOI. Порог по документам ниже. Логика проще. Но проще не значит “без правил”.</p>
  <p>Если вы не уверены, хотите ли жить в Таиланде несколько лет, DTV может быть честнее. Она не заставляет строить вокруг Таиланда всю биографию. Это нормальный маршрут для проверки страны. Особенно если вы ещё сравниваете Таиланд с Малайзией, Вьетнамом, Тайванем или Филиппинами.</p>

  <h2>Где LTR Сильнее DTV</h2>
  <p>LTR сильнее там, где нужен статус на годы, а не просто возможность регулярно приезжать. У LTR есть набор привилегий: 90-day report заменяется на 1-year report, multiple re-entry, в некоторых категориях digital work permit, а для Highly Skilled Professionals заявлена ставка personal income tax 17%. Это уже не lifestyle-виза. Это иммиграционный продукт с фильтром.</p>
  <p>Но фильтр жёсткий. BOI отдельно пишет, что условия нужно поддерживать во время срока визы. Если пропадает страховка, меняется работодатель, падает инвестиционный критерий или категория больше не совпадает с реальностью, статус может стать проблемой. Поэтому LTR подходит тем, кто не просто проходит требования сегодня, а может поддерживать их дальше.</p>

  <h2>Что Проверить Перед Решением</h2>
  <div class="guide-grid">
    <div class="guide-card"><strong>Доход</strong><p>Для DTV смотрите ликвидные средства и формат банковского подтверждения. Для LTR — годовой доход, налоговые документы и категорию BOI.</p></div>
    <div class="guide-card"><strong>Работодатель</strong><p>Если вы remote worker, важно, где зарегистрирован работодатель и что написано в контракте. Для LTR Work-From-Thailand это особенно критично.</p></div>
    <div class="guide-card"><strong>Срок жизни в Таиланде</strong><p>DTV лучше для гибкого stay. LTR лучше для долгого горизонта, если документы сильные.</p></div>
    <div class="guide-card"><strong>Семья</strong><p>Проверьте spouse, children under 20, лимиты dependants и страховку. Не переносите правила одной визы на другую.</p></div>
  </div>

  <h2>10 Официальных Источников, Которые Стоит Открыть</h2>
  <p>Это не декоративный блок. По этим страницам нужно сверять факты перед подачей, оплатой жилья, билетами и разговором с агентом.</p>
  <ul class="guide-sources">
    <li><a href="https://thailand.go.th/visit-thailand-detail/-destination-thailand-visa-dtv" rel="nofollow noopener" target="_blank">Thailand.go.th: Ministry of Foreign Affairs Launches Destination Thailand Visa</a></li>
    <li><a href="https://thailand.go.th/issue-focus-detail/3---destination-thailand-visa-dtv?hl=en" rel="nofollow noopener" target="_blank">Thailand.go.th: 3 Special Types of Destination Thailand Visa</a></li>
    <li><a href="https://www.thaievisa.go.th/" rel="nofollow noopener" target="_blank">Thailand e-Visa Official Website</a></li>
    <li><a href="https://thaiconsulatela.thaiembassy.org/en/publicservice/dtv-visa%3Fcate%3D61a8019ec0e81b444e7a5b52" rel="nofollow noopener" target="_blank">Royal Thai Consulate-General Los Angeles: Destination Thailand Visa</a></li>
    <li><a href="https://www.thaiembassy.at/en/type-of-visa/destination-thailand-visa-dtv.html" rel="nofollow noopener" target="_blank">Royal Thai Embassy Vienna: Destination Thailand Visa</a></li>
    <li><a href="https://ltr.boi.go.th/" rel="nofollow noopener" target="_blank">Thailand BOI: Long-Term Resident Visa</a></li>
    <li><a href="https://ltr.boi.go.th/page/visa-issuance-info.html" rel="nofollow noopener" target="_blank">BOI LTR Visa Issuance Information</a></li>
    <li><a href="https://ltr.boi.go.th/page/required-documents.html" rel="nofollow noopener" target="_blank">BOI LTR Required Documents Hub</a></li>
    <li><a href="https://ltr.boi.go.th/documents/Required-docs-Work-From-Thailand-Professional-30-06-2025.pdf" rel="nofollow noopener" target="_blank">BOI: Required Documents For Work-From-Thailand Professionals</a></li>
    <li><a href="https://ltr.boi.go.th/documents/Spouses-and-dependents-required-documents.pdf" rel="nofollow noopener" target="_blank">BOI: Required Documents For Spouses And Dependants</a></li>
  </ul>

  <h2>Итог: Что Выбирать</h2>
  <p>Если вы хотите проверить Таиланд, работать удалённо на зарубежный источник дохода и не строить тяжёлую иммиграционную конструкцию, DTV чаще выглядит логичнее. Но она требует аккуратности: purpose of visit, документы, финансы и локальные требования консульства.</p>
  <p>Если у вас сильный доход, понятный работодатель, хорошая страховая и вы хотите long-term структуру, LTR может быть мощнее. Но только если профиль действительно проходит. Иначе вы сравниваете не две визы, а свою мечту о Таиланде с официальным фильтром BOI. Фильтр обычно побеждает.</p>

  <h2>FAQ По Thailand DTV vs LTR Visa</h2>
  <div class="faq-item"><h3>Thailand DTV Лучше Чем LTR Visa?</h3><p>Не всегда. DTV проще и гибче для medium-stay сценария. LTR сильнее для долгого статуса, если вы проходите требования BOI.</p></div>
  <div class="faq-item"><h3>Можно Ли По DTV Жить В Таиланде Как Резидент?</h3><p>Нужно быть осторожным с таким выводом. DTV даёт stay по конкретной визовой логике, но не стоит читать её как полноценный путь к резидентству.</p></div>
  <div class="faq-item"><h3>Кому Реально Подходит LTR Work-From-Thailand?</h3><p>Тем, кто работает на well-established overseas company, может подтвердить доход и собрать документы так, как требует BOI.</p></div>
  <div class="faq-item"><h3>Можно Ли Взять Семью По DTV Или LTR?</h3><p>Да, но правила разные. По DTV консульские страницы говорят о spouse и children under 20. По LTR BOI указывает spouse и children under 20, максимум 4 dependants.</p></div>
  <div class="faq-item"><h3>Что Проверять Первым: Город Или Визу?</h3><p>Визу. Город важен, но он не исправит слабый legal route. Сначала срок, доход, документы, dependants и работа. Потом уже районы, аренда и lifestyle.</p></div>
</article>
"""


def ru_where_to_live_on_1500_article(title: str) -> str:
    return f"""
<article class="guide-page">
  <div class="guide-hero">
    <span class="badge">Бюджет 2026 · Азия без иллюзий</span>
    <h1>{html.escape(title)}</h1>
    <p>$1500 в месяц в Азии могут работать. Но не как универсальный ответ. Один человек в Дананге, Чиангмае или Пенанге — это один сценарий. Семья, Бангкок, острова, частая медицина и квартира “как дома” — уже совсем другой.</p>
  </div>

  <div class="guide-note"><strong>Короткий ответ:</strong> $1500 в месяц реалистичны для аккуратного solo-сценария или очень компактной пары в отдельных городах Азии. Для семьи, премиальных районов, международной школы, частной медицины и частых перелётов это слабый бюджет. Тут решает не страна в целом, а город, район, виза, страховка и то, сколько ошибок вы можете себе позволить.</div>

  <h2>Где Жить В Азии На $1500: Сначала Честный Фильтр</h2>
  <p>Самая плохая версия такого вопроса звучит так: “Какая страна дешёвая?” Потому что дешёвая страна не равна дешёвой жизни. Аренда может быть низкой, но виза короткая. Еда может стоить мало, но страховка и перелёты съедят запас. Город может быть комфортным, но нормальная квартира в нужном районе уже не попадает в расчёт.</p>
  <p>Поэтому $1500 лучше читать не как обещание, а как фильтр. Он помогает убрать направления, где бюджет почти сразу треснет. И оставить те, где можно жить без постоянного ощущения, что любой счёт выбивает план из рук.</p>
  <p>Практически это значит вот что: на $1500 можно проверять страну, жить проще, снимать не в самом дорогом районе, не строить семейный premium-сценарий и держать расходы под контролем. Если нужен западный уровень квартиры, частые кафе, спортзал, поездки, страховка, coworking и запас на визовые выезды — сумма быстро становится тесной.</p>

  <h2>Что Должно Входить В $1500 В Месяц</h2>
  <table class="guide-table">
    <tr><th>Категория</th><th>Что считать</th><th>Где чаще ошибаются</th></tr>
    <tr><td>Жильё</td><td>Аренда, депозит, коммунальные, интернет, район, срок договора.</td><td>Берут цену “от”, но потом выбирают район для экспатов.</td></tr>
    <tr><td>Еда</td><td>Локальная еда, продукты, кафе, доставка, кофе, бытовые мелочи.</td><td>Считают только street food, хотя живут иначе.</td></tr>
    <tr><td>Виза</td><td>Сборы, продления, выезды, документы, возможные поездки в соседние страны.</td><td>Думают, что дешёвый месяц равен дешёвому году.</td></tr>
    <tr><td>Страховка</td><td>Медицинская страховка, франшиза, хронические вопросы, emergency fund.</td><td>Исключают медицину, потому что “я почти не болею”.</td></tr>
    <tr><td>Работа</td><td>Интернет, coworking, тишина дома, резервный мобильный интернет.</td><td>Снимают дешёвое жильё, где невозможно нормально работать.</td></tr>
    <tr><td>Запас</td><td>10-20% на ошибки, переезды, поломки, срочные билеты.</td><td>Планируют месяц в ноль. Это не план, а надежда.</td></tr>
  </table>

  <h2>Города, Где $1500 Выглядят Реалистичнее</h2>
  <p>Вьетнам часто выглядит сильным вариантом для такого бюджета. Дананг, Нячанг, иногда Ханой или Хошимин при скромном жилье могут дать нормальный баланс. Официальный eVisa-маршрут Вьетнама сейчас позволяет планировать пребывание до 90 дней, single или multiple entry, но это всё равно не резидентская стратегия. Это важно. Бюджет может сходиться, а визовый ритм всё равно требовать дисциплины.</p>
  <p>Таиланд может работать, но не везде. Чиангмай обычно проще для бюджета, чем премиальные районы Бангкока или островной lifestyle. Thailand DTV может быть интересна, если ваш purpose реально попадает в категории DTV, но это уже не просто “дешёвая жизнь”. Там есть документы, финансовое подтверждение и логика подачи. Если вы просто тестируете страну, не надо притворяться, что визовый вопрос решён сам собой.</p>
  <p>Малайзия сильна городским комфортом: Куала-Лумпур, Пенанг, английский язык, медицина, инфраструктура. Но $1500 в Куала-Лумпуре и $1500 в более спокойном районе — разные деньги. Чем больше хочется “удобно и без компромиссов”, тем быстрее Малайзия выходит за рамку.</p>
  <p>Камбоджа может быть бюджетной, но с ней осторожнее. Она может дать низкие повседневные расходы, но медицина, инфраструктура, качество жилья и долгосрочный комфорт требуют отдельной проверки. Если бюджет маленький, слабая медицина и отсутствие запаса становятся не теорией, а реальным риском.</p>

  <h2>Где $1500 Становятся Слишком Оптимистичными</h2>
  <p>Сингапур, Гонконг, центральный Токио, премиальные районы Бали и островной Таиланд обычно ломают эту цифру быстро. Даже если можно найти комнату или краткосрочный компромисс, это не значит, что бюджет устойчивый. Устойчивость — это когда вы можете прожить несколько месяцев, заболеть, переехать, продлить документы и не разрушить весь план.</p>
  <p>Для семьи $1500 почти всегда слишком мало. Не потому что “в Азии дорого”, а потому что семья добавляет школу, медицину, большую квартиру, страховку на нескольких человек, dependants, больше транспорта и меньше пространства для ошибок. Один человек может потерпеть неудобство. Семья обычно нет.</p>

  <h2>Кому Подходит Бюджет $1500 В Азии</h2>
  <div class="guide-grid">
    <div class="guide-card"><strong>Подходит</strong><p>Solo remote worker, который готов жить проще, выбирать не самый дорогой район и держать расходы под контролем.</p></div>
    <div class="guide-card"><strong>Подходит Частично</strong><p>Паре без детей, если жильё скромное, город выбран аккуратно, а визовые расходы заранее заложены.</p></div>
    <div class="guide-card"><strong>Не Подходит</strong><p>Семье с детьми, международной школой, частой медициной и ожиданием западного уровня жилья.</p></div>
    <div class="guide-card"><strong>Рискованно</strong><p>Тем, кто планирует жить в ноль, без страховки, emergency fund и денег на выезд.</p></div>
  </div>

  <h2>Как Проверить Свой Сценарий До Переезда</h2>
  <p>Не начинайте с красивого видео о стране. Сначала откройте бюджет. Потом визу. Потом город. И только потом район.</p>
  <p>На сайте есть три инструмента, которые как раз должны стоять рядом с этой страницей:</p>
  <ul class="guide-sources">
    <li><a href="/ru/tools/cost-calculator/">Калькулятор стоимости жизни</a> — посчитать месячный бюджет по стране и стилю жизни.</li>
    <li><a href="/ru/tools/budget-planner/">Планировщик бюджета</a> — добавить перелёты, депозиты, визы, первый месяц и запас.</li>
    <li><a href="/ru/compare-cities/">Сравнение городов</a> — проверить, где $1500 выглядят реалистичнее: не по стране, а по конкретной базе.</li>
  </ul>

  <h2>Практический Вывод</h2>
  <p>$1500 в Азии — это не бедность и не свобода. Это рабочий, но тонкий бюджет. Он требует дисциплины. Он не любит спонтанные перелёты, дорогие районы, слабую страховку и визовые сюрпризы.</p>
  <p>Если вы один, работаете удалённо, готовы жить проще и выбираете город без премиальной наценки, shortlist есть. Вьетнам, отдельные города Таиланда, часть Малайзии, Камбоджа и некоторые филиппинские направления могут быть в игре. Если вы хотите комфорт “как в большом западном городе”, лучше сразу считать другой бюджет. Это честнее.</p>

  <h2>FAQ: Где Жить В Азии На $1500 В Месяц</h2>
  <div class="faq-item"><h3>Можно Ли Жить В Азии На $1500 В Месяц?</h3><p>Да, но не везде. Реалистичнее для одного человека в выбранных городах, если аренда, страховка, визы и lifestyle под контролем.</p></div>
  <div class="faq-item"><h3>Какая Страна В Азии Лучшая Для Бюджета $1500?</h3><p>Часто стоит смотреть Вьетнам, отдельные города Таиланда, Малайзию вне дорогих районов и Камбоджу. Но выбирать нужно по городу и визе, а не только по стране.</p></div>
  <div class="faq-item"><h3>Хватит Ли $1500 Для Семьи В Азии?</h3><p>Обычно нет. Семье нужны большая квартира, медицина, школа, страховка и запас. Такой бюджет быстро становится слишком тесным.</p></div>
  <div class="faq-item"><h3>Можно Ли Жить На $1500 В Таиланде?</h3><p>Иногда да, особенно вне премиальных районов. Но Бангкок, острова, частые кафе и слабое планирование визы быстро поднимают расходы.</p></div>
  <div class="faq-item"><h3>Что Проверить Перед Выбором Города?</h3><p>Визовый срок, стоимость жилья, страховку, интернет, транспорт, депозит, район и запас на выезд или продление.</p></div>
</article>
"""


def ru_vietnam_evisa_vs_thailand_dtv_article(title: str) -> str:
    return f"""
<article class="guide-page">
  <div class="guide-hero">
    <span class="badge">Обновлено в апреле 2026 · Vietnam eVisa vs Thailand DTV</span>
    <h1>{html.escape(title)}</h1>
    <p>Vietnam eVisa и Thailand DTV часто сравнивают как два способа “пожить в Юго-Восточной Азии”. Но это разные инструменты. Vietnam eVisa лучше для понятного тестового stay. Thailand DTV сильнее, если ваш сценарий реально попадает в DTV-категории и вы хотите возвращаться в Таиланд как в базу.</p>
  </div>

  <div class="guide-note"><strong>Короткий ответ:</strong> выбирайте Vietnam eVisa, если вам нужен простой тест Вьетнама на срок до 90 дней и без тяжёлой иммиграционной конструкции. Смотрите Thailand DTV, если вы удалёнщик, freelancer, участник soft-power активности, едете на лечение или идёте как dependant, и можете подтвердить цель, документы и финансовые требования.</div>

  <h2>Vietnam eVisa vs Thailand DTV: Главное Различие</h2>
  <p>Vietnam eVisa — это въездной инструмент. Он удобен, потому что официальная иммиграционная страница Вьетнама описывает eVisa как электронную визу сроком максимум до 90 дней, single или multiple entry. Официальный туристический сайт Вьетнама также пишет, что с 15 августа 2023 года граждане всех стран и территорий могут подаваться на eVisa и использовать 90-day duration, valid for multiple entry.</p>
  <p>Thailand DTV — другой зверёк. Это не просто “въехать и посмотреть страну”. На правительственных страницах Thailand.go.th DTV описывается через цели: workcation, digital nomad, remote worker, foreign talent, freelancer, Thai soft power activities, medical treatment и dependants. Там же фигурирует срок до 180 дней за stay и отдельная логика продления. На странице типов DTV указано financial evidence не менее 500 000 THB и validity period 5 years.</p>
  <p>Практический смысл: Vietnam eVisa проще для теста. Thailand DTV интереснее для повторяющегося medium-stay сценария, но требует более точного совпадения с категорией.</p>

  <h2>Ключевые Факты По Vietnam eVisa И Thailand DTV</h2>
  <table class="guide-table">
    <tr><th>Пункт</th><th>Vietnam eVisa</th><th>Thailand DTV</th></tr>
    <tr><td>Срок</td><td>До 90 дней, single или multiple entry по официальному порталу иммиграции.</td><td>До 180 дней за stay, с контекстом продления ещё на 180 дней на Thailand.go.th.</td></tr>
    <tr><td>Назначение</td><td>Въезд и тест страны без отдельной digital nomad категории.</td><td>Workcation, remote work, freelancer, soft power, лечение, dependants.</td></tr>
    <tr><td>Финансовый фильтр</td><td>В официальном eVisa-описании основной акцент на паспорт, подачу, fee и условия въезда.</td><td>Официальная DTV-страница по типам указывает financial evidence не менее 500 000 THB.</td></tr>
    <tr><td>Сложность</td><td>Проще как тестовый въезд.</td><td>Сложнее, потому что нужно доказать purpose и документы категории.</td></tr>
    <tr><td>Лучший сценарий</td><td>Проверить Вьетнам, город, бюджет, ритм жизни.</td><td>Использовать Таиланд как повторяющуюся базу, если ваш профиль подходит под DTV.</td></tr>
    <tr><td>Главный риск</td><td>Принять 90-day eVisa за долгосрочную релокацию.</td><td>Считать DTV простой туристической визой без проверки цели и документов.</td></tr>
  </table>

  <h2>Кому Больше Подходит Vietnam eVisa</h2>
  <p>Vietnam eVisa подходит тем, кто хочет проверить страну без тяжёлой визовой архитектуры. Например: пожить в Дананге, Ханое или Хошимине, понять бюджет, интернет, жильё, климат, шум, транспорт, еду и реальный рабочий ритм.</p>
  <p>Это хороший вариант, если вы ещё не уверены, нужна ли вам Азия надолго. Вьетнам часто силён по повседневным расходам. Но eVisa не надо романтизировать. Это не обещание резидентства, не work permit и не автоматический long-stay план. Если вам нужен годовой или семейный сценарий, нужно заранее понимать, что будет после 90 дней.</p>
  <p>Где люди ошибаются: считают, что раз въезд простой, то и переезд простой. Нет. Виза может быть простой, а жизнь — нет. Жильё, качество воздуха, медицина, банковские вопросы, налоги, школа и долгосрочный статус всё равно требуют отдельной проверки.</p>

  <h2>Кому Больше Подходит Thailand DTV</h2>
  <p>Thailand DTV больше подходит тем, кто уже понимает, почему именно Таиланд. Не просто “нравится Бангкок” или “хочу на остров”. А есть сценарий: удалённая работа на иностранного работодателя, freelance portfolio, soft-power activity, medical treatment или family dependant route.</p>
  <p>У DTV сильная сторона — повторяемая база. Если вы хотите регулярно жить в Таиланде средними периодами, DTV выглядит серьёзнее, чем постоянная импровизация с короткими въездами. Но у неё есть фильтр. Официальные страницы перечисляют категории и документы, а консульские чеклисты показывают, что нужны паспорт, фото, current location, финансовое подтверждение и доказательство цели.</p>
  <p>Если ваш профиль не попадает в категорию, DTV не становится подходящей только потому, что Таиланд вам нравится. Это неприятная, но полезная мысль.</p>

  <h2>Бюджет: Вьетнам Часто Проще, Но Не Всегда Лучше</h2>
  <p>Если смотреть только на расходы, Вьетнам часто выигрывает. Дананг и Нячанг могут быть мягче по аренде, еде и повседневной жизни, чем Бангкок или популярные районы Таиланда. Но бюджет — это не вся релокация.</p>
  <p>Таиланд может стоить дороже, но давать больше привычной инфраструктуры для части людей: медицина в крупных городах, expat-сервисы, выбор жилья, международные сообщества, больше familiar lifestyle. Вопрос не в том, где дешевле. Вопрос в том, где ваш бюджет, виза и рабочая жизнь сходятся одновременно.</p>

  <h2>Как Выбрать Между Vietnam eVisa И Thailand DTV</h2>
  <div class="guide-grid">
    <div class="guide-card"><strong>Берите Vietnam eVisa</strong><p>Если хотите протестировать страну на понятный срок, без сложной категории и без обещаний себе, что это уже переезд.</p></div>
    <div class="guide-card"><strong>Берите Thailand DTV</strong><p>Если ваш purpose попадает в DTV, документы готовы, и Таиланд нужен как повторяющаяся база.</p></div>
    <div class="guide-card"><strong>Осторожно С Vietnam eVisa</strong><p>Если вам нужна семья, школа, long-stay и понятный путь на год или дольше.</p></div>
    <div class="guide-card"><strong>Осторожно С DTV</strong><p>Если нет финансового подтверждения, слабый work proof или цель поездки не совпадает с категорией.</p></div>
  </div>

  <h2>Официальные Источники Для Быстрой Проверки</h2>
  <ul class="guide-sources">
    <li><a href="https://evisa.immigration.gov.vn/web/guest/trang-chu-ttdt" rel="nofollow noopener" target="_blank">Vietnam Immigration: eVisa official portal</a></li>
    <li><a href="https://vietnam.travel/plan-your-trip/official-vietnam-evisa-application" rel="nofollow noopener" target="_blank">Vietnam Tourism: official eVisa guide</a></li>
    <li><a href="https://immigration.gov.vn/en_US/khai-thi-thuc-dien-tu/cap-thi-thuc-dien-tu" rel="nofollow noopener" target="_blank">Vietnam Immigration: foreigner eVisa application instructions</a></li>
    <li><a href="https://thailand.go.th/visit-thailand-detail/-destination-thailand-visa-dtv" rel="nofollow noopener" target="_blank">Thailand.go.th: DTV launch and stay context</a></li>
    <li><a href="https://thailand.go.th/issue-focus-detail/3---destination-thailand-visa-dtv?hl=en" rel="nofollow noopener" target="_blank">Thailand.go.th: 3 DTV types and required documents</a></li>
    <li><a href="https://www.thaievisa.go.th/" rel="nofollow noopener" target="_blank">Thailand e-Visa official website</a></li>
  </ul>

  <h2>Практический Вывод</h2>
  <p>Если вы ещё только тестируете Юго-Восточную Азию, Vietnam eVisa обычно честнее. Она не требует делать вид, что вы уже выбрали долгую базу. Приехали, пожили, посчитали, поняли город. Потом уже можно решать, нужен ли более длинный маршрут.</p>
  <p>Если вы уже выбрали Таиланд и ваш сценарий совпадает с DTV, тогда DTV может быть сильнее. Но она требует аккуратной подачи. Не надо идти в неё как в “удобную туристическую визу”. Это как раз тот случай, где название звучит проще, чем документы.</p>

  <h2>FAQ: Vietnam eVisa vs Thailand DTV</h2>
  <div class="faq-item"><h3>Что Лучше Для Первого Теста Азии: Vietnam eVisa Или Thailand DTV?</h3><p>Для первого теста чаще проще Vietnam eVisa. Она подходит для ограниченного пребывания и проверки страны без тяжёлой визовой конструкции.</p></div>
  <div class="faq-item"><h3>Можно Ли Работать Удалённо По Vietnam eVisa?</h3><p>Нужно быть осторожным. Vietnam eVisa — это въездной инструмент, а не отдельная digital nomad visa. Не стоит приписывать ей права, которых официальный источник прямо не даёт.</p></div>
  <div class="faq-item"><h3>Thailand DTV Подходит Всем Удалёнщикам?</h3><p>Нет. Нужно попасть в категорию DTV и подтвердить цель, документы и финансовые требования. Сам факт удалённой работы ещё не равен одобрению.</p></div>
  <div class="faq-item"><h3>Где Дешевле Жить: Во Вьетнаме Или В Таиланде?</h3><p>Часто Вьетнам дешевле в повседневном сценарии, но всё зависит от города, жилья, страховки, визового ритма и lifestyle.</p></div>
  <div class="faq-item"><h3>Что Проверить Перед Выбором?</h3><p>Срок stay, цель визы, документы, бюджет, страховку, город, интернет и план выхода после окончания разрешённого срока.</p></div>
</article>
"""


def ru_guide_article(slug: str, title: str) -> str | None:
    if slug == "thailand-dtv-vs-ltr-visa":
        return ru_thailand_dtv_vs_ltr_article(title)
    if slug == "where-to-live-in-asia-on-1500-a-month":
        return ru_where_to_live_on_1500_article(title)
    if slug == "vietnam-evisa-vs-thailand-dtv":
        return ru_vietnam_evisa_vs_thailand_dtv_article(title)

    data = {
        "can-you-extend-japan-digital-nomad-visa": (
            "Япония выглядит как идеальная короткая база. Но у digital nomad маршрута есть жёсткая рамка: до 6 месяцев и без продления.",
            "Если вам нужен тест страны, сезон в Японии или понятный рабочий период с датой выезда — маршрут может подойти. Если вы ищете релокацию, школу для детей, долгую аренду или путь к резиденции, это не тот инструмент.",
            "Главная ошибка — считать визу началом переезда. Это скорее ограниченное окно для удалённой работы, а не long-stay стратегия.",
        ),
        "japan-digital-nomad-visa-income-requirement": (
            "По Японии вопрос не только в сумме дохода. Важнее то, можно ли этот доход нормально подтвердить документами.",
            "Правило по доходу отсекает людей, у которых деньги есть, но доказательная база слабая: нерегулярные выплаты, крипта без понятной отчётности, смешанные личные и бизнес-счета.",
            "Перед подачей проверьте документы так, будто их будет читать человек, которому всё равно, насколько убедительно вы рассказываете историю. Ему нужны цифры, даты и источник дохода.",
        ),
        "thailand-dtv-vs-ltr-visa": (
            "Thailand DTV и LTR нельзя сравнивать как две версии одной визы. Они решают разные задачи.",
            "DTV чаще выглядит как гибкий маршрут для среднего stay, soft-power активностей, лечения или удалённой работы при подходящем профиле. LTR — более тяжёлый и строгий route для людей с сильным доходом, документами и long-term планом.",
            "Если вы хотите просто пожить в Таиланде и проверить страну, DTV может быть логичнее. Если нужен более стабильный профессиональный статус и профиль тянет требования, смотрите LTR.",
        ),
        "malaysia-de-rantau-vs-thailand-dtv": (
            "DE Rantau и Thailand DTV привлекают похожую аудиторию, но устроены по-разному.",
            "Малайзия сильнее там, где важны английский, Куала-Лумпур, понятная digital nomad программа и городская инфраструктура. Таиланд сильнее там, где важны lifestyle, выбор городов и более гибкий сценарий stay.",
            "Не выбирайте между странами по настроению. Сравните работодателя, доход, срок, dependants и то, где вам реально удобнее жить каждый день.",
        ),
        "taiwan-gold-card-income-requirement": (
            "Taiwan Gold Card — серьёзный профессиональный маршрут, а не casual nomad visa.",
            "Если вы идёте по salary-based логике, важно не просто заработать нужную сумму, а доказать её так, как требует официальный критерий. Зарплата, налоговые документы и контракты должны складываться в понятную историю.",
            "Gold Card может быть сильным решением для специалистов, которым нужен work permit и residence logic в одной связке. Но слабые документы быстро превращают хороший профиль в риск.",
        ),
        "best-asian-countries-with-easy-long-stay-visas": (
            "Лёгкая long-stay виза — это не всегда низкий порог входа. Иногда «лёгкая» значит понятная. Иногда — дешёвая. Иногда — гибкая по сроку.",
            "Для пенсионера easy route может быть SRRV. Для remote worker — DE Rantau или DTV. Для специалиста — Taiwan Gold Card. Для теста региона — eVisa или туристический маршрут, если он честно подходит под цель.",
            "Сначала определите свой профиль: возраст, доход, работодатель, семья, срок и документы. Потом уже выбирайте страну.",
        ),
        "where-to-live-in-asia-on-1500-a-month": (
            "$1,500 в месяц в Азии могут работать. Но не везде и не для любого уровня комфорта.",
            "Один человек с аккуратным бюджетом может нормально жить в части городов Вьетнама, Таиланда, Малайзии или Камбоджи. Семья, международная школа, частая медицина и центральная аренда быстро меняют расчёт.",
            "Не сравнивайте только rent. Смотрите визу, страховку, депозиты, перелёты, интернет, транспорт и запас на выход из страны.",
        ),
        "best-asian-countries-for-remote-workers-with-family": (
            "Семейная релокация ломается не там, где solo remote worker просто потерпит неудобство.",
            "Для семьи важны dependants, школа, медицина, жильё, район, страховка и предсказуемость продления. Красивая страна может не подойти, если ребёнку нужна школа, супругу нужен статус, а аренда требует длинного договора.",
            "Начинайте с legal stay для всей семьи. Потом медицина и школа. Только после этого lifestyle.",
        ),
        "philippines-srrv-vs-thailand-retirement-visa": (
            "Philippines SRRV и пенсионные маршруты Таиланда сравнивают часто, но критерии разные.",
            "SRRV интересен тем, кто хочет меньше border anxiety и смотрит на indefinite stay logic. Таиланд часто выигрывает по lifestyle, медицине в крупных городах и привычной expat-инфраструктуре.",
            "Решение зависит от возраста, депозита, страховки, медицинских потребностей, банка и того, где вы реально хотите жить после первых трёх месяцев.",
        ),
        "vietnam-evisa-vs-thailand-dtv": (
            "Vietnam eVisa и Thailand DTV — это разные сценарии, а не прямые конкуренты.",
            "Vietnam eVisa полезна для теста страны, бюджета и городского ритма. Thailand DTV больше похожа на маршрут для повторяемого medium-stay сценария, если ваша цель и документы попадают в категории.",
            "Если вы просто проверяете Юго-Восточную Азию, Вьетнам может быть проще. Если уже нужен более оформленный stay в Таиланде, смотрите DTV.",
        ),
    }
    item = data.get(slug)
    if not item:
        return None
    intro, practical, risk = item
    return f"""
<article class="guide-page">
  <div class="guide-hero">
    <span class="badge">Гайд 2026</span>
    <h1>{html.escape(title)}</h1>
    <p>{html.escape(intro)}</p>
  </div>
  <div class="guide-note"><strong>Короткий ответ:</strong> {html.escape(practical)}</div>
  <h2>Что написано в правилах</h2>
  <p>Смотрите на официальный срок stay, продление, тип разрешённой деятельности, требования к доходу и документы. Если правило не говорит о продлении, dependants или местной работе, не стоит додумывать это как скрытую возможность.</p>
  <h2>Что это значит на практике</h2>
  <p>{html.escape(risk)} Практический подход простой: сначала legal route, затем деньги, затем город и быт. Обратный порядок почти всегда создаёт лишние ожидания.</p>
  <div class="guide-grid">
    <div class="guide-card"><strong>Подходит</strong><span>Тем, чей доход, срок stay и документы совпадают с официальным маршрутом.</span></div>
    <div class="guide-card"><strong>Не подходит</strong><span>Тем, кто ищет обходные варианты, не может подтвердить доход или планирует жить дольше разрешённого срока.</span></div>
  </div>
  <h2>Где люди чаще ошибаются</h2>
  <p>Самая частая ошибка — читать визу как lifestyle-обещание. Виза не обещает дешёвую аренду, хорошую школу, понятную медицину или лёгкую интеграцию. Она только задаёт легальные рамки.</p>
  <h2>FAQ</h2>
  <h3>Можно ли использовать этот гайд как юридическую консультацию?</h3>
  <p>Нет. Это планировочный материал. Перед подачей проверяйте официальный источник или консультируйтесь со специалистом.</p>
  <h3>Что проверять первым?</h3>
  <p>Срок stay, продление, доход, dependants, страховку и разрешённую деятельность.</p>
  <h3>Можно ли ориентироваться только на стоимость жизни?</h3>
  <p>Нет. Дешёвая страна не помогает, если визовый маршрут не совпадает с вашим профилем.</p>
  <h3>Что делать после чтения?</h3>
  <p>Откройте страновую страницу, визовый гид и калькулятор бюджета. Решение должно сходиться по правилам и деньгам одновременно.</p>
  <h3>Почему формулировки такие осторожные?</h3>
  <p>Потому что визовые правила меняются, а неподтверждённые обещания стоят дороже, чем честная пауза перед подачей.</p>
</article>
"""


def localized_post_content(content: str) -> str:
    replacements = [
        ("Read in English", "Читать на английском"),
        ("Requirements: что подтверждено", "Требования: что подтверждено"),
        ("remote work route", "маршрут для удалённой работы"),
        ("remote-worker route", "маршрут для удалённой работы"),
        ("one-year validity", "срок действия один год"),
        ("90-day stay", "пребывание до 90 дней"),
        ("one-year multiple entry", "годовая multiple-entry виза"),
        ("single or multiple entry", "однократный или многократный въезд"),
        ("single или многократный въезд", "однократный или многократный въезд"),
        ("multiple entry", "многократный въезд"),
        ("indefinite stay", "бессрочное пребывание"),
        ("short visit", "краткий визит"),
        ("какой срок дают stay", "какой срок пребывания дают"),
        ("residence route", "маршрут резидентства"),
        ("work permit", "разрешение на работу"),
        ("self-sponsored маршрут", "самостоятельный визовый маршрут"),
        ("visa-free entry", "безвизовый въезд"),
        ("top talent маршрут", "маршрут для top talent"),
        ("nomad workaround", "обходной nomad-маршрут"),
        ("self-sponsored маршрут", "self-sponsored маршрут"),
        ("30-day option", "30-дневный вариант"),
        ("5-year option", "5-летний вариант"),
        ("Initial stay", "Первичный срок пребывания"),
        ("Extension ceiling", "Потолок продления"),
        ("Sojourn period", "Срок пребывания"),
        ("Income standard", "Требование по доходу"),
        ("Income benchmark", "Порог дохода"),
        ("Salary benchmark", "Порог зарплаты"),
        ("LTR categories", "Категории LTR"),
        ("Job offer", "Job offer"),
        ("Validity", "Срок действия"),
        ("Route Type", "Тип маршрута"),
        ("Stay Length", "Срок stay"),
        ("Extension", "Продление"),
        ("Core Check", "Что проверить"),
        ("Benefit", "Преимущество"),
        ("Activity", "Разрешённая деятельность"),
        ("Period of stay", "Срок пребывания"),
        ("What it combines", "Что объединяет карта"),
        ("Checked Planning Facts", "Проверенные факты для планирования"),
        ("Official Sources", "Официальные источники"),
        ("Official Links", "Официальные ссылки"),
        ("Internet Users", "Пользователи интернета"),
        ("April 2026", "апрель 2026"),
        ("Country", "Страна"),
        ("Capital", "Столица"),
        ("Currency", "Валюта"),
        ("Требования: что подтверждено", "Требования: что подтверждено"),
    ]
    content = replace_many(content, replacements)
    content = content.replace("single или многократный въезд", "однократный или многократный въезд")
    return content


def replace_many(text: str, replacements: list[tuple[str, str]]) -> str:
    for old, new in replacements:
        text = text.replace(old, new)
    return text


def localized_generic_content(content: str) -> str:
    replacements = [
        ('Updated March 2026', 'Проверено в марте 2026'),
        ('Updated April 2026', 'Проверено в апреле 2026'),
        ('5 Countries', '5 стран'),
        ('Read In English', 'Читать на английском'),
        ('Read in English', 'Читать на английском'),
        ('Read In Russian', 'Читать на русском'),
        ('Read in Russian', 'Читать на русском'),
        ('Free Tools', 'Бесплатные инструменты'),
        ('Choose Your Tool', 'Выберите инструмент'),
        ('Cost Calculator', 'Калькулятор стоимости жизни'),
        ('Budget Planner', 'Планировщик бюджета'),
        ('Country Compare', 'Сравнение стран'),
        ('No Sign-Up', 'Без регистрации'),
        ('Instant Results', 'Моментальный результат'),
        ('Sign-ups needed', 'Нужна регистрация'),
        ('Country 1', 'Страна 1'),
        ('Country 2', 'Страна 2'),
        ('Display Currency', 'Валюта расчёта'),
        ('Accommodation', 'Жильё'),
        ('Food Style', 'Питание'),
        ('Transport', 'Транспорт'),
        ('Lifestyle', 'Образ жизни'),
        ('Calculate Monthly Budget', 'Рассчитать ежемесячный бюджет'),
        ('Read in English', 'Читать на английском'),
        ('Compare Cities in Asia', 'Сравнение городов Азии'),
        ('Сравнить города in Asia', 'Сравнение городов Азии'),
        ('LIVE DATA · TELEPORT API', 'Данные по городам'),
        ('LIVE DATA', 'Данные по городам'),
        ('TELEPORT API', 'городские метрики'),
        ('Bali / Indonesia', 'Бали / Индонезия'),
        ('China', 'Китай'),
        ('UAE / Dubai', 'ОАЭ / Дубай'),
        ('Housing Setup', 'Старт жилья'),
        ('Жильё Setup', 'Старт жилья'),
        ('Shipping / Baggage', 'Багаж / доставка'),
        ('Visa Fee', 'Визовый сбор'),
        ('Legal / Agent Fees', 'Юрист / агент'),
        ('Monthly Budget', 'Месячный бюджет'),
        ('Utilities and Internet', 'Коммунальные услуги и интернет'),
        ('Образ жизни and Entertainment', 'Образ жизни и досуг'),
        ('Health insurance est.', 'Оценка страховки'),
        ('Live rates:', 'Курсы:'),
        ('Cost data:', 'Данные по расходам:'),
        ('ExchangeRate-API', 'актуальные курсы валют'),
        ('Rates:', 'Курсы валют:'),
        ('Numbeo March 2026', 'Numbeo, март 2026'),
        ('Numbeo</a> March 2026', 'Numbeo</a>, март 2026'),
        ('Калькулятор стоимости жизни — Asia 2026', 'Калькулятор стоимости жизни в Азии — 2026'),
        ('Сравните Страны Азии', 'Сравните страны Азии'),
        ('Fetching real-time data&#8230;', 'Загружаем актуальные данные&#8230;'),
        ('Please select two different countries.', 'Выберите две разные страны.'),
        ('Error fetching data: ', 'Ошибка при загрузке данных: '),
        ('. Please try again.', '. Попробуйте ещё раз.'),
        ('Cost of Living Calculator', 'Калькулятор стоимости жизни'),
        ('Калькулятор стоимости жизни &mdash; Asia 2026', 'Калькулятор стоимости жизни в Азии &mdash; 2026'),
        ('Relocation Budget Planner', 'Планировщик бюджета на переезд'),
        ('Compare Countries', 'Сравнить страны'),
        ('Compare Cities', 'Сравнить города'),
        ('Comparisons', 'Сравнения'),
        ('Country Facts For Relocation Planning', 'Факты о стране для планирования переезда'),
        ('Best Countries in Asia to Move', 'Лучшие страны Азии для переезда'),
        ('Best Countries In Asia To Move To', 'Лучшие страны Азии для переезда'),
        ('Cheapest Countries in Asia', 'Самые дешёвые страны Азии'),
        ('Cheapest Countries In Asia', 'Самые дешёвые страны Азии'),
        ('Read comparison &rarr;', 'Открыть сравнение &rarr;'),
        ('See full ranking &rarr;', 'Открыть рейтинг &rarr;'),
        ('Full ranking of the top 5 Asian countries for expats and digital nomads in 2026. Updated data.', 'Полный рейтинг 5 стран Азии для expats и digital nomads в 2026 году. Данные обновлены.'),
        ('Start with the broader ranking if you do not yet know which countries belong on your shortlist.', 'Начните с общего рейтинга, если ещё не ясно, какие страны стоит оставить в shortlist.'),
        ('Focus on monthly budgets, housing and day-to-day costs before comparing visas.', 'Сначала проверьте месячный бюджет, жильё и повседневные расходы, а уже потом сравнивайте визы.'),
        ('Capital', 'Столица'),
        ('Currency', 'Валюта'),
        ('Languages', 'Языки'),
        ('Internet Users', 'Пользователи интернета'),
        ('Life Expectancy', 'Ожидаемая продолжительность жизни'),
        ('World Bank Year', 'Год данных World Bank'),
        ('Use these facts as planning context, then compare visas, housing and healthcare before making a paid commitment.', 'Используйте эти факты как базовый контекст, а затем уже сравнивайте визы, жильё и медицину до любых платных решений.'),
        ('Для YMYL-тем вроде виз общие впечатления не заменяют официальный источник.', 'В вопросах виз, денег и медицины общие впечатления не заменяют официальный источник.'),
        ('Для YMYL-темы важнее другое:', 'Важнее другое:'),
        ('для YMYL-тем вроде виз, медицины и денег сначала проверяют легальность маршрута и устойчивость бюджета.', 'сначала нужно проверить легальный маршрут, срок пребывания, медицину и запас бюджета.'),
        ('Для YMYL-решений нужна связка факторов, иначе план получается хрупким.', 'Для переезда нужна связка факторов: виза, деньги, медицина, город и понятный план выхода.'),
        ('Для YMYL-решений лучше скучная проверка, чем красивый, но хрупкий план.', 'Скучная проверка документов часто спасает больше денег, чем красивый план.'),
        ('В YMYL-темах исправление одного числа может быть важнее, чем переписывание красивого абзаца.', 'В визовых, финансовых и медицинских темах исправление одного числа может быть важнее, чем переписывание красивого абзаца.'),
        ('Для визовых и YMYL-страниц это важнее косметики:', 'Для визовых, финансовых и медицинских страниц это важнее косметики:'),
        ('Compare Thailand, Malaysia, Bali, Vietnam and Taiwan based on cost, visa and образ жизни.', 'Сравните Таиланд, Малайзию, Бали, Вьетнам и Тайвань по расходам, визам и повседневной логике.'),
        ('Find the right visa — digital nomad, долгосрочный, retirement or work permit.', 'Подберите подходящий маршрут: digital nomad, long-stay, пенсионный или рабочий.'),
        ('The Калькулятор стоимости жизни lets you customise your образ жизни profile and сразу увидеть помесячную разбивку бюджета по странам.', 'Калькулятор стоимости жизни даёт помесячную разбивку под выбранный стиль жизни.'),
        ('The Калькулятор стоимости жизни lets you customise your lifestyle profile and instantly see a monthly budget breakdown for any of our five covered countries.', 'Калькулятор стоимости жизни даёт помесячную разбивку под выбранный стиль жизни.'),
        ('The Планировщик бюджета переезда focuses on the one-time costs that most guides overlook', 'Планировщик бюджета показывает разовые расходы, которые часто забывают'),
        ('The Relocation Планировщик бюджета focuses on the one-time costs that most guides overlook', 'Планировщик бюджета показывает разовые расходы, которые часто забывают'),
        ('The Country Comparison Tool puts two destinations side-by-side across more than 15 metrics so you can make a data-driven choice.', 'Инструмент сравнения ставит две страны рядом по 15+ метрикам, чтобы решение было не на ощущениях.'),
        ('The инструмент сравнения стран puts two destinations side-by-side across more than 15 metrics so you can make a data-driven choice.', 'Инструмент сравнения ставит две страны рядом по 15+ метрикам, чтобы решение было не на ощущениях.'),
        ('visa application fees, international flights, shipping, rental deposits, and first-month setup.', 'визовые сборы, перелёты, багаж, депозиты и первый месяц.'),
        ('visa application fees, international flights, shipping, rental deposits, and first-month setup', 'визовые сборы, перелёты, багаж, депозиты и первый месяц'),
        ('The primary appeal is the dramatic reduction in cost of living. A comfortable образ жизни in Бангкок or Чиангмай can cost $1,200–1,800 per month — a fraction of what the same quality of life would cost in London, New York, or Sydney. Malaysia offers modern infrastructure and an English-speaking population. Bali has built the world’s most vibrant digital nomad ecosystem.', 'Главный мотив — заметно ниже стоимость жизни. Комфортный сценарий в Бангкоке или Чиангмае может укладываться в $1,200–1,800 в месяц, тогда как похожий уровень в Лондоне, Нью-Йорке или Сиднее стоит совсем других денег. Малайзия даёт современную инфраструктуру и английский в быту, а Бали держится на сильном сообществе удалёнщиков.'),
        ('If образ жизни matters most, Bali’s nomad ecosystem is unmatched.', 'Если важнее образ жизни и сообщество, Бали сложно игнорировать.'),
        ('Which is cheaper, easier to get a visa, and better for long-term living?', 'Что дешевле, где проще визовый маршрут и какая страна лучше для долгого проживания?'),
        ('Budget, mid-range and comfortable образ жизни costs per country', 'Бюджетный, средний и комфортный сценарий по странам'),
        ('Бюджет, mid-range and comfortable образ жизни costs per country', 'Бюджетный, средний и комфортный сценарий по странам'),
        ('Find the right visa — digital nomad, долгосрочный, retirement or work permit.', 'Подберите подходящий маршрут: digital nomad, long-stay, пенсионный или рабочий.'),
        ('Find the right visa — digital nomad, долгосрочный, retirement or work permit', 'Подберите подходящий маршрут: digital nomad, long-stay, пенсионный или рабочий'),
        ('Asia has become the world’s most popular destination for экспатов, удалёнщиков, retirees, and location-independent professionals.', 'Азия стала одним из самых популярных направлений для экспатов, удалёнщиков, пенсионеров и специалистов, не привязанных к офису.'),
        ('Asia has become the world&#8217;s most popular destination for экспатов, удалённых специалистов, retirees, and location-independent professionals.', 'Азия стала одним из самых популярных направлений для экспатов, удалёнщиков, пенсионеров и специалистов, не привязанных к офису.'),
        ('Free все инструменты и гайды бесплатны', 'Бесплатно: все инструменты и гайды'),
        ('Calculate Your Бюджет', 'Посчитайте бюджет'),
        ('Use our cost calculator to estimate your exact monthly expenses based on your образ жизни.', 'Используйте калькулятор, чтобы прикинуть месячные расходы под ваш стиль жизни.'),
        ('Ultra-low cost of living — ideal for долгосрочный stays and passive income образ жизниs', 'Очень низкие расходы — вариант для долгого проживания и сценариев с пассивным доходом'),
        ('Niche destinations for specific образ жизниs — yoga, adventure, tech, beaches', 'Нишевые направления под конкретный стиль жизни: йога, приключения, tech-среда или море'),
        ('Emerging destinations with minimal competition and growing экспат communities', 'Новые направления с меньшей конкуренцией и растущими expat-сообществами'),
        ('Use our инструмент сравнения стран to compare any two destinations, or start with our Калькулятор стоимости жизни чтобы понять, насколько далеко реально тянется ваш бюджет.', 'Используйте инструмент сравнения стран, чтобы сопоставить два направления, или начните с калькулятора стоимости жизни, чтобы понять реальный запас бюджета.'),
        ('Get an instant personalised monthly budget with full expense breakdown — rent, food, transport, entertainment and more.', 'Получите быстрый расчёт месячного бюджета с разбивкой по аренде, еде, транспорту, досугу и базовым расходам.'),
        ('All budget estimates are based on verified экспат data from Бангкок, Kuala Lumpur, Bali, Ho Chi Minh City and Taipei — updated for 2026.', 'Бюджетные оценки собраны по реальным сценариям в Бангкоке, Куала-Лумпуре, Бали, Хошимине и Тайбэе и обновлены под 2026 год.'),
        ('Real Экспат Data', 'реальные расходы экспатов'),
        ('Ranked by real monthly costs — rent, food, transport and образ жизни — for a comfortable solo экспат life.', 'Рейтинг по реальным месячным расходам: аренда, еда, транспорт и базовый комфорт для одного человека.'),
        ('Full Cost Сравнение Table', 'Полная таблица расходов'),
        ('Money-Saving Tips', 'Как экономить без самообмана'),
        ('USD Валюта used', 'USD часто используется'),
        ('Образ жизни-Based Results adapt to your образ жизни — budget backpacker, mid-range экспат, or comfortable professional.', 'Расчёт меняется под ваш сценарий: бюджетный формат, средний expat-уровень или комфортный профессиональный переезд.'),
        ('Our data is based on aggregated экспат reports, Numbeo indices, and local research updated quarterly.', 'Оценки опираются на агрегированные expat-отчёты, индексы стоимости жизни и локальные проверки. Данные нужно воспринимать как ориентир, а не как обещание точной цены.'),
        ('Our free relocation planning tools are designed to remove the guesswork from that decision.', 'Наши инструменты нужны, чтобы убрать часть догадок из решения: быстро прикинуть бюджет, сравнить страны и увидеть слабые места до оплаты билетов или аренды.'),
        ('The Калькулятор стоимости жизни lets you customise your образ жизни profile and сразу увидеть помесячную разбивку бюджета по странам.', 'Калькулятор стоимости жизни даёт помесячную разбивку под выбранный стиль жизни.'),
        ('The Планировщик бюджета переезда focuses on the one-time costs that most guides overlook — визовые сборы, перелёты, багаж, депозиты и первый месяц.', 'Планировщик бюджета показывает разовые расходы, которые часто забывают: визовые сборы, перелёты, багаж, депозиты и первый месяц.'),
        ('The инструмент сравнения стран puts two destinations side-by-side across more than 15 metrics so you can make a data-driven choice.', 'Инструмент сравнения ставит две страны рядом по 15+ метрикам, чтобы решение было не на ощущениях.'),
        ('Юго-Восточной and East Asia', 'Юго-Восточной и Восточной Азии'),
        ('Ultra-low cost of living — ideal for долгосрочный stays and passive income образ жизниs', 'Очень низкие расходы — вариант для долгого проживания и сценариев с пассивным доходом'),
        ('Use our инструмент сравнения стран to compare any two destinations, or start with our Калькулятор стоимости жизни чтобы понять, насколько далеко реально тянется ваш бюджет.', 'Используйте инструмент сравнения стран, чтобы сопоставить два направления, или начните с калькулятора стоимости жизни, чтобы понять реальный запас бюджета.'),
        ('баланс lifestyle, медицины и городов', 'баланс быта, медицины и городов'),
        ('digital nomads, пары, ранняя пенсия', 'удалёнщики, пары, ранняя пенсия'),
        ('семьи, long-stay, спокойная релокация', 'семьи, долгий stay, спокойная релокация'),
        ('The key Japan question is not образ жизни. It is the six-month limit and no-extension rule.', 'Главный вопрос по Японии — не образ жизни, а лимит 6 месяцев и отсутствие продления.'),
        ('Can You Extend Japan Digital Nomad виза?', 'Можно ли продлить Japan Digital Nomad Visa?'),
        ('Japan Digital Nomad виза Income Requirement', 'Требование к доходу для Japan Digital Nomad Visa'),
        ('A practical comparison for удалённых специалистов choosing between Malaysia and Thailand.', 'Практическое сравнение для удалённых специалистов, которые выбирают между Малайзией и Таиландом.'),
        ('Check члены семьи, schooling, healthcare and housing before you fall in love with a city.', 'Проверьте статус членов семьи, школу, медицину и жильё до того, как влюбитесь в город.'),
        ('For people moving with члены семьи, where school and healthcare matter as much as rent.', 'Для переезда с семьёй, где школа и медицина важны не меньше аренды.'),
        ('Use them to understand the decision, then verify the official source before applying or paying anyone.', 'Используйте их для первичного решения, а перед подачей или оплатой сверяйте правило с официальным источником.'),
        ('Start with the constraint that can break your plan: visa length, income proof, family eligibility, retirement route or monthly budget.', 'Начинайте с ограничения, которое может сломать план: срок визы, подтверждение дохода, семья, пенсионный маршрут или месячный бюджет.'),
        ('The best new pages here should come from real search questions: extension, income, renewal, family rules, cost thresholds and country-versus-country decisions.', 'Новые страницы в этом разделе должны начинаться с реальных поисковых вопросов: продление, доход, обновление статуса, правила для семьи, бюджетные пороги и сравнение стран.'),
        ('All budgets below represent a comfortable solo образ жизни : private apartment, eating out regularly, local transport, good internet, and occasional entertainment.', 'Все бюджеты ниже рассчитаны для комфортного solo-сценария: отдельное жильё, регулярная еда вне дома, местный транспорт, хороший интернет и умеренный досуг.'),
        ('Cambodia is consistently the cheapest country in Asia for экспатов.', 'Камбоджа часто оказывается самым дешёвым направлением в Азии для экспатов.'),
        ('Phnom Penh offers modern apartments, good internet, and a growing экспат community at rock-bottom prices.', 'Пномпень даёт современные квартиры, нормальный интернет и растущее expat-сообщество при очень низких расходах.'),
        ('Siem Reap is quieter and even cheaper.', 'Сиемреап спокойнее и часто ещё дешевле.'),
        ('The USD is the de facto currency, making budgeting straightforward for Western экспатов.', 'Доллар США широко используется в расчётах, поэтому бюджетировать расходы многим иностранцам проще.'),
        ('Studio apartment (central)', 'Студия в центре'),
        ('Food (mix local + western)', 'Еда: местная + западная'),
        ('Utilities + internet', 'Коммунальные услуги и интернет'),
        ('Entertainment & misc', 'Досуг и прочее'),
        ('Total', 'Итого'),
        ('USD accepted everywhere', 'USD широко принимают'),
        ('Business visa renewable indefinitely', 'Бизнес-визу можно продлевать при соблюдении правил'),
        ('Very low cost of food and rent', 'Очень низкие расходы на еду и аренду'),
        ('Warm welcoming culture', 'Тёплая и дружелюбная культура'),
        ('Healthcare limited outside capital', 'Медицина слабее за пределами столицы'),
        ('Infrastructure still developing', 'Инфраструктура всё ещё развивается'),
        ('Explore Next', 'Что посмотреть дальше'),
        ('Quick Facts', 'Короткие факты'),
        ('Contents', 'Содержание'),
        ('Visa Options', 'Визовые варианты'),
        ('Cost of Living', 'Стоимость жизни'),
        ('Pros &amp; Cons', 'Плюсы и минусы'),
        ('Ready to Move to', 'Готовы планировать переезд в'),
        ('Ready to Move to Asia?', 'Готовы планировать переезд в Азию?'),
        ('Compare costs, visas, and plan your relocation step by step.', 'Сравните расходы, визы и соберите план переезда шаг за шагом.'),
        ('All countries →', 'Все страны →'),
        ('Popular Country Pages', 'Популярные страницы стран'),
        ('What To Read Next', 'Что открыть дальше'),
        ('Official Sources And Next Steps', 'Официальные источники и следующие шаги'),
        ('Official Sources', 'Официальные источники'),
        ('Quick answer', 'Короткий ответ'),
        ('Short answer', 'Короткий ответ'),
        ('Who This Fits And Who Should Be Careful', 'Кому подходит и где стоит быть осторожнее'),
        ('What This Means In Practice', 'Что это значит на практике'),
        ('Confirmed Facts To Start With', 'Подтверждённые факты для старта'),
        ('The Rule That Decides The Whole Plan', 'Правило, которое решает весь сценарий'),
        ('Best Cities', 'Лучшие города'),
        ('Best City', 'Лучший город'),
        ('Time Zone', 'Часовой пояс'),
        ('Best Visa', 'Основной визовый маршрут'),
        ('Budget / mo.', 'Бюджет / мес.'),
        ('from $', 'от $'),
        ('Generally safe', 'в целом безопасно'),
        ('avg', 'в среднем'),
        ('Thai Baht', 'тайский бат'),
        ('Thai (English in cities)', 'тайский, английский в городах'),
        ('Bangkok', 'Бангкок'),
        ('Chiang Mai', 'Чиангмай'),
        ('Phuket', 'Пхукет'),
        ('Koh Samui', 'Самуи'),
        ('Thailand for Expats', 'Таиланд для релокации'),
        ('Pros', 'Плюсы'),
        ('Cons', 'Минусы'),
        ('Urban hub, world-class infrastructure, best for professionals and those who want big city amenities.', 'Крупный городской хаб с сильной инфраструктурой. Лучше для профессионалов и тех, кому нужны сервисы большого города.'),
        ('Affordable digital nomad capital. Huge expat community, co-working spaces, calm pace.', 'Доступная база для digital nomads: большое expat-сообщество, коворкинги и более спокойный ритм.'),
        ('Beach lifestyle with higher cost. Great for those who want sea + amenities.', 'Пляжный сценарий с более высоким бюджетом. Подходит тем, кому нужны море и развитые сервисы.'),
        ('Island life, relaxed pace, smaller expat community, ideal for remote workers seeking calm.', 'Островная жизнь, спокойный ритм и меньшее expat-сообщество. Хорошо для удалёнщиков, которым нужна тишина.'),
        ('Very low cost of living', 'Низкая стоимость жизни'),
        ('Warm climate year-round', 'Тёплый климат круглый год'),
        ('Excellent food scene', 'Сильная гастрономическая сцена'),
        ('Large, established expat community', 'Большое и давно сложившееся expat-сообщество'),
        ('Multiple visa options', 'Несколько визовых маршрутов'),
        ('Great internet infrastructure', 'Хорошая интернет-инфраструктура'),
        ('Complex long-term visa rules', 'Сложные правила long-stay виз'),
        ('Language barrier outside cities', 'Языковой барьер за пределами крупных городов'),
        ('Air pollution in dry season', 'Загрязнение воздуха в сухой сезон'),
        ('High heat and humidity', 'Жара и высокая влажность'),
        ('No path to permanent residency', 'Нет простого пути к постоянной резиденции'),
        ('Compare Thailand with other Asian countries or calculate your exact monthly budget.', 'Сравните Таиланд с другими странами Азии или заранее посчитайте реалистичный месячный бюджет.'),
        ('Compare All Countries', 'Сравнить все страны'),
        ('Compare All Страны', 'Сравнить все страны'),
        ('Beach lifestyle', 'Пляжный образ жизни'),
        ('co-working spaces', 'коворкинги'),
        ('world-class infrastructure', 'инфраструктура мирового уровня'),
        ('big city amenities', 'сервисы большого города'),
        ('remote workers seeking calm', 'удалёнщики, которым нужен спокойный ритм'),
        ('distinct environments for expats, each with its own character, cost, and community', 'разные среды для релокации: со своим характером, бюджетом и сообществом'),
        ('Digital Nomad Visa', 'Digital Nomad виза'),
        ('Long-Term Resident', 'Long-Term Resident'),
        ('digital nomads', 'удалёнщиков'),
        ('Digital nomads', 'Удалёнщики'),
        ('remote workers', 'удалённых специалистов'),
        ('Remote workers', 'Удалённые специалисты'),
        ('expats', 'экспатов'),
        ('Expats', 'Экспаты'),
        ('expat', 'экспат'),
        ('Expat', 'Экспат'),
        ('lifestyle', 'образ жизни'),
        ('Lifestyle', 'Образ жизни'),
        ('shortlist', 'список вариантов'),
        ('Shortlist', 'Список вариантов'),
        ('dependants', 'члены семьи'),
        ('Dependants', 'Члены семьи'),
        ('long-stay', 'долгосрочный'),
        ('Long-stay', 'Долгосрочный'),
        ('remote-work', 'удалённый'),
        ('Remote-work', 'Удалённый'),
        ('Compare costs, visas and образ жизни — pick your destination and explore everything you need to know', 'Сравните расходы, визы и повседневную жизнь, выберите направление и откройте подробный гид.'),
        ('Compare costs, visas and образ жизни &mdash; pick your destination and explore everything you need to know', 'Сравните расходы, визы и повседневную жизнь, выберите направление и откройте подробный гид.'),
        ('Compare costs, visas, and образ жизни across every major Asian relocation destination. Find your perfect country.', 'Сравните расходы, визы и повседневную жизнь по ключевым направлениям Азии. Так проще выбрать страну, которая подходит именно вашему сценарию.'),
        ('Low cost, easy образ жизни, warm weather year-round. The most popular destination for удалёнщиков in Asia.', 'Невысокие расходы, простой быт и тёплая погода круглый год. Одно из самых популярных направлений Азии для удалёнщиков.'),
        ('Low cost, easy образ жизни, warm weather year-round.', 'Невысокие расходы, простой быт и тёплая погода круглый год.'),
        ('Strong visa program, English-friendly, инфраструктура мирового уровня. One of Asia’s most established экспат destinations.', 'Сильные визовые маршруты, английский в быту и инфраструктура мирового уровня. Одно из самых понятных направлений Азии для экспатов.'),
        ('Strong visa program, English-friendly, инфраструктура мирового уровня. One of Asia&#8217;s most established экспат destinations.', 'Сильные визовые маршруты, английский в быту и инфраструктура мирового уровня. Одно из самых понятных направлений Азии для экспатов.'),
        ('English-friendly, MM2H visa, инфраструктура мирового уровня. Top экспат hub in SEA.', 'Английский в быту, MM2H и инфраструктура мирового уровня. Один из сильных expat-хабов Юго-Восточной Азии.'),
        ('World’s nomad capital. Unmatched образ жизни, community and culture. Canggu, Ubud, Seminyak await.', 'Одна из главных nomad-баз мира: сильное сообщество, культура, Чангу, Убуд и Семиньяк.'),
        ('World&#8217;s nomad capital. Unmatched образ жизни, community and culture. Canggu, Ubud, Seminyak await.', 'Одна из главных nomad-баз мира: сильное сообщество, культура, Чангу, Убуд и Семиньяк.'),
        ('Select country, city and образ жизни — get a full monthly budget breakdown instantly.', 'Выберите страну, город и сценарий жизни, чтобы сразу увидеть разбивку месячного бюджета.'),
        ('Select country, city and образ жизни &mdash; get a full monthly budget breakdown instantly.', 'Выберите страну, город и сценарий жизни, чтобы сразу увидеть разбивку месячного бюджета.'),
        ('The 7 core countries chosen by the majority of экспатов and удалёнщиков moving to Asia', '7 основных стран, с которых чаще всего начинают экспаты и удалёнщики при переезде в Азию'),
        ('NOMAD-СТОЛИЦА', 'СТОЛИЦА УДАЛЁНЩИКОВ'),
        ('Bali, Indonesia', 'Бали, Индонезия'),
        ('Free Все гайды и инструменты', 'Бесплатно: все гайды и инструменты'),
        ('LTR Visa and Thailand Elite.', 'LTR Visa и Thailand Elite.'),
        ('/month including rent, food, and transport.', ' в месяц с арендой, едой и транспортом.'),
        ('food-сцена', 'гастрономическая сцена'),
        ('nomad-сцена', 'среда удалёнщиков'),
        ('nomad-сцены', 'среды удалёнщиков'),
    ]
    return replace_many(content, replacements)


def localized_country_content(slug: str, title: str, content: str) -> tuple[str, str]:
    content = localized_generic_content(content)
    forms = COUNTRY_FORMS_RU.get(slug)
    if forms:
        nominative, accusative, prep = forms
        english_name = COUNTRY_EN_NAMES.get(slug, nominative)
        replacements = [
            ("Home", "Главная"),
            ("Countries", "Страны"),
            ("Country Guide", "Гид по стране"),
            (f"Move to {english_name}", f"Переезд в {accusative}"),
            (f"Move to {nominative}", f"Переезд в {accusative}"),
            (f"Move to {english_name}: Complete Relocation Guide 2026", f"Переезд в {accusative}: полный гид 2026"),
            (f"Move to {english_name}: Complete Relocation Guide 2025", f"Переезд в {accusative}: полный гид 2026"),
            (f"Move to {nominative}: Complete Relocation Guide 2026", f"Переезд в {accusative}: полный гид 2026"),
            ("Complete Relocation Guide 2026", "полный гид 2026"),
            ("Complete Relocation Guide 2025", "полный гид 2026"),
            (f"Why Move to {english_name}?", f"Почему стоит рассмотреть {accusative}?"),
            (f"Why Move to {nominative}?", f"Почему стоит рассмотреть {accusative}?"),
            (f"Ready to Move to {english_name}?", f"Готовы планировать переезд в {accusative}?"),
            (f"Ready to Move to {nominative}?", f"Готовы планировать переезд в {accusative}?"),
            (f"Move To {english_name}", f"Переезд в {accusative}"),
            (f"Move To {nominative}", f"Переезд в {accusative}"),
            (f"Costs, cities, visa logic and trade-offs for {english_name}.", f"Расходы, города, визовая логика и реальные компромиссы по стране {nominative}."),
            (f"Costs, cities, visa logic and trade-offs for {nominative}.", f"Расходы, города, визовая логика и реальные компромиссы по стране {nominative}."),
            (f"Everything you need to know about relocating to {english_name} — visas, cost of living, best cities, and practical tips for a successful move.", f"Всё, что нужно знать о переезде в {accusative}: визовые маршруты, стоимость жизни, города и практические детали до реального переезда."),
            (f"Everything you need to know about relocating to {nominative} — visas, cost of living, best cities, and practical tips for a successful move.", f"Всё, что нужно знать о переезде в {accusative}: визовые маршруты, стоимость жизни, города и практические детали до реального переезда."),
            (f"Everything about relocating to {english_name} — MM2H visa, DE Rantau digital nomad program, cost of living, and best cities.", f"Всё о переезде в {accusative}: MM2H, DE Rantau, стоимость жизни и лучшие города для долгого проживания."),
            (f"Everything about relocating to {nominative} — MM2H visa, DE Rantau digital nomad program, cost of living, and best cities.", f"Всё о переезде в {accusative}: MM2H, DE Rantau, стоимость жизни и лучшие города для долгого проживания."),
            ("8 min read", "8 минут чтения"),
            ("Budget / month", "Бюджет / месяц"),
            ("Population", "Население"),
            ("Avg temperature", "Средняя температура"),
            ("Affordability", "Доступность по бюджету"),
            ("Nomad Popularity", "Популярность у nomad-сцены"),
            ("From $700/mo", "От $700/мес."),
            ("From $800/mo", "От $800/мес."),
            ("Overview", "Обзор"),
            ("Visas", "Визы"),
            ("Visa Type", "Тип визы"),
            ("Duration", "Срок"),
            ("Who It&#8217;s For", "Для кого"),
            ("Income Req.", "Требование по доходу"),
            ("Difficulty", "Сложность"),
            ("Tip:", "Практический вывод:"),
            ("Cost of Living", "Стоимость жизни"),
            ("Cost of Living in", "Стоимость жизни в"),
            ("Best Areas", "Города и районы"),
            ("Best Cities to Live in", "Где жить в"),
            ("Budget Lifestyle", "Базовый сценарий"),
            ("Mid-Range", "Средний уровень"),
            ("Comfortable", "Комфортный уровень"),
            ("per month", "в месяц"),
            ("English Widely Spoken", "Английский в повседневной жизни"),
            ("Strong MM2H Visa", "Сильный маршрут MM2H"),
            ("Modern KL", "Современный Куала-Лумпур"),
            ("Diverse Food Scene", "Сильная гастрономическая сцена"),
            ("Low Cost of Living", "Низкая стоимость жизни"),
            ("Warm Climate Year-Round", "Тёплый климат круглый год"),
            ("World-Class Food", "Сильная food-сцена"),
            ("Great Connectivity", "Хорошая транспортная связность"),
            ("Budget/mo", "Бюджет / мес."),
            ("Climate", "Климат"),
            ("Language", "Язык"),
            ("Internet", "Интернет"),
            ("Safety", "Безопасность"),
            ("Why Move to", "Почему стоит рассмотреть"),
            (">Easy<", ">Низкая<"),
            (">Medium<", ">Средняя<"),
            (">Hard<", ">Высокая<"),
        ]
        content = replace_many(content, replacements)
        content = re.sub(
            rf"Everything about relocating to {re.escape(english_name)}[^.]*\.",
            f"Всё о переезде в {accusative}: визы, стоимость жизни, города и практические детали.",
            content,
        )
        content = content.replace(f">{english_name}<", f">{nominative}<")
        slug_specific = {
            "move-to-malaysia": [
                ("Почему стоит рассмотреть Malaysia?", "Почему стоит рассмотреть Малайзию?"),
                ("Everything about relocating to Malaysia — MM2H visa, DE Rantau digital nomad program, cost of living, and best cities.", "Всё о переезде в Малайзию: MM2H, DE Rantau, стоимость жизни и лучшие города для долгого проживания."),
                (">Malaysia<", ">Малайзия<"),
                ("Malaysia Визовые варианты 2026", "Визовые варианты Малайзии в 2026 году"),
                ("English is an official business language — one of the easiest countries in Asia for English speakers to settle in.", "Английский широко используется в бизнесе и быту. Для англоговорящих это один из самых простых входов в Азию."),
                ("One of Asia&#8217;s most established long-term residency programs with 5+5 year renewable stays.", "Один из самых узнаваемых long-stay маршрутов в Азии, с логикой 5+5 лет при выполнении условий программы."),
                ("Kuala Lumpur has world-class hospitals, metro system, international schools, and shopping malls.", "В Куала-Лумпуре сильные больницы, метро, международные школы и привычная городская инфраструктура."),
                ("Incredible mix of Malay, Chinese, and Indian cuisine at street food prices — consistently rated among Asia&#8217;s best.", "Сильная смесь малайской, китайской и индийской кухни. По еде Малайзия почти всегда попадает в короткий список лучших стран Азии."),
                (">5+5 years<", ">5+5 лет<"),
                (">Long-term residents<", ">Долгосрочное проживание<"),
                (">RM40,000/mo passive income<", ">RM40,000/мес. пассивного дохода<"),
                (">12mo renewable<", ">12 месяцев с продлением<"),
                (">Remote workers / nomads<", ">Удалёнщики / digital nomads<"),
                (">$24,000/yr<", ">$24,000/год<"),
                (">2 years<", ">2 года<"),
                (">Company employees<", ">Сотрудники компаний<"),
                (">Employer required<", ">Нужен работодатель<"),
                (">Retirement Visa<", ">Пенсионный маршрут<"),
                (">10 years<", ">10 лет<"),
                (">50+ years old<", ">50+ лет<"),
                (">RM350,000 savings<", ">RM350,000 сбережений<"),
                ("Malaysia is one of the easiest transitions for English speakers. English is widely spoken, infrastructure is modern, and the MM2H visa is one of Asia&#8217;s most established long-term residency programs. Kuala Lumpur is a fully modern city with world-class hospitals and transport.", "Малайзия — один из самых мягких переходов для тех, кому важен английский язык. Английский широко используется в повседневной жизни, инфраструктура современная, а MM2H остаётся одним из самых узнаваемых long-stay маршрутов в Азии. Куала-Лумпур — это полноценный большой город с сильной медициной и удобным транспортом."),
                ("With a cost of living significantly lower than Singapore next door, yet similar infrastructure quality, Malaysia offers exceptional value for expats and digital nomads who want Southeast Asian convenience without sacrificing urban comforts.", "По сравнению с соседним Сингапуром Малайзия заметно дешевле, но по базовому качеству городской инфраструктуры разрыв уже не кажется драматическим. Поэтому для expats и digital nomads она часто даёт очень сильный баланс между удобством Юго-Восточной Азии и нормальным городским комфортом."),
                ("Malaysia offers a range of visa paths for long-term residents, digital nomads, and retirees. Here are the key options:", "У Малайзии есть несколько реальных маршрутов для long-stay, удалённой работы и пенсионных сценариев. Ниже — основные варианты, с которых имеет смысл начинать."),
                ("The DE Rantau digital nomad pass is the easiest path for remote workers — requires just $24,000/yr income proof and is processed quickly online. MM2H is ideal for those wanting long-term stability.", "Для удалёнщиков DE Rantau обычно выглядит самым прямым маршрутом: относительно понятный порог по доходу и быстрая онлайн-логика. MM2H сильнее там, где важна долгая стабильность, а не просто удобная база на ближайший год."),
                ("Malaysia is one of Southeast Asia&#8217;s most affordable countries for expats, with Kuala Lumpur offering urban amenities at a fraction of Singapore or Hong Kong prices.", "Малайзия остаётся одной из самых доступных стран Юго-Восточной Азии для expats, а Куала-Лумпур даёт городской комфорт за заметно меньшие деньги, чем Сингапур или Гонконг."),
                ("Typical monthly expenses in KL: rent $400–700, food $150–300, transport $50–100, entertainment $100–200. Penang is around 20% cheaper than KL for similar lifestyle quality.", "Типичный месячный сценарий в Куала-Лумпуре выглядит так: аренда $400–700, еда $150–300, транспорт $50–100, досуг $100–200. Пенанг при сопоставимом уровне жизни часто оказывается ещё примерно на 20% дешевле."),
            ],
            "move-to-thailand": [
                ("Переезд в Таиланд: Complete Relocation Guide 2026", "Переезд в Таиланд: полный гид 2026"),
                (">Thailand<", ">Таиланд<"),
                ("Thailand Визовые варианты 2026", "Визовые варианты Таиланда в 2026 году"),
                ("Комфортный уровень lifestyle from $800–$1,200/month including rent, food, and transport.", "Комфортный сценарий от $800–$1,200 в месяц с арендой, едой и транспортом."),
                ("Комфортный уровень образ жизни from $800–$1,200/month including rent, food, and transport.", "Комфортный сценарий от $800–$1,200 в месяц с арендой, едой и транспортом."),
                ("Tropical weather with average temperatures of 28–35°C throughout the year.", "Тропический климат с типичными температурами около 28–35°C в течение года."),
                ("Incredible cuisine at street food prices. Meal for $1–3, restaurant for $5–15.", "Сильная food-сцена: уличная еда часто стоит $1–3, обычный ресторан — примерно $5–15."),
                ("Suvarnabhumi airport connects to 150+ destinations worldwide.", "Аэропорт Suvarnabhumi связывает страну с 150+ направлениями по миру."),
                (">10 years<", ">10 лет<"),
                (">Remote workers, retirees, HNW<", ">Удалёнщики, пенсионеры, HNW<"),
                (">$80,000/yr<", ">$80,000/год<"),
                (">5–20 years<", ">5–20 лет<"),
                (">Anyone (paid program)<", ">Платная программа<"),
                (">Purchase from $15,000<", ">Покупка от $15,000<"),
                (">6 months<", ">6 месяцев<"),
                (">Tourists / nomads<", ">Туристы / digital nomads<"),
                (">None<", ">Нет<"),
                (">1 year<", ">1 год<"),
                (">Employed by Thai company<", ">Работа в тайской компании<"),
                (">Employer required<", ">Нужен работодатель<"),
                ("Everything you need to know about relocating to Thailand — visas, cost of living, best cities, and practical tips for a successful move.", "Всё, что нужно знать о переезде в Таиланд: визы, стоимость жизни, города и практические детали для нормального long-stay сценария."),
                ("Why Переезд в Таиланд?", "Почему стоит рассмотреть Таиланд?"),
                ("Thailand is one of the most popular destinations for digital nomads and expats worldwide. With a low cost of living, warm climate, excellent food, and a welcoming culture, it&#8217;s easy to see why hundreds of thousands of foreigners choose Thailand as their new home.", "Таиланд остаётся одним из самых популярных направлений для digital nomads и expats в мире. Невысокая стоимость жизни, тёплый климат, сильная food-сцена и комфортная бытовая среда — именно поэтому туда год за годом едут сотни тысяч иностранцев."),
                ("Thailand is one of the most popular destinations for удалёнщиков and экспатов worldwide. With a low cost of living, warm climate, excellent food, and a welcoming culture, it&#8217;s easy to see why hundreds of thousands of foreigners choose Thailand as their new home.", "Таиланд остаётся одним из самых популярных направлений для удалённых специалистов и экспатов в мире. Невысокая стоимость жизни, тёплый климат, сильная гастрономическая сцена и комфортная бытовая среда — именно поэтому туда год за годом едут сотни тысяч иностранцев."),
                ("From the buzzing capital Bangkok to the laid-back digital nomad capital of Chiang Mai, and the beach lifestyle of Phuket — Thailand offers multiple distinct environments to suit different lifestyles and budgets.", "У Таиланда нет одного единственного сценария. Бангкок, Чиангмай и Пхукет — это три очень разные модели жизни, и именно в этом страна часто выигрывает: можно подбирать среду под свой ритм, бюджет и тип работы."),
                ("From the buzzing capital Бангкок to the laid-back digital nomad capital of Чиангмай, and the beach образ жизни of Пхукет — Thailand offers multiple distinct environments to suit different образ жизниs and budgets.", "У Таиланда нет одного единственного сценария. Бангкок, Чиангмай и Пхукет — это три очень разные модели жизни, и именно в этом страна часто выигрывает: можно подбирать среду под свой ритм, бюджет и тип работы."),
                ("Low Стоимость жизни", "Низкая стоимость жизни"),
                ("Thailand has significantly expanded its long-term visa options in recent years. Here&#8217;s a breakdown of the most relevant visas for expats and digital nomads:", "За последние годы Таиланд заметно расширил выбор long-stay маршрутов. Ниже — те визы, которые чаще всего реально имеют смысл для expats и удалёнщиков."),
                ("Most digital nomads start with METV (multiple-entry tourist visa) while researching long-term options. The LTR Visa is the best path for those earning $80k+ remotely.", "Многие digital nomads начинают с METV, пока изучают долгий сценарий. LTR уже имеет смысл там, где есть сильный удалённый доход и понятный профиль под официальный маршрут."),
                ("Thailand&#8217;s cost of living varies significantly between cities. Bangkok is more expensive than Chiang Mai, but both remain affordable compared to Western standards.", "Стоимость жизни в Таиланде сильно зависит от города. Бангкок ощутимо дороже Чиангмая, но оба варианта всё ещё остаются доступнее многих западных сценариев."),
                ("Typical monthly expenses in Chiang Mai: rent $300–600, food $200–400, transport $50–100, entertainment $100–200. Bangkok adds roughly 30–40% to these figures.", "Типичный месячный сценарий в Чиангмае — это аренда $300–600, еда $200–400, транспорт $50–100 и досуг $100–200. Бангкок обычно добавляет к этим цифрам ещё примерно 30–40%."),
            ],
        }
        content = replace_many(content, slug_specific.get(slug, []))
        content = content.replace(english_name, nominative)
        content = localized_generic_content(content)
        ru_title = f"Переезд в {accusative}: полный гид 2026"
    else:
        ru_title = title
    return ru_title, content


def localized_simple_page_content(slug: str, title: str, content: str) -> tuple[str, str]:
    content = localized_generic_content(content)
    title = RU_STATIC_TITLES.get(slug, title)
    use_ru_hub = slug in {
        "visas",
        "move-to-asia",
        "digital-nomad-visas-asia",
        "retire-in-asia",
    }
    hub_content = ru_hub_content(slug) if use_ru_hub or not strip_html(content).strip() else None
    if hub_content:
        return title, hub_content
    specific = {
        "__home__": [
            ("Updated March 2026 · 5 Countries · Free Tools", "Обновлено в марте 2026 · 5 стран · бесплатные инструменты"),
            ("Updated March 2026 &middot; 5 Countries &middot; Free Tools", "Обновлено в марте 2026 &middot; 5 стран &middot; бесплатные инструменты"),
            ("Relocate to Asia: Compare Countries, Costs & Visas", "Переезд в Азию: страны, расходы и визы"),
            ("Relocate to Asia:", "Переезд в Азию:"),
            ("Compare Countries,", "Сравнить страны,"),
            ("Costs &amp; Visas", "расходы и визы"),
            ("Find the best country to move to, calculate your monthly budget, and plan your relocation step-by-step.", "Сравните страны, прикиньте бюджет и соберите понятный план переезда шаг за шагом."),
            ("Compare Countries", "Сравнить страны"),
            ("Choose Country", "Выбрать страну"),
            ("Cost Calculator", "Калькулятор расходов"),
            ("Destinations", "Направления"),
            ("Best Countries to Move to in Asia in 2026", "Лучшие страны Азии для переезда в 2026 году"),
            ("Compare costs, visas and lifestyle &mdash; pick your destination and explore everything you need to know", "Сравните расходы, визовые маршруты и повседневную логику — а потом уже выбирайте страну глубже."),
            ("Low cost, easy lifestyle, warm weather year-round. The most popular destination for digital nomads in Asia.", "Невысокие базовые расходы, простой повседневный ритм и тёплая погода круглый год. Самое популярное направление для digital nomads в Азии."),
            ("Strong visa program, English-friendly, world-class infrastructure. One of Asia&#8217;s most established expat destinations.", "Сильная визовая база, английский в повседневной жизни и очень удобная инфраструктура. Один из самых понятных expat-маршрутов в Азии."),
            ("World&#8217;s nomad capital. Unmatched lifestyle, community and culture. Canggu, Ubud, Seminyak await.", "Неформальная столица nomad-сцены. Очень сильный lifestyle, сообщество и культурная среда, но со своими бытовыми компромиссами."),
            ("The most affordable option in Asia with vibrant cities and incredible food culture. Ho Chi Minh City, Da Nang, Hanoi.", "Один из самых доступных вариантов в Азии с живыми городами и сильной food-сценой. Обычно начинают с Хошимина, Дананга или Ханоя."),
            ("Tech hub, top safety rating, universal healthcare. Asia&#8217;s most underrated destination for professionals.", "Технологичный хаб с очень сильной безопасностью и медициной. Один из самых недооценённых профессиональных маршрутов в Азии."),
            ("Plan Your Move", "Спланируйте переезд"),
            ("Interactive tools to help you make the right decision", "Инструменты, которые помогают принять решение без лишних догадок."),
            ("Select country, city and lifestyle &mdash; get a full monthly budget breakdown instantly.", "Выберите страну, город и сценарий жизни — и сразу получите помесячную разбивку бюджета."),
            ("Relocation Budget Planner", "Планировщик бюджета на переезд"),
            ("Plan your total move cost &mdash; visa fees, flights, first month setup and savings buffer.", "Соберите полный бюджет переезда: визовые сборы, перелёты, стартовые траты и финансовую подушку."),
            ("Country Comparison Tool", "Инструмент сравнения стран"),
            ("Compare any two countries side-by-side &mdash; cost, safety, visas, climate and quality of life.", "Сравните любые две страны по расходам, безопасности, визам, климату и качеству жизни."),
            ("Try Calculator &rarr;", "Открыть калькулятор &rarr;"),
            ("Plan Budget &rarr;", "Открыть планировщик &rarr;"),
            ("Compare Now &rarr;", "Сравнить сейчас &rarr;"),
            ("Explore Guide", "Открыть гид"),
            ("From $800/mo", "От $800/мес."),
            ("From $700/mo", "От $700/мес."),
            ("From $600/mo", "От $600/мес."),
            ("From $1,200/mo", "От $1,200/мес."),
            ("Can’t Decide? Compare Head-to-Head", "Трудно выбрать? Сравните варианты напрямую"),
            ("Can&#8217;t Decide? Compare Head-to-Head", "Трудно выбрать? Сравните варианты напрямую"),
            ("Detailed breakdowns to help you make the right choice", "Подробные сравнения по расходам, визам и повседневной логике."),
            ("Which is cheaper, easier to get a visa, and better for long-term living? Full comparison across costs, lifestyle, and visas.", "Что дешевле, где проще визовый маршрут и какая страна лучше для long-stay: сравнение расходов, быта и виз."),
            ("Lifestyle vs infrastructure &mdash; the two most popular nomad destinations compared across every key metric.", "Lifestyle против инфраструктуры: сравнение двух популярных nomad-направлений по ключевым метрикам."),
            ("Bali vs Thailand", "Бали vs Таиланд"),
            ("Thailand vs Malaysia", "Таиланд vs Малайзия"),
            ("Monthly Budget Comparison 2026", "Сравнение ежемесячного бюджета в 2026 году"),
            ("Budget, mid-range and comfortable lifestyle costs per country", "Бюджетный, средний и комфортный сценарий по странам"),
            ("Country", "Страна"),
            ("Budget", "Бюджет"),
            ("Rating", "Оценка"),
            ("Cheapest", "Самый дешёвый вариант"),
            ("Very Affordable", "Очень доступно"),
            ("Affordable", "Доступно"),
            ("Mid-Range", "Средний уровень"),
            ("Comfortable", "Комфортный"),
            ("Process", "Процесс"),
            ("Choose a Страна", "Выберите страну"),
            ("A simple 4-step framework used by thousands of successful expats", "Простая логика из 4 шагов, которая помогает не начинать переезд с хаоса"),
            ("Choose a Country", "Выберите страну"),
            ("Compare Thailand, Malaysia, Bali, Vietnam and Taiwan based on cost, visa and lifestyle.", "Сравните Таиланд, Малайзию, Бали, Вьетнам и Тайвань по расходам, визам и повседневной логике."),
            ("Check Визовые варианты", "Проверьте визы"),
            ("Find the right visa &mdash; digital nomad, long-stay, retirement or work permit.", "Сначала разберитесь с маршрутом: digital nomad, long-stay, retirement или work permit."),
            ("Calculate Your Budget", "Посчитайте бюджет"),
            ("Use our cost calculator to estimate your exact monthly expenses based on your lifestyle.", "Используйте калькулятор, чтобы прикинуть месячные расходы под ваш стиль жизни."),
            ("How to Relocate to Asia", "Как подойти к переезду в Азию"),
            ("Why Trust Us", "Почему этим данным можно доверять"),
            ("Data-Driven Relocation Research", "Релокационный ресёрч на основе данных"),
            ("Not opinions &mdash; verified data updated for 2026", "Не мнения, а проверенные данные, обновлённые под 2026 год"),
            ("Countries covered in depth", "стран разобрано подробно"),
            ("Data points per country", "точек данных по каждой стране"),
            ("All data updated this year", "данные обновлены в этом году"),
            ("All tools &amp; guides free", "все инструменты и гайды бесплатны"),
            ("Use our relocation checklist and step-by-step guides to execute your move with confidence.", "Используйте чеклисты и пошаговые гайды, чтобы планировать переезд без хаоса."),
            ("Asia has become the world&#8217;s most popular destination for expats, digital nomads, retirees and families seeking better lifestyle, lower costs and new opportunities.", "Азия стала одним из самых популярных направлений для expats, digital nomads, пенсионеров и семей, которым важны ниже расходы, другой ритм жизни и больше вариантов для выбора."),
            ("Asia has become the world&#8217;s most popular destination for expats, digital nomads, retirees, and location-independent professionals. Countries like Thailand, Malaysia, Bali, Vietnam, and Taiwan offer lifestyles that are simply not achievable at equivalent cost in Western countries.", "Азия стала одним из самых популярных направлений для expats, digital nomads, пенсионеров и специалистов, не привязанных к офису. Таиланд, Малайзия, Бали, Вьетнам и Тайвань дают уровень быта, который в западных странах часто стоит заметно дороже."),
            ("Relocating to Asia: The Complete Overview", "Переезд в Азию: короткая общая картина"),
            ("Why Move to Asia?", "Почему люди вообще выбирают Азию?"),
            ("The primary appeal is the dramatic reduction in cost of living. A comfortable lifestyle in Bangkok or Chiang Mai can cost $1,200&ndash;1,800 per month &mdash; a fraction of what the same quality of life would cost in London, New York, or Sydney. Malaysia offers modern infrastructure and an English-speaking population. Bali has built the world&#8217;s most vibrant digital nomad ecosystem.", "Главная причина — разница в стоимости жизни. Комфортный сценарий в Бангкоке или Чиангмае может укладываться в $1,200–1,800 в месяц, тогда как похожий уровень в Лондоне, Нью-Йорке или Сиднее стоит совсем других денег. Малайзия даёт современную инфраструктуру и сильную англоязычную среду. Бали держится на одном из самых активных digital nomad сообществ в мире."),
            ("How to Choose the Right Country", "Как выбрать подходящую страну"),
            ("How to Choose the Right Страна", "Как выбрать подходящую страну"),
            ("If cost is the primary factor, Vietnam or Malaysia offer the best value. If lifestyle matters most, Bali&#8217;s nomad ecosystem is unmatched. For long-term visa stability, Malaysia&#8217;s MM2H program offers the strongest framework. If safety is non-negotiable, Taiwan is the clear winner. Use our Инструмент сравнения стран to make a data-driven decision.", "Если главный фильтр — бюджет, чаще всего в shortlist попадают Вьетнам и Малайзия. Если важнее lifestyle и сообщество, Бали сложно игнорировать. Для долгой визовой устойчивости стоит смотреть на MM2H в Малайзии. Если безопасность — жёсткое условие, Тайвань обычно выходит очень сильным кандидатом. Для первого отбора используйте инструмент сравнения стран."),
            ("If cost is the primary factor, Vietnam or Malaysia offer the best value. If lifestyle matters most, Bali&#8217;s nomad ecosystem is unmatched. For long-term visa stability, Malaysia&#8217;s MM2H program offers the strongest framework. If safety is non-negotiable, Taiwan is the clear winner. Use our Инструмент сравнения стран to make a data-driven decision.", "Если главный фильтр — бюджет, чаще всего в shortlist попадают Вьетнам и Малайзия. Если важнее lifestyle и сообщество, Бали сложно игнорировать. Для долгой визовой устойчивости стоит смотреть на MM2H в Малайзии. Если безопасность — жёсткое условие, Тайвань обычно выходит очень сильным кандидатом. Для первого отбора используйте инструмент сравнения стран."),
        ],
        "cheapest-countries-in-asia": [
            ("Updated March 2026 · Real Expat Data", "Обновлено в марте 2026 · реальные расходы экспатов"),
            ("Real Expat Data", "реальные расходы экспатов"),
            ("Cheapest Countries in Asia to Live In 2026", "Самые дешёвые страны Азии для жизни в 2026 году"),
            ("Самые дешёвые страны Азии to Live In 2026", "Самые дешёвые страны Азии для жизни в 2026 году"),
            ("Ranked by real monthly costs — rent, food, transport and lifestyle — for a comfortable solo expat life.", "Рейтинг по реальным месячным расходам: аренда, еда, транспорт и базовый комфорт для одного человека."),
            ("Lowest budget", "Минимальный бюджет"),
            ("Countries ranked", "Стран в рейтинге"),
            ("Updated data", "Данные обновлены"),
            ("Asia offers some of the world’s most affordable places to live — without sacrificing comfort, safety, or quality of life.", "В Азии есть направления, где можно жить заметно дешевле, не отказываясь от нормального жилья, безопасности и базового качества жизни."),
            ("Asia offers some of the world&#8217;s most affordable places to live — without sacrificing comfort, safety, or quality of life.", "В Азии есть направления, где можно жить заметно дешевле, не отказываясь от нормального жилья, безопасности и базового качества жизни."),
            ("Whether you’re a budget traveller, digital nomad, or early retiree, the countries on this list let you live well for a fraction of what you’d spend in the West.", "Для budget traveller, digital nomad или раннего пенсионера это список стран, где расходы часто ниже западных сценариев в несколько раз."),
            ("Whether you&#8217;re a budget traveller, digital nomad, or early retiree, the countries on this list let you live well for a fraction of what you&#8217;d spend in the West.", "Для budget traveller, digital nomad или раннего пенсионера это список стран, где расходы часто ниже западных сценариев в несколько раз."),
            ("All budgets below represent a comfortable solo lifestyle : private apartment, eating out regularly, local transport, good internet, and occasional entertainment.", "Бюджеты ниже считаются для комфортного solo-сценария: отдельное жильё, регулярная еда вне дома, местный транспорт, хороший интернет и умеренный досуг."),
            ("All budgets below represent a <strong>comfortable solo lifestyle</strong>: private apartment, eating out regularly, local transport, good internet, and occasional entertainment.", "Бюджеты ниже считаются для <strong>комфортного solo-сценария</strong>: отдельное жильё, регулярная еда вне дома, местный транспорт, хороший интернет и умеренный досуг."),
            ("Ultra-budget figures assume shared housing and cooking at home.", "Ультрабюджетные цифры предполагают комнату или shared housing и регулярную готовку дома."),
            ("Contents", "Содержание"),
            ("Cambodia — from", "Камбоджа — от"),
            ("Laos — from", "Лаос — от"),
            ("Myanmar — from", "Мьянма — от"),
            ("Nepal — from", "Непал — от"),
            ("Vietnam — from", "Вьетнам — от"),
            ("India — from", "Индия — от"),
            ("Philippines — from", "Филиппины — от"),
            ("Indonesia (Bali) — from", "Индонезия (Бали) — от"),
            ("Thailand — from", "Таиланд — от"),
            ("Malaysia — from", "Малайзия — от"),
            ("/mo", "/мес."),
            ("Full Cost Comparison Table 2026", "Полная таблица расходов 2026"),
            ("Full Cost Сравнение Table", "Полная таблица расходов"),
            ("Frequently Asked Questions", "FAQ"),
            ("Which Cheap Asian Country is Right for You?", "Какую недорогую страну Азии выбрать"),
            ("Monthly Cost Breakdown", "Разбивка расходов за месяц"),
            ("Ultra budget", "Ультрабюджет"),
            ("Comfortable+", "Комфорт+"),
            ("Comfortable", "Комфортно"),
            ("Currency used", "Валюта в быту"),
            ("Cheapest in Asia", "Самый дешёвый вариант в Азии"),
            ("Peaceful & Affordable", "Спокойно и недорого"),
            ("Best Value in South Asia", "Лучшее соотношение цены в Южной Азии"),
            ("Best Infrastructure for the Price", "Лучшая инфраструктура за эти деньги"),
            ("Best Value for Long-Term Living", "Сильный вариант для долгого проживания"),
            ("Best for English Speakers on a Budget", "Лучше для тех, кому нужен английский при малом бюджете"),
            ("Best Lifestyle per Dollar", "Лучший lifestyle за свои деньги"),
            ("Best All-Round Value", "Самый сбалансированный вариант"),
            ("Best Value with English + Modern Life", "Лучший баланс английского и городского комфорта"),
            ("Pros", "Плюсы"),
            ("Cons", "Минусы"),
            ("Explore Cambodia", "Открыть Камбоджу"),
            ("Explore Laos", "Открыть Лаос"),
            ("Explore Nepal", "Открыть Непал"),
            ("Explore Vietnam", "Открыть Вьетнам"),
            ("Explore India", "Открыть Индию"),
            ("Explore Philippines", "Открыть Филиппины"),
            ("Explore Bali", "Открыть Бали"),
            ("Explore Thailand", "Открыть Таиланд"),
            ("Explore Malaysia", "Открыть Малайзию"),
            ("Ultra cheap", "Очень дешево"),
            ("Budget", "Бюджетно"),
            ("Mid-range", "Средний уровень"),
            ("Visa Ease", "Виза"),
            ("English", "Английский"),
            ("Tier", "Категория"),
            ("Basic", "Базовый"),
            ("Limited", "Ограниченный"),
            ("Good", "Хороший"),
            ("Official", "Официальный"),
            ("Tourist", "Туристический"),
            ("Widely spoken", "широко используется"),
            ("10 Tips to Live Cheaply in Asia in 2026", "10 практичных способов жить дешевле в Азии в 2026 году"),
            ("Eat local:", "Ешьте локально:"),
            ("Rent long-term:", "Снимайте на долгий срок:"),
            ("Use a scooter:", "Используйте скутер:"),
            ("Avoid tourist areas:", "Не селитесь в самом туристическом районе:"),
            ("Get a local SIM:", "Подключите местную SIM:"),
            ("Use coworking day passes:", "Берите day pass в коворкинге:"),
            ("Withdraw large amounts:", "Снимайте деньги реже и крупнее:"),
            ("Cook occasionally:", "Иногда готовьте дома:"),
            ("Travel in shoulder season:", "Планируйте поездки вне пика сезона:"),
            ("Use the Cost Calculator:", "Используйте калькулятор расходов:"),
            ("What is the cheapest country in Asia to live in?", "Какая страна Азии самая дешёвая для жизни?"),
            ("Can I live in Asia on $1,000 a month?", "Можно ли жить в Азии на $1,000 в месяц?"),
            ("Which cheap Asian country has the best internet for remote work?", "Где среди недорогих стран Азии лучший интернет для удалённой работы?"),
            ("Which cheap Asian country is easiest to get a long-term visa?", "Где проще с long-stay визой среди недорогих стран Азии?"),
            ("Is it safe to live cheaply in Asia?", "Безопасно ли жить в Азии с небольшим бюджетом?"),
            ("Use our Cost of Living Calculator to get a personalised budget estimate for any Asian country, or browse all 20 country guides for detailed relocation information.", "Используйте калькулятор стоимости жизни для своего сценария или откройте страновые гайды, если хотите проверить визы, города и реальные компромиссы."),
            ("Cambodia is consistently the cheapest country in Asia for expats. Phnom Penh offers modern apartments, good internet, and a growing expat community at rock-bottom prices. Siem Reap is quieter and even cheaper. The USD is the de facto currency, making budgeting straightforward for Western expats.", "Камбоджа обычно выходит самой дешёвой страной Азии для экспатов. В Пномпене есть современные квартиры, нормальный интернет и растущее expat-сообщество при очень низких расходах. Сиемреап спокойнее и часто ещё дешевле. Доллар США широко используется в быту, поэтому бюджет проще считать заранее."),
            ("Laos is Southeast Asia’s hidden gem — rarely crowded, genuinely peaceful, and extremely affordable. Vientiane (the capital) is a sleepy city with a surprisingly pleasant expat scene. Luang Prabang is a UNESCO heritage town beloved by slow travellers. Internet and infrastructure have improved significantly by 2026.", "Лаос — спокойный и недооценённый вариант Юго-Восточной Азии. Здесь меньше шума, ниже темп и часто ниже расходы. Вьентьян выглядит сонным, но для части экспатов это плюс. Луангпхабанг любят slow travellers. Интернет и инфраструктура стали лучше, но это всё ещё не самый сильный выбор для тяжёлой онлайн-работы."),
            ("Nepal is dramatically underrated as a long-term base. Kathmandu has a thriving expat and NGO community, excellent trekking access, and a cost of living among the lowest in Asia. Pokhara is even cheaper and surrounded by the Himalayas. English is widely spoken, and the culture is warm and welcoming.", "Непал часто недооценивают как базу на несколько месяцев. В Катманду есть expat- и NGO-среда, доступ к трекингу и один из самых низких уровней расходов в Азии. Покхара спокойнее и дешевле. Английский встречается часто, но инфраструктуру и медицину нужно проверять под свой сценарий."),
            ("Vietnam is the sweet spot of cheap living + excellent infrastructure. Da Nang offers some of the fastest internet in Southeast Asia, beautiful beaches, and a modern lifestyle for $800–1,100/month. Ho Chi Minh City is more expensive but packed with co-working spaces and a booming startup scene. Hanoi blends tradition with affordability.", "Вьетнам часто даёт лучший баланс цены и инфраструктуры. Дананг подходит тем, кому нужны море, быстрый интернет и понятный городской быт. Хошимин дороже, зато сильнее по coworking и бизнес-среде. Ханой дешевле части крупных азиатских столиц и даёт совсем другой, более традиционный ритм."),
            ("India’s sheer size means costs vary wildly by location. Goa remains the expat favourite — beach lifestyle, good food, and English everywhere for $900–1,400/month. Bangalore is the tech hub with excellent infrastructure. Rishikesh and Dharamsala attract the yoga/spiritual crowd at very low costs. The e-visa is valid for up to 365 days.", "Индия слишком большая, чтобы оценивать её одной цифрой. Гоа остаётся знакомой expat-базой с пляжным бытом, едой и английским языком. Бангалор сильнее для tech-среды. Ришикеш и Дхарамсала тянут людей, которым важны йога, горы и низкие расходы. Визовый режим нужно проверять отдельно под гражданство и срок."),
            ("The Philippines is the most English-friendly cheap country in Asia. Cebu offers a modern city with beaches nearby for under $1,000/month. Davao is even cheaper and increasingly popular with expats. Island lifestyle in Siargao or El Nido is possible from $800/month. Tourist visas can be extended up to 36 months without leaving the country.", "Филиппины — один из самых понятных дешёвых вариантов для тех, кому важен английский. Себу даёт городской быт и пляжи рядом. Давао часто дешевле. Сиаргао и Эль-Нидо подходят тем, кто хочет островной lifestyle, но там сильнее сезонность и зависимость от района. Визовые продления выглядят гибко, но правила нужно сверять перед планированием."),
            ("Bali offers unmatched lifestyle value — world-class coworking spaces, stunning nature, a massive international community, and incredible food, all at Southeast Asian prices. Canggu is the nomad capital; Ubud is for the spiritual and creative crowd; Seminyak for nightlife. The Digital Nomad Visa (E33G) exempts foreign income from Indonesian tax for 60–180 days.", "Бали силён не тем, что он самый дешёвый, а тем, сколько lifestyle даёт за свои деньги: coworking, природа, международное сообщество, еда и привычная среда для удалённой работы. Чангу — nomad-база, Убуд — более творческий и спокойный сценарий, Семиньяк — nightlife. Но визовую и налоговую логику Индонезии нельзя заменять слухами из чатов."),
            ("Chiang Mai remains the most affordable of Thailand’s major expat cities — from $850/month comfortably. Bangkok costs more ($1,200–1,800 for a comfortable lifestyle) but offers world-class infrastructure and nightlife. Hua Hin, Pattaya, and Koh Samui attract retirees seeking beach life at mid-range costs. Thailand’s LTR Visa and Thailand Elite offer excellent long-term options.", "Чиангмай остаётся самым доступным из крупных expat-городов Таиланда. Бангкок дороже, зато даёт инфраструктуру, медицину, транспорт и деловую среду другого уровня. Хуахин, Паттайя и Самуи чаще смотрят пенсионеры и те, кому нужен морской быт. Визовых маршрутов у Таиланда много, но именно поэтому их нужно сравнивать аккуратно."),
            ("Malaysia is the priciest on this list but offers something no other budget Asian country does: English everywhere, First World infrastructure, excellent private healthcare, and the region’s best long-term visa (MM2H). Kuala Lumpur costs $1,200–2,000/month comfortably; Penang and Ipoh offer the same quality at 20–30% less.", "Малайзия самая дорогая в этом списке, но она даёт то, чего часто не хватает более дешёвым странам: английский в быту, сильную городскую инфраструктуру, частную медицину и понятные long-stay маршруты вроде MM2H. Куала-Лумпур дороже, Пенанг и Ипох могут дать похожее качество жизни дешевле."),
        ],
        "tools": [
            ("Free Relocation Tools for Asia 2026", "Бесплатные инструменты для релокации в Азию в 2026 году"),
            ("Free Relocation Tools", "Бесплатные инструменты для релокации"),
            ("<h1>Free <span>Relocation Tools</span> for Asia 2026</h1>", "<h1>Бесплатные <span>инструменты релокации</span> в Азию 2026</h1>"),
            ("Free · Без регистрации · Моментальный результат", "Бесплатно · без регистрации · быстрый расчёт"),
            ("<span class=\"tp-tool-tag\">Calculator</span>", "<span class=\"tp-tool-tag\">Калькулятор</span>"),
            ("<span class=\"tp-tool-tag\" style=\"background:#f0fdf4;color:#16a34a\">Planning Tool</span>", "<span class=\"tp-tool-tag\" style=\"background:#f0fdf4;color:#16a34a\">Планировщик</span>"),
            ("<span class=\"tp-tool-tag\" style=\"background:#fef3c7;color:#92400e\">Comparison</span>", "<span class=\"tp-tool-tag\" style=\"background:#fef3c7;color:#92400e\">Сравнение</span>"),
            ("<span class=\"tp-tool-tag\">Most Popular</span>", "<span class=\"tp-tool-tag\">Самый популярный</span>"),
            ("Most Popular", "Самый популярный"),
            ("<h3>Relocation Планировщик бюджета</h3>", "<h3>Планировщик бюджета переезда</h3>"),
            ("<h3>Country Comparison Tool</h3>", "<h3>Сравнение стран</h3>"),
            ("<h3>Cost of Living Calculator</h3>", "<h3>Калькулятор стоимости жизни</h3>"),
            ("Select country, city and lifestyle level. Get an instant personalised monthly budget with full expense breakdown — rent, food, transport, entertainment and more.", "Выберите страну, город и уровень жизни. Получите быстрый расчёт месячного бюджета: аренда, еда, транспорт, досуг и базовые расходы."),
            ("Select your destination country, city and lifestyle level. Get an instant personalised monthly budget with full expense breakdown — rent, food, transport, entertainment and more.", "Выберите страну, город и уровень жизни. Получите быстрый расчёт месячного бюджета: аренда, еда, транспорт, досуг и базовые расходы."),
            ("Calculate your total one-time moving cost including visa fees, flights, shipping, deposits and first-month setup expenses.", "Посчитайте разовые расходы на переезд: визовые сборы, перелёты, багаж, депозиты и первый месяц на месте."),
            ("Calculate your total one-time relocation cost including visa fees, flights, shipping, deposits and first-month setup.", "Посчитайте разовые расходы на переезд: визовые сборы, перелёты, багаж, депозиты и первый месяц на месте."),
            ("Calculate your total one-time relocation cost including visa fees, flights, shipping, deposits and first-month setup expenses.", "Посчитайте разовые расходы на переезд: визовые сборы, перелёты, багаж, депозиты и первый месяц на месте."),
            ("✓ Free to use", "✓ Бесплатно"),
            ("Plan your move to Asia with data-driven tools. Calculate costs, plan budgets and compare countries — all free, all instant.", "Планируйте переезд в Азию с практическими инструментами. Считайте расходы, собирайте бюджет и сравнивайте страны — без регистрации и лишней воды."),
            ("Three interactive tools to help you make the right relocation decision.", "Три интерактивных инструмента, которые помогают принять решение о переезде спокойнее и точнее."),
            ("Three interactive tools to help you make the right relocation decision — no account required.", "Три практических инструмента для раннего планирования переезда — без аккаунта и регистрации."),
            ("Know exactly how much you need before you move.", "Поймите порядок расходов до переезда, а не после покупки билетов."),
            ("Compare any two countries side-by-side across 15+ metrics — cost of living, safety score, healthcare, climate, visa difficulty, internet speed and quality of life index.", "Сравните две страны по ключевым метрикам: расходы, безопасность, медицина, климат, визовая сложность, интернет и качество жизни."),
            ("Why Use Our Tools", "Зачем пользоваться этими инструментами"),
            ("All budget estimates are based on verified expat data from Bangkok, Kuala Lumpur, Bali, Ho Chi Minh City and Taipei — updated for 2026.", "Бюджетные оценки собраны по реальным сценариям в Бангкоке, Куала-Лумпуре, Бали, Хошимине и Тайбэе и обновлены под 2026 год."),
            ("No waiting, no email required. Enter your preferences and get your personalised relocation budget in seconds.", "Без ожидания и без email. Укажите параметры и получите расчёт бюджета за несколько секунд."),
            ("Lifestyle-Based Results", "Расчёт под ваш стиль жизни"),
            ("Results adapt to your lifestyle — budget backpacker, mid-range expat, or comfortable professional. Not one-size-fits-all.", "Расчёт меняется под ваш сценарий: бюджетный формат, средний expat-уровень или комфортный профессиональный переезд."),
            ("No Account Needed", "Аккаунт не нужен"),
            ("All tools are completely free and require zero sign-up. No email, no credit card, no paywall. Just answers.", "Все инструменты бесплатные и работают без регистрации. Никакого email, карты и paywall."),
            ("Frequently Asked Questions", "Частые вопросы"),
            ("Common questions about our relocation planning tools.", "Частые вопросы по инструментам планирования переезда."),
            ("How accurate is the Калькулятор стоимости жизни?", "Насколько точен калькулятор стоимости жизни?"),
            ("Our data is based on aggregated expat reports, Numbeo indices, and local research updated quarterly. Estimates are accurate within 10–15% for most lifestyle types. Real costs vary by neighbourhood, personal habits, and market fluctuations.", "Оценки опираются на агрегированные expat-отчёты, индексы стоимости жизни и локальные проверки. Для большинства сценариев это ориентир с погрешностью примерно 10–15%, но район, привычки и рынок жилья всё равно меняют итог."),
            ("Which countries are covered?", "Какие страны есть в инструментах?"),
            ("All tools currently cover Thailand (Bangkok, Chiang Mai, Phuket), Malaysia (Kuala Lumpur, Penang), Indonesia/Bali (Canggu, Ubud, Seminyak), Vietnam (Ho Chi Minh City, Hanoi, Da Nang), and Taiwan (Taipei). More countries coming soon.", "Сейчас инструменты покрывают Таиланд, Малайзию, Индонезию / Бали, Вьетнам и Тайвань. Больше стран добавим позже."),
            ("Is the Relocation Планировщик бюджета a one-time or monthly cost tool?", "Планировщик бюджета считает разовые или месячные расходы?"),
            ("The Планировщик бюджета calculates your one-time upfront relocation costs — visa fees, flights, shipping, deposits. The Калькулятор стоимости жизни handles ongoing monthly expenses. Use both together for a complete financial picture.", "Планировщик считает стартовые разовые расходы: визы, перелёты, багаж, депозиты и первый месяц. Калькулятор стоимости жизни считает регулярный месячный бюджет. Лучше использовать оба."),
            ("Can I save my results?", "Можно ли сохранить результат?"),
            ("Currently results are shown instantly on screen. We recommend taking a screenshot or copying your figures. Saved profiles and PDF export are on our roadmap for later in 2026.", "Сейчас результат показывается на экране. Проще сделать скриншот или перенести цифры в свой файл. Сохранённые профили и PDF-экспорт запланированы позже."),
            ("About Our Бесплатные инструменты для релокации", "О наших инструментах релокации"),
            ("Moving to Asia is one of the biggest financial and lifestyle decisions you can make. Our free relocation planning tools are designed to remove the guesswork from that decision.", "Переезд в Азию — это не только билеты и чемодан. Это деньги, визы, жильё, медицина, быт и запасной план. Инструменты нужны, чтобы убрать хотя бы часть догадок из этого решения."),
            ("Whether you are comparing Thailand and Malaysia on cost, trying to understand how far your monthly budget goes in Bali, or calculating the total upfront cost of relocating to Vietnam — our tools give you real, actionable numbers in seconds.", "Если вы сравниваете Таиланд и Малайзию, прикидываете бюджет на Бали или считаете стартовые расходы для Вьетнама, инструменты быстро дают рабочий порядок цифр."),
            ("The Калькулятор стоимости жизни lets you customise your lifestyle profile and instantly see a monthly budget breakdown for any of our five covered countries.", "Калькулятор стоимости жизни даёт помесячную разбивку под выбранный стиль жизни."),
            ("The Relocation Планировщик бюджета focuses on the one-time costs that most guides overlook — visa application fees, international flights, shipping, rental deposits, and first-month setup.", "Планировщик бюджета ловит разовые расходы, которые часто забывают: визовые сборы, перелёты, багаж, депозиты и первый месяц."),
            ("The Country Comparison Tool puts two destinations side-by-side across more than 15 metrics so you can make a data-driven choice.", "Инструмент сравнения ставит две страны рядом по 15+ метрикам, чтобы решение было не на ощущениях."),
            ("The Калькулятор стоимости жизни lets you customise your lifestyle profile and instantly see a monthly budget breakdown for any of our five covered countries. The Relocation Планировщик бюджета focuses on the one-time costs that most guides overlook — visa application fees, international flights, shipping, rental deposits, and first-month setup. The Country Comparison Tool puts two destinations side-by-side across more than 15 metrics so you can make a data-driven choice.", "Калькулятор стоимости жизни даёт помесячную разбивку под выбранный стиль жизни. Планировщик бюджета ловит разовые расходы, которые часто забывают: визовые сборы, перелёты, багаж, депозиты и первый месяц. Инструмент сравнения ставит две страны рядом по 15+ метрикам, чтобы решение было не на ощущениях."),
            ("All tools are completely free, require no account or email, and are updated regularly to reflect current visa", "Все инструменты бесплатные, не требуют аккаунта или email и регулярно обновляются под актуальные визовые"),
            ("Choose Your Tool", "Выберите подходящий инструмент"),
            ("Try Calculator", "Открыть калькулятор"),
            ("Plan Budget", "Открыть планировщик"),
            ("Compare Now", "Сравнить сейчас"),
            ("Built for Real Relocation Decisions", "Собрано под реальные решения о переезде"),
            ("Real Cost Data", "Реальные данные по расходам"),
            ("Not generic travel data — purpose-built for people planning a permanent or long-term move to Asia.", "Это не туристические советы, а рабочие инструменты для тех, кто планирует долгий или постоянный переезд в Азию."),
        ],
        "cost-calculator": [
            ("Cost of Living Calculator — Asia 2026", "Калькулятор стоимости жизни в Азии — 2026"),
            ("Cost of Living Calculator &mdash; Asia 2026", "Калькулятор стоимости жизни в Азии &mdash; 2026"),
            ("Real monthly budget for 19 Asian countries &middot; Prices in your currency &middot; Live exchange rates", "Реалистичный ежемесячный бюджет по странам Азии · суммы в вашей валюте · актуальные курсы."),
            ("Rate:", "Курс:"),
            ("loading&#8230;", "загрузка&#8230;"),
            ("Display currency", "Валюта расчёта"),
            ("Country", "Страна"),
            ("Accommodation", "Жильё"),
            ("Food style", "Питание"),
            ("Food Style", "Питание"),
            ("Transport", "Транспорт"),
            ("Lifestyle", "Образ жизни"),
            ("People", "Состав"),
            ("Calculate Monthly Budget", "Рассчитать ежемесячный бюджет"),
            ("<option value=\"thailand\">Thailand</option>", "<option value=\"thailand\">Таиланд</option>"),
            ("<option value=\"malaysia\">Malaysia</option>", "<option value=\"malaysia\">Малайзия</option>"),
            ("<option value=\"vietnam\">Vietnam</option>", "<option value=\"vietnam\">Вьетнам</option>"),
            ("<option value=\"bali\">Bali / Indonesia</option>", "<option value=\"bali\">Бали / Индонезия</option>"),
            ("<option value=\"philippines\">Philippines</option>", "<option value=\"philippines\">Филиппины</option>"),
            ("<option value=\"cambodia\">Cambodia</option>", "<option value=\"cambodia\">Камбоджа</option>"),
            ("<option value=\"singapore\">Singapore</option>", "<option value=\"singapore\">Сингапур</option>"),
            ("<option value=\"japan\">Japan</option>", "<option value=\"japan\">Япония</option>"),
            ("<option value=\"south_korea\">South Korea</option>", "<option value=\"south_korea\">Южная Корея</option>"),
            ("<option value=\"taiwan\">Taiwan</option>", "<option value=\"taiwan\">Тайвань</option>"),
            ("<option value=\"china\">China</option>", "<option value=\"china\">Китай</option>"),
            ("<option value=\"uae\">UAE / Dubai</option>", "<option value=\"uae\">ОАЭ / Дубай</option>"),
            ("<option value=\"india\">India</option>", "<option value=\"india\">Индия</option>"),
            ("<option value=\"sri_lanka\">Sri Lanka</option>", "<option value=\"sri_lanka\">Шри-Ланка</option>"),
            ("<option value=\"nepal\">Nepal</option>", "<option value=\"nepal\">Непал</option>"),
            ("<option value=\"laos\">Laos</option>", "<option value=\"laos\">Лаос</option>"),
            ("<option value=\"myanmar\">Myanmar</option>", "<option value=\"myanmar\">Мьянма</option>"),
            ("<option value=\"kazakhstan\">Kazakhstan</option>", "<option value=\"kazakhstan\">Казахстан</option>"),
            ("<option value=\"uzbekistan\">Uzbekistan</option>", "<option value=\"uzbekistan\">Узбекистан</option>"),
            ("Budget (shared/hostel)", "Бюджетный вариант (комната / hostel)"),
            ("Comfortable (modern 1BR)", "Комфортный вариант (современная 1BR)"),
            ("Luxury (2BR premium)", "Премиум (2BR)"),
            ("Mid-range (1BR apartment)", "Средний уровень (1-bedroom квартира)"),
            ("Budget studio / room", "Бюджетная студия / комната"),
            ("Comfortable condo / central", "Комфортное жильё / ближе к центру"),
            ("Mostly local / street food", "В основном местная еда / стритфуд"),
            ("Local food mostly", "В основном местная еда"),
            ("Mix of local and Western", "Смешанное питание: местное + западное"),
            ("Mostly Western / dining out", "В основном западная еда / рестораны"),
            ("Western food often", "Часто западная еда"),
            ("Public transport only", "Только общественный транспорт"),
            ("Public transport + motorbike", "Транспорт + байк"),
            ("Ride-hailing + some taxi", "Такси и ride-hailing"),
            ("Grab/taxi daily", "Grab / такси каждый день"),
            ("Own car / scooter rental", "Своя машина / аренда скутера"),
            ("Minimal &mdash; work focused", "Минимальный сценарий &mdash; фокус на работе"),
            ("Social &mdash; gyms, cafes, travel", "Социальный ритм &mdash; залы, кафе, поездки"),
            ("Active &mdash; sports, events, trips", "Активный ритм &mdash; спорт, события, поездки"),
            ("Luxury &mdash; rooftop bars, spas", "Премиальный ритм &mdash; rooftop-бары, spa"),
            ("Minimal", "Минимальный сценарий"),
            ("Social — gyms, cafes, travel", "Социальный ритм — залы, кафе, поездки"),
            ("Comfortable expat routine", "Комфортный экспатский ритм"),
            ("Solo", "Один человек"),
            ("Couple", "Пара"),
            ("Family (1 child)", "Семья (1 ребёнок)"),
            ("Family (2 children)", "Семья (2 ребёнка)"),
            ("Small family", "Небольшая семья"),
            ("Per Month", "В месяц"),
            ("Per Day", "В день"),
            ("Per Year", "В год"),
            ("Monthly Breakdown", "Разбивка по месяцам"),
            ("Food and Dining", "Еда и кафе"),
        ],
        "budget-planner": [
            ("Relocation Budget Planner", "Планировщик бюджета на переезд"),
            ("Select a country and all costs are auto-filled from real 2026 data. Edit any field to customise.", "Выберите страну, и базовые расходы подставятся автоматически по данным за 2026 год. Дальше можно поправить цифры под свой сценарий."),
            ("Select destination", "Выберите направление"),
            ("Choose country", "Выберите страну"),
            ("Auto-fill data", "Подставить данные"),
            ("loading live rates&#8230;", "загружаем актуальные курсы&#8230;"),
            ("Getting There", "Дорога"),
            ("Flights ($)", "Перелёты ($)"),
            ("Shipping / Baggage ($)", "Багаж / доставка ($)"),
            ("Visa &amp; Legal", "Визы и документы"),
            ("Visa Fee ($)", "Визовый сбор ($)"),
            ("Legal / Agent Fees ($)", "Юрист / агент ($)"),
            ("Housing Setup", "Старт жилья"),
            ("Deposit (months)", "Депозит (месяцы)"),
            ("Monthly Rent ($)", "Аренда в месяц ($)"),
            ("First Month Setup", "Первый месяц"),
            ("Furniture / Household ($)", "Мебель / быт ($)"),
            ("SIM / Internet Setup ($)", "SIM / интернет ($)"),
            ("Safety Buffer", "Финансовая подушка"),
            ("Emergency Fund (months)", "Запас (месяцы)"),
            ("Monthly Budget ($)", "Месячный бюджет ($)"),
            ("Calculate Total Budget", "Посчитать общий бюджет"),
            ("Your Relocation Budget", "Ваш бюджет переезда"),
            ("Total you need before moving", "Сколько нужно до переезда"),
            ("One-Time Costs Breakdown", "Разовые расходы"),
            ("Rental Deposit", "Депозит за жильё"),
            ("Furniture and Household", "Мебель и быт"),
            ("SIM and Internet Setup", "SIM и интернет"),
            ("Emergency Fund", "Финансовая подушка"),
            ("Total One-Time", "Всего разово"),
            ("Annual Total", "Годовой итог"),
            ("First Month Total", "Первый месяц"),
            ("Per Day Average", "В среднем в день"),
            ("Recalculate", "Пересчитать"),
            ("Visa fees", "Визовые сборы"),
            ("Flights", "Перелёты"),
            ("Deposit / housing setup", "Депозит и запуск жилья"),
            ("Insurance", "Страховка"),
            ("Emergency buffer", "Финансовая подушка"),
            ("Monthly budget", "Ежемесячный бюджет"),
            ("Total relocation budget", "Общий бюджет на переезд"),
        ],
        "compare-cities": [
            ("Compare Cities in Asia", "Сравните города в Азии"),
            ("Select two cities and compare quality of life, cost of living, safety, internet and more — fetched live from Teleport", "Выберите два города и сравните качество жизни, стоимость, безопасность, интернет и другие важные показатели."),
            ("City 1", "Город 1"),
            ("City 2", "Город 2"),
            ("Compare Cities", "Сравнить города"),
            ("Quality of Life", "Качество жизни"),
            ("Cost of Living", "Стоимость жизни"),
            ("Safety", "Безопасность"),
            ("Internet Access", "Интернет"),
            ("Housing", "Жильё"),
            ("Commute", "Транспорт"),
        ],
        "countries": [
            ("Countries", "Страны Азии для релокации"),
            ("20 DESTINATIONS &middot; UPDATED MARCH 2026", "20 направлений &middot; проверено в марте 2026"),
            ("<h1>Move to Asia: <span>All Страны Азии для релокации</span> Guide</h1>", "<h1>Переезд в Азию: <span>гид по странам</span></h1>"),
            ("<h1>Move to Asia: <span>All Countries</span> Guide</h1>", "<h1>Переезд в Азию: <span>гид по странам</span></h1>"),
            ("Move to Asia: All Countries Guide", "Переезд в Азию: гид по странам"),
            ("Страны Азии для релокации covered", "стран разобрано"),
            ("Compare costs, visas, and lifestyle across every major Asian relocation destination. Find your perfect country.", "Сравните расходы, визы и повседневную логику по основным направлениям Азии. Так проще убрать неподходящие страны ещё до детального планирования."),
            ("20 Countries covered", "20 стран разобрано"),
            ("Starting budget/mo", "Стартовый бюджет / мес."),
            ("All guides &amp; tools", "Все гайды и инструменты"),
            ("Browse Countries", "Страны"),
            ("Choose your destination and explore detailed relocation guides.", "Выберите направление и откройте подробный гид по переезду."),
            ("Each country guide includes visa options, cost of living, best cities, healthcare quality, internet speeds, safety ratings, and practical step-by-step moving advice. All data verified and updated for 2026.", "В каждой страновой странице есть визовые варианты, стоимость жизни, города, медицина, интернет, безопасность и практические детали для переезда. Данные обновлены под 2026 год."),
            ("Our guides cover everything you need: visa options, cost of living breakdowns by city, the best neighbourhoods, healthcare quality, internet speeds, safety ratings, and practical step-by-step moving advice. All data verified and updated for 2026.", "В гайдах собраны визовые варианты, расходы по городам, районы, медицина, интернет, безопасность и практические шаги. Данные обновлены под 2026 год."),
            ("Use our Country Comparison Tool to compare any two destinations, or start with our", "Используйте сравнение стран, чтобы быстро сопоставить два направления, или начните с"),
            ("<a href=\"/ru/compare/\">Country Comparison Tool</a>", "<a href=\"/ru/compare/\">инструмента сравнения стран</a>"),
            ("Use our Country Comparison Tool to compare any two destinations, or start with our Калькулятор стоимости жизни to find out exactly how far your budget goes.", "Используйте инструмент сравнения стран, чтобы сопоставить два направления, или начните с калькулятора стоимости жизни, чтобы понять реальный запас бюджета."),
            ("to find out exactly how far your budget goes.", "чтобы понять, насколько далеко реально тянется ваш бюджет."),
            ("FOUNDATION &mdash; MUST HAVE", "БАЗА &mdash; СТОИТ НАЧАТЬ"),
            ("Most Popular Relocation Destinations", "Самые популярные направления для релокации"),
            ("The 7 core countries chosen by the majority of expats and digital nomads moving to Asia", "7 стран, с которых чаще всего начинают expats и digital nomads при переезде в Азию"),
            ("MOST POPULAR", "САМЫЙ ПОПУЛЯРНЫЙ"),
            ("Low cost, easy lifestyle, warm weather year-round. LTR Visa and Thailand Elite.", "Невысокие расходы, простой быт, тёплая погода круглый год. LTR Visa и Thailand Elite."),
            ("CHEAPEST IN ASIA", "ОДИН ИЗ САМЫХ ДОСТУПНЫХ"),
            ("Ultra-affordable, fast internet, vibrant food scene. Da Nang, Hanoi, Ho Chi Minh.", "Очень доступный бюджет, быстрый интернет и сильная food-сцена. Дананг, Ханой, Хошимин."),
            ("BEST VISA", "СИЛЬНЫЕ ВИЗЫ"),
            ("English-friendly, MM2H visa, world-class infrastructure. Top expat hub in SEA.", "Английский в быту, MM2H и сильная инфраструктура. Один из главных expat-хабов региона."),
            ("NOMAD CAPITAL", "NOMAD-СТОЛИЦА"),
            ("World&#8217;s nomad capital. Canggu, Ubud, Seminyak. Unmatched community.", "Одна из главных nomad-баз мира: Чангу, Убуд, Семиньяк и сильное сообщество."),
            ("SAFEST IN ASIA", "ОЧЕНЬ ВЫСОКАЯ БЕЗОПАСНОСТЬ"),
            ("Excellent healthcare, fast internet, safety. Gold Card visa for professionals.", "Сильная медицина, быстрый интернет, безопасность. Gold Card для специалистов."),
            ("ENGLISH OFFICIAL", "АНГЛИЙСКИЙ ОФИЦИАЛЬНЫЙ"),
            ("English is the official language. Cebu, Manila, Davao. SRRV retirement visa.", "Английский широко используется. Себу, Манила, Давао. Пенсионный маршрут SRRV."),
            ("GIANT MARKET", "БОЛЬШОЙ РЫНОК"),
            ("Ancient culture meets modern megacities. Shanghai, Beijing, Chengdu.", "Старая культура и современные мегаполисы: Шанхай, Пекин, Чэнду."),
            ("Explore &rarr;", "Открыть &rarr;"),
            ("From $800/mo", "От $800/мес."),
            ("From $600/mo", "От $600/мес."),
            ("From $700/mo", "От $700/мес."),
            ("From $1,200/mo", "От $1,200/мес."),
            ("From $900/mo", "От $900/мес."),
            ("From $1,500/mo", "От $1,500/мес."),
            ("From $1,600/mo", "От $1,600/мес."),
            ("From $1,800/mo", "От $1,800/мес."),
            ("From $2,500/mo", "От $2,500/мес."),
            (">Singapore<", ">Сингапур<"),
            (">South Korea<", ">Южная Корея<"),
            (">Japan<", ">Япония<"),
            (">UAE<", ">ОАЭ<"),
            ("STRONG MARKETS", "СИЛЬНЫЕ РЫНКИ"),
            ("Premium &amp; High-Income Destinations", "Премиальные и высокодоходные направления"),
            ("For professionals, entrepreneurs, and high earners seeking top-tier infrastructure", "Для специалистов, предпринимателей и людей с высоким доходом, которым важна инфраструктура высокого уровня"),
            ("FINANCIAL HUB", "ФИНАНСОВЫЙ ХАБ"),
            ("World-class city-state. Top salaries, tech jobs, EntrePass for founders.", "Город-государство мирового уровня: высокие зарплаты, tech-рынок и EntrePass для founders."),
            ("K-TECH HUB", "K-TECH ХАБ"),
            ("Seoul is ultra-modern. D-10 startup visa, K-culture, excellent infrastructure.", "Сеул очень современный: D-10 startup visa, K-культура и сильная инфраструктура."),
            ("TRADITION + TECH", "ТРАДИЦИЯ + ТЕХНОЛОГИИ"),
            ("Ancient temples, futuristic cities. Tokyo, Osaka, Kyoto. Business visa available.", "Храмы, мегаполисы и высокая организация быта. Токио, Осака, Киото."),
            ("TAX-FREE", "БЕЗ НАЛОГА НА ДОХОД"),
            ("Zero income tax, luxury lifestyle. Dubai and Abu Dhabi. 85% expat population.", "Нулевой подоходный налог, Дубай и Абу-Даби, сильная expat-среда."),
            ("BUDGET-FRIENDLY &amp; GROWING", "БЮДЖЕТНО И С ПЕРСПЕКТИВОЙ"),
            ("Most Affordable Destinations in Asia", "Самые доступные направления Азии"),
            ("Ultra-low cost of living — ideal for long-term stays and passive income lifestyles", "Очень низкая стоимость жизни — подходит для долгих stay-сценариев и пассивного дохода"),
            ("CHEAPEST IN SEA", "ОДНО ИЗ САМЫХ ДЕШЁВЫХ В SEA"),
            ("Phnom Penh and Siem Reap. Dollar economy. Easy long-term visas, no foreign taxes.", "Пномпень и Сиемреап. Долларовая экономика, сравнительно простые long-stay маршруты."),
            ("HIDDEN GEM", "НЕДООЦЕНЁННОЕ НАПРАВЛЕНИЕ"),
            ("Serene Mekong lifestyle. Luang Prabang UNESCO heritage. Ultra-peaceful.", "Спокойная жизнь у Меконга, Луангпхабанг и очень тихий ритм."),
            ("ULTRA BUDGET", "УЛЬТРАБЮДЖЕТНО"),
            ("Bagan&#8217;s ancient temples, Inle Lake. Very affordable. Check current entry requirements.", "Баган, озеро Инле и очень низкие расходы. Перед поездкой обязательно проверяйте правила въезда."),
            ("SPECIFIC INTENT", "ДЛЯ КОНКРЕТНЫХ СЦЕНАРИЕВ"),
            ("Unique Образ жизни Destinations", "Направления под особый стиль жизни"),
            ("Niche destinations for specific lifestyles — yoga, adventure, tech, beaches", "Нишевые направления для йоги, приключений, tech-среды или жизни у моря"),
            ("TECH HUB", "TECH-ХАБ"),
            ("Bangalore and Hyderabad tech scene. Goa beaches. Rich culture, English widely spoken.", "Бангалор и Хайдарабад как tech-сцена, Гоа у моря, английский широко используется."),
            ("ISLAND PARADISE", "ОСТРОВНОЙ СЦЕНАРИЙ"),
            ("Beaches, tea hills, colonial cities. Digital Nomad Visa. Galle, Colombo, Ella.", "Пляжи, чайные холмы, колониальные города. Галле, Коломбо, Элла."),
            ("ADVENTURE BASE", "БАЗА ДЛЯ ПРИКЛЮЧЕНИЙ"),
            ("Himalayan trekking, yoga retreats, Kathmandu expat community. Ultra-affordable.", "Гималайский трекинг, йога-ретриты и expat-сообщество в Катманду."),
            ("CENTRAL ASIA &amp; EXTRAS", "ЦЕНТРАЛЬНАЯ АЗИЯ И ДОПОЛНИТЕЛЬНЫЕ ВАРИАНТЫ"),
            ("Low Competition, High Opportunity", "Меньше конкуренции, больше неожиданных возможностей"),
            ("Emerging destinations with minimal competition and growing expat communities", "Новые направления с меньшей конкуренцией и растущими expat-сообществами"),
            ("EMERGING MARKET", "РАЗВИВАЮЩИЙСЯ РЫНОК"),
            ("Central Asia&#8217;s powerhouse.", "Один из сильнейших рынков Центральной Азии."),
            ("Almaty and Astana — modern cities with low taxes.", "Алматы и Астана — современные города с относительно низкими налогами."),
            ("SILK ROAD", "ШЁЛКОВЫЙ ПУТЬ"),
            ("Samarkand, Bukhara, Tashkent. UNESCO heritage, warm hospitality, ultra-affordable.", "Самарканд, Бухара, Ташкент. Наследие UNESCO, гостеприимство и низкие расходы."),
            ("OIL RICH &bull; TAX-FREE", "НЕФТЬ &bull; НИЗКИЕ НАЛОГИ"),
            ("Zero income tax, subsidized healthcare. Very low crime. Pristine rainforests on Borneo.", "Нулевой подоходный налог, субсидированная медицина, низкая преступность и природа Борнео."),
            ("Where to Move in Asia: Country-by-Country Guide", "Куда переезжать в Азии: обзор по странам"),
            ("Asia offers the most diverse range of relocation destinations in the world. Whether you are looking for the lowest possible cost of living in Cambodia or Laos, the best visa programs in Malaysia, the most vibrant nomad community in Bali, or the highest quality of life in Singapore or Japan &mdash; there is an Asian country that matches your priorities and budget.", "Азия даёт очень широкий выбор сценариев: минимальный бюджет в Камбодже или Лаосе, сильные визовые программы в Малайзии, активное nomad-сообщество на Бали или высокий уровень жизни в Сингапуре и Японии. Вопрос не в том, какая страна «лучшая», а какая совпадает с вашим бюджетом, визовой логикой и бытом."),
            ("Popular Country Pages", "Популярные страницы стран"),
        ],
        "guides": [
            ("Asia Relocation Guides For Visa, Budget And Country Decisions", "Гайды по релокации в Азию: визы, бюджет и выбор страны"),
            ("Relocation Decision Guides 2026", "Гайды для релокационных решений 2026"),
            ("Asia Relocation Guides For Visa, Budget And Country Decisions", "Гайды по релокации в Азию: визы, бюджет и выбор страны"),
            ("This section is for the moment when a broad country article is too slow, but a one-line answer is too risky.", "Этот раздел нужен для конкретных вопросов, где общей статьи по стране уже мало, а короткий ответ слишком опасен."),
            ("You already have a concrete question:", "У вас уже есть конкретный вопрос:"),
            ("can Japan's digital nomad stay be extended, whether Taiwan Gold Card fits your profile, whether Thailand or Malaysia makes more sense, or whether $1,500 a month is realistic in Asia.", "можно ли продлить digital nomad stay в Японии, подходит ли вам Taiwan Gold Card, что практичнее — Таиланд или Малайзия, и реалистичен ли бюджет $1,500 в месяц в Азии."),
            ("Start here if the question is specific.", "Начинайте здесь, если вопрос уже конкретный."),
            ("If you are still choosing a region, use the country and comparison pages first.", "Если вы ещё выбираете регион, лучше начать со страниц стран и сравнений."),
            ("If you are already comparing one visa, one budget, or one country pair, these guides are the shortcut.", "Если вы уже сравниваете одну визу, один бюджет или пару стран, эти гайды помогут быстрее сузить выбор."),
            ("Best Asian Countries With Easy Long-Stay Visas", "Страны Азии с более простыми long-stay визами"),
            ("Best Asian Countries For Remote Workers With Family", "Страны Азии для удалёнщиков с семьёй"),
            ("Compare Asian Countries", "Сравнить страны Азии"),
            ("Cost Of Living Calculator", "Калькулятор стоимости жизни"),
            ("Cost Of Living In Asia", "Стоимость жизни в Азии"),
            ("Retire In Asia", "Пенсия в Азии"),
            ("Relocation research gets messy fast. People start with a country they like, then discover the visa does not fit. Or they find a visa that looks easy, then realise the city is too expensive. The order matters.", "Ресёрч по релокации быстро становится хаотичным. Люди начинают со страны, которая нравится, а потом выясняют, что виза не подходит. Или находят визу, которая выглядит простой, но город оказывается слишком дорогим. Порядок важен."),
            ("A good move starts with the constraint that can break the plan: legal stay, income proof, family eligibility, rent, healthcare, or the length of time you really want to be there.", "Нормальный план начинается с ограничения, которое может всё сломать: легальный срок stay, подтверждение дохода, семья, аренда, медицина или реальный срок, на который вы хотите остаться."),
            ("The guides below are built around those decision points. They are not travel inspiration. They are not sales pages for visa services. They are practical checks: what the rule appears to say, what that means in real planning, who should keep reading, and who should stop before wasting time.", "Гайды ниже построены вокруг таких решений. Это не travel inspiration и не продажа визовых услуг. Это практические проверки: что написано в правилах, что это значит для планирования, кому стоит читать дальше, а кому лучше остановиться до потери времени."),
            ("Can You Extend Japan Digital Nomad Visa?", "Можно ли продлить Japan Digital Nomad Visa?"),
            ("The key Japan question is not lifestyle. It is the six-month limit and no-extension rule.", "Главный вопрос по Японии — не lifestyle, а лимит 6 месяцев и отсутствие продления."),
            ("Japan Digital Nomad Visa Income Requirement", "Требование к доходу для Japan Digital Nomad Visa"),
            ("Useful if the visa looks attractive, but the income proof may be the real blocker.", "Полезно, если виза выглядит привлекательно, но реальным блокером может стать подтверждение дохода."),
            ("Thailand DTV vs LTR Visa", "Thailand DTV vs LTR Visa"),
            ("A short-stay flexible route and a stricter long-term route are not substitutes for each other.", "Гибкий short-stay маршрут и более строгий long-term маршрут не заменяют друг друга."),
            ("Malaysia DE Rantau vs Thailand DTV", "Malaysia DE Rantau vs Thailand DTV"),
            ("The practical difference is not just country preference. It is employer logic, length of stay and renewal clarity.", "Разница не только в стране. Важны логика работодателя, срок stay и понятность продления."),
            ("What This Page Is Actually About", "О чём этот раздел на самом деле"),
            ("Start With The Question You Actually Have", "Начинайте с реального вопроса, который у вас уже есть"),
            ("How To Use These Guides Without Fooling Yourself", "Как пользоваться этими гайдами без самообмана"),
            ("Visa And Country Comparisons", "Сравнения виз и стран"),
            ("Where To Go Next", "Куда идти дальше"),
        ],
        "visas": [
            ("Asia Visa Guide", "Гид по визам Азии"),
            ("official sources checked", "проверено по официальным источникам"),
            ("Remote workers", "Удалённая работа"),
            ("Professionals", "Профессиональные маршруты"),
            ("Retirees", "Пенсионные сценарии"),
            ("Families", "Семьи"),
            ("Official sources checked", "Проверено по официальным источникам"),
            ("Best starting points", "С чего лучше начать"),
        ],
    }
    content = replace_many(content, specific.get(slug, []))
    ru_cleanup = [
        ("Relocation Планировщик бюджета", "Планировщик бюджета переезда"),
        ("Country Comparison Tool", "инструмент сравнения стран"),
        ("Cost of Living Calculator", "калькулятор стоимости жизни"),
        ("Free Relocation Tools", "бесплатные инструменты релокации"),
        ("Free to use", "Бесплатно"),
        ("Most Popular", "Самый популярный"),
        ("Planning Tool", "Планировщик"),
        ("Comparison", "Сравнение"),
        ("Countries covered in depth", "стран разобрано подробно"),
        ("Data points per country", "точек данных по стране"),
        ("All data updated this year", "данные обновлены в этом году"),
        ("All tools &amp; guides free", "все инструменты и гайды бесплатны"),
        ("Choose a Страна", "Выберите страну"),
        ("How to Choose the Right Страна", "Как выбрать подходящую страну"),
        ("How to Choose the Right Country", "Как выбрать подходящую страну"),
        ("Comfortable", "Комфортный"),
        ("Process", "Процесс"),
        ("Explore &rarr;", "Открыть &rarr;"),
        ("From $600/mo", "От $600/мес."),
        ("From $700/mo", "От $700/мес."),
        ("From $800/mo", "От $800/мес."),
        ("From $900/mo", "От $900/мес."),
        ("From $1,200/mo", "От $1,200/мес."),
        ("From $1,500/mo", "От $1,500/мес."),
        ("From $1,600/mo", "От $1,600/мес."),
        ("From $1,800/mo", "От $1,800/мес."),
        ("From $2,500/mo", "От $2,500/мес."),
        (">Thailand<", ">Таиланд<"),
        (">Malaysia<", ">Малайзия<"),
        (">Vietnam<", ">Вьетнам<"),
        (">Taiwan<", ">Тайвань<"),
        (">Singapore<", ">Сингапур<"),
        (">South Korea<", ">Южная Корея<"),
        (">Japan<", ">Япония<"),
        (">Philippines<", ">Филиппины<"),
        (">Cambodia<", ">Камбоджа<"),
        (">Laos<", ">Лаос<"),
        (">Myanmar<", ">Мьянма<"),
        (">India<", ">Индия<"),
        (">Sri Lanka<", ">Шри-Ланка<"),
        (">Nepal<", ">Непал<"),
        (">Kazakhstan<", ">Казахстан<"),
        (">Uzbekistan<", ">Узбекистан<"),
        (">Brunei<", ">Бруней<"),
        (">UAE<", ">ОАЭ<"),
        ("Bali vs Thailand", "Бали vs Таиланд"),
        ("Thailand vs Malaysia", "Таиланд vs Малайзия"),
        ("Vietnam $", "Вьетнам $"),
        ("Malaysia $", "Малайзия $"),
        ("Thailand $", "Таиланд $"),
        ("Bali $", "Бали $"),
        ("Taiwan $", "Тайвань $"),
        ("REST Countries", "страновым данным"),
        ("World Bank population", "население по World Bank"),
        ("World Bank internet users", "пользователи интернета по World Bank"),
        ("Образ жизни vs infrastructure &mdash; the two most popular nomad destinations compared across every key metric.", "Lifestyle против инфраструктуры: сравнение двух популярных nomad-направлений по ключевым метрикам."),
        ("If cost is the primary factor, Vietnam or Malaysia offer the best value. If lifestyle matters most, Bali&#8217;s nomad ecosystem is unmatched. For long-term visa stability, Malaysia&#8217;s MM2H program offers the strongest framework. If safety is non-negotiable, Taiwan is the clear winner. Use our Инструмент сравнения стран to make a data-driven decision.", "Если главный фильтр — бюджет, чаще всего в shortlist попадают Вьетнам и Малайзия. Если важнее lifestyle и сообщество, Бали сложно игнорировать. Для долгой визовой устойчивости стоит смотреть на MM2H в Малайзии. Если безопасность — жёсткое условие, Тайвань обычно выходит очень сильным кандидатом. Для первого отбора используйте инструмент сравнения стран."),
        ("The Калькулятор стоимости жизни lets you customise your lifestyle profile and instantly see a monthly budget breakdown for any of our five covered countries.", "Калькулятор стоимости жизни даёт помесячную разбивку под выбранный стиль жизни."),
        ("The Планировщик бюджета переезда focuses on the one-time costs that most guides overlook — visa application fees, international flights, shipping, rental deposits, and first-month setup.", "Планировщик бюджета ловит разовые расходы, которые часто забывают: визовые сборы, перелёты, багаж, депозиты и первый месяц."),
        ("The инструмент сравнения стран puts two destinations side-by-side across more than 15 metrics so you can make a data-driven choice.", "Инструмент сравнения ставит две страны рядом по 15+ метрикам, чтобы решение было не на ощущениях."),
        ("costs, rental prices, and living expenses across Southeast", "расходы, аренду и бытовые траты в Юго-Восточной"),
        ("instantly see a monthly budget breakdown for any of our five covered countries.", "сразу увидеть помесячную разбивку бюджета по странам."),
        ("If cost is the primary factor, Vietnam or Malaysia offer the best value.", "Если главный фильтр — бюджет, чаще всего в shortlist попадают Вьетнам и Малайзия."),
        ("If lifestyle matters most, Bali&#8217;s nomad ecosystem is unmatched.", "Если важнее lifestyle и сообщество, Бали сложно игнорировать."),
        ("For long-term visa stability, Malaysia&#8217;s MM2H program offers the strongest framework.", "Для долгой визовой устойчивости стоит смотреть на MM2H в Малайзии."),
        ("If safety is non-negotiable, Taiwan is the clear winner.", "Если безопасность — жёсткое условие, Тайвань обычно выходит очень сильным кандидатом."),
        ("Use our Инструмент сравнения стран to make a data-driven decision.", "Для первого отбора используйте инструмент сравнения стран."),
        ("Useful if Japan looks perfect, but your proof of income may be the weak point.", "Полезно, если Япония кажется идеальной, но подтверждение дохода может стать слабым местом."),
        ("For people who want Thailand but are not sure which route matches their profile.", "Для тех, кто хочет в Таиланд, но не понимает, какой маршрут совпадает с профилем."),
        ("A practical comparison for remote workers choosing between Malaysia and Thailand.", "Практическое сравнение для удалёнщиков, которые выбирают между Малайзией и Таиландом."),
        ("For skilled professionals checking whether Taiwan is a real option, not just an attractive idea.", "Для квалифицированных специалистов, которые проверяют, Тайвань — реальный вариант или просто красивая идея."),
        ("Where To Live In Asia On $1500 A Month", "Где жить в Азии на $1500 в месяц"),
        ("A budget guide that separates lean living from unrealistic relocation planning.", "Бюджетный гид, который отделяет экономный сценарий от фантазии."),
        ("If The Issue Is Visa Length", "Если вопрос в сроке визы"),
        ("Look first at stay duration, extension wording and what happens after the allowed period ends.", "Сначала смотрите срок stay, формулировку продления и то, что происходит после разрешённого периода."),
        ("A beautiful country is not useful if the legal window is too short for your plan.", "Красивая страна не помогает, если легальное окно слишком короткое для вашего плана."),
        ("If The Issue Is Money", "Если вопрос в деньгах"),
        ("Separate monthly living costs from visa costs, deposits, insurance, flights and emergency buffer.", "Разделяйте месячные расходы, визовые траты, депозиты, страховку, перелёты и финансовую подушку."),
        ("A country can be cheap month to month and still expensive to enter properly.", "Страна может быть дешёвой каждый месяц, но дорогой на входе."),
        ("If The Issue Is Family", "Если переезд с семьёй"),
        ("Check dependants, schooling, healthcare and housing before you fall in love with a city.", "Проверьте dependants, школы, медицину и жильё до того, как влюбитесь в город."),
        ("Family relocation breaks faster than solo nomad travel.", "Семейная релокация ломается быстрее, чем solo nomad сценарий."),
        ("If The Issue Is Retirement", "Если это пенсионный сценарий"),
        ("Do not compare only deposits. Look at medical access, renewals, banking, language and what daily life looks like after the first few months.", "Не сравнивайте только депозиты. Смотрите медицину, продления, банки, язык и реальную повседневность после первых месяцев."),
        ("Visa And Country Сравнения", "Сравнения виз и стран"),
        ("Some decisions are not about one country. They are about two imperfect options.", "Иногда выбор не между хорошим и плохим вариантом, а между двумя несовершенными маршрутами."),
        ("Thailand may feel easier socially, but Malaysia may be cleaner for English, infrastructure and remote work paperwork.", "Таиланд может быть проще социально, а Малайзия — понятнее по английскому, инфраструктуре и документам для удалённой работы."),
        ("Japan may be more attractive emotionally, while Taiwan may", "Япония может сильнее цеплять эмоционально, а Тайвань может"),
        ("be stronger if you need a longer professional route.", "быть сильнее, если нужен более долгий профессиональный маршрут."),
        ("The point is not to crown a winner. The point is to expose the trade-off early.", "Смысл не в том, чтобы объявить победителя. Смысл в том, чтобы раньше увидеть компромисс."),
        ("For readers who want the easiest route, but need to define what “easy” actually means.", "Для тех, кто ищет более простой маршрут, но сначала должен понять, что именно значит «простой»."),
        ("For people moving with dependants, where school and healthcare matter as much as rent.", "Для переезда с dependants, где школы и медицина важны не меньше аренды."),
        ("Philippines SRRV vs Thailand Retirement Visa", "Philippines SRRV vs пенсионная виза Таиланда"),
        ("A retirement-focused comparison where deposit, healthcare and daily life all matter.", "Пенсионное сравнение, где важны депозит, медицина и повседневная жизнь."),
        ("Vietnam E-Visa vs Thailand DTV", "Vietnam eVisa vs Thailand DTV"),
        ("For people testing Southeast Asia and trying not to confuse a trial stay with relocation.", "Для тех, кто тестирует Юго-Восточную Азию и не хочет путать пробный stay с релокацией."),
        ("If a guide confirms that the route fits, go deeper.", "Если гайд показывает, что маршрут подходит, копайте глубже."),
        ("Read the full visa article, then the country page, then compare cities and budget.", "Читайте полную визовую статью, потом страновую страницу, затем сравнивайте города и бюджет."),
        ("If a guide shows the route does not fit, that is not a failure.", "Если гайд показывает, что маршрут не подходит, это не провал."),
        ("It saves time.", "Это экономит время."),
        ("The wrong visa can make a good country useless for your situation.", "Неподходящая виза может сделать хорошую страну бесполезной именно для вашей ситуации."),
        ("Digital Nomad Visas In Asia", "Digital Nomad визы в Азии"),
        ("for remote-work routes across the region.", "для remote-work маршрутов по региону."),
        ("when two destinations look close on paper.", "когда два направления на бумаге выглядят близко."),
        ("when you need a rough monthly number.", "когда нужен грубый месячный ориентир."),
        ("Are these guides different from blog articles?", "Эти гайды отличаются от статей блога?"),
        ("Yes. Blog articles go deeper into one visa or country. These pages answer narrower decision questions and then point you to the deeper page when it makes sense.", "Да. Статьи блога глубже разбирают одну визу или страну. Эти страницы отвечают на узкие вопросы и ведут к более подробному материалу, когда это нужно."),
        ("Why are some guides about one small rule?", "Почему некоторые гайды про одно маленькое правило?"),
        ("Because one rule can decide the whole move.", "Потому что одно правило может решить весь переезд."),
        ("Japan's six-month limit, Taiwan's professional eligibility, or a family dependant rule can matter more", "Лимит Японии на шесть месяцев, профессиональные критерии Тайваня или правило по dependants для семьи могут значить больше"),
    ]
    content = replace_many(content, ru_cleanup)
    content = re.sub(
        r"The Планировщик бюджета переезда focuses.*?first-month setup\.",
        "Планировщик бюджета ловит разовые расходы, которые часто забывают: визовые сборы, перелёты, багаж, депозиты и первый месяц.",
        content,
    )
    content = re.sub(
        r"The Калькулятор стоимости жизни lets.*?covered countries\.",
        "Калькулятор стоимости жизни даёт помесячную разбивку под выбранный стиль жизни.",
        content,
    )
    content = re.sub(
        r"Образ жизни-Based Results adapt.*?professional\.",
        "Расчёт меняется под ваш сценарий: бюджетный формат, средний expat-уровень или комфортный профессиональный переезд.",
        content,
    )
    content = re.sub(
        r"The инструмент сравнения стран puts.*?data-driven choice\.",
        "Инструмент сравнения ставит две страны рядом по 15+ метрикам, чтобы решение было не на ощущениях.",
        content,
    )
    content = content.replace(
        "Real costs vary by neighbourhood, personal habits, and market fluctuations.",
        "Реальные расходы зависят от района, привычек и рынка жилья.",
    )
    content = content.replace(
        "All tools currently cover Thailand (Бангкок, Чиангмай, Пхукет), Malaysia (Kuala Lumpur, Penang), Indonesia/Bali (Canggu, Ubud, Seminyak), Vietnam (Ho Chi Minh City, Hanoi, Da Nang), and Taiwan (Taipei). More countries coming soon.",
        "Сейчас инструменты покрывают Таиланд, Малайзию, Индонезию / Бали, Вьетнам и Тайвань. Больше стран добавим позже.",
    )
    content = content.replace("Southeast and East Asia", "Юго-Восточной и Восточной Азии")
    content = localized_generic_content(content)
    content = re.sub(
        r"The Калькулятор стоимости жизни lets.*?странам\.",
        "Калькулятор стоимости жизни даёт помесячную разбивку под выбранный стиль жизни.",
        content,
    )
    content = re.sub(
        r"The .*?lets you customise.*?budget.*?\.",
        "Калькулятор стоимости жизни даёт помесячную разбивку под выбранный стиль жизни.",
        content,
    )
    content = re.sub(
        r"The Планировщик бюджета переезда focuses.*?первый месяц\.",
        "Планировщик бюджета показывает разовые расходы, которые часто забывают: визовые сборы, перелёты, багаж, депозиты и первый месяц.",
        content,
    )
    content = re.sub(
        r"The .*?focuses on the one-time costs.*?\.",
        "Планировщик бюджета показывает разовые расходы, которые часто забывают: визовые сборы, перелёты, багаж, депозиты и первый месяц.",
        content,
    )
    content = re.sub(
        r"The инструмент сравнения стран puts.*?choice\.",
        "Инструмент сравнения ставит две страны рядом по 15+ метрикам, чтобы решение было не на ощущениях.",
        content,
    )
    content = re.sub(
        r"The .*?puts two destinations side-by-side.*?choice\.",
        "Инструмент сравнения ставит две страны рядом по 15+ метрикам, чтобы решение было не на ощущениях.",
        content,
    )
    content = re.sub(
        r"Find the right visa.*?work permit\.",
        "Подберите подходящий маршрут: digital nomad, long-stay, пенсионный или рабочий.",
        content,
    )
    content = content.replace(
        "Ultra-low cost of living — ideal for долгосрочный stays and passive income образ жизниs",
        "Очень низкие расходы — вариант для долгого проживания и сценариев с пассивным доходом",
    )
    content = re.sub(
        r"Ultra-low cost of living.*?passive income .*?s",
        "Очень низкие расходы — вариант для долгого проживания и сценариев с пассивным доходом",
        content,
    )
    content = content.replace(
        "Use our инструмент сравнения стран to compare any two destinations, or start with our Калькулятор стоимости жизни чтобы понять, насколько далеко реально тянется ваш бюджет.",
        "Используйте инструмент сравнения стран, чтобы сопоставить два направления, или начните с калькулятора стоимости жизни, чтобы понять реальный запас бюджета.",
    )
    content = re.sub(
        r"The primary appeal is the dramatic reduction in cost of living\..*?digital nomad ecosystem\.",
        "Главный мотив — заметно ниже стоимость жизни. Комфортный сценарий в Бангкоке или Чиангмае может укладываться в $1,200–1,800 в месяц, тогда как похожий уровень в Лондоне, Нью-Йорке или Сиднее стоит совсем других денег. Малайзия даёт современную инфраструктуру и английский в быту, а Бали держится на сильном сообществе удалёнщиков.",
        content,
    )
    content = re.sub(
        r"Asia has become the world.*?Western countries\.",
        "Азия стала одним из самых популярных направлений для экспатов, удалёнщиков, пенсионеров и специалистов, не привязанных к офису. Таиланд, Малайзия, Бали, Вьетнам и Тайвань дают уровень быта, который в западных странах часто стоит заметно дороже.",
        content,
    )
    content = re.sub(
        r"All budgets below represent.*?occasional entertainment\.",
        "Все бюджеты ниже рассчитаны для комфортного solo-сценария: отдельное жильё, регулярная еда вне дома, местный транспорт, хороший интернет и умеренный досуг.",
        content,
    )
    content = content.replace(
        "All budgets below represent a comfortable solo образ жизни : private apartment, eating out regularly, local transport, good internet, and occasional entertainment.",
        "Все бюджеты ниже рассчитаны для комфортного solo-сценария: отдельное жильё, регулярная еда вне дома, местный транспорт, хороший интернет и умеренный досуг.",
    )
    content = content.replace("Entertainment & misc", "Досуг и прочее")
    content = content.replace("mix local + western", "местная + западная")
    return title, content


def localized_guide_content(slug: str, title: str, content: str) -> tuple[str, str]:
    title = RU_GUIDE_TITLES.get(slug, title)
    guide_content = ru_guide_article(slug, title)
    if guide_content:
        return title, guide_content
    content = localized_generic_content(content)
    guide_replacements = [
        ("Updated April 2026 · ", "Проверено в апреле 2026 · "),
        ("Updated March 2026 · ", "Проверено в марте 2026 · "),
        ("Japan Visa Decision", "виза Японии"),
        ("Japan Income Check", "проверка дохода для Японии"),
        ("Thailand Visa Decision", "виза Таиланда"),
        ("Malaysia vs Thailand", "Малайзия vs Таиланд"),
        ("Taiwan Gold Card", "Taiwan Gold Card"),
        ("Long-Stay Visa Shortlist", "shortlist по long-stay визам"),
        ("Budget Decision", "бюджетный выбор"),
        ("Family Relocation", "семейная релокация"),
        ("Retirement Decision", "пенсионный выбор"),
        ("Southeast Asia Decision", "выбор по Юго-Восточной Азии"),
        ("Can You Extend Japan Digital Nomad Visa In 2026?", "Можно ли продлить визу digital nomad в Японии в 2026 году?"),
        ("Japan Digital Nomad Visa Income Requirement 2026", "Требование к доходу для Japan Digital Nomad Visa в 2026 году"),
        ("Thailand DTV vs LTR Visa 2026: Which Route Actually Fits Your Move?", "Thailand DTV vs LTR Visa: какой маршрут реально подходит под ваш переезд в 2026 году"),
        ("Malaysia DE Rantau vs Thailand DTV 2026", "Malaysia DE Rantau vs Thailand DTV в 2026 году"),
        ("Taiwan Gold Card Income Requirement 2026", "Требование к доходу для Taiwan Gold Card в 2026 году"),
        ("Best Asian Countries With Easy Long-Stay Visas 2026", "Лучшие страны Азии с более простыми long-stay маршрутами в 2026 году"),
        ("Where To Live In Asia On $1500 A Month In 2026", "Где можно жить в Азии на $1500 в месяц в 2026 году"),
        ("Best Asian Countries For Remote Workers With Family 2026", "Лучшие страны Азии для удалёнщиков с семьёй в 2026 году"),
        ("Philippines SRRV vs Thailand Retirement Visa 2026", "Philippines SRRV vs пенсионная виза Таиланда в 2026 году"),
        ("Vietnam E-Visa vs Thailand DTV 2026", "Vietnam eVisa vs Thailand DTV в 2026 году"),
        ("Quick answer", "Короткий ответ"),
        ("Short answer", "Короткий ответ"),
        ("The Rule That Decides The Whole Plan", "Правило, которое меняет весь сценарий"),
        ("What This Means In Practice", "Что это значит на практике"),
        ("Who This Fits And Who Should Be Careful", "Кому подходит и где стоит быть осторожнее"),
        ("Official Sources And Next Steps", "Официальные источники и следующие шаги"),
        ("The Real Difference", "В чём реальная разница"),
        ("Who Should Choose", "Кому стоит выбрать"),
        ("Where People Usually Make The Wrong Choice", "Где люди чаще всего делают неверный выбор"),
        ("Decision Table", "Таблица выбора"),
        ("Bottom Line", "Итог"),
        ("Confirmed Facts To Start With", "Подтверждённые факты для старта"),
        ("Confirmed Facts From Official Sources", "Подтверждённые факты из официальных источников"),
        ("Official Sources Checked", "Какие официальные источники проверены"),
        ("Why The Income Rule Matters", "Почему правило по доходу вообще решает так много"),
        ("Proof Matters More Than Optimism", "Документы важнее оптимизма"),
        ("How To Decide Before Applying", "Как принимать решение до подачи"),
        ("The Real Comparison", "В чём реальное сравнение"),
        ("Malaysia’s Practical Strength", "В чём практическая сила Малайзии"),
        ("Thailand’s Practical Strength", "В чём практическая сила Таиланда"),
        ("The Salary Rule People Misread", "Как правило по доходу чаще всего читают неправильно"),
        ("Why Taiwan Is Still Worth Checking", "Почему Тайвань всё равно стоит проверить"),
        ("Easy Is Not One Thing", "Лёгкая виза — это не одна конкретная вещь"),
        ("Good Shortlist By Profile", "Рабочий shortlist по типу профиля"),
        ("Where People Get Burned", "Где люди чаще всего ошибаются"),
        ("The Budget Has To Include More Than Rent", "Бюджет должен включать не только аренду"),
        ("Planning Facts To Start With", "Факты для планирования на старте"),
        ("Where $1,500 Can Work", "Где $1,500 действительно может работать"),
        ("Where $1,500 Is Weak", "Где $1,500 уже слишком слабый бюджет"),
        ("Family Moves Break In Different Places", "Семейный переезд ломается в других местах"),
        ("The Practical Shortlist", "Практический shortlist"),
        ("What To Check Before You Promise The Move", "Что проверить до того, как пообещаете семье переезд"),
        ("What SRRV Actually Offers", "Что SRRV реально даёт на практике"),
        ("Thailand’s Retirement Appeal", "В чём пенсионная привлекательность Таиланда"),
        ("The Real Decision", "Где здесь реальное решение"),
        ("The Difference Is Not Just Country Preference", "Разница не сводится к тому, какая страна просто больше нравится"),
        ("When Vietnam Makes More Sense", "Когда Вьетнам выглядит разумнее"),
        ("When Thailand Makes More Sense", "Когда Таиланд выглядит разумнее"),
        ("Stay Period", "Срок пребывания"),
        ("Extension", "Продление"),
        ("Activity", "Разрешённая активность"),
        ("Income Proof", "Подтверждение дохода"),
        ("Insurance", "Страховка"),
        ("Good Fit", "Подходит"),
        ("Bad Fit", "Не подходит"),
        ("Risky Fit", "Рискованный сценарий"),
        ("Family Caution", "Семейный риск"),
        ("Better Comparison", "Что сравнить вместо этого"),
        ("Income Threshold", "Порог по доходу"),
        ("Proof Examples", "Какие доказательства подходят"),
        ("Stay Limit", "Лимит по сроку"),
        ("Salary Figure", "Порог по зарплате"),
        ("Proof Issue", "Где обычно проблема"),
        ("Excluded Income", "Что не засчитывается"),
        ("Validity", "Срок действия"),
        ("Malaysia Route", "Маршрут в Малайзии"),
        ("Thailand Route", "Маршрут в Таиланде"),
        ("DTV Financial Evidence", "Финансовое подтверждение для DTV"),
        ("Main Decision Filter", "Главный фильтр выбора"),
        ("Budget Type", "Тип бюджета"),
        ("Strongest Filter", "Главный фильтр"),
        ("Must Include", "Что обязательно учитывать"),
        ("Usually Weak For", "Где бюджет чаще всего ломается"),
        ("Family Warning", "Предупреждение для семьи"),
        ("Planning Rule", "Практическое правило"),
        ("Remote Workers", "Удалёнщики"),
        ("Retirees", "Пенсионные сценарии"),
        ("Families", "Семьи"),
        ("Move To Vietnam", "Переезд во Вьетнам"),
        ("Move To Thailand", "Переезд в Таиланд"),
        ("Compare Asian Cities", "Сравнить города Азии"),
        ("Cost Of Living Asia", "Стоимость жизни в Азии"),
        ("Cheapest Countries In Asia", "Самые дешёвые страны Азии"),
        ("FAQ", "Частые вопросы"),
    ]
    specific = {
        "where-to-live-in-asia-on-1500-a-month": [
            ("A $1,500 monthly budget can work in parts of Asia. It can also become fantasy if you choose the wrong city, visa rhythm or housing standard.", "Бюджет в $1,500 в месяц может работать в части азиатских городов. Но он быстро превращается в иллюзию, если ошибиться со страной, визовым ритмом или стандартом жилья."),
            ("Short answer: $1,500/month is realistic for a careful single person in selected cities, but not for every Asian capital and not for a comfortable family move. Rent, visa costs, insurance and flights decide the real number.", "Короткий ответ: $1,500 в месяц может хватать аккуратному одному человеку в выбранных городах, но не в каждой азиатской столице и не для комфортного семейного переезда. Реальную цифру решают аренда, визовые расходы, страховка и перелёты."),
        ],
        "best-asian-countries-with-easy-long-stay-visas": [
            ("“Easy visa” sounds useful until you ask: easy for whom? A retiree, remote employee, freelancer and family do not need the same route.", "Фраза «лёгкая виза» звучит удобно ровно до того момента, пока не спросишь: лёгкая для кого? Пенсионеру, удалённому сотруднику, фрилансеру и семье нужен не один и тот же маршрут."),
            ("Short answer: The easiest long-stay visa is the one where your real profile matches the official rule. Start with age, income type, employer, family, stay length and proof. Then choose the country.", "Короткий ответ: самая простая long-stay виза — та, где ваш реальный профиль совпадает с официальным правилом. Сначала смотрите на возраст, тип дохода, работодателя, семью, нужный срок и документы. Уже потом выбирайте страну."),
        ],
        "best-asian-countries-for-remote-workers-with-family": [
            ("Moving alone is forgiving. Moving with family is not. A visa that works for one person can become weak once school, healthcare and dependants enter the plan.", "Переезд в одиночку прощает ошибки. Переезд с семьёй — нет. Виза, которая подходит одному человеку, может резко ослабнуть, как только в план входят школа, медицина и dependants."),
            ("Short answer: Malaysia, Thailand, Taiwan and Singapore can all make sense for remote workers with family, but the right choice depends on dependant rules, school budget, healthcare comfort and how stable the main applicant’s work is.", "Короткий ответ: Малайзия, Таиланд, Тайвань и Сингапур могут подходить удалёнщикам с семьёй, но выбор зависит от правил по dependants, бюджета на школу, качества медицины и устойчивости дохода основного заявителя."),
        ],
        "japan-digital-nomad-visa-income-requirement": [
            ("The income rule looks simple on paper. The harder part is proving it cleanly enough for the application.", "Правило по доходу выглядит простым только на бумаге. Намного сложнее показать его так, чтобы документы выглядели чисто и без двусмысленностей."),
            ("Short answer: Japan asks for documents proving annual income of JPY 10 million or more. If your income is real but hard to document, the route may still be fragile.", "Короткий ответ: Япония ждёт документы, подтверждающие годовой доход от 10 млн JPY. Даже если деньги у вас реально есть, но доказать их сложно, маршрут остаётся хрупким."),
        ],
        "malaysia-de-rantau-vs-thailand-dtv": [
            ("Malaysia and Thailand both work for remote workers, but they solve different problems. One feels more structured. The other feels more flexible.", "Малайзия и Таиланд оба подходят удалёнщикам, но решают разные задачи. Один маршрут ощущается более структурным, другой — более гибким."),
            ("Short answer: Choose Malaysia DE Rantau if you want a clearer digital nomad programme and Malaysia’s city infrastructure. Choose Thailand DTV if your Thailand purpose matches the DTV categories and you want a more flexible lifestyle base.", "Короткий ответ: выбирайте Malaysia DE Rantau, если вам нужен более прямой digital nomad маршрут и городская инфраструктура Малайзии. Thailand DTV сильнее тогда, когда ваш сценарий реально попадает в DTV-категории, а сама Таиландская база для вас важнее гибкости."),
        ],
        "taiwan-gold-card-income-requirement": [
            ("Taiwan Gold Card is one of Asia’s stronger professional routes. But the salary-based path is stricter than many remote workers expect.", "Taiwan Gold Card — один из самых сильных профессиональных маршрутов в Азии. Но salary-based путь в нём строже, чем многие удалёнщики ожидают."),
            ("Short answer: The official Gold Card site describes NT$160,000 monthly salary logic for salary-based qualification. The practical risk is whether your proof is accepted as salary, not just whether you earned enough money.", "Короткий ответ: официальный сайт Gold Card описывает salary-based логику через порог в NT$160,000 в месяц. Практический риск не только в сумме, а в том, примут ли ваш доход именно как salary."),
        ],
        "philippines-srrv-vs-thailand-retirement-visa": [
            ("The Philippines and Thailand both attract retirees, but the decision is not just deposit size. It is language, healthcare, banking, renewals and whether normal weekdays feel livable.", "Филиппины и Таиланд оба притягивают пенсионные сценарии, но решение здесь не сводится к размеру депозита. Важны язык, медицина, банковская бытовая часть, продления и то, насколько вам в стране вообще удобно жить по будням."),
            ("Short answer: Philippines SRRV is stronger if indefinite stay and English comfort matter. Thailand can be stronger for healthcare hubs and lifestyle infrastructure, but retirement routes require careful insurance and renewal checks.", "Короткий ответ: Philippines SRRV сильнее там, где важны indefinite stay и английский язык в повседневной жизни. Таиланд может быть сильнее по медицинским хабам и инфраструктуре, но пенсионные маршруты там требуют особенно аккуратной проверки страховки и продлений."),
        ],
        "vietnam-evisa-vs-thailand-dtv": [
            ("Vietnam and Thailand both work for testing Southeast Asia. But Vietnam eVisa and Thailand DTV are not the same kind of tool.", "Вьетнам и Таиланд оба подходят, если вы хотите проверить Юго-Восточную Азию на себе. Но Vietnam eVisa и Thailand DTV — это не один и тот же тип инструмента."),
            ("Short answer: Vietnam eVisa is better for a defined test stay. Thailand DTV is better if your purpose matches the DTV categories and you want Thailand as a repeated medium-stay base.", "Короткий ответ: Vietnam eVisa лучше подходит для понятного тестового пребывания. Thailand DTV сильнее тогда, когда ваш сценарий реально совпадает с DTV-категориями и вы хотите использовать Таиланд как повторяющуюся базу среднего срока."),
        ],
    }
    content = replace_many(content, guide_replacements)
    content = replace_many(content, specific.get(slug, []))
    extra_slug_replacements = {
        "can-you-extend-japan-digital-nomad-visa": [
            ("Japan is attractive, but this route has one hard edge: it is short. If that does not fit your plan, the rest of the lifestyle argument does not matter much.", "Япония выглядит очень привлекательно, но у этого маршрута есть жёсткая граница: он короткий. Если это не укладывается в ваш план, все разговоры про lifestyle уже почти не имеют значения."),
            ("No. Japan’s Ministry of Foreign Affairs states a 6-month period of stay and says no extension will be granted. Treat this as a fixed-window stay, not a relocation path.", "Нет. Министерство иностранных дел Японии прямо указывает срок пребывания 6 месяцев и отдельно пишет, что продление не предоставляется. Это фиксированное окно для проживания, а не маршрут на переезд."),
            ("The official wording is unusually direct. It does not say “renewable if approved” or “extension may be possible”. It says the period of stay is 6 months, with no extension. That one line changes the whole use case.", "Официальная формулировка здесь unusually прямолинейная. Там не сказано «можно продлить после одобрения» или «продление возможно». Там сказано: 6 месяцев и без продления. Одна эта строка полностью меняет практический смысл маршрута."),
            ("Remote workers who want Japan for one defined stay and can leave cleanly after six months.", "Удалёнщикам, которым нужна Япония на один понятный ограниченный период и которые могут спокойно уехать через шесть месяцев."),
            ("Anyone looking for a long-term base, a soft residence path, or an easy extension.", "Тем, кто ищет долгую базу, мягкий путь к резиденции или простое продление."),
        ],
        "japan-digital-nomad-visa-income-requirement": [
            ("Japan’s digital nomad visa filters applicants before the lifestyle discussion starts. The MOFA page asks for proof of annual income of JPY 10 million or more. That is not a monthly budget estimate. It is an eligibility threshold.", "Японская digital nomad visa отсекает часть заявителей ещё до разговоров про комфорт и lifestyle. На странице MOFA прямо указано: нужен документ, подтверждающий годовой доход от 10 млн JPY. Это не оценка бюджета на жизнь. Это порог допуска к категории."),
            ("People sometimes argue that they can live in Japan on less. Maybe they can. But immigration rules do not need to match your rent. The rule is about whether the applicant fits this category.", "Люди часто спорят, что жить в Японии можно и на меньшие деньги. Может быть. Но иммиграционные правила не обязаны совпадать с вашей арендой. Здесь вопрос не в том, хватает ли вам на жизнь, а в том, подходите ли вы под саму категорию."),
            ("An employment contract or tax certificate is easier to understand than a patchwork of screenshots, informal invoices and vague client promises. If you are employed, the evidence may be straightforward. If you are freelance, the story needs to be very clean: who pays you, how much, for how long, and whether the contract supports the number.", "Трудовой контракт или налоговая справка читаются намного проще, чем набор скриншотов, неформальных инвойсов и расплывчатых обещаний от клиентов. Если вы наемный сотрудник, доказательная часть обычно проще. Если вы фрилансер, история должна быть очень чистой: кто платит, сколько, на какой срок и подтверждает ли это контракт."),
        ],
        "best-asian-countries-with-easy-long-stay-visas": [
            ("Some people mean low income requirement. Some mean long validity. Some mean low paperwork. Some mean family-friendly. Those are different filters. A 90-day eVisa can be easy but not long-term. A 10-year route can be powerful but difficult. A retirement visa can be excellent if you meet the age and deposit rules, and irrelevant if you are 34.", "Для одних «простая виза» означает низкий порог по доходу. Для других — длинный срок. Для третьих — мало бумаг. Для четвёртых — удобство для семьи. Это вообще разные фильтры. 90-дневная eVisa может быть простой, но не долгой. Десятилетний маршрут может быть сильным, но сложным. Пенсионная виза бывает отличной, если вы проходите по возрасту и депозиту, и совершенно бесполезной, если вам 34."),
            ("The smarter question is not “which Asian visa is easiest?” It is “which route is easiest for this exact profile?”", "Полезнее спрашивать не «какая виза в Азии самая простая», а «какой маршрут самый реалистичный именно для моего профиля»."),
        ],
        "best-asian-countries-for-remote-workers-with-family": [
            ("Malaysia, Thailand, Taiwan and Singapore can all make sense for remote workers with family, but the right choice depends on dependant rules, school budget, healthcare comfort and how stable the main applicant’s work is.", "Малайзия, Таиланд, Тайвань и Сингапур могут подходить удалёнщикам с семьёй, но правильный выбор здесь зависит от правил по dependants, бюджета на школу, качества медицины и того, насколько устойчив доход у основного заявителя."),
            ("Solo remote workers can tolerate inconvenience. Families cannot. If a visa expires awkwardly, if insurance is weak, if school timing is wrong, or if housing is too small, the move becomes stressful fast. This is why family planning should start with legal stay and dependants, not beaches or coworking spaces.", "Один человек ещё может терпеть неудобства. Семья — уже нет. Если виза заканчивается не вовремя, если слабая страховка, если школа не бьётся по срокам или жильё слишком тесное, переезд очень быстро становится нервным. Поэтому семейное планирование надо начинать с legal stay и dependants, а не с пляжей и коворкингов."),
        ],
        "where-to-live-in-asia-on-1500-a-month": [
            ("$1,500/month is realistic for a careful single person in selected cities, but not for every Asian capital and not for a comfortable family move. Rent, visa costs, insurance and flights decide the real number.", "$1,500 в месяц может хватать аккуратному одному человеку в выбранных городах, но не в каждой азиатской столице и не для комфортного семейного переезда. Реальную цифру здесь решают аренда, визовые расходы, страховка и перелёты."),
            ("Most cheap-country lists start with apartment prices. That is only one piece. A real relocation budget includes visa fees, health insurance, deposits, flights, local transport, coworking, phone, emergency buffer and the cost of leaving or renewing if the visa requires it.", "Большинство подборок «дешёвых стран» начинают с аренды квартиры. Но это только один кусок картины. Реальный бюджет на релокацию включает визовые сборы, страховку, депозиты, перелёты, местный транспорт, коворкинг, связь, финансовую подушку и стоимость выезда или продления, если виза это требует."),
            ("If you ignore those costs, $1,500 looks stronger than it is. If you include them, the shortlist becomes clearer: some cities still work, some become tight, and some should be removed immediately.", "Если эти расходы игнорировать, $1,500 выглядит сильнее, чем есть на самом деле. Если посчитать их честно, shortlist сразу проясняется: какие-то города всё ещё подходят, какие-то становятся впритык, а какие-то лучше убрать сразу."),
            ("Single-person or lean-couple planning number.", "Это ориентир для одного человека или очень компактного сценария на двоих."),
            ("Rent plus visa rhythm.", "Аренда плюс визовый ритм: именно они быстрее всего ломают расчёт."),
            ("Insurance, flights, deposits, renewals or exits.", "Страховка, перелёты, депозиты, продления и вынужденные выезды."),
            ("Страховка, flights, deposits, renewals or exits.", "Страховка, перелёты, депозиты, продления и вынужденные выезды."),
            ("Families, premium districts, major financial hubs.", "Семьи, дорогие районы и крупные финансовые столицы."),
            ("Семьи, premium districts, major financial hubs.", "Семьи, дорогие районы и крупные финансовые столицы."),
            ("Vietnam, Cambodia, parts of Thailand, the Philippines and some Malaysian cities can fit a careful budget. The best fit is usually outside premium expat districts. A simple apartment, local food, limited nightlife and good health insurance discipline matter more than the country name.", "При аккуратном сценарии в такой бюджет могут укладываться Вьетнам, Камбоджа, часть Таиланда, Филиппины и отдельные города Малайзии. Обычно лучше всего работают не премиальные expat-районы. Простая квартира, местная еда, умеренный lifestyle и дисциплина по страховке значат здесь больше, чем само название страны."),
            ("Bangkok can work for some people and feel tight for others. Kuala Lumpur can be efficient but rent choices change everything. Da Nang may be easier than Singapore by a mile, but that does not mean every lifestyle in Da Nang is cheap.", "Бангкок у одних людей может работать, а у других быстро становится тесным по бюджету. Куала-Лумпур бывает эффективным, но там всё решает выбор жилья. Дананг действительно проще Сингапура почти по всем деньгам, но это не значит, что любой образ жизни в Дананге автоматически дешёвый."),
            ("Singapore, Hong Kong, central Tokyo and premium island lifestyles usually break this budget fast. The problem is not groceries. It is housing, insurance, school if you have children, and the lack of room for mistakes.", "Сингапур, Гонконг, центральный Токио и премиальный island-lifestyle обычно быстро ломают этот бюджет. Проблема там не в продуктах. Проблема в жилье, страховке, школе, если у вас есть дети, и в том, что у вас почти не остаётся пространства для ошибки."),
            ("Flexible remote workers who can live outside premium districts.", "Гибким удалёнщикам, которые готовы жить вне самых дорогих районов."),
            ("People expecting a Western big-city lifestyle on a lean budget.", "Тем, кто ждёт западный big-city lifestyle при очень ограниченном бюджете."),
            ("expecting a Western big-city lifestyle on a lean budget.", "тем, кто ждёт западный big-city lifestyle при очень ограниченном бюджете."),
            ("A family budget needs schools, healthcare and larger housing. $1,500 is usually too tight.", "Семейный бюджет требует школы, медицины и более крупного жилья. Для этого $1,500 обычно уже слишком мало."),
            ("Use a country as a filter, but budget by city.", "Используйте страну как фильтр, но считайте бюджет именно по городу."),
            ("Can I live in Asia on $1,500 a month?", "Можно ли жить в Азии на $1,500 в месяц?"),
            ("Yes in selected cities and with careful choices, but not everywhere.", "Да, в отдельных городах и при аккуратных решениях, но точно не везде."),
            ("Is Thailand possible on $1,500?", "Реален ли Таиланд на $1,500?"),
            ("Sometimes. Bangkok or islands can be tight; smaller cities may be easier.", "Иногда да. Бангкок и острова легко делают такой бюджет тесным, а города поменьше могут быть заметно проще."),
            ("Is Vietnam better for this budget?", "Лучше ли Вьетнам для такого бюджета?"),
            ("Often yes for lean living, but visa rhythm and housing still matter.", "Часто да, если речь про lean-сценарий, но визовый ритм и жильё всё равно решают очень много."),
            ("Is $1,500 enough for a family?", "Хватит ли $1,500 для семьи?"),
            ("Usually not comfortably.", "Обычно нет, если говорить о нормальном уровне комфорта."),
            ("What should I calculate first?", "Что считать в первую очередь?"),
            ("Rent, insurance, visa costs and exit or renewal costs.", "Аренду, страховку, визовые расходы и стоимость выезда или продления."),
        ],
    }
    content = replace_many(content, extra_slug_replacements.get(slug, []))
    return title, content


def breadcrumb_schema(items: list[tuple[str, str]], current_title: str, current_path: str) -> dict:
    is_ru = current_path.startswith("/ru/")
    schema_items = [("Главная" if is_ru else "Home", "/ru/" if is_ru else "/"), *items, (strip_html(current_title), current_path)]
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
        "logo": absolute_url(FAVICON_PATH),
        "email": CONTACT_EMAIL,
        "publishingPrinciples": absolute_url("/editorial-policy/"),
        "contactPoint": {
            "@type": "ContactPoint",
            "contactType": "editorial corrections",
            "email": CONTACT_EMAIL,
            "availableLanguage": ["English", "Russian"],
        },
    }


def editorial_team_schema(lang: str = "en") -> dict:
    return {
        "@type": "Organization",
        "name": DEFAULT_AUTHOR,
        "url": absolute_url(EDITORIAL_TEAM_URL if lang == "en" else "/ru/authors/editorial-team/"),
        "description": (
            "Editorial team checking relocation, visa and cost guides against official public sources."
            if lang == "en"
            else "Редакционная команда, которая сверяет визовые, страновые и бюджетные материалы с официальными источниками."
        ),
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
    for _quote, question, answer in re.findall(
        r'<div[^>]+class=(["\'])(?:[^"\']*\s)?faq-item(?:\s[^"\']*)?\1[^>]*>\s*<h3>(.*?)</h3>\s*<p>(.*?)</p>\s*</div>',
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


def trust_page_schema(title: str, path: str, *, page_type: str = "WebPage") -> dict:
    return {
        "@context": "https://schema.org",
        "@type": page_type,
        "name": strip_html(title),
        "url": absolute_url(path),
        "publisher": organization_schema(),
        "author": editorial_team_schema("ru" if path.startswith("/ru/") else "en"),
        "reviewedBy": editorial_team_schema("ru" if path.startswith("/ru/") else "en"),
        "dateModified": "2026-05-13",
        "publishingPrinciples": absolute_url("/ru/editorial-policy/" if path.startswith("/ru/") else "/editorial-policy/"),
        "isPartOf": {"@type": "WebSite", "name": SITE_NAME, "url": SITE_URL},
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


def country_meta_description_ru(slug: str, title: str, facts: sqlite3.Row | None) -> str:
    forms = COUNTRY_FORMS_RU.get(slug)
    country = forms[2] if forms else strip_html(title)
    details = []
    if facts:
        if facts["capital"]:
            details.append(f"столица {facts['capital']}")
        if facts["currency_code"]:
            details.append(f"валюта {facts['currency_code']}")
        if facts["internet_pct"]:
            details.append(f"интернетом пользуются {facts['internet_pct']:.1f}% населения")
    suffix = f" В фактах: {', '.join(details)}." if details else ""
    return f"{strip_html(title)}: визы, расходы, города и практические компромиссы для переезда в {country} в 2026 году.{suffix}"


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
    sources = extract_official_sources(row["content"])
    schema = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": strip_html(row["title"]),
        "description": trim_text(strip_html(row["excerpt"] or row["content"]), 200),
        "datePublished": published,
        "dateModified": published or "2026-05-13",
        "author": editorial_team_schema(lang),
        "reviewedBy": editorial_team_schema(lang),
        "publisher": organization_schema(),
        "editor": editorial_team_schema(lang),
        "mainEntityOfPage": absolute_url(canonical_path),
        "url": absolute_url(canonical_path),
        "inLanguage": lang,
        "image": [absolute_url(DEFAULT_OG_IMAGE)],
        "isAccessibleForFree": True,
        "publishingPrinciples": absolute_url("/editorial-policy/" if lang == "en" else "/ru/editorial-policy/"),
        "correction": absolute_url("/contact/" if lang == "en" else "/ru/contact/"),
    }
    if sources:
        schema["citation"] = [{"@type": "CreativeWork", "name": source["title"], "url": source["url"]} for source in sources]
    return schema


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
    if len(alternates) == 1:
        paired_lang = "ru" if lang == "en" else "en"
        paired_prefix = "/ru/blog" if paired_lang == "ru" else "/blog"
        paired = one("SELECT slug FROM posts WHERE slug = ? AND lang = ?", (row["slug"], paired_lang))
        if paired:
            alternates.append({"lang": paired_lang, "url": absolute_url(f"{paired_prefix}/{paired['slug']}/")})
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


def compare_pair_map() -> dict[str, list[dict[str, str]]]:
    rows = many("SELECT slug, parent, link FROM pages WHERE parent IN ('compare', 'ru-compare') OR slug IN ('compare', 'ru-compare')")
    pairs: dict[str, dict[str, str]] = {}
    for row in rows:
        if row["slug"] == "compare":
            pairs.setdefault("compare", {})["en"] = "/compare/"
        elif row["slug"] == "ru-compare":
            pairs.setdefault("compare", {})["ru"] = "/ru/compare/"
        elif row["parent"] == "compare":
            pairs.setdefault(row["slug"], {})["en"] = f"/compare/{row['slug']}/"
        elif row["parent"] == "ru-compare":
            normalized_slug = row["slug"].removeprefix("ru-")
            pairs.setdefault(normalized_slug, {})["ru"] = f"/ru/compare/{normalized_slug}/"
    alternate_map: dict[str, list[dict[str, str]]] = {}
    for pair in pairs.values():
        if "en" not in pair or "ru" not in pair:
            continue
        alternates = localized_page_alternates(en_path=pair["en"], ru_path=pair["ru"])
        alternate_map[pair["en"]] = alternates
        alternate_map[pair["ru"]] = alternates
    return alternate_map


def static_localized_pairs() -> dict[str, str]:
    return {
        "/": "/ru/",
        "/countries/": "/ru/countries/",
        "/tools/": "/ru/tools/",
        "/compare/": "/ru/compare/",
        "/compare-cities/": "/ru/compare-cities/",
        "/visas/": "/ru/visas/",
        "/best-countries-in-asia-to-move/": "/ru/best-countries-in-asia-to-move/",
        "/cheapest-countries-in-asia/": "/ru/cheapest-countries-in-asia/",
        "/move-to-asia/": "/ru/move-to-asia/",
        "/digital-nomad-visas-asia/": "/ru/digital-nomad-visas-asia/",
        "/retire-in-asia/": "/ru/retire-in-asia/",
        "/cost-of-living-asia/": "/ru/cost-of-living-asia/",
        "/guides/": "/ru/guides/",
        "/about/": "/ru/about/",
        "/authors/": "/ru/authors/",
        "/authors/editorial-team/": "/ru/authors/editorial-team/",
        "/contact/": "/ru/contact/",
        "/editorial-policy/": "/ru/editorial-policy/",
        "/how-we-verify-data/": "/ru/how-we-verify-data/",
    }


def default_page_alternates(path: str) -> list[dict[str, str]] | None:
    static_pairs = static_localized_pairs()
    if path in static_pairs:
        return localized_page_alternates(en_path=path, ru_path=static_pairs[path])
    reverse_pairs = {ru: en for en, ru in static_pairs.items()}
    if path in reverse_pairs:
        return localized_page_alternates(en_path=reverse_pairs[path], ru_path=path)
    patterns = [
        (r"^/countries/([^/]+)/$", "/countries/{slug}/", "/ru/countries/{slug}/"),
        (r"^/ru/countries/([^/]+)/$", "/countries/{slug}/", "/ru/countries/{slug}/"),
        (r"^/tools/([^/]+)/$", "/tools/{slug}/", "/ru/tools/{slug}/"),
        (r"^/ru/tools/([^/]+)/$", "/tools/{slug}/", "/ru/tools/{slug}/"),
        (r"^/guides/([^/]+)/$", "/guides/{slug}/", "/ru/guides/{slug}/"),
        (r"^/ru/guides/([^/]+)/$", "/guides/{slug}/", "/ru/guides/{slug}/"),
        (r"^/compare/([^/]+)/$", "/compare/{slug}/", "/ru/compare/{slug}/"),
        (r"^/ru/compare/([^/]+)/$", "/compare/{slug}/", "/ru/compare/{slug}/"),
    ]
    for pattern, en_template, ru_template in patterns:
        match = re.match(pattern, path)
        if match:
            slug = match.group(1)
            return localized_page_alternates(
                en_path=en_template.format(slug=slug),
                ru_path=ru_template.format(slug=slug),
            )
    blog_match = re.match(r"^/(ru/)?blog/page/(\d+)/$", path)
    if blog_match:
        page_num = blog_match.group(2)
        return localized_page_alternates(
            en_path=f"/blog/page/{page_num}/",
            ru_path=f"/ru/blog/page/{page_num}/",
        )
    return None

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


def _external_links_nofollow(text: str) -> str:
    def repl(match: re.Match) -> str:
        attrs = match.group(1)
        href_match = re.search(r'\bhref=(["\'])(https?://.*?)\1', attrs, flags=re.IGNORECASE)
        if not href_match:
            return match.group(0)
        if re.search(r"\brel=", attrs, flags=re.IGNORECASE):
            attrs = re.sub(
                r'\brel=(["\'])(.*?)\1',
                lambda rel: f'rel={rel.group(1)}{rel.group(2)} nofollow noopener{rel.group(1)}'
                if "nofollow" not in rel.group(2).lower()
                else rel.group(0),
                attrs,
                count=1,
                flags=re.IGNORECASE,
            )
        else:
            attrs = f'{attrs} rel="nofollow noopener"'
        if not re.search(r"\btarget=", attrs, flags=re.IGNORECASE):
            attrs = f'{attrs} target="_blank"'
        return f"<a{attrs}>"

    return re.sub(r"<a\b([^>]*)>", repl, text, flags=re.IGNORECASE)


def _localize_internal_links(text: str, *, lang: str) -> str:
    if lang != "ru":
        return text
    replacements = [
        ('href="/countries/', 'href="/ru/countries/'),
        ('href="/tools/', 'href="/ru/tools/'),
        ('href="/guides/', 'href="/ru/guides/'),
        ('href="/compare-cities/', 'href="/ru/compare-cities/'),
        ('href="/compare/', 'href="/ru/compare/'),
        ('href="/visas/', 'href="/ru/visas/'),
        ('href="/best-countries-in-asia-to-move/', 'href="/ru/best-countries-in-asia-to-move/'),
        ('href="/cheapest-countries-in-asia/', 'href="/ru/cheapest-countries-in-asia/'),
        ('href="/move-to-asia/', 'href="/ru/move-to-asia/'),
        ('href="/digital-nomad-visas-asia/', 'href="/ru/digital-nomad-visas-asia/'),
        ('href="/retire-in-asia/', 'href="/ru/retire-in-asia/'),
        ('href="/cost-of-living-asia/', 'href="/ru/cost-of-living-asia/'),
        ('href="/about/', 'href="/ru/about/'),
        ('href="/editorial-policy/', 'href="/ru/editorial-policy/'),
        ('href="/how-we-verify-data/', 'href="/ru/how-we-verify-data/'),
        ('href="/"', 'href="/ru/"'),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    return text


@app.template_filter("wp_clean")
def wp_clean(content: str | None) -> str:
    if not content:
        return ""

    cleaned = content
    # JSON-LD is generated centrally from the current route. Old embedded blocks
    # in imported content can create duplicate or stale schema.
    cleaned = re.sub(
        r"<script\b(?=[^>]*type=[\"']application/ld\+json[\"'])[^>]*>.*?</script>",
        "",
        cleaned,
        flags=re.IGNORECASE | re.DOTALL,
    )
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
    cleaned = _localize_internal_links(cleaned, lang="ru" if request.path.startswith("/ru/") else "en")
    cleaned = _external_links_nofollow(cleaned)
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
            final_url = url
            if lang == "ru" and url.startswith("/") and not url.startswith("/ru/"):
                final_url = f"/ru{url}"
            links.append(_link(
                ru_title if lang == "ru" else en_title,
                final_url,
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
            _link("Гайд по визам Азии", "/ru/visas/", "Главная страница для сравнения визовых маршрутов."),
            _link("Сравнить страны", "/ru/compare/", "Быстрое сравнение стран для переезда в Азию."),
            _link("Калькулятор стоимости жизни", "/ru/tools/cost-calculator/", "Проверка бюджета перед выбором страны."),
            _link("Планировщик бюджета", "/ru/tools/budget-planner/", "Разложить переезд по основным расходам."),
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
    lang = "ru" if current_path.startswith("/ru/") else "en"
    links = _matched_country_links(text, lang)
    if lang == "ru":
        links.extend([
            _link("Гид по странам", "/ru/countries/", "Начните со страновых страниц, если ещё выбираете направление."),
            _link("Гайд по визам Азии", "/ru/visas/", "Сначала сравните визовые маршруты, а уже потом жильё и билеты."),
            _link("Короткие гайды по решениям", "/ru/guides/", "Страницы под конкретные визовые и релокационные вопросы."),
            _link("Сравнить страны", "/ru/compare/", "Сводные сравнения стран для переезда и долгого проживания."),
            _link("Сравнить города", "/ru/compare-cities/", "Посмотрите городские компромиссы до выбора базы."),
            _link("Бесплатные инструменты", "/ru/tools/", "Калькулятор расходов и планировщик бюджета."),
            _link("Блог на русском", "/ru/blog/", "Свежие русскоязычные статьи по визам, странам и переезду."),
        ])
    else:
        links.extend([
            _link("Countries hub", "/countries/", "Start with country pages if you are still choosing a destination."),
            _link("Asia visa guide", "/visas/", "Compare visa routes before planning housing or flights."),
            _link("Focused SEO guides", "/guides/", "Short decision pages for long-tail visa and relocation questions."),
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
                WHERE lang = ?
                  AND (lower(slug) LIKE ? OR lower(title) LIKE ? OR lower(excerpt) LIKE ?)
                ORDER BY date DESC, id DESC
                LIMIT 3
                """,
                (lang, f"%{str(key).lower()}%", f"%{str(key).lower()}%", f"%{str(key).lower()}%"),
            )
            for post in topic_posts:
                links.append(_link(strip_html(post["title"]), post_path(post), trim_text(strip_html(post["excerpt"] or ""), 110)))
            if topic_posts:
                break
    latest_posts = many("SELECT slug, title, excerpt, lang FROM posts WHERE lang = ? ORDER BY date DESC, id DESC LIMIT 4", (lang,))
    for post in latest_posts:
        links.append(_link(strip_html(post["title"]), post_path(post), trim_text(strip_html(post["excerpt"] or ""), 110)))
    return _dedupe_links(links, current_path=current_path, limit=8)


def internal_links_for_blog(lang: str) -> list[dict[str, str]]:
    if lang == "ru":
        return [
            _link("Гид по странам", "/ru/countries/", "Страницы стран: стоимость жизни, города, визовая логика и практические компромиссы."),
            _link("Гайд по визам Азии", "/ru/visas/", "Сравнение визовых маршрутов до выбора страны."),
            _link("Сравнить страны", "/ru/compare/", "Быстрое сравнение направлений для переезда."),
            _link("Калькулятор стоимости жизни", "/ru/tools/cost-calculator/", "Проверка бюджета перед планированием переезда."),
            _link("Планировщик бюджета", "/ru/tools/budget-planner/", "Разложить расходы на переезд по категориям."),
            _link("Сравнить города", "/ru/compare-cities/", "Сравнение городов по практическим метрикам."),
        ]
    return [
        _link("Countries hub", "/countries/", "Country pages for costs, cities, visa logic and trade-offs."),
        _link("Asia visa guide", "/visas/", "Compare visa routes before choosing a destination."),
        _link("Focused visa questions", "/guides/", "Long-tail answers for specific relocation decisions."),
        _link("Compare countries", "/compare/", "Side-by-side comparison for relocation decisions."),
        _link("Cost of living calculator", "/tools/cost-calculator/", "Check the monthly budget before planning a move."),
        _link("Budget planner", "/tools/budget-planner/", "Break relocation expenses into practical categories."),
        _link("Compare Asian cities", "/compare-cities/", "City-level comparison for choosing a base."),
    ]


SOURCE_EXCLUDE_TERMS = (
    "worldbank",
    "api.worldbank",
    "restcountries",
    "flagcdn",
    "github",
    "localhost",
    "127.0.0.1",
)


VISA_FACT_HINTS = [
    (
        ("japan-digital-nomad", "yaponiya-digital-nomad"),
        [
            ("Stay Length", "6 months"),
            ("Extension", "No extension will be granted"),
            ("Work Logic", "Remote work in Japan, not local employment"),
        ],
    ),
    (
        ("taiwan-gold-card",),
        [
            ("Validity", "1 year, 2 years or 3 years"),
            ("Route Type", "Work permit, residence permit and visa combined"),
        ],
    ),
    (
        ("indonesia-e33g",),
        [
            ("Core Limit", "Remote work for an overseas employer"),
            ("Planning Risk", "Local Indonesian employment is a separate issue"),
        ],
    ),
    (
        ("thailand-ltr",),
        [
            ("Route Type", "Long-term resident visa category"),
            ("Planning Risk", "Eligibility depends on profile and documents"),
        ],
    ),
    (
        ("philippines-srrv",),
        [
            ("Benefit", "Multiple entry and indefinite stay"),
            ("Core Check", "Deposit tier and age category"),
        ],
    ),
    (
        ("south-korea-workation", "yuzhnaya-koreya-workation"),
        [
            ("Visa Route", "F-1-D Workation"),
            ("Core Limit", "Remote work route, not local employment"),
        ],
    ),
    (
        ("malaysia-de-rantau",),
        [
            ("Route", "DE Rantau Nomad Pass"),
            ("Planning Check", "Income, work profile and location fit"),
        ],
    ),
    (
        ("singapore-one-pass",),
        [
            ("Validity", "5 years"),
            ("Route Type", "Top talent pass"),
        ],
    ),
    (
        ("vietnam-evisa", "vietnam-evisa-guide"),
        [
            ("Stay Length", "Up to 90 days"),
            ("Entry Type", "Single or multiple entry"),
        ],
    ),
    (
        ("sri-lanka-eta",),
        [
            ("Route Type", "ETA for short visits"),
            ("Core Check", "Short-visit purpose and extension rules"),
        ],
    ),
    (
        ("india-e-tourist",),
        [
            ("Route Type", "e-Tourist Visa"),
            ("Options", "30 days, 1 year or 5 years"),
        ],
    ),
    (
        ("uae-virtual-work",),
        [
            ("Route Type", "Virtual Work Residence"),
            ("Validity", "One-year self-sponsored route"),
        ],
    ),
]


def extract_official_sources(content: str | None, *, limit: int = 6) -> list[dict[str, str]]:
    if not content:
        return []
    sources: list[dict[str, str]] = []
    for attrs, label in re.findall(r"<a\b([^>]*)>(.*?)</a>", content, flags=re.IGNORECASE | re.DOTALL):
        href_match = re.search(r'\bhref=(["\'])(https?://.*?)\1', attrs, flags=re.IGNORECASE)
        if not href_match:
            continue
        url = href_match.group(2)
        lowered = url.lower()
        if any(term in lowered for term in SOURCE_EXCLUDE_TERMS):
            continue
        title = strip_html(label) or url
        if not any(item["url"] == url for item in sources):
            sources.append({"title": trim_text(title, 90), "url": url})
        if len(sources) >= limit:
            break
    return sources


def matched_country_fact(text: str) -> sqlite3.Row | None:
    lowered = text.lower()
    for *keys, url, _en_title, _ru_title in COUNTRY_INTERNAL_LINKS:
        if any(str(key).lower() in lowered for key in keys):
            slug = url.rstrip("/").rsplit("/", 1)[-1]
            return one("SELECT * FROM country_facts WHERE slug = ?", (slug,))
    return None


def post_seo_panel(row: sqlite3.Row | dict, *, lang: str) -> dict:
    text = f"{row['slug']} {strip_html(row['title'])} {strip_html(row['excerpt'] or '')}"
    sources = extract_official_sources(row["content"])
    country = matched_country_fact(text)
    labels = {
        "title": "Проверенные факты для планирования" if lang == "ru" else "Checked Planning Facts",
        "source_title": "Официальные источники" if lang == "ru" else "Official Sources",
        "source_note": (
            "API и технические источники здесь не показываются: они используются только внутри сайта."
            if lang == "ru"
            else "Technical APIs are not shown here because they are internal data infrastructure."
        ),
        "checked": "Проверено" if lang == "ru" else "Checked",
        "country": "Страна" if lang == "ru" else "Country",
        "capital": "Столица" if lang == "ru" else "Capital",
        "currency": "Валюта" if lang == "ru" else "Currency",
        "internet": "Пользователи интернета" if lang == "ru" else "Internet Users",
        "official_links": "Официальные ссылки" if lang == "ru" else "Official Links",
    }
    rows = [
        {"label": labels["checked"], "value": "апрель 2026" if lang == "ru" else "April 2026"},
        {"label": labels["official_links"], "value": str(len(sources)) if sources else "1+"},
    ]
    if country:
        rows.extend([
            {"label": labels["country"], "value": country["name"]},
            {"label": labels["capital"], "value": country["capital"]},
            {"label": labels["currency"], "value": country["currency_code"]},
        ])
        if country["internet_pct"]:
            rows.append({"label": labels["internet"], "value": f"{country['internet_pct']:.1f}%"})
    slug = row["slug"].lower()
    for patterns, facts in VISA_FACT_HINTS:
        if any(pattern in slug for pattern in patterns):
            rows.extend({"label": label, "value": value} for label, value in facts)
            break
    if lang == "ru":
        panel_replacements = [
            ("Stay Length", "Срок stay"),
            ("Extension", "Продление"),
            ("Work Logic", "Логика работы"),
            ("Validity", "Срок действия"),
            ("Route Type", "Тип маршрута"),
            ("Core Limit", "Главное ограничение"),
            ("Planning Risk", "Риск планирования"),
            ("Benefit", "Преимущество"),
            ("Core Check", "Что проверить"),
            ("Visa Route", "Визовый маршрут"),
            ("Income standard", "Требование по доходу"),
            ("Options", "Варианты"),
            ("6 months", "6 месяцев"),
            ("No extension will be granted", "продление не заявлено"),
            ("Remote work in Japan, not local employment", "удалённая работа из Японии, не местное трудоустройство"),
            ("1 year, 2 years or 3 years", "1, 2 или 3 года"),
            ("Work permit, residence permit and visa combined", "work permit, residence permit и visa в одном маршруте"),
            ("Remote work for an overseas employer", "удалённая работа на иностранного работодателя"),
            ("Local Indonesian employment is a separate issue", "местная работа в Индонезии — отдельный вопрос"),
            ("Long-term resident visa category", "категория long-term resident visa"),
            ("Eligibility depends on profile and documents", "eligibility зависит от профиля и документов"),
            ("Multiple entry and indefinite stay", "multiple entry и indefinite stay"),
            ("Deposit tier and age category", "deposit tier и возрастная категория"),
            ("F-1-D Workation", "F-1-D Workation"),
            ("Remote work route, not local employment", "маршрут для удалённой работы, не местное трудоустройство"),
            ("DE Rantau Nomad Pass", "DE Rantau Nomad Pass"),
            ("Income, work profile and location fit", "доход, рабочий профиль и location fit"),
            ("5 years", "5 лет"),
            ("Top talent pass", "top talent pass"),
            ("Up to 90 days", "до 90 дней"),
            ("Single or multiple entry", "single или multiple entry"),
            ("ETA for short visits", "ETA для short visit"),
            ("Short-visit purpose and extension rules", "цель short visit и правила продления"),
            ("e-Tourist Visa", "e-Tourist Visa"),
            ("30 days, 1 year or 5 years", "30 дней, 1 год или 5 лет"),
            ("Virtual Work Residence", "Virtual Work Residence"),
            ("One-year self-sponsored route", "годовой self-sponsored маршрут"),
        ]
        rows = [
            {
                "label": replace_many(str(row["label"]), panel_replacements),
                "value": replace_many(str(row["value"]), panel_replacements),
            }
            for row in rows
        ]
    return {
        "labels": labels,
        "rows": rows[:8],
        "sources": sources,
        "country": country,
    }


def article_trust_panel(row: sqlite3.Row | dict, *, lang: str) -> dict:
    sources = extract_official_sources(row["content"])
    if lang == "ru":
        return {
            "eyebrow": "Проверка и ответственность",
            "author_label": "Автор",
            "author": DEFAULT_AUTHOR,
            "author_url": "/ru/authors/editorial-team/",
            "reviewer_label": "Проверка фактов",
            "reviewer": DEFAULT_AUTHOR,
            "reviewed_label": "Последняя редакционная проверка",
            "reviewed": LAST_REVIEWED_RU,
            "sources_label": "Официальных источников в материале",
            "sources_count": str(len(sources)) if sources else "1+",
            "methodology_label": "Как мы проверяем данные",
            "methodology_url": "/ru/how-we-verify-data/",
            "corrections_label": "Сообщить об ошибке",
            "corrections_url": "/ru/contact/",
            "disclaimer": "Материал помогает планировать переезд, но не является юридической, налоговой, медицинской или финансовой консультацией. Перед подачей документов проверяйте официальный источник.",
        }
    return {
        "eyebrow": "Review And Accountability",
        "author_label": "Author",
        "author": DEFAULT_AUTHOR,
        "author_url": "/authors/editorial-team/",
        "reviewer_label": "Fact checked by",
        "reviewer": DEFAULT_AUTHOR,
        "reviewed_label": "Last editorial check",
        "reviewed": LAST_REVIEWED_EN,
        "sources_label": "Official sources in this guide",
        "sources_count": str(len(sources)) if sources else "1+",
        "methodology_label": "How We Verify Data",
        "methodology_url": "/how-we-verify-data/",
        "corrections_label": "Report outdated information",
        "corrections_url": "/contact/",
        "disclaimer": "This guide is for relocation planning only. It is not legal, tax, medical or financial advice. Always verify the official source before applying or paying for services.",
    }


def page_trust_panel(path: str, *, lang: str) -> dict | None:
    skip_paths = {
        "/about/", "/ru/about/", "/authors/", "/ru/authors/",
        "/authors/editorial-team/", "/ru/authors/editorial-team/",
        "/editorial-policy/", "/ru/editorial-policy/",
        "/how-we-verify-data/", "/ru/how-we-verify-data/",
        "/contact/", "/ru/contact/",
    }
    if path in skip_paths:
        return None
    ymyl_prefixes = (
        "/visas/", "/ru/visas/",
        "/guides/", "/ru/guides/",
        "/countries/", "/ru/countries/",
        "/compare/", "/ru/compare/",
        "/tools/", "/ru/tools/",
        "/retire-in-asia/", "/ru/retire-in-asia/",
        "/cost-of-living-asia/", "/ru/cost-of-living-asia/",
        "/digital-nomad-visas-asia/", "/ru/digital-nomad-visas-asia/",
    )
    if path != "/" and not path.startswith(ymyl_prefixes):
        return None
    if lang == "ru":
        return {
            "title": "Как проверена эта страница",
            "items": [
                ("Редакция", DEFAULT_AUTHOR),
                ("Последняя проверка", LAST_REVIEWED_RU),
                ("Методология", "официальные источники, страновые данные и ручная редакционная проверка"),
            ],
            "methodology_url": "/ru/how-we-verify-data/",
            "methodology_label": "Как мы проверяем данные",
            "contact_url": "/ru/contact/",
            "contact_label": "Сообщить об ошибке",
            "disclaimer": "Информация помогает сузить выбор страны, визы или бюджета. Это не юридическая, налоговая, медицинская или финансовая консультация.",
        }
    return {
        "title": "How This Page Is Checked",
        "items": [
            ("Editorial team", DEFAULT_AUTHOR),
            ("Last checked", LAST_REVIEWED_EN),
            ("Method", "official sources, country data and manual editorial review"),
        ],
        "methodology_url": "/how-we-verify-data/",
        "methodology_label": "How We Verify Data",
        "contact_url": "/contact/",
        "contact_label": "Report outdated information",
        "disclaimer": "This page supports relocation planning. It is not legal, tax, medical or financial advice.",
    }


def _official_source(title: str, url: str, note_en: str, note_ru: str, *, lang: str) -> dict[str, str]:
    return {"title": title, "url": url, "note": note_ru if lang == "ru" else note_en}


def page_source_panel(path: str, *, lang: str) -> dict | None:
    guide_match = re.match(r"^/(?:ru/)?guides/([^/]+)/$", path)
    is_visa_hub = path in {"/visas/", "/ru/visas/"}
    simple_source_map = {
        "/countries/": ["world_bank", "thailand_dtv", "malaysia", "taiwan", "japan", "vietnam"],
        "/ru/countries/": ["world_bank", "thailand_dtv", "malaysia", "taiwan", "japan", "vietnam"],
        "/guides/": ["japan", "thailand_dtv", "thailand_ltr", "malaysia", "taiwan", "vietnam"],
        "/ru/guides/": ["japan", "thailand_dtv", "thailand_ltr", "malaysia", "taiwan", "vietnam"],
        "/compare/": ["world_bank", "thailand_dtv", "malaysia", "taiwan", "japan", "vietnam"],
        "/ru/compare/": ["world_bank", "thailand_dtv", "malaysia", "taiwan", "japan", "vietnam"],
        "/retire-in-asia/": ["world_bank", "philippines", "thailand_ltr", "malaysia"],
        "/ru/retire-in-asia/": ["world_bank", "philippines", "thailand_ltr", "malaysia"],
        "/digital-nomad-visas-asia/": ["japan", "taiwan", "indonesia", "thailand_dtv", "malaysia", "south-korea", "uae"],
        "/ru/digital-nomad-visas-asia/": ["japan", "taiwan", "indonesia", "thailand_dtv", "malaysia", "south-korea", "uae"],
        "/cost-of-living-asia/": ["world_bank", "thailand_dtv", "thailand_ltr", "malaysia", "taiwan", "japan", "vietnam", "indonesia"],
        "/ru/cost-of-living-asia/": ["world_bank", "thailand_dtv", "thailand_ltr", "malaysia", "taiwan", "japan", "vietnam", "indonesia"],
        "/best-countries-in-asia-to-move/": ["world_bank", "thailand_dtv", "thailand_ltr", "malaysia", "taiwan", "japan", "vietnam", "indonesia", "philippines", "singapore", "uae", "cambodia"],
        "/ru/best-countries-in-asia-to-move/": ["world_bank", "thailand_dtv", "thailand_ltr", "malaysia", "taiwan", "japan", "vietnam", "indonesia", "philippines", "singapore", "uae", "cambodia"],
        "/cheapest-countries-in-asia/": ["world_bank", "vietnam", "indonesia", "malaysia", "philippines", "cambodia", "thailand_dtv"],
        "/ru/cheapest-countries-in-asia/": ["world_bank", "vietnam", "indonesia", "malaysia", "philippines", "cambodia", "thailand_dtv"],
    }
    simple_source_keys = simple_source_map.get(path)
    country_match = re.match(r"^/(?:ru/)?countries/move-to-([^/]+)/$", path)
    compare_match = re.match(r"^/(?:ru/)?compare/([^/]+)/$", path)
    if not guide_match and not is_visa_hub and not country_match and not compare_match and not simple_source_keys:
        return None

    sources = {
        "world_bank": [
            _official_source("World Bank Data: Individuals Using The Internet", "https://data.worldbank.org/indicator/IT.NET.USER.ZS", "Public World Bank indicator used to sanity-check internet access context by country.", "Публичный показатель World Bank для сверки контекста по доступу к интернету в странах.", lang=lang),
            _official_source("World Bank Data: Population, Total", "https://data.worldbank.org/indicator/SP.POP.TOTL", "Public World Bank population indicator used for country-scale context.", "Публичный показатель World Bank по населению для проверки масштаба страны.", lang=lang),
            _official_source("World Bank Data: GDP Per Capita", "https://data.worldbank.org/indicator/NY.GDP.PCAP.CD", "Public macro indicator used only as background, not as a personal budget figure.", "Макропоказатель для общего контекста, не как персональный бюджет переезда.", lang=lang),
        ],
        "japan": [
            _official_source("Japan Immigration Services Agency: Digital Nomad / Designated Activities", "https://www.moj.go.jp/isa/applications/status/designatedactivities53_00001.html", "Primary rule page for stay length, activity and no-extension language.", "Основная страница с правилом по сроку, деятельности и формулировке no extension.", lang=lang),
            _official_source("Japan MOFA: Specified Visa For Digital Nomad", "https://www.mofa.go.jp/ca/fna/pagewe_000001_00046.html", "MOFA visa page for documents, income proof and insurance requirements.", "Страница MOFA по визе: документы, подтверждение дохода и страховка.", lang=lang),
            _official_source("JNTO: Digital Nomad Visa", "https://www.japan.travel/en/plan/digital-nomad-visa/", "Public Japan travel summary of the six-month non-renewable route.", "Публичное резюме японского маршрута: шесть месяцев и без продления.", lang=lang),
            _official_source("Japan ISA: Designated Activities English Page", "https://www.moj.go.jp/isa/applications/status/designatedactivities10_00001.html?hl=en", "Immigration Services Agency page for the Japanese designated activities status.", "Страница Immigration Services Agency по статусу Designated Activities.", lang=lang),
            _official_source("Japan ISA: Digital Nomad Outline PDF", "https://www.moj.go.jp/isa/content/001422249.pdf", "Official ISA PDF used for route outline and Q&A checks.", "Официальный PDF ISA для проверки outline и Q&A по маршруту.", lang=lang),
            _official_source("JNTO: Japan Visa Information", "https://www.japan.travel/en/plan/visa-information/", "Official tourism visa information page linking the digital nomad route.", "Официальная туристическая страница по визам с ссылкой на digital nomad route.", lang=lang),
            _official_source("MOFA Japan: Visa Information", "https://www.mofa.go.jp/j_info/visit/visa/index.html", "MOFA visa information hub for cross-checking Japanese visa guidance.", "Визовый раздел MOFA для дополнительной проверки японских визовых правил.", lang=lang),
            _official_source("Japan ISA: Status Of Residence List", "https://www.moj.go.jp/isa/applications/status/designatedactivities", "Official status-of-residence reference for Designated Activities.", "Официальный справочник по статусу Designated Activities.", lang=lang),
            _official_source("JNTO: Digital Nomad Visa Spanish Page", "https://www.japan.travel/es/plan/digital-nomad-visa/", "Official JNTO localized page used as a secondary consistency check.", "Официальная локализованная страница JNTO для дополнительной сверки формулировок.", lang=lang),
            _official_source("JNTO: Digital Nomad Visa French Page", "https://www.japan.travel/fr/plan/digital-nomad-visa/", "Official JNTO localized page used as a secondary consistency check.", "Официальная локализованная страница JNTO для дополнительной сверки формулировок.", lang=lang),
        ],
        "thailand_dtv": [
            _official_source("Thailand e-Visa Official Website", "https://www.thaievisa.go.th/", "Official application entry point for Thai visa categories.", "Официальная точка входа для заявок по тайским визовым категориям.", lang=lang),
            _official_source("Thailand.go.th: Destination Thailand Visa Launch", "https://thailand.go.th/visit-thailand-detail/-destination-thailand-visa-dtv", "Government page confirming DTV purpose, 180-day stay and extension context.", "Государственная страница по DTV: цель маршрута, пребывание до 180 дней и контекст продления.", lang=lang),
            _official_source("Thailand.go.th: 3 DTV Tourist Visa Types", "https://thailand.go.th/issue-focus-detail/3---destination-thailand-visa-dtv?hl=en", "Government page listing DTV categories, 500,000 THB financial evidence and 5-year validity.", "Государственная страница с категориями DTV, финансовым подтверждением 500 000 THB и сроком действия 5 лет.", lang=lang),
            _official_source("Royal Thai Consulate-General Los Angeles: DTV", "https://thaiconsulatela.thaiembassy.org/en/publicservice/dtv-visa%3Fcate%3D61a8019ec0e81b444e7a5b52", "Official consulate checklist for DTV workcation, soft-power and dependant routes.", "Официальный чеклист консульства по DTV: workcation, soft power и dependants.", lang=lang),
            _official_source("Royal Thai Embassy Vienna: DTV", "https://www.thaiembassy.at/en/type-of-visa/destination-thailand-visa-dtv.html", "Embassy DTV page for local application and document cross-checks.", "Страница посольства по DTV для проверки документов и местных требований подачи.", lang=lang),
        ],
        "thailand_ltr": [
            _official_source("Thailand BOI: Long-Term Resident Visa", "https://ltr.boi.go.th/", "Official LTR program portal and category overview.", "Официальный портал программы LTR и обзор категорий.", lang=lang),
            _official_source("BOI LTR Visa Issuance", "https://ltr.boi.go.th/page/visa-issuance-info.html", "Official issuance page for endorsement validity, visa stamp and work permit handling.", "Официальная страница выдачи LTR: срок endorsement, штамп визы и логика work permit.", lang=lang),
            _official_source("BOI LTR Required Documents", "https://ltr.boi.go.th/page/required-documents.html", "Official hub for required document checklists by LTR category.", "Официальный раздел BOI с чеклистами документов по категориям LTR.", lang=lang),
            _official_source("BOI LTR Work-From-Thailand Documents", "https://ltr.boi.go.th/documents/Required-docs-Work-From-Thailand-Professional-30-06-2025.pdf", "Official checklist for Work-From-Thailand Professionals, including insurance and proof requirements.", "Официальный чеклист Work-From-Thailand Professionals: страховка, документы и подтверждения.", lang=lang),
            _official_source("BOI LTR Wealthy Pensioners Documents", "https://ltr.boi.go.th/documents/Required-docs-Wealthy-Pensioners-30-06-2025.pdf", "Official pensioner checklist for passive income and investment evidence.", "Официальный чеклист Wealthy Pensioners: пассивный доход и инвестиционные подтверждения.", lang=lang),
            _official_source("BOI LTR Wealthy Global Citizens Documents", "https://ltr.boi.go.th/documents/Required-docs-Wealthy-Global-Citizens-30-06-2025.pdf", "Official checklist for Wealthy Global Citizens, including asset and investment evidence.", "Официальный чеклист Wealthy Global Citizens: активы и инвестиционные подтверждения.", lang=lang),
            _official_source("BOI LTR Dependants Documents", "https://ltr.boi.go.th/documents/Spouses-and-dependents-required-documents.pdf", "Official checklist for spouses and dependants under LTR.", "Официальный чеклист для супругов и dependants по LTR.", lang=lang),
            _official_source("Royal Thai Embassy Vienna: LTR Visa", "https://www.thaiembassy.at/en/type-of-visa/long-term-resident-ltr-visa.html", "Embassy page explaining LTR application flow through BOI and e-Visa.", "Страница посольства с логикой подачи LTR через BOI и e-Visa.", lang=lang),
        ],
        "malaysia": [
            _official_source("MDEC: DE Rantau FAQ For Foreign Applicants", "https://mdec.my/static/pdf/derantau/DE%20Rantau%20Pass%20FAQ-Foreign.pdf", "Official FAQ used to check DE Rantau applicant logic.", "Официальный FAQ для проверки логики DE Rantau для иностранных заявителей.", lang=lang),
            _official_source("MDEC: DE Rantau Programme Updates", "https://www.mdec.my/media-release/news-press-release/336/mdec-expands-de-rantau-programme-new-opportunities-for-global-digital-nomads-and-exciting-partnerships", "MDEC programme update and expansion context.", "Обновление MDEC по программе и её расширению.", lang=lang),
            _official_source("MDEC: DE Rantau Sarawak Announcement", "https://www.mdec.my/media-release/news-press-release/346/de-rantau-sarawak-the-new-frontier-for-digital-nomads-in-borneo", "Official MDEC announcement for DE Rantau Sarawak and family usage context.", "Официальный анонс MDEC по DE Rantau Sarawak и контексту семейных заявителей.", lang=lang),
            _official_source("Immigration Department of Malaysia", "https://www.imi.gov.my/", "Official Malaysian immigration portal for pass and entry cross-checks.", "Официальный портал иммиграционной службы Малайзии для проверки pass и въезда.", lang=lang),
            _official_source("Malaysia Immigration: Professional Visit Pass", "https://www.imi.gov.my/index.php/en/main-services/pass/professional-visitor-pass/", "Official immigration page for professional visit pass context.", "Официальная страница иммиграции по Professional Visit Pass для контекста pass-логики.", lang=lang),
            _official_source("ESD Malaysia: MYXpats Centre FAQ", "https://esd.imi.gov.my/portal/faq/myxpats/", "Official ESD FAQ for expatriate pass processing context.", "Официальный FAQ ESD по обработке expatriate passes.", lang=lang),
            _official_source("Malaysia Digital Arrival Card", "https://imigresen-online.imi.gov.my/mdac/egate", "Official MDAC page for arrival-card checks before entry.", "Официальная страница MDAC для проверки arrival card перед въездом.", lang=lang),
        ],
        "taiwan": [
            _official_source("Taiwan Gold Card: Salary Requirement FAQ", "https://goldcard.nat.gov.tw/en/faq/how-do-i-meet-the-salary-requirements-of-the-gold-card-application/", "Official Gold Card FAQ for salary-based qualification.", "Официальный FAQ Gold Card по salary-based квалификации.", lang=lang),
            _official_source("Taiwan Gold Card Official Portal", "https://goldcard.nat.gov.tw/en/", "Official portal for Employment Gold Card categories and application logic.", "Официальный портал Employment Gold Card с категориями и логикой подачи.", lang=lang),
            _official_source("Taiwan Gold Card: Application Information", "https://goldcard.nat.gov.tw/en/application/", "Official application guide for documents, timeline and pick-up logic.", "Официальный guide по подаче: документы, сроки и получение карты.", lang=lang),
            _official_source("Taiwan Gold Card: Application Guide", "https://goldcard.nat.gov.tw/en/apply/", "Official step-by-step Gold Card application guide.", "Официальный пошаговый guide по заявке на Gold Card.", lang=lang),
            _official_source("Taiwan Gold Card: What Is The Gold Card?", "https://goldcard.nat.gov.tw/en/about/", "Official explanation of the 4-in-1 open work permit, residence visa, ARC and re-entry permit.", "Официальное объяснение 4-in-1 карты: work permit, residence visa, ARC и re-entry permit.", lang=lang),
            _official_source("Taiwan Gold Card FAQ", "https://goldcard.nat.gov.tw/en/faq/", "Official FAQ hub for application, family, tax, work and validity questions.", "Официальный FAQ по заявке, семье, налогам, работе и сроку действия.", lang=lang),
            _official_source("Taiwan Gold Card: How To Apply", "https://goldcard.nat.gov.tw/en/faq/how-to-apply/", "Official FAQ for online application and required digital documents.", "Официальный FAQ по онлайн-подаче и цифровым документам.", lang=lang),
            _official_source("Taiwan Gold Card: Application Conditions", "https://goldcard.nat.gov.tw/en/subtags/application-conditions/", "Official FAQ section for application conditions.", "Официальный FAQ-раздел по условиям подачи.", lang=lang),
            _official_source("Taiwan Gold Card: Application Qualification", "https://goldcard.nat.gov.tw/en/subtags/application-qualification/", "Official FAQ section for qualification checks.", "Официальный FAQ-раздел по проверке квалификации.", lang=lang),
            _official_source("Taiwan Gold Card: NHI Eligibility PDF", "https://goldcard.nat.gov.tw/cms-uploads/nhi-eligibility.pdf", "Official PDF for National Health Insurance eligibility of Gold Card holders and dependents.", "Официальный PDF по National Health Insurance для Gold Card holders и dependents.", lang=lang),
        ],
        "philippines": [
            _official_source("Philippine Retirement Authority: SRRVisa", "https://pra.gov.ph/SRRVisa", "Official SRRV page for retirement visa benefits and route logic.", "Официальная страница SRRV с логикой пенсионного маршрута.", lang=lang),
            _official_source("PRA: SRRV Deposit Instructions", "https://pra.gov.ph/Uploads/MediaFile/FileUpload/Updated_-SRRVisa-Deposit-Remittance-Instruction.pdf", "Official deposit remittance instruction for SRRV applicants.", "Официальная инструкция PRA по депозиту для SRRV.", lang=lang),
        ],
        "vietnam": [
            _official_source("Vietnam Immigration: eVisa Portal", "https://evisa.immigration.gov.vn/trang-chu-ttdt", "Official immigration portal for Vietnam eVisa applications.", "Официальный портал иммиграционной службы для Vietnam eVisa.", lang=lang),
            _official_source("Vietnam Tourism: Official eVisa Guide", "https://vietnam.travel/plan-your-trip/official-vietnam-evisa-application", "Official tourism guide summarising the 90-day eVisa route.", "Официальный туристический гид по eVisa на 90 дней.", lang=lang),
            _official_source("Vietnam Immigration: eVisa New Portal Notice", "https://evisa.immigration.gov.vn/web/guest/trang-chu-ttdt", "Official immigration notice for eVisa domains, 90-day validity and entry conditions.", "Официальное уведомление иммиграции по доменам eVisa, сроку до 90 дней и условиям въезда.", lang=lang),
            _official_source("Vietnam Immigration: Foreigner eVisa Application", "https://immigration.gov.vn/en_US/khai-thi-thuc-dien-tu/cap-thi-thuc-dien-tu", "Official application instructions and fee logic for foreign eVisa applicants.", "Официальная инструкция по подаче и сборам для иностранных заявителей eVisa.", lang=lang),
            _official_source("Vietnam Tourism: eVisa Extended To 90 Days", "https://vietnam.travel/things-to-do/big-news-vietnam-approves-extending-e-visas-90-days", "Official tourism update on 90-day multiple-entry eVisas.", "Официальное туристическое обновление по eVisa на 90 дней и multiple entry.", lang=lang),
            _official_source("Vietnam Tourism: eVisa Border Gates Update", "https://vietnam.travel/node/1766", "Official update on eVisa entry and exit border gates.", "Официальное обновление по пунктам въезда и выезда для eVisa.", lang=lang),
            _official_source("Vietnam Immigration: eVisa Country List PDF", "https://immigration.gov.vn/documents/20181/117155/evisa-country-list.pdf/6d522d1e-25ed-410b-b966-27198ae58b49", "Official PDF list of countries allowed for eVisa issuing.", "Официальный PDF со списком стран, которым доступна eVisa.", lang=lang),
            _official_source("Vietnam Immigration: eVisa Port List PDF", "https://evisa.immigration.gov.vn/documents/20181/117155/List-of-evisa-port.pdf/c774e24b-1ab8-4fb6-9ac1-dcdfaccecf8e", "Official PDF list of ports allowed for eVisa entry and exit.", "Официальный PDF со списком портов и пунктов въезда/выезда по eVisa.", lang=lang),
            _official_source("Vietnam Immigration: eVisa Status Search", "https://evisa.immigration.gov.vn/tra-cuu-ho-so", "Official status check page for issued or pending eVisa applications.", "Официальная страница проверки статуса eVisa-заявки.", lang=lang),
        ],
        "india": [
            _official_source("Indian Visa Online: eVisa", "https://indianvisaonline.gov.in/evisa/", "Official eVisa portal for India.", "Официальный портал eVisa для Индии.", lang=lang),
            _official_source("India e-Tourist Visa Fee PDF", "https://indianvisaonline.gov.in/evisa/images/Etourist_fee_final.pdf", "Official fee table showing 30-day, 1-year and 5-year options by country.", "Официальная таблица сборов с вариантами 30 дней, 1 год и 5 лет по странам.", lang=lang),
        ],
        "sri_lanka": [
            _official_source("Sri Lanka ETA Official Website", "https://www.eta.gov.lk/slvisa/visainfo/center.jsp?locale=en_US", "Official ETA page for short-visit entry rules.", "Официальная страница ETA для short visit правил.", lang=lang),
        ],
        "cambodia": [
            _official_source("Cambodia eVisa Official Government Website", "https://www.evisa.gov.kh/", "Official Cambodian government website for eVisa applications.", "Официальный сайт правительства Камбоджи для eVisa.", lang=lang),
        ],
        "indonesia": [
            _official_source("Indonesia eVisa Official Portal", "https://evisa.imigrasi.go.id/", "Official Indonesian immigration portal for visa applications and status checks.", "Официальный портал иммиграционной службы Индонезии для визовых заявок и проверки статуса.", lang=lang),
        ],
        "uae": [
            _official_source("UAE Government: Residence Visa For Working Outside The UAE", "https://u.ae/en/information-and-services/visa-and-emirates-id/residence-visas/residence-visa-for-working-outside-the-uae", "Official UAE government page for the virtual work residence route.", "Официальная страница правительства ОАЭ по virtual work residence.", lang=lang),
            _official_source("UAE ICP Smart Services", "https://icp.gov.ae/en/", "Federal authority portal for UAE identity, citizenship and visa services.", "Федеральный портал ОАЭ по identity, citizenship и визовым сервисам.", lang=lang),
        ],
        "singapore": [
            _official_source("Singapore MOM: Overseas Networks & Expertise Pass", "https://www.mom.gov.sg/passes-and-permits/overseas-networks-expertise-pass", "Official MOM page for Singapore ONE Pass eligibility and pass logic.", "Официальная страница MOM по Singapore ONE Pass и условиям маршрута.", lang=lang),
        ],
        "south-korea": [
            _official_source("Korea Visa Portal", "https://www.visa.go.kr/?LANG_TYPE=EN", "Official Korea visa portal for visa navigation and application checks.", "Официальный визовый портал Кореи для проверки визовых категорий и заявок.", lang=lang),
            _official_source("Korean Embassy: Digital Nomad Workcation Visa", "https://www.mofa.go.kr/us-en/brd/m_4502/view.do?page=1&seq=715884", "Official embassy guidance for the Digital Nomad / Workcation visa route.", "Официальная инструкция посольства по Digital Nomad / Workcation visa.", lang=lang),
        ],
        "hong-kong": [
            _official_source("Hong Kong Talent Engage: Top Talent Pass Scheme", "https://www.hkengage.gov.hk/en/how-to-apply/", "Official Hong Kong Talent Engage entry point for talent admission schemes.", "Официальная точка входа Hong Kong Talent Engage для talent admission routes.", lang=lang),
            _official_source("Hong Kong Immigration Department", "https://www.immd.gov.hk/eng/services/visas/TTPS.html", "Official Immigration Department page for the Top Talent Pass Scheme.", "Официальная страница Immigration Department по Top Talent Pass Scheme.", lang=lang),
        ],
        "qatar": [
            _official_source("Hayya Official Portal", "https://hayya.qa/", "Official Hayya portal for Qatar entry and visitor permit checks.", "Официальный портал Hayya для проверки въезда и visitor permits в Катар.", lang=lang),
            _official_source("Qatar Ministry of Interior", "https://portal.moi.gov.qa/", "Official Qatar MOI portal for immigration and visa services.", "Официальный портал МВД Катара по иммиграционным и визовым сервисам.", lang=lang),
        ],
        "saudi": [
            _official_source("Saudi eVisa Official Portal", "https://visa.visitsaudi.com/", "Official Saudi tourism eVisa portal for application and stay checks.", "Официальный портал Saudi eVisa для проверки подачи и срока пребывания.", lang=lang),
            _official_source("Visit Saudi: Visa Information", "https://www.visitsaudi.com/en/travel-regulations", "Official tourism visa information and travel regulation hub.", "Официальный туристический раздел по визам и правилам поездки.", lang=lang),
        ],
    }
    guide_sources = {
        "can-you-extend-japan-digital-nomad-visa": ["japan"],
        "japan-digital-nomad-visa-income-requirement": ["japan"],
        "thailand-dtv-vs-ltr-visa": ["thailand_dtv", "thailand_ltr"],
        "malaysia-de-rantau-vs-thailand-dtv": ["malaysia", "thailand_dtv"],
        "taiwan-gold-card-income-requirement": ["taiwan"],
        "best-asian-countries-with-easy-long-stay-visas": ["japan", "malaysia", "taiwan", "philippines"],
        "where-to-live-in-asia-on-1500-a-month": ["vietnam", "thailand_dtv", "malaysia", "cambodia"],
        "best-asian-countries-for-remote-workers-with-family": ["japan", "malaysia", "thailand_ltr", "taiwan"],
        "philippines-srrv-vs-thailand-retirement-visa": ["philippines", "thailand_ltr"],
        "vietnam-evisa-vs-thailand-dtv": ["vietnam", "thailand_dtv"],
    }
    if simple_source_keys:
        keys = simple_source_keys
    elif is_visa_hub:
        keys = ["japan", "malaysia", "thailand_dtv", "thailand_ltr", "taiwan", "philippines", "vietnam", "india"]
    elif country_match:
        country_key = country_match.group(1)
        country_source_map = {
            "bali": ["indonesia"],
            "indonesia": ["indonesia"],
            "thailand": ["thailand_dtv", "thailand_ltr"],
            "malaysia": ["malaysia"],
            "japan": ["japan"],
            "taiwan": ["taiwan"],
            "philippines": ["philippines"],
            "vietnam": ["vietnam"],
            "india": ["india"],
            "sri-lanka": ["sri_lanka"],
            "cambodia": ["cambodia"],
            "uae": ["uae"],
            "united-arab-emirates": ["uae"],
            "singapore": ["singapore"],
            "south-korea": ["south-korea"],
        }
        keys = country_source_map.get(country_key, ["world_bank"])
    elif compare_match:
        compare_slug = compare_match.group(1)
        tokens = compare_slug.split("-vs-")
        compare_source_map = {
            "bali": ["indonesia"],
            "indonesia": ["indonesia"],
            "thailand": ["thailand_dtv", "thailand_ltr"],
            "malaysia": ["malaysia"],
            "japan": ["japan"],
            "taiwan": ["taiwan"],
            "philippines": ["philippines"],
            "vietnam": ["vietnam"],
            "india": ["india"],
            "sri-lanka": ["sri_lanka"],
            "cambodia": ["cambodia"],
            "uae": ["uae"],
            "qatar": ["qatar"],
            "singapore": ["singapore"],
            "hong-kong": ["hong-kong"],
            "south-korea": ["south-korea"],
        }
        keys = []
        for token in tokens:
            keys.extend(compare_source_map.get(token, []))
    else:
        keys = guide_sources.get(guide_match.group(1), [])
    panel_sources: list[dict[str, str]] = []
    for key in keys:
        for source in sources.get(key, []):
            if not any(item["url"] == source["url"] for item in panel_sources):
                panel_sources.append(source)
    if not panel_sources:
        return None
    if lang == "ru":
        return {
            "eyebrow": "Официальные проверки",
            "title": "Что сверить в официальных источниках",
            "intro": "Эти ссылки нужны не для красоты. По ним проверяются сроки, продления, доход, разрешённая деятельность, dependants и документы перед тем, как платить за жильё, билеты или услуги.",
            "sources": panel_sources[:10],
            "checks": ["срок stay", "продление", "доход", "страховка", "dependants", "разрешённая работа"],
        }
    return {
        "eyebrow": "Official Checks",
        "title": "Official Sources To Verify Before You Pay",
        "intro": "Use these official pages for stay length, renewal logic, income proof, permitted activity, dependants and document checks before paying for housing, flights or services.",
        "sources": panel_sources[:10],
        "checks": ["stay length", "extension", "income", "insurance", "dependants", "permitted work"],
    }


def blog_trust_panel(*, lang: str) -> dict:
    if lang == "ru":
        return {
            "title": "Как проверяются материалы блога",
            "items": [
                ("Редакция", DEFAULT_AUTHOR),
                ("Последняя проверка", LAST_REVIEWED_RU),
                ("Подход", "официальные источники, ручная редактура и пометка спорных мест"),
            ],
            "methodology_url": "/ru/how-we-verify-data/",
            "methodology_label": "Как мы проверяем данные",
            "contact_url": "/ru/contact/",
            "contact_label": "Сообщить об ошибке",
            "disclaimer": "Блог помогает разобраться в визах, бюджете и выборе страны. Это не юридическая, налоговая, медицинская или финансовая консультация.",
        }
    return {
        "title": "How Blog Articles Are Checked",
        "items": [
            ("Editorial team", DEFAULT_AUTHOR),
            ("Last checked", LAST_REVIEWED_EN),
            ("Method", "official sources, manual editing and clear limits where rules are uncertain"),
        ],
        "methodology_url": "/how-we-verify-data/",
        "methodology_label": "How We Verify Data",
        "contact_url": "/contact/",
        "contact_label": "Report outdated information",
        "disclaimer": "The blog supports relocation planning. It is not legal, tax, medical or financial advice.",
    }


def blog_depth_panel(*, lang: str) -> dict:
    if lang == "ru":
        return {
            "title": "Как читать блог, если вы реально планируете переезд",
            "intro": "Визовые и денежные темы быстро становятся опасными, если читать их как обычные travel-заметки. Здесь лучше идти скучным путём: сначала официальный маршрут, потом бюджет, потом город и бытовые детали.",
            "sections": [
                ("Сначала проверяйте правило", "Если статья говорит о визе, сроке, доходе, страховке или продлении, ищите рядом официальный источник. Если источник не подтверждает исключение, не закладывайте его в план. Это особенно важно для digital nomad visa, retirement visa и long-stay маршрутов."),
                ("Отделяйте факт от вывода", "Факт — это то, что написано в правилах или подтверждается данными. Вывод — что это значит для человека: подходит ли маршрут семье, удалённому специалисту, пенсионеру или человеку с ограниченным бюджетом. Эти вещи нельзя смешивать."),
                ("Не принимайте решение по одной статье", "Хорошая статья сокращает шум, но не заменяет проверку. Перед депозитом за жильё, оплатой агента или покупкой билетов сравните страну с альтернативой, откройте страницу визы и проверьте дату обновления официального сайта."),
            ],
            "faq": [
                ("Можно ли использовать блог как юридическую консультацию?", "Нет. Материалы помогают принять более трезвое решение, но финальную проверку нужно делать по официальному источнику или с профильным специалистом."),
                ("Почему в статьях иногда осторожные формулировки?", "Потому что визовые правила меняются. Если продление, исключение или льгота не подтверждены официально, безопаснее не писать это как обещание."),
            ],
        }
    return {
        "title": "How To Use The Blog For Real Relocation Decisions",
        "intro": "Visa and money topics can become risky when they read like travel inspiration. The safer order is less glamorous: official route first, budget second, city and lifestyle after that.",
        "sections": [
            ("Check The Rule First", "When an article discusses a visa, stay length, income proof, insurance or extension, look for the official source. If the official source does not confirm an exception, do not build your plan around it."),
            ("Separate Fact From Meaning", "A fact is what the rule or dataset says. The meaning is the practical consequence for a remote worker, retiree, family or budget-limited mover. Mixing those two creates bad relocation decisions."),
            ("Do Not Decide From One Page", "A strong article reduces noise, but it does not replace verification. Before paying for housing, agents or flights, compare one alternative country and check the official visa page again."),
        ],
        "faq": [
            ("Is This Blog Legal Advice?", "No. It is editorial relocation guidance based on public sources. Verify the official authority before applying or paying for services."),
            ("Why Are Some Articles Cautious?", "Because visa rules change. If an extension, exception or benefit is not officially confirmed, it should not be treated as a promise."),
        ],
    }


RU_ARTICLE_EXPANSIONS = {
    "yaponiya-digital-nomad-visa-2026": {
        "keyword": "Japan Digital Nomad Visa",
        "title": "Japan Digital Nomad Visa: где заканчивается мечта и начинаются правила",
        "lead": "Япония легко продаёт себя сама: безопасность, транспорт, города, еда, культура. Но Japan Digital Nomad Visa не становится от этого мягче. Это короткий и довольно узкий маршрут для удалённой работы из страны, а не тихий вход в долгую резиденцию.",
        "rule": "В официальной логике ключевой пункт простой: пребывание ограничено шестью месяцами, а продление не заявлено как рабочая опция. Значит, этот маршрут нельзя честно планировать как год жизни в Японии через одно разрешение. Если нужен длинный горизонт, лучше сразу сравнивать другие страны или другие японские основания.",
        "practice": "На практике это хорошо работает для человека, который хочет провести в Японии один понятный отрезок: поработать удалённо, проверить бытовую реальность, пожить в Токио, Осаке, Фукуоке или другом городе без обещаний самому себе про “потом разберусь”. Чем яснее дата выезда, тем меньше риск.",
        "fit": "Japan Digital Nomad Visa подходит тем, у кого доход идёт из-за рубежа, документы можно подтвердить без натяжек, а сама поездка укладывается в шесть месяцев. Особенно хорошо, если это тест страны, а не попытка спрятать полноценный переезд под временную визу.",
        "bad": "Не подходит тем, кто ищет путь к резиденции, хочет работать на японского работодателя, планирует школу для детей на долгий срок или рассчитывает продлить пребывание по ходу дела. Тут как раз опасно путать симпатию к стране с подходящим правовым маршрутом.",
        "risk": "Самая частая ошибка — начинать с города и аренды. В Японии это особенно соблазнительно. Но сначала нужно проверить срок, разрешённую деятельность, страховку, семейные условия и документы по доходу. Только потом имеет смысл смотреть районы, квартиры и сезонность цен.",
        "check": "Перед оплатой жилья стоит ещё раз открыть официальный источник, проверить формулировку про срок, отсутствие продления и требования к удалённой работе. Если в правилах нет прямого подтверждения нужной вам возможности, её лучше не закладывать в план.",
    },
    "taiwan-gold-card-2026": {
        "keyword": "Taiwan Gold Card",
        "title": "Taiwan Gold Card: сильный маршрут, но не универсальная кнопка для переезда",
        "lead": "Taiwan Gold Card выглядит куда серьёзнее обычной digital nomad визы. И в этом её сила. Но сила маршрута не отменяет отбора: карта рассчитана на конкретные профессиональные профили, а не на всех, кто хочет пожить в Тайбэе.",
        "rule": "Официальная идея Taiwan Gold Card в том, что один документ объединяет несколько функций: visa, work permit и residence permit. Срок может быть 1, 2 или 3 года. Это уже не короткая поездка, а более взрослый вариант для людей, которые проходят по профессии, доходу или квалификации.",
        "practice": "На практике главное — не сам Тайвань, а ваша категория. Если профиль подтверждается документами, Gold Card даёт гибкость: можно жить, работать и строить более длинный план. Если профиль слабый или доход не подтверждается чисто, красивое название карты мало помогает.",
        "fit": "Taiwan Gold Card подходит специалистам с понятным профессиональным треком: tech, business, finance, culture, science и другие категории, которые можно доказать бумагами. Хорошо подходит тем, кому нужен не отпуск, а база на несколько лет с нормальной правовой логикой.",
        "bad": "Не подходит тем, кто хочет просто дешёвую страну, не имеет подтверждаемой квалификации или рассчитывает пройти по общим словам вроде “remote worker”. В этом маршруте важны документы, а не настроение. Без них лучше смотреть более простые визовые варианты.",
        "risk": "Ошибка здесь обычно другая: люди видят 1-3 года и забывают про критерии. Но срок — только результат одобрения, а не автоматическое право. Сначала категория и доказательства, потом уже разговор о районах Тайбэя, школах, аренде и бюджете.",
        "check": "Перед подачей стоит проверить свою категорию на официальном портале, собрать подтверждения дохода или квалификации и трезво оценить, насколько документы читаются для ведомства. Если приходится объяснять слишком много, заявка может оказаться слабее, чем кажется.",
    },
    "indonesia-e33g-remote-worker-visa-2026": {
        "keyword": "Indonesia E33G Remote Worker Visa",
        "title": "Indonesia E33G Remote Worker Visa: Бали не должен быть первым аргументом",
        "lead": "Индонезия часто начинается с картинки: Бали, океан, кафе, мотоцикл. Но Indonesia E33G Remote Worker Visa устроена не вокруг картинки, а вокруг происхождения дохода и связи с иностранным работодателем.",
        "rule": "Смысл E33G в том, что человек работает удалённо на иностранного работодателя или клиентов за пределами Индонезии. Это важная граница. Виза не должна превращаться в способ работать на местном рынке, брать локальные проекты или обходить обычные рабочие разрешения.",
        "practice": "На практике этот маршрут удобен тем, у кого уже есть стабильная удалённая работа и понятные документы: контракт, доход, банковские подтверждения, страховка, адрес проживания. Если работа фрилансерская и хаотичная, нужно заранее понять, как именно её можно показать без серых зон.",
        "fit": "Indonesia E33G Remote Worker Visa подходит тем, кто хочет жить в Индонезии, но зарабатывать вне страны. Хорошо, если есть один понятный работодатель, регулярные выплаты и готовность соблюдать местные ограничения, а не искать подработки на месте.",
        "bad": "Не подходит тем, кто едет “посмотрим, найду клиентов на Бали”, хочет работать в местной компании или рассчитывает, что туристическая логика заменит визовую. Для таких сценариев риск слишком высокий, даже если бытовая сторона выглядит простой.",
        "risk": "Главная ошибка — считать Бали отдельной реальностью, где правила мягче. На деле визовый вопрос остаётся индонезийским. Аренда виллы, комьюнити и coworking не подтверждают право на пребывание. Его подтверждают документы и соответствие условиям.",
        "check": "До бронирования жилья проверьте официальные требования к E33G, список документов и формулировки по источнику дохода. Если доход зависит от индонезийских клиентов, лучше не притворяться, что это remote work из-за рубежа.",
    },
    "malaysia-dlya-digital-nomads-2026": {
        "keyword": "Malaysia DE Rantau",
        "title": "Malaysia DE Rantau: удобная база, если профиль действительно совпадает",
        "lead": "Малайзия часто кажется спокойным выбором: английский, Куала-Лумпур, Пенанг, нормальная инфраструктура, перелёты по региону. Но Malaysia DE Rantau всё равно начинается не с города, а с того, проходите ли вы по условиям программы.",
        "rule": "DE Rantau рассчитан на digital professionals и remote workers, которые могут подтвердить работу, доход и профиль. Это не просто “виза для тех, кто с ноутбуком”. Важны документы: чем понятнее контракт, деятельность и платежи, тем меньше вопросов к маршруту.",
        "practice": "На практике Малайзия сильна именно как рабочая база. Здесь легче жить без постоянного языкового напряжения, проще решать бытовые вопросы и удобнее летать по Азии. Но если доход нестабилен или документы собраны небрежно, бытовой комфорт не спасает заявку.",
        "fit": "Malaysia DE Rantau подходит удалённым специалистам, которым нужна городская база с нормальным интернетом, аэропортами и более мягкой стоимостью жизни, чем в Сингапуре или Гонконге. Особенно хорошо, если работа уже стабильна и не требует местного трудоустройства.",
        "bad": "Не подходит тем, кто хочет переехать без подтверждаемого дохода, искать работу уже после въезда или использовать программу как общий long-stay без связи с цифровой профессией. Тут лучше заранее выбрать маршрут честно, чем потом переделывать план.",
        "risk": "Частая ошибка — сравнивать Малайзию только по ценам. Но DE Rantau не решает всё: остаются медицина, страховка, район, налоги, школьные вопросы, визы для семьи и реальная стоимость жизни в выбранном городе.",
        "check": "Перед подачей проверьте официальный сайт программы, требования к доходу, список профессий и документы по работе. Потом уже считайте город: Куала-Лумпур, Пенанг и Джохор дают очень разный бюджет и разный ритм жизни.",
    },
    "tailand-ltr-dlya-udalennyh-specialistov-2026": {
        "keyword": "Thailand LTR Work-From-Thailand",
        "title": "Thailand LTR Work-From-Thailand: не путайте сильную визу с простой визой",
        "lead": "Thailand LTR Work-From-Thailand выглядит привлекательно именно потому, что обещает длинный горизонт. Но это не облегчённая версия туристического пребывания. Это отборочная программа с серьёзными требованиями к работодателю, доходу и профилю.",
        "rule": "В LTR важны категории заявителя. Для удалённых специалистов проверяются не только личный доход, но и связь с подходящей компанией, опыт, документы и соответствие программе. Значит, вопрос не в том, нравится ли Таиланд, а в том, проходит ли ваша профессиональная ситуация.",
        "practice": "На практике LTR имеет смысл для людей с устойчивой карьерой и сильной документальной базой. Если всё подтверждается, Таиланд становится не просто зимовкой, а более долгой базой. Если документы спорные, лучше сразу сравнить DTV или другие маршруты.",
        "fit": "Thailand LTR Work-From-Thailand подходит специалистам с хорошим доходом, международным работодателем и понятной историей работы. Особенно тем, кому нужен срок, а не серия коротких въездов и постоянное визовое напряжение.",
        "bad": "Не подходит тем, кто работает нестабильно, только начинает фриланс, не может показать работодателя или рассчитывает пройти за счёт общей привлекательности страны. У LTR другая логика: меньше романтики, больше проверки.",
        "risk": "Главная ошибка — ставить LTR в один ряд с лёгкими digital nomad маршрутами. Это разные уровни. Если человек не проходит по критериям, попытка “дотянуть” документы часто заканчивается потерей времени и денег.",
        "check": "Перед расчётом бюджета проверьте категорию LTR, требования к работодателю, доходу и опыту. Если хотя бы один базовый пункт не закрыт, сначала ищите альтернативу, а уже потом выбирайте город в Таиланде.",
    },
    "philippines-srrv-retirement-visa-2026": {
        "keyword": "Philippines SRRV",
        "title": "Philippines SRRV: пенсионный маршрут, где депозит важнее красивых обещаний",
        "lead": "Philippines SRRV часто звучит почти слишком удобно: retirement visa, multiple entry, indefinite stay. Но это не значит, что маршрут подходит каждому пенсионеру. Здесь всё упирается в возраст, депозит, медицинскую страховку, документы и личную готовность жить именно на Филиппинах.",
        "rule": "Официальная логика SRRV строится вокруг пенсионного статуса и финансового депозита. У разных категорий могут быть разные условия, поэтому нельзя читать только одну короткую фразу про indefinite stay. Нужно смотреть конкретный тип SRRV и актуальные требования.",
        "practice": "На практике SRRV может быть сильным решением для тех, кто хочет долгий горизонт без постоянных выездов. Но депозит — это не декоративная цифра. Деньги оказываются частью визового решения, а не просто расходом на оформление.",
        "fit": "Philippines SRRV подходит пенсионерам, которым важны английский язык, мягкий климат, long-stay логика и более понятное пребывание, чем по туристическим продлениям. Хорошо, если человек уже понимает страну и не выбирает её только по рекламе.",
        "bad": "Не подходит тем, кто не готов к депозиту, хочет европейский уровень городской инфраструктуры везде или имеет медицинские потребности, которые проще закрывать в другой стране. Также не стоит идти в SRRV, если вы ещё не уверены, что Филиппины подходят бытово.",
        "risk": "Ошибка — смотреть только на слово indefinite. Долгий срок не отменяет расходы, страховку, медицину, перелёты, банковские вопросы и выбор острова. Манила, Себу, Давао и маленький остров — это разные жизни.",
        "check": "Перед решением проверьте официальный сайт PRA, категорию SRRV, сумму депозита, возрастные условия и требования к документам. Если цифра депозита вызывает напряжение уже на старте, лучше сравнить Таиланд, Малайзию и другие retirement routes.",
    },
    "yuzhnaya-koreya-workation-visa-2026": {
        "keyword": "South Korea Workation Visa",
        "title": "South Korea Workation Visa: красивая страна, но жёсткая логика удалённой работы",
        "lead": "Южная Корея кажется сильным вариантом для тех, кто хочет инфраструктуру, безопасность и городскую энергию. Но South Korea Workation Visa не про поиск работы в Сеуле. Она про временное пребывание с удалённым доходом из-за рубежа.",
        "rule": "Маршрут F-1-D связан с workation и удалённой работой. Важны доход, страховка, зарубежная занятость и запрет на местную работу. Это ключевая граница: находиться в Корее можно по одному основанию, но зарабатывать на местном рынке по нему нельзя.",
        "practice": "На практике Корея подходит тем, у кого уже есть стабильная работа и хороший запас бюджета. Страна не самая дешёвая, а комфорт быстро зависит от района, жилья, страховки и знания бытовых правил. Виза решает въезд, но не делает жизнь автоматически простой.",
        "fit": "South Korea Workation Visa подходит удалённым специалистам, которые хотят пожить в Корее ограниченный период, не устраиваясь в местную компанию. Хорошо, если есть регулярный доход, понятный работодатель и готовность соблюдать ограничения.",
        "bad": "Не подходит тем, кто едет искать корейскую работу, строит план вокруг подработок или не проходит по доходу. Если цель — местная карьера, нужны другие основания, а не попытка растянуть workation под employment.",
        "risk": "Частая ошибка — путать культурный интерес с визовой пригодностью. Любить Корею можно сколько угодно, но заявка всё равно проверяется по документам. Ещё одна ошибка — недооценить стоимость жилья и повседневных расходов в Сеуле.",
        "check": "Перед подачей проверьте официальные требования к F-1-D, доходу, страховке и разрешённой деятельности. Потом считайте бюджет не по среднему чек-листу, а по конкретному городу и району.",
    },
    "singapore-one-pass-2026": {
        "keyword": "Singapore ONE Pass",
        "title": "Singapore ONE Pass: маршрут для top talent, а не обычная виза для переезда",
        "lead": "Сингапур часто хочется рассматривать как идеальную базу: бизнес, аэропорт, безопасность, школы, медицина. Но Singapore ONE Pass — это не универсальный long-stay для всех. Он создан для людей с очень сильным профессиональным и доходным профилем.",
        "rule": "ONE Pass заявлен как 5-летний pass для top talent. В этой логике важны высокий доход, достижения или положение в своей сфере. Это не категория, где можно компенсировать слабые документы хорошей мотивацией.",
        "practice": "На практике Singapore ONE Pass стоит рассматривать только после честной проверки профиля. Если вы проходите, Сингапур даёт редкую гибкость и статус. Если нет, лучше не тратить силы на маршрут, который изначально не совпадает с реальностью.",
        "fit": "Singapore ONE Pass подходит руководителям, предпринимателям, специалистам высокого уровня и людям с подтверждаемыми достижениями. Особенно тем, кому нужна не дешёвая база, а деловая юрисдикция с высокой плотностью возможностей.",
        "bad": "Не подходит обычным digital nomads, начинающим фрилансерам и тем, кто ищет бюджетный переезд. Сингапур дорогой, а ONE Pass отбирает по верхнему сегменту. Это надо принять до расчёта аренды.",
        "risk": "Главная ошибка — сравнивать ONE Pass с визами для удалённой работы в Юго-Восточной Азии. Это другой класс. Здесь важна не только страна, но и уровень заявителя, подтверждения, доход и репутация.",
        "check": "Перед любыми планами проверьте официальные критерии MOM, доходные требования и условия для dependants. Если профиль не проходит по базовым признакам, лучше смотреть Employment Pass или другие страны.",
    },
    "hong-kong-top-talent-pass-2026": {
        "keyword": "Hong Kong Top Talent Pass",
        "title": "Hong Kong Top Talent Pass: хороший вариант, если вы действительно top talent",
        "lead": "Hong Kong Top Talent Pass звучит широко, но на практике это отбор по доходу, университету или профессиональному уровню. Гонконг может быть мощной базой, но дешёвым и простым переездом его назвать сложно.",
        "rule": "Маршрут TTPS строится вокруг категорий top talent. Официальные условия завязаны на доход, образование и другие критерии. Поэтому важно сначала понять, к какой категории вы относитесь, а не начинать с поиска квартиры на острове Гонконг.",
        "practice": "На практике TTPS интересен людям, которым нужна деловая среда, Азия, английский и доступ к рынкам. Но Гонконг дорогой. Если доход на границе требований, бытовой бюджет может быстро съесть преимущество статуса.",
        "fit": "Hong Kong Top Talent Pass подходит специалистам с сильным CV, высоким доходом или дипломом из подходящего списка. Хорошо работает для тех, кто понимает, зачем ему именно Гонконг, а не просто хочет “Азию с английским”.",
        "bad": "Не подходит тем, кто ищет спокойный бюджетный long-stay, работает нестабильно или не проходит по категории. В этом случае лучше сравнивать Малайзию, Тайвань или Таиланд, где бытовой порог может быть мягче.",
        "risk": "Ошибка — считать одобрение главным финишем. После него начинается реальность: аренда, медицина, налоги, школа, плотность города и высокая конкуренция. Для семьи эти вопросы особенно важны.",
        "check": "Перед подачей проверьте официальные категории TTPS, требования по доходу или университету и срок действия stay. Потом считайте бюджет по реальному району, а не по средним цифрам из обзоров.",
    },
    "uae-virtual-work-visa-2026": {
        "keyword": "UAE Virtual Work Residence",
        "title": "UAE Virtual Work Residence: год в ОАЭ без местной работы",
        "lead": "ОАЭ удобны для тех, кому важны перелёты, безопасность, сервис и налоговая предсказуемость. Но UAE Virtual Work Residence не превращает удалённого специалиста в местного работника. Это self-sponsored маршрут с чёткой границей по источнику дохода.",
        "rule": "Логика визы строится вокруг удалённой работы на компанию или клиентов за пределами ОАЭ. Обычно такой маршрут рассматривают как годовое пребывание при подтверждении дохода, занятости и страховки. Местная работа требует других оснований.",
        "practice": "На практике ОАЭ подходят тем, кто уже зарабатывает достаточно и хочет жить в Дубае, Абу-Даби или другом эмирате без поиска местного работодателя. Но стоимость жилья, страховка и повседневные расходы быстро отделяют реальный план от красивой картинки.",
        "fit": "UAE Virtual Work Residence подходит удалённым специалистам и предпринимателям с подтверждаемым доходом из-за рубежа. Особенно тем, кому нужен деловой хаб, аэропорт, банковская инфраструктура и понятный срок.",
        "bad": "Не подходит тем, кто рассчитывает найти работу на месте после въезда, едет без финансового запаса или выбирает ОАЭ только из-за налоговой темы. Если доход нестабилен, дорогая среда быстро станет проблемой.",
        "risk": "Частая ошибка — считать, что годовая виза сама по себе делает страну доступной. В ОАЭ главный фильтр часто не срок, а бюджет. Аренда, депозиты, транспорт и страховка могут быть выше ожиданий.",
        "check": "Перед подачей проверьте официальный список документов, требования к доходу, страховке и работе за пределами ОАЭ. Потом считайте первый месяц отдельно: депозит, жильё, транспорт и подключение сервисов.",
    },
    "saudi-arabia-evisa-2026": {
        "keyword": "Saudi Arabia eVisa",
        "title": "Saudi Arabia eVisa: годовая виза не означает год непрерывного проживания",
        "lead": "Saudi Arabia eVisa легко неправильно прочитать. Формулировка про один год и multiple entry звучит щедро. Но для планирования важнее другое: сколько дней можно находиться в стране за один визит и какие цели поездки разрешены.",
        "rule": "Визовая логика Saudi Arabia eVisa связана с туристическим въездом и короткими stay periods. Один год validity не равен одному году проживания. Если правило говорит про ограничение дней пребывания, именно это ограничение и управляет планом.",
        "practice": "На практике eVisa удобна для поездок, разведки страны, деловых встреч в рамках разрешённой цели или короткого проживания. Но её нельзя превращать в long-stay маршрут для релокации, если официальные условия этого не поддерживают.",
        "fit": "Saudi Arabia eVisa подходит тем, кто хочет посетить страну, оценить города, посмотреть инфраструктуру и провести ограниченное время без сложной резидентской логики. Хорошо, если поездка имеет ясную дату въезда и выезда.",
        "bad": "Не подходит тем, кто хочет переехать, работать на месте или жить в Саудовской Аравии непрерывно. Для таких целей нужны другие основания, и туристическая eVisa не должна маскировать долгосрочный план.",
        "risk": "Главная ошибка — смотреть на validity, а не на duration of stay. Это разные вещи. Validity отвечает, когда можно использовать визу, а duration of stay — сколько можно находиться в стране.",
        "check": "Перед покупкой билетов проверьте официальные условия eVisa, допустимые цели поездки, лимит дней и требования к страховке. Если план длиннее разрешённого stay, его нужно перестроить заранее.",
    },
    "vietnam-evisa-2026": {
        "keyword": "Vietnam eVisa",
        "title": "Vietnam eVisa: 90 дней дают гибкость, но не заменяют резиденцию",
        "lead": "Vietnam eVisa стала намного удобнее для тех, кто хочет пожить в стране, проверить Хошимин, Дананг, Ханой или Нячанг. Но 90 дней — это всё ещё визовый коридор, а не полноценный переезд.",
        "rule": "Ключевой факт по Vietnam eVisa — возможность въезда на срок до 90 дней с single или multiple entry, если заявка соответствует условиям. Это удобно для теста страны и региональных поездок, но не равно праву на местную работу.",
        "practice": "На практике Вьетнам хорош для людей, которые хотят недорогую базу на ограниченный срок и готовы заранее следить за датами. Multiple entry может помочь с поездками по региону, но не отменяет необходимость соблюдать срок пребывания.",
        "fit": "Vietnam eVisa подходит digital nomads и экспатам на разведке, если доход идёт из-за рубежа, план ограничен несколькими месяцами, а бюджет чувствителен к аренде и еде. Это сильный вариант для теста, не для вечного решения.",
        "bad": "Не подходит тем, кто хочет работать на местном рынке, жить без визового планирования или переехать с семьёй без понятного long-stay основания. Для таких задач 90 дней быстро становятся слишком короткими.",
        "risk": "Ошибка — недооценить календарь. Когда жильё оплачено на несколько месяцев, легко забыть, что визовый срок управляет всей логистикой. Билеты, страховка и депозит должны совпадать с датами.",
        "check": "Перед поездкой проверьте официальный eVisa portal, тип въезда, срок, паспортные данные и дату окончания. Ошибка в заявке может стоить больше, чем кажется, особенно если план завязан на аренду.",
    },
    "cambodia-evisa-visa-e-2026": {
        "keyword": "Cambodia eVisa",
        "title": "Cambodia eVisa: простой въезд, но не вся визовая логика Камбоджи",
        "lead": "Камбоджа часто выглядит простой: оформить онлайн, прилететь, пожить дешевле, чем в соседних странах. Но Cambodia eVisa нужно читать аккуратно. eVisa и более длинные визовые сценарии — не одно и то же.",
        "rule": "Официальный eVisa сайт подтверждает электронный формат въезда для конкретных целей и сроков. Это удобно, но сама eVisa не должна автоматически восприниматься как long-stay route. Для более долгого пребывания нужно смотреть отдельные визовые основания и правила продления.",
        "practice": "На практике Cambodia eVisa хороша для короткой поездки, проверки Пномпеня, Сиемреапа или побережья. Если план — жить дольше, работать удалённо и строить быт, нужно заранее понять, какой статус будет после первого въезда.",
        "fit": "Cambodia eVisa подходит тем, кто едет на разведку, хочет коротко оценить страну и не строит сложный переезд на одном электронном разрешении. Хорошо, если есть запасной план выезда.",
        "bad": "Не подходит тем, кто хочет сразу арендовать жильё надолго, не разобравшись с визовой цепочкой. Простота первого въезда может создать ложное ощущение, что всё остальное тоже решится само.",
        "risk": "Ошибка — смешивать eVisa, visa on arrival, ordinary visa и продления в одну общую историю. Для SEO это выглядит удобно, но для человека опасно: разные типы въезда дают разные последствия.",
        "check": "Перед оплатой жилья проверьте официальный eVisa сайт, пункты въезда, срок действия, цель поездки и дальнейшую визовую стратегию. Если нужен long-stay, проверяйте не только первый въезд.",
    },
    "sri-lanka-eta-2026": {
        "keyword": "Sri Lanka ETA",
        "title": "Sri Lanka ETA: хороший short visit, но продление нужно проверять отдельно",
        "lead": "Шри-Ланка притягивает мягким климатом, океаном и более спокойным ритмом. Но Sri Lanka ETA — это прежде всего разрешение для short visit. Если план длиннее обычной поездки, детали становятся важнее пляжа.",
        "rule": "ETA обычно связан с коротким въездом, часто вокруг 30 дней, а дальнейшие возможности зависят от актуальных правил продления. Нельзя автоматически считать, что разрешение легко растянется на любой срок.",
        "practice": "На практике ETA подходит для разведки страны: Коломбо, Галле, южное побережье, Канди или другие места. Для удалённой работы на несколько месяцев нужно заранее проверить не только въезд, но и легальность более длинного пребывания.",
        "fit": "Sri Lanka ETA подходит тем, кто хочет коротко пожить, посмотреть районы и понять, выдерживает ли страна бытовые ожидания. Хорошо, если сроки гибкие и нет сложной семейной логистики.",
        "bad": "Не подходит тем, кто планирует долгую релокацию без проверки продления, медицинских вопросов и стабильности интернета в конкретном месте. Шри-Ланка может быть приятной, но это не отменяет визовой дисциплины.",
        "risk": "Ошибка — принимать красивую digital nomad картинку за визовый план. На островах и побережье бытовые условия могут сильно отличаться от ожиданий: связь, транспорт, медицина и сезонность влияют на реальную жизнь.",
        "check": "Перед поездкой проверьте официальный ETA сайт, срок, цель въезда, правила продления и требования к паспорту. Для длинного проживания считайте не только аренду, но и запас на выезд или смену статуса.",
    },
    "india-e-tourist-visa-2026": {
        "keyword": "India e-Tourist Visa",
        "title": "India e-Tourist Visa: 30 дней, 1 год и 5 лет — это разные планы",
        "lead": "Индия не про один универсальный сценарий. India e-Tourist Visa может быть на 30 дней, 1 год или 5 лет, но эти варианты нельзя читать как одинаковые. Validity, entries и duration of stay решают больше, чем название.",
        "rule": "Официальная логика e-Tourist Visa разделяет срок действия визы и разрешённое пребывание. Долгая validity не всегда означает возможность жить в Индии непрерывно. Это нужно проверять по конкретному типу визы и гражданству.",
        "practice": "На практике Индия подходит тем, кто умеет планировать маршрут по датам и не путает туристический въезд с релокацией. Для Гоа, Дели, Бангалора, Кералы или Ришикеша будут разные бюджеты и разные бытовые риски.",
        "fit": "India e-Tourist Visa подходит для поездок, разведки городов, отдыха и ограниченного пребывания. Хорошо, если вы точно знаете, какой тип визы оформляете и сколько дней реально можно находиться в стране.",
        "bad": "Не подходит тем, кто хочет работать на индийском рынке, жить без ограничения по сроку или строить долгий переезд на туристическом основании. Для таких целей нужна другая правовая база.",
        "risk": "Главная ошибка — смотреть на 1 year или 5 years и забывать про лимит пребывания. Это разные параметры. Ещё одна ошибка — выбирать город по романтическому образу, не считая медицину, транспорт и сезон.",
        "check": "Перед подачей откройте официальный Indian Visa Online, проверьте тип e-Tourist Visa, allowed stay, entries и условия для вашего паспорта. Потом уже планируйте билеты и жильё.",
    },
    "qatar-hayya-tourist-visa-2026": {
        "keyword": "Qatar Hayya",
        "title": "Qatar Hayya: быстрый въезд не равен релокационному маршруту",
        "lead": "Катар удобен как транзитный и деловой хаб, но Qatar Hayya и visa-free логика не должны превращаться в план переезда. Это хороший пример, где лёгкость въезда может сбить с толку.",
        "rule": "Hayya и безвизовые варианты зависят от гражданства, цели поездки, срока и актуальных правил. Важно проверять не только возможность въезда, но и то, что именно разрешено делать в стране.",
        "practice": "На практике Катар подходит для коротких поездок, разведки, мероприятий и ограниченного пребывания. Если человек думает о жизни в Дохе, главными становятся работа, резиденция, бюджет, медицина и жильё, а не только въезд.",
        "fit": "Qatar Hayya подходит тем, кто едет на понятный короткий срок и хочет минимизировать бумажную часть въезда. Хорошо, если есть обратный билет, ясная цель поездки и запас по бюджету.",
        "bad": "Не подходит тем, кто ищет дешёвую long-stay базу или рассчитывает решить вопрос работы уже на месте. Катар дорогой, а туристический въезд не заменяет рабочую или резидентскую логику.",
        "risk": "Ошибка — считать, что если въезд простой, то переезд тоже простой. В странах Персидского залива это особенно неверно: право жить и право работать обычно требуют отдельного основания.",
        "check": "Перед поездкой проверьте официальный Hayya portal или government source, условия для вашего паспорта, срок пребывания и допустимые цели. Если нужен переезд, ищите резидентский маршрут отдельно.",
    },
    "prostye-vizy-v-azii-dlya-ekspatov-2026": {
        "keyword": "Easy Long-Stay Visas In Asia",
        "title": "Easy Long-Stay Visas In Asia: простая виза не всегда лучший выбор",
        "lead": "Когда люди ищут простую визу в Азии, они часто хотят не простоту, а меньше риска. Это разные вещи. Easy Long-Stay Visas In Asia нужно сравнивать не по названию, а по сроку, продлению, документам и реальной пригодности для жизни.",
        "rule": "У каждой страны своя логика: где-то сильнее срок, где-то проще продление, где-то выше требования к доходу, где-то маршрут подходит только пенсионерам или специалистам. Нельзя переносить вывод из Малайзии на Таиланд или Тайвань.",
        "practice": "На практике хороший shortlist начинается с фильтра: сколько вы хотите жить, как зарабатываете, едете один или с семьёй, нужен ли местный работодатель, сколько денег готовы заморозить или показать. После этого список стран обычно резко сокращается.",
        "fit": "Easy Long-Stay Visas In Asia подходят тем, кто готов выбирать страну через правила, а не через эмоцию. Это особенно полезно remote workers, пенсионерам и семьям, которым ошибка со сроком или продлением стоит дорого.",
        "bad": "Не подходит подход “выберу страну, а визу потом найду”. В Азии это быстро ломается: где-то нельзя продлить, где-то нужен доход, где-то нет пути для семьи, где-то комфортная жизнь дороже ожидаемой.",
        "risk": "Главная ошибка — искать самую лёгкую визу без вопроса “лёгкую для кого?”. Для одного человека SRRV логична, для другого лучше DE Rantau, для третьего — Taiwan Gold Card, а кому-то вообще стоит начать с короткой eVisa.",
        "check": "Перед решением сравните минимум три страны по одному шаблону: срок, продление, доход, семья, работа, страховка, стоимость первого месяца и официальный источник. Только после этого выбирайте город.",
    },
    "luchshie-strany-azii-dlya-ekspatov-2026": {
        "keyword": "Лучшие страны Азии для экспатов",
        "title": "Лучшие страны Азии для экспатов: рейтинг полезен только после личных фильтров",
        "lead": "Лучшие страны Азии для экспатов не существуют в вакууме. Для удалённого специалиста, пенсионера, семьи с детьми и человека с маленьким бюджетом список будет разным. Поэтому рейтинг без фильтров может больше мешать, чем помогать.",
        "rule": "Сравнивать страны нужно по проверяемым параметрам: визовый срок, стоимость жизни, медицина, безопасность, интернет, язык, налоги, школа, перелёты и риск изменения правил. Ощущения важны, но они идут после базовых условий.",
        "practice": "На практике Таиланд может выигрывать по образу жизни, Малайзия — по бытовой простоте, Тайвань — по статусу и инфраструктуре, Вьетнам — по цене, Филиппины — по английскому и retirement routes. Но каждый плюс имеет обратную сторону.",
        "fit": "Рейтинг лучших стран Азии для экспатов полезен как стартовая карта, если вы ещё не выбрали направление. Сначала уберите страны, где не проходит виза или бюджет. Потом сравнивайте города, климат и личный комфорт.",
        "bad": "Не подходит идея выбрать страну по одному сильному плюсу. Дешёвая аренда не спасает слабый визовый маршрут. Хорошая медицина не компенсирует неподходящий бюджет. Любимый город не решает проблему документов.",
        "risk": "Частая ошибка — читать списки как финальный ответ. На деле это только первый слой. Реальный выбор появляется, когда страна сталкивается с вашим доходом, семьёй, здоровьем, сроком и терпимостью к бюрократии.",
        "check": "Перед финальным shortlist возьмите две страны-фаворита и одну запасную. Проверьте официальные визовые страницы, посчитайте первый месяц, сравните медицину и выпишите, что может сорвать план.",
    },
}


def article_expansion_panel(row: sqlite3.Row | dict, *, lang: str) -> dict | None:
    if lang != "ru":
        return None
    spec = RU_ARTICLE_EXPANSIONS.get(str(row["slug"]))
    if not spec:
        return None
    keyword = spec["keyword"]
    return {
        "title": spec["title"],
        "lead": spec["lead"],
        "sections": [
            (f"Что написано в правилах по {keyword}", spec["rule"]),
            ("Что это значит на практике", spec["practice"]),
            (f"Кому подходит {keyword}", spec["fit"]),
            (f"Кому не подходит {keyword}", spec["bad"]),
            ("Где чаще ошибаются", spec["risk"]),
            ("Что проверить перед оплатой", spec["check"]),
            (f"Как связать {keyword} с бюджетом", f"Визовый маршрут нельзя считать отдельно от денег. Даже если {keyword} формально подходит, проверьте первый месяц: депозит за жильё, перелёт, страховку, местный транспорт, связь, coworking или рабочее место, а также запас на выезд. Для коротких маршрутов этот запас особенно важен, потому что ошибка со сроком быстро превращается в срочную покупку билетов."),
            ("Когда лучше выбрать запасной маршрут", "Если правило требует слишком много допущений, лучше не героизировать план. Запасная страна или другая виза не означает отказ от мечты; это нормальная страховка. Хороший shortlist обычно содержит один основной вариант и один реалистичный запасной, где документы, срок и бюджет сходятся без попытки притянуть условия."),
        ],
        "points": [
            "Сначала официальный срок и разрешённая деятельность, потом город и аренда.",
            "Если продление или исключение не подтверждены официально, не считайте их частью плана.",
            "Отдельно считайте первый месяц: жильё, депозит, страховка, перелёт и запас на выезд.",
            "Для семьи проверяйте dependants, школу, медицину и срок пребывания до оплаты жилья.",
        ],
        "closing": "Хороший визовый выбор обычно выглядит скучно: меньше догадок, больше проверенных условий. Зато потом меньше дорогих сюрпризов.",
    }


def article_depth_panel(row: sqlite3.Row | dict, *, lang: str) -> dict:
    title = strip_html(row["title"])
    slug = str(row["slug"])
    haystack = f"{slug} {title}".lower()
    is_visa = any(token in haystack for token in ["visa", "dtv", "ltr", "gold-card", "srrv", "de-rantau", "evisa"])
    is_budget = any(token in haystack for token in ["budget", "cost", "1500", "living", "cheap"])
    is_compare = any(token in haystack for token in [" vs ", "-vs-", "compare"])
    if lang == "ru":
        if is_visa:
            sections = [
                ("Что является правилом", "Правило — это срок пребывания, возможность продления, требования к доходу, страховке, работодателю, семье и разрешённой деятельности. Если официальный источник не подтверждает пункт прямо, его нельзя считать рабочей опцией."),
                ("Что это значит на практике", "Практический вывод появляется после проверки вашего профиля: как вы зарабатываете, сколько хотите оставаться, какие документы можете показать и насколько быстро правило может измениться до подачи."),
                ("Где чаще ошибаются", "Люди часто читают название визы и додумывают удобные детали: продление, работу на местный рынок, переезд семьи или путь к резидентству. Если этого нет в правилах, лучше считать, что такой возможности нет."),
            ]
        elif is_budget:
            sections = [
                ("Цифра без контекста опасна", "Бюджет работает только вместе с городом, типом жилья, визовым ритмом, страховкой, перелётами и запасом на первый месяц. Одна средняя цифра по стране не отвечает на вопрос, выдержит ли план реальную жизнь."),
                ("Что считать отдельно", "Аренда, депозит, визовые сборы, медицина, транспорт, связь, коворкинг, перелёты и emergency fund должны считаться раздельно. Так быстрее видно, где план ломается."),
                ("Кому нужен запас больше", "Семьям, пенсионерам, людям с медицинскими требованиями и тем, кто едет в дорогие столицы, нужен более широкий коридор расходов. Экономный solo-сценарий на них не переносится автоматически."),
            ]
        elif is_compare:
            sections = [
                ("Сравнение не выбирает за вас", "Оно показывает слабые места двух вариантов. Дешевле не всегда лучше. Более сильная виза может проиграть по городу, медицине или семье. Смотрите связку факторов, а не победителя по одной колонке."),
                ("Факт отдельно, вывод отдельно", "Факт — это срок, сбор, требование, официальный статус или проверяемая цифра. Вывод — как это влияет на ваш сценарий. Если сценарий другой, вывод тоже меняется."),
                ("Когда остановиться", "Если один вариант не совпадает с доходом, сроком, документами или семейной логистикой, его лучше убрать из shortlist до оплаты жилья и билетов."),
            ]
        else:
            sections = [
                ("Сначала проверяйте основание", "Для релокации важны не ощущения, а опорные факты: легальный срок, бюджет, город, медицина, документы и риск изменения правил. Без этого хороший текст превращается в красивую гипотезу."),
                ("Что переносить в свой план", "Берите только то, что совпадает с вашим доходом, семьёй, сроком и типом работы. Универсальных выводов в переезде почти нет."),
                ("Где нужна дополнительная проверка", "Перед оплатой агента, жилья, страховки или билетов ещё раз откройте официальный источник и проверьте дату правила. Это скучно, но дешевле ошибки."),
            ]
        return {
            "title": f"Как использовать этот материал без лишнего риска",
            "intro": "Текст помогает сузить выбор, но не должен заменять проверку правил. Для виз, денег, медицины и переезда безопаснее идти от подтверждённого факта к личному сценарию, а не наоборот.",
            "sections": sections,
            "faq": [
                ("Можно ли принимать решение только по статье?", "Нет. Статья помогает понять направление, но перед подачей документов или оплатой услуг нужно сверить официальный источник."),
                ("Почему вывод может не подойти мне?", "Потому что переезд зависит от дохода, семьи, здоровья, города, срока и документов. Один и тот же маршрут может быть хорошим для одного человека и слабым для другого."),
            ],
        }
    if is_visa:
        sections = [
            ("What The Rule Actually Says", "The rule is the stay length, extension logic, income proof, insurance, employer setup, dependants and permitted activity. If the official source does not confirm something directly, do not treat it as available."),
            ("What It Means In Practice", "The useful conclusion depends on your profile: how you earn, how long you want to stay, which documents you can prove and whether the route still works if the rule changes before you apply."),
            ("Where People Get It Wrong", "People often read the visa name and assume extension, local work rights, family access or residence logic. If the rule does not say it, the plan should not rely on it."),
        ]
    elif is_budget:
        sections = [
            ("A Number Needs Context", "A budget only makes sense with city, housing type, visa rhythm, insurance, flights and first-month buffer. A national average does not tell you whether your exact plan survives real life."),
            ("Count The Lines Separately", "Rent, deposit, visa fees, healthcare, transport, phone, coworking, flights and emergency buffer should be separated. That is how weak plans become visible early."),
            ("Who Needs More Buffer", "Families, retirees, people with medical needs and anyone targeting expensive capitals need a wider budget range. A lean solo estimate does not transfer automatically."),
        ]
    elif is_compare:
        sections = [
            ("The Comparison Does Not Decide For You", "It exposes weak points. Cheaper is not always better. A stronger visa can still lose on city fit, healthcare or family logistics. Read the whole pattern, not one winning column."),
            ("Fact Separate From Meaning", "A fact is a stay length, fee, requirement, official status or verifiable figure. The meaning is how that fact affects your scenario. Change the scenario and the conclusion changes too."),
            ("When To Stop", "If one option does not match your income, timeline, documents or family logistics, remove it from the shortlist before paying for housing or flights."),
        ]
    else:
        sections = [
            ("Start With The Basis", "Relocation decisions need facts first: legal stay, budget, city, healthcare, documents and rule-change risk. Without that, even a good article becomes a nice hypothesis."),
            ("What To Carry Into Your Plan", "Use only the parts that match your income, family, timeline and work setup. Relocation has very few universal answers."),
            ("Where To Verify Again", "Before paying an agent, housing deposit, insurance or flights, open the official source and check the date. It is boring. It is also cheaper than a bad assumption."),
        ]
    return {
        "title": "How To Use This Article Without Taking Unnecessary Risk",
        "intro": "Use the article to narrow the decision, not to skip verification. For visas, money, healthcare and relocation, the safer path is confirmed fact first, personal scenario second.",
        "sections": sections,
        "faq": [
            ("Can I Decide From This Article Alone?", "No. Use it for orientation, then verify the official source before applying or paying for services."),
            ("Why Might The Conclusion Not Fit Me?", "Because relocation depends on income, family, health, city, timeline and documents. The same route can be strong for one person and weak for another."),
        ],
    }


def _title_from_slug(slug: str) -> str:
    return slug.replace("move-to-", "").replace("ru-", "").replace("-", " ").title()


def _compare_names_from_path(path: str, lang: str) -> tuple[str, str] | None:
    match = re.search(r"/compare/([^/]+)/", path)
    if not match:
        return None
    parts = match.group(1).replace("ru-", "").split("-vs-")
    if len(parts) != 2:
        return None
    ru_names = {
        "thailand": "Таиланд", "malaysia": "Малайзия", "bali": "Бали", "vietnam": "Вьетнам",
        "japan": "Япония", "taiwan": "Тайвань", "singapore": "Сингапур", "hong-kong": "Гонконг",
        "uae": "ОАЭ", "qatar": "Катар",
    }
    if lang == "ru":
        return ru_names.get(parts[0], _title_from_slug(parts[0])), ru_names.get(parts[1], _title_from_slug(parts[1]))
    return _title_from_slug(parts[0]), _title_from_slug(parts[1])


def content_depth_panel(path: str, row: sqlite3.Row | dict, *, lang: str) -> dict | None:
    if path.startswith(("/blog/", "/ru/blog/")):
        return None
    if path in {
        "/about/", "/ru/about/", "/authors/", "/ru/authors/",
        "/authors/editorial-team/", "/ru/authors/editorial-team/",
        "/contact/", "/ru/contact/", "/editorial-policy/", "/ru/editorial-policy/",
        "/how-we-verify-data/", "/ru/how-we-verify-data/",
    }:
        if lang == "ru":
            return {
                "title": "Как читать страницы доверия на Relocate to Asia",
                "intro": "Эти страницы нужны не для украшения футера. Они объясняют, кто отвечает за материалы, как проверяются визовые факты, куда сообщать об ошибках и почему сайт отделяет официальное правило от практического вывода.",
                "sections": [
                    ("Кто отвечает за факты", "Материалы ведёт редакционная команда. Для виз, расходов и релокации это важно: читателю нужно понимать, что страница не является личной консультацией, но факты сверяются по официальным источникам там, где это возможно."),
                    ("Как исправляются ошибки", "Если правило изменилось, появился более точный источник или ссылка больше не работает, такую информацию нужно отправлять через страницу контактов. В визовых, финансовых и медицинских темах исправление одного числа может быть важнее, чем переписывание красивого абзаца."),
                    ("Чего сайт не обещает", "Relocate to Asia не гарантирует одобрение визы, не заменяет юриста и не продаёт иммиграционные услуги. Задача сайта — помочь читателю отсеять слабые варианты до того, как появятся платные обязательства."),
                ],
                "faq": [
                    ("Можно ли считать материалы юридической консультацией?", "Нет. Это редакционные материалы для планирования. Перед подачей документов нужно сверить официальный источник или обратиться к профильному специалисту."),
                    ("Почему важна дата проверки?", "Визовые правила меняются. Месяц и год проверки помогают понять, насколько осторожно нужно относиться к конкретному материалу."),
                ],
            }
        return {
            "title": "How To Read Relocate To Asia Trust Pages",
            "intro": "These pages are not footer decoration. They explain who is responsible for the content, how visa facts are checked, where corrections go and why the site separates official rules from practical interpretation.",
            "sections": [
                ("Who Owns The Facts", "Relocate to Asia uses an editorial team model. For visas, costs and relocation planning, that matters because readers need to know the page is not personal legal advice, while factual claims are checked against official sources where possible."),
                ("How Corrections Work", "If a visa rule, cost number, healthcare detail or official link changes, corrections should go through the contact page. For relocation decisions, fixing one factual error matters more than rewriting a polished paragraph."),
                ("What The Site Does Not Promise", "Relocate to Asia does not guarantee visa approval, replace an immigration lawyer or sell visa services. The goal is to help readers remove weak options before they spend money."),
            ],
            "faq": [
                ("Is This Legal Advice?", "No. The content supports planning. Verify the official authority or a qualified professional before applying."),
                ("Why Does The Review Date Matter?", "Visa rules change. The review month and year help readers judge how cautiously to treat a page."),
            ],
        }
    title = strip_html(row["title"])
    slug = str(row["slug"]).removeprefix("ru-") if "slug" in row.keys() else path.strip("/")
    compare_names = _compare_names_from_path(path, lang)
    if lang == "ru":
        if compare_names:
            first, second = compare_names
            return {
                "title": f"Как читать сравнение {first} и {second}",
                "intro": f"Сравнение {first} и {second} полезно только тогда, когда вы не ищете абстрактно «лучшую страну», а проверяете конкретный сценарий: доход, срок проживания, визовый маршрут, город и состав семьи.",
                "sections": [
                    ("Сначала legal route", "Если одна страна дешевле, но легальный маршрут слабее, цена не решает вопрос. Смотрите срок stay, продление, требования к доходу, возможность удалённой работы и то, что прямо написано в официальных правилах. Неподтверждённые исключения лучше считать недоступными."),
                    ("Потом реальные расходы", "Бюджет нужно считать не только по аренде. В переезде есть депозит, страховка, перелёты, визовые сборы, emergency fund, местный транспорт и стоимость выхода из страны или продления статуса. Именно эти детали часто меняют победителя сравнения."),
                    ("Где риск ошибки", "Самая частая ошибка — выбрать страну по одному сильному плюсу. Хороший интернет не компенсирует неподходящую визу. Низкая аренда не помогает, если медицина или семейная логистика не подходят. Безопасность важна, но она тоже не заменяет бюджет."),
                ],
                "faq": [
                    ("Можно ли выбрать страну только по цене?", "Нет. Цена важна, но сначала нужно проверить легальный маршрут, срок пребывания, медицину и запас бюджета. Дешёвая страна не помогает, если вы не можете спокойно и законно там оставаться."),
                    ("Что проверять после сравнения?", "Откройте страновую страницу, визовый гайд и официальный источник по выбранному маршруту. После этого считайте город и жильё."),
                ],
            }
        if path == "/ru/countries/":
            return {
                "title": "Как выбирать страну в Азии без самообмана",
                "intro": "Страновой хаб полезен не как список красивых направлений, а как фильтр. Сначала убирайте страны, где не сходятся legal stay, бюджет, медицина или городская среда. Потом уже сравнивайте lifestyle.",
                "sections": [
                    ("Сначала сценарий", "Удалённый специалист, семья, пенсионер и человек с ограниченным бюджетом выбирают разные страны. Один рейтинг не может одинаково хорошо отвечать на все эти сценарии."),
                    ("Потом документы и деньги", "Проверьте срок пребывания, продление, доход, страховку, депозит, первый месяц и город, где вы реально будете жить. Общая дешевизна страны не гарантирует дешёвый переезд."),
                    ("Где чаще ошибаются", "Ошибка — выбрать страну по одному сильному плюсу: климату, аренде, еде или популярности у nomads. Для переезда нужна связка факторов: виза, деньги, медицина, город и понятный план выхода."),
                ],
                "faq": [
                    ("С какой страны начать?", "С той, где уже виден подходящий визовый маршрут и реалистичный бюджет. Если этого нет, лучше сначала сравнить 2-3 альтернативы."),
                    ("Можно ли выбирать по рейтингу?", "Рейтинг полезен как старт, но финальное решение должно учитывать ваш доход, семью, здоровье, город и документы."),
                ],
            }
        if "/countries/" in path:
            country = ru_country_display(slug)
            return {
                "title": f"Как оценивать переезд в {ru_country_accusative(slug)} без самообмана",
                "intro": f"{country} может выглядеть привлекательно по цене, климату или визам, но решение о переезде должно выдерживать проверку по документам, деньгам и повседневной жизни.",
                "sections": [
                    ("Что является фактом", "Факт — это то, что подтверждается официальным источником или структурированными страновыми данными: столица, валюта, язык, население, визовый срок, условия продления, требования к доходу или депозиту. Всё остальное нужно читать как практическую интерпретацию."),
                    ("Что это значит на практике", "Практический смысл появляется только после связки нескольких факторов. Например, низкая аренда помогает, если у вас есть подходящий legal stay. Хорошая медицина важна, если вы едете с семьёй или на долгий срок. Английский язык может быть решающим, если вы не готовы быстро входить в местную среду."),
                    ("Кому стоит быть осторожнее", "Осторожнее стоит быть тем, кто планирует долгий переезд без подтверждённого дохода, рассчитывает на неофициальное продление или выбирает страну только по впечатлениям из короткой поездки. Скучная проверка документов часто спасает больше денег, чем красивый план."),
                ],
                "faq": [
                    (f"Подходит ли {country} для долгого переезда?", "Это зависит не от страны в целом, а от вашего визового маршрута, бюджета, города, медицины и срока, на который вы реально хотите остаться."),
                    ("Какие данные проверять первыми?", "Срок пребывания, продление, подтверждение дохода, страховку, жильё и расходы на первый месяц."),
                ],
            }
        if "/guides/" in path:
            return {
                "title": "Как использовать этот гайд для решения, а не просто чтения",
                "intro": "Узкий гайд полезен, когда у вас уже есть конкретный вопрос. Не «куда переехать в Азии вообще», а можно ли продлить визу, хватает ли дохода, реалистичен ли бюджет или какой маршрут меньше конфликтует с вашим профилем.",
                "sections": [
                    ("Отделяйте правило от вывода", "Правило — это срок, доход, validity, продление, dependants или разрешённая деятельность. Вывод — это практическое последствие правила. Если источник не говорит о продлении, нельзя превращать молчание в обещание."),
                    ("Проверяйте слабое место", "У каждого сценария есть ограничение, которое ломает план: короткий срок, высокий доход, неподходящий работодатель, семья, страховка, дорогой город или отсутствие понятного long-stay пути. Начинайте именно с него."),
                    ("Когда остановиться", "Если маршрут не совпадает с вашим доходом, сроком или типом работы, лучше остановиться сразу. Это не провал. Это экономия времени и денег до подачи документов, аренды и перелётов."),
                ],
                "faq": [
                    ("Можно ли считать гайд юридической консультацией?", "Нет. Это редакционный материал для планирования. Перед подачей всегда проверяйте официальный источник."),
                    ("Почему формулировки осторожные?", "Потому что визовые правила меняются, а неподтверждённые обещания вредят сильнее, чем честная пауза."),
                ],
            }
        if path.startswith("/ru/tools/") or path in {"/ru/tools/", "/ru/compare-cities/"}:
            return {
                "title": "Как использовать расчёты без ложной точности",
                "intro": "Инструменты помогают сузить выбор, но не заменяют личный бюджет. Цифра на экране — это ориентир, а не гарантия, что именно столько вы потратите после переезда.",
                "sections": [
                    ("Что считать обязательно", "В бюджет должны входить аренда, депозит, страховка, визовые сборы, перелёты, связь, транспорт, еда, emergency fund и расходы на выезд или продление. Если оставить только аренду и еду, итог получится слишком красивым."),
                    ("Где цифры чаще ломаются", "Рынок жилья, район, сезон, курс валют и личные привычки быстро меняют итог. Семья, школа, медицина и частые перелёты делают бюджет совсем другим, чем у solo remote worker."),
                    ("Как принимать решение", "Сравнивайте не точную цифру до доллара, а устойчивость сценария. Если бюджет держится только при идеальной аренде и отсутствии непредвиденных расходов, это слабый план."),
                ],
                "faq": [
                    ("Можно ли полагаться только на калькулятор?", "Нет. Используйте его как первый фильтр, затем проверяйте реальные объявления, страховку и визовые расходы."),
                    ("Почему нужен запас?", "Потому что переезд почти всегда дороже первого расчёта: депозиты, документы, билеты и первые недели на месте добавляют нагрузку."),
                ],
            }
        return {
            "title": "Как использовать эту страницу для реального решения",
            "intro": "Страница полезна, если читать её как часть процесса: сначала легальный маршрут, затем бюджет, потом город, жильё и бытовые компромиссы.",
            "sections": [
                ("Факт против впечатления", "Факты проверяются по официальным источникам и данным. Впечатления помогают понять комфорт, но не должны заменять визу, деньги, медицину и сроки."),
                ("Порядок проверки", "Сначала проверьте stay и продление, затем доход и документы, потом расходы, страховку, жильё и город. Такой порядок скучнее, зато он защищает от дорогих ошибок."),
                ("Кому нужна дополнительная проверка", "Семьям, пенсионерам, людям с медицинскими требованиями и тем, кто планирует долгий срок, лучше проверять правила глубже и не принимать решение по одной странице."),
            ],
            "faq": [
                ("Что делать после чтения?", "Сравнить страну с альтернативой, открыть визовый гайд и проверить официальный источник."),
                ("Можно ли принимать платные решения сразу?", "Лучше нет. Сначала подтвердите правила, бюджет и документы."),
            ],
        }
    if compare_names:
        first, second = compare_names
        return {
            "title": f"How To Use This {first} vs {second} Comparison",
            "intro": f"This comparison is strongest when you use it for a real relocation scenario, not a generic country ranking. The useful question is whether {first} or {second} fits your income, legal stay route, work style and time horizon.",
            "sections": [
                ("Start With Legal Stay", "A cheaper country can still be the wrong answer if the visa route is weak. Check stay length, renewal logic, income proof, local work limits and what the official rule actually confirms."),
                ("Then Test The Budget", "Rent is only one line. A serious relocation budget includes deposits, insurance, flights, visa fees, emergency buffer, transport and the cost of leaving or renewing when the stay period ends."),
                ("Watch The Common Mistake", "Do not let one attractive feature decide the move. Good internet does not fix a poor visa fit. Low rent does not solve healthcare or family logistics. Safety matters, but it does not replace a sustainable budget."),
            ],
            "faq": [
                ("Should I choose the cheaper country?", "Not automatically. Cost matters, but legal stay, healthcare, safety and daily logistics can outweigh rent."),
                ("What should I do after comparing?", "Open the country guide, visa guide and official source for the route you are considering."),
            ],
        }
    if path == "/countries/":
        return {
            "title": "How To Choose An Asian Country Without Fooling Yourself",
            "intro": "The countries hub is a filter, not a travel wishlist. Start by removing destinations where legal stay, budget, healthcare or city fit does not hold up. Lifestyle comes after feasibility.",
            "sections": [
                ("Start With The Scenario", "A remote worker, family, retiree and budget-limited mover need different countries. One ranking cannot answer all of those situations equally well."),
                ("Then Check Documents And Money", "Verify stay length, renewal, income proof, insurance, deposits, first-month setup and the city you would actually live in. A cheap country does not always mean a cheap move."),
                ("The Common Mistake", "Choosing by one strong feature is risky. Climate, rent, food or nomad popularity can be real advantages, but relocation decisions need several factors to work together: legal stay, money, healthcare, city fit and an exit plan."),
            ],
            "faq": [
                ("Which country should I start with?", "Start with a country where the visa route and budget already look realistic. If that is unclear, compare two or three alternatives first."),
                ("Can I choose from a ranking alone?", "No. Rankings are useful for discovery, but the final choice depends on income, family, healthcare needs, city fit and documents."),
            ],
        }
    if "/countries/" in path:
        country = _title_from_slug(slug)
        return {
            "title": f"How To Evaluate A Move To {country}",
            "intro": f"{country} should be judged by the whole relocation picture: visa fit, cost pressure, healthcare, city choice, documents and the length of stay you actually want.",
            "sections": [
                ("What Counts As A Fact", "A fact is something confirmed by an official source or structured country data: currency, capital, population, visa duration, renewal, income proof, insurance or deposit requirements. Everything else is practical interpretation."),
                ("What It Means In Practice", "The practical decision comes from combining those facts. Cheap housing is useful only if the legal stay works. Strong healthcare matters more for families and retirees. English level can matter more than climate if daily admin will be difficult."),
                ("Who Should Be Careful", "Be careful if you are planning a long stay without confirmed income, relying on unofficial extensions or choosing the country because a short trip felt easy. Boring verification should come before exciting plans."),
            ],
            "faq": [
                (f"Is {country} good for long-term relocation?", "It depends on your visa route, budget, city, healthcare needs and the length of stay you need."),
                ("What should I verify first?", "Stay duration, renewal, income proof, insurance, housing and first-month setup costs."),
            ],
        }
    if "/guides/" in path:
        return {
            "title": "How To Use This Guide For A Real Decision",
            "intro": "A focused guide works best when you already have a specific question: extension, income, visa fit, family eligibility, budget or the difference between two routes.",
            "sections": [
                ("Separate Rule From Meaning", "The rule is the official stay length, validity, extension, income, dependants or permitted activity. The meaning is the planning consequence. If an official page does not confirm an exception, do not build a plan around it."),
                ("Find The Constraint", "Every move has a constraint that can break it: short stay, high income proof, employer logic, family eligibility, insurance, expensive cities or unclear renewal. Start there."),
                ("Know When To Stop", "If the route does not match your income, work profile or time horizon, stop before paying for applications, flights or housing. That is a good planning result, not a failure."),
            ],
            "faq": [
                ("Is this legal advice?", "No. It is planning guidance based on public sources. Always verify the official authority before applying."),
                ("Why is the wording cautious?", "Because immigration rules change and unsupported promises can cause expensive mistakes."),
            ],
        }
    if path.startswith("/tools/") or path in {"/tools/", "/compare-cities/"}:
        return {
            "title": "How To Use The Numbers Without False Precision",
            "intro": "The tools are decision filters, not guarantees. A calculator can show whether a country belongs on your shortlist, but your final budget still depends on city, housing, visa route and risk tolerance.",
            "sections": [
                ("Include The Costs People Forget", "A real move includes rent, deposit, visa fees, insurance, flights, local transport, phone, emergency buffer and the cost of leaving or renewing. Leaving out one-time costs makes the plan look safer than it is."),
                ("Treat Ranges As Ranges", "Housing markets, exchange rates, neighbourhoods and seasons move quickly. A single number is less useful than asking whether your plan survives a bad month, a higher deposit or a more expensive district."),
                ("Use The Result As A Filter", "If the budget only works in the cheapest possible case, the route is fragile. If it still works with a buffer, then the country is worth deeper visa and city research."),
            ],
            "faq": [
                ("Can I rely only on the calculator?", "No. Use it for screening, then verify housing, insurance and visa costs manually."),
                ("Why add an emergency buffer?", "Because relocation almost always creates costs that were not in the first spreadsheet."),
            ],
        }
    return {
        "title": "How To Turn This Page Into A Relocation Decision",
        "intro": "Use this page as one part of a sequence: legal stay, budget, city, housing and practical trade-offs. Skipping that order is how people make expensive relocation mistakes.",
        "sections": [
            ("Fact Before Preference", "Preferences matter, but facts decide feasibility. Visa rules, income proof, healthcare access and costs should come before beaches, food and lifestyle impressions."),
            ("The Safe Order", "Check stay length and renewal first. Then check income and documents. After that, compare living costs, insurance, housing and the city you would actually live in."),
            ("Who Needs Extra Verification", "Families, retirees, people with medical needs and anyone planning a long stay should verify official rules more deeply before making paid commitments."),
        ],
        "faq": [
            ("What should I do next?", "Compare one alternative country, read the visa guide and verify the official source."),
            ("Should I pay for anything yet?", "Not until the visa route, budget and documents make sense together."),
        ],
    }


def content_quality_panel(path: str, row: sqlite3.Row | dict, *, lang: str) -> dict | None:
    if path.startswith(("/blog/", "/ru/blog/")):
        return None
    title = strip_html(row["title"] if "title" in row.keys() else "")
    slug = str(row["slug"]).removeprefix("ru-") if "slug" in row.keys() else path.strip("/")
    compare_names = _compare_names_from_path(path, lang)
    is_ru = lang == "ru"

    if "/countries/move-to-" in path:
        if is_ru:
            country = ru_country_display(slug)
            return {
                "title": f"Что проверить перед переездом в {ru_country_accusative(slug)}",
                "intro": f"{country} нельзя оценивать только по аренде, климату или впечатлениям из короткой поездки. Для релокации важнее связка: легальный срок stay, понятный бюджет, медицина, городская среда и запасной план, если правила или расходы изменятся.",
                "sections": [
                    ("Виза и срок пребывания", "Сначала проверьте, какой маршрут реально подходит вашему доходу, типу работы и семье. Если страна хороша по быту, но legal stay держится на коротких въездах или неясном продлении, это не долгосрочный план, а временная гипотеза."),
                    ("Бюджет без самообмана", "Считайте не минимальную аренду, а нормальный месяц жизни: район, депозит, интернет, связь, транспорт, страховку, визовые расходы, перелёты и резерв. В дешёвой стране ошибка в районе или визовом ритме быстро съедает экономию."),
                    ("Медицина, язык и город", "Для solo remote worker слабый английский или медицина могут быть терпимым компромиссом. Для семьи, пенсионера или человека с регулярными медицинскими потребностями это уже ключевой фильтр. Поэтому страну нужно проверять через город, а не через среднюю картинку."),
                    ("Когда лучше выбрать другое направление", "Если нужный статус не подтверждается официально, доход не проходит по требованиям, бюджет держится без запаса или вы не понимаете, что делать после окончания stay, лучше сравнить альтернативу. Это дешевле, чем исправлять ошибку после переезда."),
                    ("Что проверить до оплаты", "До депозита за жильё, визового сбора или длинного перелёта откройте официальный источник по въезду, проверьте дату обновления, требования к документам и ограничения по работе. Если в правилах есть неоднозначность, не стройте на ней весь план."),
                    ("Какой нужен план B", "План B — это не паника, а нормальная часть релокации: соседняя страна, другой город, запас денег на выезд, временное жильё и понимание, что делать, если продление не подтвердится или расходы окажутся выше расчёта."),
                    ("С чем сравнивать", "Сравнивайте не только страны, но и сценарии. Один вариант может быть сильнее для короткой remote-work базы, другой — для семьи, третий — для пенсионного маршрута. Если критерий не связан с вашим реальным сценарием, он не должен решать выбор."),
                    ("Когда вернуться к расчётам", "После выбора страны вернитесь к цифрам ещё раз: курс валют, цена жилья, страховка, перелёт и визовые сборы могли измениться. Для переезда это нормальная проверка перед каждым крупным платежом."),
                ],
            }
        country = COUNTRY_EN_NAMES.get(slug, title.replace("Move to ", "").replace(": Complete Relocation Guide 2026", ""))
        return {
            "title": f"What To Verify Before Moving To {country}",
            "intro": f"{country} should not be judged only by rent, weather or a good short trip. A relocation decision needs legal stay, a realistic monthly budget, healthcare access, city fit and a fallback plan if rules or costs change.",
            "sections": [
                ("Visa And Length Of Stay", "Start with the route that actually fits your income, work type and family situation. If daily life looks attractive but legal stay depends on short entries or vague renewal assumptions, it is a temporary test, not a durable relocation plan."),
                ("Budget Without Wishful Thinking", "Use a normal month, not the cheapest possible month: neighborhood, deposit, internet, phone, transport, insurance, visa costs, flights and emergency buffer. In a low-cost country, one bad housing or visa assumption can erase the savings."),
                ("Healthcare, Language And City Fit", "For a solo remote worker, weak English or uneven healthcare may be manageable. For a family, retiree or anyone with recurring medical needs, those details become primary filters. Judge the country through the city where you would actually live."),
                ("When To Choose Another Direction", "If the status is not confirmed by official rules, your income does not fit, the budget has no buffer or the exit plan is unclear, compare another country before spending money. That is not pessimism. It is basic risk control."),
                ("What To Check Before Paying", "Before a housing deposit, visa fee or long flight, open the official entry source, check the update date, document requirements and work restrictions. If the rule is ambiguous, do not build the whole move on that ambiguity."),
                ("What A Plan B Looks Like", "A fallback plan is not panic. It is normal relocation hygiene: another country, another city, money to leave, temporary housing and a clear answer for what happens if renewal is unavailable or costs run higher than expected."),
                ("What To Compare It Against", "Compare scenarios, not only countries. One option may be stronger for a short remote-work base, another for a family move and another for retirement. If a criterion does not match your real scenario, it should not decide the move."),
                ("When To Recheck The Numbers", "After choosing a country, run the numbers again: exchange rates, housing prices, insurance, flights and visa fees may have changed. For relocation, this is normal due diligence before every large payment."),
            ],
        }

    if compare_names:
        first, second = compare_names
        if is_ru:
            return {
                "title": f"Финальная проверка перед выбором: {first} или {second}",
                "intro": f"Сравнение {first} и {second} полезно только тогда, когда оно заканчивается практическим решением. Не какая страна «лучше вообще», а какая меньше конфликтует с вашим доходом, визовым маршрутом, семьёй, медициной и горизонтом проживания.",
                "sections": [
                    ("Где правила сильнее впечатлений", "Если одна страна кажется удобнее, но виза короче, дороже или хуже подходит под ваш тип работы, впечатление не решает проблему. Сначала правило. Потом город, район и lifestyle."),
                    ("Где бюджет может обмануть", "Разница в аренде важна, но её нужно сравнивать вместе со страховкой, перелётами, депозитами, налоговой логикой, визовыми сборами и стоимостью выезда или продления. Иначе дешёвая страна выглядит сильнее, чем она есть."),
                    ("Где риск выше", "Семьям важны школы, медицина и dependants. Remote workers смотрят на интернет, банки и легальность работы. Пенсионерам важнее стабильность статуса и больницы. Один и тот же победитель не подходит всем."),
                ],
            }
        return {
            "title": f"Final Decision Check: {first} Or {second}",
            "intro": f"A {first} vs {second} comparison is useful only when it ends in a practical decision. The question is not which country is better in general, but which one conflicts less with your income, visa route, family needs, healthcare and time horizon.",
            "sections": [
                ("Where Rules Matter More Than Taste", "If one country feels easier but the visa is shorter, more expensive or weaker for your work type, the feeling does not fix the rule. Check the legal route first. Then compare the city, neighborhood and lifestyle."),
                ("Where The Budget Can Mislead You", "Rent matters, but it belongs beside insurance, flights, deposits, tax exposure, visa fees and the cost of leaving or renewing. Without those lines, the cheaper country can look stronger than it really is."),
                ("Where Risk Changes By Profile", "Families need schools, healthcare and dependant logic. Remote workers need internet, banking and legal work clarity. Retirees need status stability and hospital access. The same winner will not fit every reader."),
            ],
        }

    if "/guides/" in path:
        if is_ru:
            return {
                "title": "Как использовать этот гайд без опасных допущений",
                "intro": "Узкий guide отвечает на один вопрос, но решение всё равно зависит от вашего профиля. Проверьте, что правило написано в официальном источнике, а практический вывод не превращает молчание источника в обещание.",
                "sections": [
                    ("Что считать фактом", "Факт — это срок stay, validity, доход, депозит, право на работу, dependants или продление, если это прямо указано источником. Если источник не говорит о продлении или исключении, безопаснее считать, что его нет."),
                    ("Что считать практическим смыслом", "Практический смысл — это вывод из правила: подходит ли маршрут для короткой базы, семьи, long-stay плана или пенсионного сценария. Такой вывод помогает отсеять слабые варианты, но не заменяет официальную проверку перед подачей."),
                    ("Где чаще ошибаются", "Люди часто начинают с страны, а не с маршрута. Потом выясняется, что доход не проходит, stay слишком короткий, семья не включается или город дороже ожидаемого. Лучше найти этот конфликт до покупки билетов."),
                ],
            }
        return {
            "title": "How To Use This Guide Without Risky Assumptions",
            "intro": "A focused guide answers one question, but the decision still depends on your profile. Check that the rule is stated by an official source and that the practical interpretation does not turn silence into a promise.",
            "sections": [
                ("What Counts As A Fact", "A fact is stay length, validity, income, deposit, work permission, dependant logic or extension language when the official source states it. If the source does not mention an extension or exception, treat it as unavailable."),
                ("What Counts As Practical Meaning", "Practical meaning is the consequence of the rule: whether the route fits a short base, family move, long-stay plan or retirement scenario. It helps remove weak options, but it does not replace checking the authority before applying."),
                ("Where People Usually Get It Wrong", "Many people start with the country, not the route. Then income fails, the stay is too short, family members do not fit or the city costs more than expected. It is better to find that conflict before buying flights."),
            ],
        }

    hub_topics = {
        "/digital-nomad-visas-asia/": ("Digital Nomad Visa Planning Check", "digital nomad visa", "remote work route"),
        "/ru/digital-nomad-visas-asia/": ("Проверка перед выбором Digital Nomad визы", "digital nomad visa", "маршрут для удалённой работы"),
        "/retire-in-asia/": ("Retirement Relocation Planning Check", "retirement visa", "long-stay retirement route"),
        "/ru/retire-in-asia/": ("Проверка перед пенсионной релокацией", "пенсионная виза", "long-stay маршрут"),
        "/cheapest-countries-in-asia/": ("Budget Country Planning Check", "low-cost country", "budget relocation route"),
        "/ru/cheapest-countries-in-asia/": ("Проверка бюджетной страны перед переездом", "дешёвая страна", "бюджетный маршрут релокации"),
    }
    if path in hub_topics:
        heading, keyword, route = hub_topics[path]
        if is_ru:
            return {
                "title": heading,
            "intro": f"{keyword} не должна выбираться по одному сильному плюсу. Важнее другое: подтверждённый {route}, реальные расходы, медицина, страховка, семья и понятный план выхода, если страна не подходит.",
                "sections": [
                    ("Сначала legal route", "Красивый бюджет или сильный lifestyle не помогают, если stay короткий, продление не подтверждено или требования к доходу не совпадают с вашей ситуацией. Официальное правило должно идти перед эмоцией."),
                    ("Потом полный бюджет", "Считайте аренду, депозит, перелёт, страховку, связь, транспорт, еду, визовые сборы, emergency fund и расходы на выезд. Именно эти строки отделяют реалистичный переезд от красивой таблицы."),
                    ("Потом личные ограничения", "Семья, здоровье, возраст, работа, налоги, язык и банковская логика могут полностью изменить выбор. Поэтому хаб полезен как shortlist, но финальное решение должно проходить через конкретную страну и официальный источник."),
                    ("Где проверять спорные места", "Если цифра или правило влияют на деньги, документы или срок проживания, проверяйте первоисточник. Блог, форум и видео могут подсказать вопрос, но не должны быть единственной опорой перед подачей или оплатой."),
                    ("Когда не торопиться", "Если маршрут держится на слухах о продлении, слишком оптимистичной аренде или неясном доходе, лучше остановиться и сравнить альтернативы. В релокации пауза часто дешевле, чем быстрый неправильный шаг."),
                    ("Как превратить список в решение", "Оставьте в shortlist только варианты, где совпадают три вещи: официальный маршрут, реальный бюджет и бытовая логистика. Если страна хороша только по одному пункту, она может быть полезной для поездки, но слабой для переезда."),
                    ("Что пересчитать перед оплатой", "Перед любым крупным платежом обновите цифры: жильё, курс валют, страховку, перелёты, визовые сборы и резерв. В релокации устаревший бюджет опасен почти так же, как устаревшее визовое правило."),
                    ("Что делать дальше", "Выберите два-три направления и откройте по каждому отдельную страновую страницу. Хаб помогает сузить выбор, но финальное решение должно опираться на конкретные условия страны, города и вашего профиля."),
                    ("Как читать итог", "Если вариант выглядит привлекательным, но требует неподтверждённого продления, идеального курса валют или слишком дешёвого жилья, считайте его рискованным. Хороший shortlist выдерживает не оптимистичный, а обычный сценарий."),
                    ("Когда нужна консультация", "Если решение затрагивает пенсию, крупный депозит, лечение, dependants или налоговые последствия, одной статьи недостаточно. Используйте страницу как фильтр, а финальные документы сверяйте с официальным органом или профильным специалистом."),
                ],
            }
        return {
            "title": heading,
            "intro": f"A {keyword} should not be chosen from one attractive advantage. The stronger filters are the confirmed {route}, real monthly costs, healthcare, insurance, family logistics and a clear exit plan if the country does not fit.",
            "sections": [
                ("Legal Route Comes First", "A good budget or strong lifestyle does not help if the stay is short, renewal is not confirmed or income requirements do not match your situation. The official rule has to come before the feeling."),
                ("Then The Full Budget", "Count rent, deposit, flights, insurance, phone, transport, food, visa fees, emergency buffer and the cost of leaving. These lines separate a realistic move from a neat comparison table."),
                ("Then Personal Constraints", "Family, health, age, work setup, tax exposure, language and banking can change the answer completely. Use the hub as a shortlist, then verify the specific country and official source."),
                ("Where To Check The Fragile Parts", "If a number or rule affects money, documents or stay length, verify the primary source. A blog, forum or video can help you discover the question, but it should not be the only basis before applying or paying."),
                ("When To Slow Down", "If the route depends on renewal rumors, optimistic rent or unclear income proof, pause and compare alternatives. In relocation, slowing down is often cheaper than making a fast wrong move."),
                ("How To Turn The List Into A Decision", "Keep only options where three things work together: the official route, the real budget and daily logistics. If a country is strong on only one point, it may be useful for travel but weak for relocation."),
                ("What To Recalculate Before Paying", "Before any large payment, refresh the numbers: housing, exchange rates, insurance, flights, visa fees and emergency buffer. In relocation, an old budget can be almost as risky as an old visa rule."),
                ("What To Do Next", "Choose two or three destinations and open the separate country page for each one. A hub helps narrow the list, but the final decision should depend on the specific country rules, city conditions and your profile."),
            ],
        }

    return None


def article_source_panel_for_post(row: sqlite3.Row | dict, *, lang: str) -> dict | None:
    slug = row["slug"] if "slug" in row.keys() else ""
    title = strip_html(row["title"] if "title" in row.keys() else "")
    haystack = f"{slug} {title}".lower()
    picked: list[dict[str, str]] = []

    def add(title: str, url: str, note_en: str, note_ru: str) -> None:
        if not any(item["url"] == url for item in picked):
            picked.append({"title": title, "url": url, "note": note_ru if lang == "ru" else note_en})

    for item in extract_official_sources(row["content"] if "content" in row.keys() else "", limit=10):
        add(item["title"], item["url"], "Official source referenced in the article.", "Официальный источник, указанный в статье.")

    if "japan" in haystack or "yaponiya" in haystack:
        add("Japan MOFA: Specified Visa For Digital Nomad", "https://www.mofa.go.jp/ca/fna/pagewe_000001_00046.html", "Checks stay length, income proof, insurance and no-extension wording.", "Проверка срока, дохода, страховки и формулировки no extension.")
        add("Japan Immigration Services Agency: Digital Nomad", "https://www.moj.go.jp/isa/applications/status/designatedactivities53_00001.html", "Immigration authority page for the Designated Activities route.", "Страница иммиграционной службы по маршруту Designated Activities.")
    if "taiwan" in haystack or "gold-card" in haystack:
        add("Taiwan Gold Card: What Is The Gold Card?", "https://goldcard.nat.gov.tw/en/about/", "Official explanation of the 4-in-1 card and 1-3 year logic.", "Официальное объяснение 4-in-1 карты и срока 1-3 года.")
        add("Taiwan Gold Card: Salary Requirement FAQ", "https://goldcard.nat.gov.tw/en/faq/how-do-i-meet-the-salary-requirements-of-the-gold-card-application/", "Salary-based qualification and proof rules.", "Правила salary-based квалификации и подтверждения дохода.")
    if "indonesia" in haystack or "bali" in haystack or "e33g" in haystack:
        add("Indonesia eVisa Official Portal", "https://evisa.imigrasi.go.id/", "Official immigration portal for Indonesian visa applications.", "Официальный портал иммиграции Индонезии для визовых заявок.")
    if "thailand" in haystack or "tailand" in haystack or "dtv" in haystack:
        add("Thailand e-Visa Official Website", "https://www.thaievisa.go.th/", "Official application entry point for Thai visa categories.", "Официальная точка входа для заявок по тайским визовым категориям.")
        add("Thailand.go.th: Destination Thailand Visa", "https://thailand.go.th/visit-thailand-detail/-destination-thailand-visa-dtv", "Government page for DTV purpose and stay context.", "Государственная страница по DTV: цель маршрута и срок stay.")
    if "ltr" in haystack:
        add("Thailand BOI: Long-Term Resident Visa", "https://ltr.boi.go.th/", "Official LTR program portal and category overview.", "Официальный портал программы LTR и обзор категорий.")
        add("BOI LTR Required Documents", "https://ltr.boi.go.th/page/required-documents.html", "Official required document hub by LTR category.", "Официальный раздел документов по категориям LTR.")
    if "malaysia" in haystack or "rantau" in haystack:
        add("MDEC: DE Rantau FAQ For Foreign Applicants", "https://mdec.my/static/pdf/derantau/DE%20Rantau%20Pass%20FAQ-Foreign.pdf", "Official FAQ for DE Rantau foreign applicants.", "Официальный FAQ DE Rantau для иностранных заявителей.")
        add("Immigration Department of Malaysia", "https://www.imi.gov.my/", "Official Malaysian immigration portal.", "Официальный портал иммиграционной службы Малайзии.")
    if "philippines" in haystack or "srrv" in haystack:
        add("Philippine Retirement Authority: SRRVisa", "https://pra.gov.ph/SRRVisa", "Official SRRV page for retirement visa checks.", "Официальная страница SRRV для проверки пенсионного маршрута.")
    if "korea" in haystack or "workation" in haystack or "yuzhnaya-koreya" in haystack:
        add("Korea Visa Portal", "https://www.visa.go.kr/?LANG_TYPE=EN", "Official Korea visa portal.", "Официальный визовый портал Кореи.")
        add("Korean Embassy: Digital Nomad Workcation Visa", "https://www.mofa.go.kr/us-en/brd/m_4502/view.do?page=1&seq=715884", "Embassy guidance for workcation visa checks.", "Инструкция посольства по workation visa.")
    if "singapore" in haystack or "one-pass" in haystack:
        add("Singapore MOM: Overseas Networks & Expertise Pass", "https://www.mom.gov.sg/passes-and-permits/overseas-networks-expertise-pass", "Official MOM page for ONE Pass eligibility.", "Официальная страница MOM по условиям ONE Pass.")
    if "hong-kong" in haystack:
        add("Hong Kong Immigration Department: Top Talent Pass Scheme", "https://www.immd.gov.hk/eng/services/visas/TTPS.html", "Official immigration page for TTPS checks.", "Официальная страница Immigration Department по TTPS.")
    if "vietnam" in haystack:
        add("Vietnam Immigration: eVisa Portal", "https://evisa.immigration.gov.vn/web/guest/trang-chu-ttdt", "Official eVisa portal for Vietnam.", "Официальный портал eVisa Вьетнама.")
        add("Vietnam Tourism: Official eVisa Guide", "https://vietnam.travel/plan-your-trip/official-vietnam-evisa-application", "Official tourism guide for eVisa checks.", "Официальный туристический гид по eVisa.")
    if "cambodia" in haystack:
        add("Cambodia eVisa Official Government Website", "https://www.evisa.gov.kh/", "Official Cambodian eVisa website.", "Официальный сайт правительства Камбоджи по eVisa.")
    if "sri-lanka" in haystack:
        add("Sri Lanka ETA Official Website", "https://www.eta.gov.lk/slvisa/visainfo/center.jsp?locale=en_US", "Official ETA page for short-visit rules.", "Официальная страница ETA по short visit правилам.")
    if "india" in haystack:
        add("Indian Visa Online: eVisa", "https://indianvisaonline.gov.in/evisa/", "Official India eVisa portal.", "Официальный портал eVisa Индии.")
    if "qatar" in haystack:
        add("Hayya Official Portal", "https://hayya.qa/", "Official Qatar visitor permit portal.", "Официальный портал Qatar visitor permit.")
    if "saudi" in haystack:
        add("Saudi eVisa Official Portal", "https://visa.visitsaudi.com/", "Official Saudi tourism eVisa portal.", "Официальный портал Saudi tourism eVisa.")
    if "uae" in haystack or "virtual-work" in haystack:
        add("UAE Government: Residence Visa For Working Outside The UAE", "https://u.ae/en/information-and-services/visa-and-emirates-id/residence-visas/residence-visa-for-working-outside-the-uae", "Official UAE government page for the virtual work residence route.", "Официальная страница правительства ОАЭ по virtual work residence.")
        add("UAE ICP Smart Services", "https://icp.gov.ae/en/", "Federal authority portal for UAE identity, citizenship and visa services.", "Федеральный портал ОАЭ по identity, citizenship и визовым сервисам.")

    if not picked:
        return None
    if lang == "ru":
        return {
            "eyebrow": "Официальные источники",
            "title": "Что проверить перед решением",
            "intro": "Эти ссылки нужны для проверки сроков, дохода, продления, документов и разрешённой деятельности. Статья помогает разобраться, но правило всегда нужно сверять у органа, который его публикует.",
            "sources": picked[:10],
            "checks": ["срок", "продление", "доход", "страховка", "dependants", "разрешённая работа"],
        }
    return {
        "eyebrow": "Official Sources",
        "title": "What To Verify Before You Decide",
        "intro": "Use these official pages to verify stay length, income proof, extensions, documents and permitted activity. The article explains the trade-offs; the authority publishes the rule.",
        "sources": picked[:10],
        "checks": ["stay length", "extension", "income", "insurance", "dependants", "permitted work"],
    }


def depth_panel_schema(panel: dict | None, path: str, *, lang: str) -> dict | None:
    if not panel or not panel.get("faq"):
        return None
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "inLanguage": lang,
        "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
            for q, a in panel["faq"]
        ],
        "url": absolute_url(path),
    }


def render_page_row(row: sqlite3.Row | dict, **kwargs):
    row = normalized_content_row(row)
    breadcrumbs = kwargs.get("breadcrumbs", [])
    lang = kwargs.get("lang", "ru" if request.path.startswith("/ru/") else "en")
    if lang == "ru":
        row = polish_ru_data(row)
        if row.get("content"):
            row["content"] = sentence_case_ru_headings(row["content"])
            row["content"] = polish_ru_text(row["content"])
        breadcrumbs = polish_ru_data(breadcrumbs)
    path = local_path(kwargs.get("canonical_path") or (row["link"] if "link" in row.keys() and row["link"] else request.path))
    slug = row["slug"] if "slug" in row.keys() else request.path.strip("/")
    schema = [
        breadcrumb_schema(breadcrumbs, row["title"], path),
        organization_schema(),
        website_schema(),
    ]
    depth_panel_data = content_depth_panel(path, row, lang=lang)
    quality_panel_data = content_quality_panel(path, row, lang=lang)
    source_panel_data = page_source_panel(path, lang=lang)
    if lang == "ru":
        depth_panel_data = polish_ru_data(depth_panel_data)
        quality_panel_data = polish_ru_data(quality_panel_data)
        source_panel_data = polish_ru_data(source_panel_data)
    internal_links = internal_links_for_page(row, current_path=path)
    faq_schema = faq_schema_from_html(row["content"], lang=lang)
    if faq_schema:
        schema.append(faq_schema)
    else:
        depth_schema = depth_panel_schema(depth_panel_data, path, lang=lang)
        if depth_schema:
            schema.append(depth_schema)
    item_list = item_list_schema(f"Internal links for {strip_html(row['title'])}", internal_links)
    if item_list:
        schema.append(item_list)
    if source_panel_data:
        source_list = item_list_schema(f"Official sources for {strip_html(row['title'])}", source_panel_data["sources"])
        if source_list:
            schema.append(source_list)
    if path in {
        "/compare/",
        "/compare-cities/",
        "/tools/cost-calculator/",
        "/tools/budget-planner/",
        "/ru/compare/",
        "/ru/compare-cities/",
        "/ru/tools/cost-calculator/",
        "/ru/tools/budget-planner/",
    }:
        schema.append(web_application_schema(row["title"], path, row["content"]))
    trust_panel_data = page_trust_panel(path, lang=lang)
    if trust_panel_data:
        schema.append(trust_page_schema(row["title"], path))
    extra_schema = kwargs.get("extra_schema")
    if extra_schema:
        if isinstance(extra_schema, list):
            schema.extend(extra_schema)
        else:
            schema.append(extra_schema)
    seo = seo_payload(
        title=row["title"],
        description=page_meta_description(row, lang=lang),
        lang=lang,
        canonical_path=path,
        alternates=kwargs.get("alternates") or default_page_alternates(path),
        schema=schema,
    )
    return render_template(
        "page.html",
        page=row,
        seo=seo,
        internal_links=internal_links,
        trust_panel=trust_panel_data,
        source_panel=source_panel_data,
        depth_panel=depth_panel_data,
        quality_panel=quality_panel_data,
        lang_code=lang,
        home_url="/ru/" if lang == "ru" else "/",
        home_label="Главная" if lang == "ru" else "Home",
        explore_next_label="Что посмотреть дальше" if lang == "ru" else "Explore Next",
        **kwargs,
    )


def render_post_row(row: sqlite3.Row, *, lang: str):
    if lang == "ru":
        row = dict(row)
        row["title"] = localized_post_content(row["title"])
        row["excerpt"] = localized_post_content(row["excerpt"] or "")
        row["content"] = localized_post_content(row["content"])
    row = normalized_content_row(row)
    if lang == "ru":
        row = polish_ru_data(row)
        if row.get("content"):
            row["content"] = sentence_case_ru_headings(row["content"])
            row["content"] = polish_ru_text(row["content"])
    canonical_path = f"/blog/{row['slug']}/" if lang == "en" else f"/ru/blog/{row['slug']}/"
    alternates = post_alternates(row, lang=lang, canonical_path=canonical_path)
    schema = [
        article_schema(row, lang=lang, canonical_path=canonical_path),
        breadcrumb_schema([("Блог" if lang == "ru" else "Blog", "/ru/blog/" if lang == "ru" else "/blog/")], row["title"], canonical_path),
        organization_schema(),
    ]
    faq_schema = faq_schema_from_html(row["content"], lang=lang)
    if faq_schema:
        schema.append(faq_schema)
    article_expansion = article_expansion_panel(row, lang=lang)
    article_depth = article_depth_panel(row, lang=lang)
    if lang == "ru":
        article_expansion = polish_ru_data(article_expansion)
        article_depth = polish_ru_data(article_depth)
    if not faq_schema:
        depth_schema = depth_panel_schema(article_depth, canonical_path, lang=lang)
        if depth_schema:
            schema.append(depth_schema)
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
    article_seo = post_seo_panel(row, lang=lang)
    article_sources = article_source_panel_for_post(row, lang=lang)
    article_trust = article_trust_panel(row, lang=lang)
    related = related_posts(row)
    if lang == "ru":
        article_seo = polish_ru_data(article_seo)
        article_sources = polish_ru_data(article_sources)
        article_trust = polish_ru_data(article_trust)
        related = polish_ru_data(related)
    return render_template(
        "post.html",
        post=row,
        seo=seo,
        lang_code=lang,
        article_seo_panel=article_seo,
        article_source_panel=article_sources,
        article_trust=article_trust,
        article_expansion=article_expansion,
        article_depth=article_depth,
        related_posts=related,
        internal_links=internal_links,
    )


def localized_page_dict(*, slug: str, title: str, content: str, link: str, parent: str | None = None) -> dict[str, str | None]:
    return {
        "slug": slug,
        "title": title,
        "content": content,
        "parent": parent,
        "link": absolute_url(link),
    }


def normalize_rendered_text(value: str | None) -> str:
    if not value:
        return ""
    replacements = [
        ("LIVE DATA · TELEPORT API", "CITY COMPARISON 2026"),
        ("LIVE DATA В· TELEPORT API", "CITY COMPARISON 2026"),
        ("LIVE DATA", "CITY COMPARISON 2026"),
        ("TELEPORT API", "CITY DATA"),
        ("fetched live from Teleport", "based on relocation planning metrics"),
        ("— fetched live from Teleport", "— based on relocation planning metrics"),
        ("Ookla 2025", "latest available Ookla data checked in 2026"),
        ("2025–2026", "2026"),
        ("2025-2026", "2026"),
    ]
    return replace_many(value, replacements)


def polish_ru_text(value: str | None) -> str:
    if not value:
        return ""
    text = str(value)
    if "<" in text and ">" in text:
        return "".join(
            part if part.startswith("<") else polish_ru_text(part)
            for part in re.split(r"(<[^>]+>)", text)
        )
    replacements = [
        ("long-stay маршруты", "маршруты долгого проживания"),
        ("long-stay маршрут", "маршрут долгого проживания"),
        ("long-stay логика", "логика долгого проживания"),
        ("long-stay варианты", "варианты долгого проживания"),
        ("long-stay план", "план долгого проживания"),
        ("long-stay путь", "путь долгого проживания"),
        ("long-stay удобство", "удобство долгого проживания"),
        ("long-stay", "долгое проживание"),
        ("long stay", "долгое проживание"),
        ("remote-work сообщество", "сообщество удалённых специалистов"),
        ("remote work", "удалённая работа"),
        ("remote-worker маршрут", "маршрут для удалённой работы"),
        ("remote-worker", "для удалённой работы"),
        ("remote income", "удалённый доход"),
        ("remote employees", "удалённые сотрудники"),
        ("remote worker", "удалённый специалист"),
        ("remote workers", "удалённые специалисты"),
        ("solo remote worker", "удалённый специалист без семьи"),
        ("solo-сценарий", "сценарий для одного человека"),
        ("solo-сценария", "сценария для одного человека"),
        ("solo-сценариям", "сценариям для одного человека"),
        ("solo/month", "в месяц для одного человека"),
        ("expat-сообществом", "сообществом экспатов"),
        ("expat-сообщество", "сообщество экспатов"),
        ("expat-среда", "среда экспатов"),
        ("expat-среду", "среду экспатов"),
        ("expat-сервисы", "сервисы для экспатов"),
        ("expat-инфраструктура", "инфраструктура для экспатов"),
        ("expat-направления", "направления для экспатов"),
        ("expat-блогов", "материалов для экспатов"),
        ("expat-маршрутов", "маршрутов для экспатов"),
        ("expat-фольклоре", "разговорах экспатов"),
        ("expat-экосистема", "экосистема для экспатов"),
        ("expat-профилей", "профилей экспатов"),
        ("expat-поддержка", "поддержка экспатов"),
        ("expat budgets", "бюджеты экспатов"),
        ("expat ", "экспат "),
        ("expats", "экспаты"),
        ("nomad-среда", "среда удалённых специалистов"),
        ("nomad-среде", "среде удалённых специалистов"),
        ("nomad-сообщество", "сообщество удалённых специалистов"),
        ("nomad-локациях", "локациях для удалённых специалистов"),
        ("nomad-визы", "визы для удалённых специалистов"),
        ("digital nomads", "удалённых специалистов"),
        ("Digital nomads", "Удалённые специалисты"),
        ("digital nomad visa", "digital nomad visa"),
        ("lifestyle-рейтинга", "рейтинга образа жизни"),
        ("lifestyle-виза", "виза про образ жизни"),
        ("lifestyle-визы", "визы про образ жизни"),
        ("lifestyle-focused", "ориентированный на образ жизни"),
        ("coastal lifestyle", "жизнь у моря"),
        ("beach lifestyle", "пляжный быт"),
        ("premium lifestyle", "премиальный образ жизни"),
        ("premium stay", "короткое проживание с высоким уровнем сервиса"),
        ("Lifestyle", "Образ жизни"),
        ("lifestyle", "образ жизни"),
        ("high earners", "люди с высоким доходом"),
        ("founders", "основатели проектов"),
        ("founder", "основатель проекта"),
        ("self-sponsored", "самостоятельный"),
        ("low-barrier", "низкопороговый"),
        ("dependants", "члены семьи"),
        ("dependent family members", "члены семьи"),
        ("eligibility", "требования к заявителю"),
        ("legal route", "легальный маршрут"),
        ("Legal Route", "Легальный маршрут"),
        ("shortlist", "короткий список"),
        ("multi-year route", "маршрут на несколько лет"),
        ("retirement route", "пенсионный маршрут"),
        ("retirement visa", "пенсионная виза"),
        ("passive income", "пассивный доход"),
        ("salary / qualification", "доходу и квалификации"),
        ("Самый сильный fit", "Самое сильное совпадение"),
        ("casual", "простой"),
        ("visa, work permit and residence permit", "виза, разрешение на работу и разрешение на проживание"),
        ("resident visa, work permit, Alien Resident Certificate и re-entry permit", "резидентская виза, разрешение на работу, Alien Resident Certificate и разрешение на повторный въезд"),
        ("work permit и residence permit", "разрешение на работу и разрешение на проживание"),
        ("official portal, guidelines", "официальный портал и правила"),
        ("short visit правилам", "правилам короткого визита"),
        ("visitor permit", "разрешению на въезд"),
        ("virtual work residence", "резидентскому маршруту для удалённой работы"),
        ("identity, citizenship и визовым сервисам", "идентификационным, гражданским и визовым сервисам"),
        ("English widely spoken", "английский широко используется"),
        ("MM2H visa program", "программа MM2H"),
        ("Modern infrastructure", "современная инфраструктура"),
        ("Very affordable", "доступная стоимость жизни"),
        ("Great food scene", "сильная гастрономическая сцена"),
        ("Near Singapore", "рядом с Сингапуром"),
        ("Humidity year-round", "влажность круглый год"),
        ("Минусervative laws", "консервативные законы"),
        ("Conservative laws", "консервативные законы"),
        ("Traffic in KL", "пробки в Куала-Лумпуре"),
        ("Limited nightlife", "ограниченная ночная жизнь"),
        ("Visa income requirements", "требования к доходу по визе"),
        ("World-Famous Nomad Hub", "известная база для удалёнщиков"),
        ("Spiritual Culture", "духовная культура"),
        ("The #1 digital nomad destination globally, with hundreds of коворкинги and a huge international community.", "Одна из самых известных баз для удалённой работы: много коворкингов и большое международное сообщество."),
        ("Unique Hindu-Балиnese culture with daily ceremonies, temples, and a peaceful rhythm.", "Уникальная индуистско-балийская культура с церемониями, храмами и спокойным ритмом."),
        ("Modern capital with инфраструктура мирового уровня, international schools, экспат community, and best", "Современная столица с сильной инфраструктурой, международными школами, сообществом экспатов и лучшими"),
        ("international schools", "международные школы"),
        ("экспат community", "сообщество экспатов"),
        ("with инфраструктура мирового уровня", "с сильной инфраструктурой"),
        ("to live in", "для жизни в"),
        ("Best cities для жизни в", "Лучшие города для жизни в"),
        ("Лучшие города to live in Малайзия", "Лучшие города для жизни в Малайзии"),
        ("Города и районы to live in Бали", "Где жить на Бали"),
        ("Лучшие города для жизни в Малайзия", "Лучшие города для жизни в Малайзии"),
        ("Города и районы для жизни в Бали", "Где жить на Бали"),
        ("Why переезд в Бали?", "Почему стоит рассмотреть Бали?"),
        ("Why переезд в Малайзию?", "Почему стоит рассмотреть Малайзию?"),
        ("Why переезд в Таиланд?", "Почему стоит рассмотреть Таиланд?"),
        ("Why переезд во Вьетнам?", "Почему стоит рассмотреть Вьетнам?"),
        ("Why переезд в Тайвань?", "Почему стоит рассмотреть Тайвань?"),
        ("Penang is around 20% cheaper than KL for similar образ жизни quality.", "Пенанг часто примерно на 20% дешевле Куала-Лумпура при сопоставимом уровне быта."),
        ("Ubud is roughly 20–30% cheaper for accommodation.", "Убуд обычно на 20–30% дешевле по жилью."),
        ("Each area of Бали has a completely different character — choose based on your образ жизни and priorities:", "Районы Бали сильно отличаются. Выбирайте не по красивой картинке, а по ритму жизни, бюджету и рабочим задачам:"),
        ("Trendy nomad hub with the most коворкинги, cafes, surf breaks, and international community.", "Модная база для удалёнщиков с большим выбором коворкингов, кафе, серфинга и международной среды."),
        ("Compare Малайзия with other Asian countries or calculate your exact monthly budget.", "Сравните Малайзию с другими странами Азии или посчитайте свой месячный бюджет."),
        ("Calculate your exact monthly budget.", "Посчитайте свой месячный бюджет."),
        ("Select your destination country, city and образ жизни level.", "Выберите страну, город и уровень жизни."),
        ("Get an instant personalised monthly budget with full expense breakdown — rent, food, transport, entertainment and more.", "Получите быстрый расчёт месячного бюджета: аренда, еда, транспорт, досуг и базовые расходы."),
        ("Пенсия в Азии for retirement-style routes and долгосрочный planning.", "Пенсия в Азии — для пенсионных маршрутов, медицины, визовой устойчивости и долгосрочного планирования."),
        ("for retirement-style routes and долгосрочный planning", "для пенсионных маршрутов, медицины, визовой устойчивости и долгосрочного планирования"),
        ("retirement-style", "пенсионных"),
        ("долгосрочный planning", "долгосрочного планирования"),
        ("Образ жизни-based Results adapt to your образ жизни — budget backpacker, mid-range экспат, or comfortable professional.", "Расчёты подстраиваются под сценарий: экономный переезд, средний бюджет или комфортный профессиональный профиль."),
        ("Results adapt to your образ жизни — budget backpacker, mid-range экспат, or comfortable professional.", "Расчёты подстраиваются под сценарий: экономный переезд, средний бюджет или комфортный профессиональный профиль."),
        ("Образ жизни-based", "С учётом образа жизни"),
        ("budget backpacker", "экономный путешественник"),
        ("mid-range экспат", "экспат со средним бюджетом"),
        ("comfortable professional", "специалист с комфортным бюджетом"),
        ("Moving to Asia is one of the biggest financial and образ жизни decisions you can make.", "Переезд в Азию — это одно из самых серьёзных решений по деньгам, быту и личному ритму."),
        ("not required to have secured an offer", "не требуется иметь оффер до подачи"),
    ]
    text = replace_many(text, replacements)
    text = re.sub(r"\bstay\b", "пребывание", text)
    text = re.sub(r"\bwork permit\b", "разрешение на работу", text, flags=re.I)
    text = re.sub(r"\bresidence permit\b", "разрешение на проживание", text, flags=re.I)
    text = re.sub(
        r"Малайзия\s+offers a range of visa paths for long-term residents,\s*удалёнщиков,\s*and retirees\. Here are the key options:",
        "У Малайзии есть несколько визовых маршрутов: для долгого проживания, удалённой работы и пенсионного сценария. Начинать лучше с этих вариантов:",
        text,
    )
    text = re.sub(
        r"With a cost of living significantly lower than Singapore next door,\s*yet similar infrastructure quality,\s*Малайзия offers exceptional value for экспатов and удалёнщиков who want Southeast Asian convenience without sacrificing urban comforts\.",
        "Малайзия заметно дешевле соседнего Сингапура, но при этом даёт сильную городскую инфраструктуру. Для экспатов и удалённых специалистов это часто хороший баланс: Юго-Восточная Азия без резкого отказа от городского комфорта.",
        text,
    )
    text = re.sub(
        r"Малайзия offers diverse living environments from the metropolitan capital to island retreats and border cities:",
        "Малайзия даёт несколько разных сценариев жизни: большой город, островной ритм и спокойные приграничные города:",
        text,
    )
    text = re.sub(
        r"Малайзия offers a range of visa paths for long-term residents,\s*удалёнщиков,\s*and retirees\. Here are the key options:",
        "У Малайзии есть несколько визовых маршрутов: для долгого проживания, удалённой работы и пенсионного сценария. Начинать лучше с этих вариантов:",
        text,
    )
    text = re.sub(
        r"Бали is the world.?s most famous digital nomad destination\. The island offers an extraordinary combination of low cost, natural beauty, spiritual culture, and a thriving international community\. Canggu, Ubud, and Seminyak each have distinct personalities to match every образ жизни\.",
        "Бали давно стал одной из самых известных баз для удалённой работы. Его выбирают не только из-за цены: здесь сходятся океан, природа, индуистская культура, кафе-среда и большое международное сообщество. Чангу, Убуд и Семиньяк дают очень разный ритм жизни.",
        text,
    )
    text = re.sub(
        r"Бали is the world&#8217;s most famous digital nomad destination\. The island offers an extraordinary combination of low cost, natural beauty, spiritual culture, and a thriving international community\. Canggu, Ubud, and Seminyak each have distinct personalities to match every образ жизни\.",
        "Бали давно стал одной из самых известных баз для удалённой работы. Его выбирают не только из-за цены: здесь сходятся океан, природа, индуистская культура, кафе-среда и большое международное сообщество. Чангу, Убуд и Семиньяк дают очень разный ритм жизни.",
        text,
    )
    text = re.sub(
        r"Whether you.?re drawn to the surf and co-working scene of Canggu, the rice terraces and spiritual atmosphere of Ubud, or the upscale beach clubs of Seminyak, Бали delivers a образ жизни quality that is hard to match anywhere else in the world at this price point\.",
        "Если нужен серфинг и плотная рабочая среда, чаще смотрят Чангу. Если важнее спокойствие, рисовые террасы и культурная атмосфера — Убуд. Если хочется более дорогого пляжного быта — Семиньяк. Но во всех трёх случаях визу, район и бюджет нужно считать заранее.",
        text,
    )
    text = re.sub(
        r"Whether you&#8217;re drawn to the surf and co-working scene of Canggu, the rice terraces and spiritual atmosphere of Ubud, or the upscale beach clubs of Seminyak, Бали delivers a образ жизни quality that is hard to match anywhere else in the world at this price point\.",
        "Если нужен серфинг и плотная рабочая среда, чаще смотрят Чангу. Если важнее спокойствие, рисовые террасы и культурная атмосфера — Убуд. Если хочется более дорогого пляжного быта — Семиньяк. Но во всех трёх случаях визу, район и бюджет нужно считать заранее.",
        text,
    )
    return text


def polish_ru_data(value):
    if isinstance(value, str):
        return polish_ru_text(value)
    if isinstance(value, list):
        return [polish_ru_data(item) for item in value]
    if isinstance(value, tuple):
        return tuple(polish_ru_data(item) for item in value)
    if isinstance(value, dict):
        return {key: polish_ru_data(item) for key, item in value.items()}
    return value


RU_HEADING_KEEP_UPPER = {
    "DTV",
    "LTR",
    "SRRV",
    "MM2H",
    "DE",
    "FAQ",
    "E33G",
    "ONE",
    "UAE",
    "ОАЭ",
    "ETA",
}


def sentence_case_ru_heading_text(text: str) -> str:
    if not re.search(r"[А-Яа-яЁё]", text):
        return text
    if text.strip().isupper() and len(text.strip()) <= 24:
        return text
    lowered = text.lower()
    for token in RU_HEADING_KEEP_UPPER:
        lowered = re.sub(rf"\b{re.escape(token.lower())}\b", token, lowered, flags=re.I)
    proper_forms = {"Азия", "Азии", "Бали", "Малайзия", "Малайзию", "Малайзии", "Таиланд", "Таиланду", "Таиланде", "Вьетнам", "Вьетнаму", "Вьетнаме", "Тайвань", "Тайваню", "Тайване", "Япония", "Японию", "Японии", "Камбоджа", "Камбоджу", "Камбодже", "Филиппины", "Филиппинам", "Филиппинах", "Сингапур", "Сингапуре", "ОАЭ"}
    for forms in COUNTRY_FORMS_RU.values():
        proper_forms.update(forms)
    for token in sorted(proper_forms, key=len, reverse=True):
        lowered = re.sub(rf"\b{re.escape(token.lower())}\b", token, lowered, flags=re.I)
    first = re.search(r"[A-Za-zА-Яа-яЁё]", lowered)
    if not first:
        return lowered
    idx = first.start()
    return lowered[:idx] + lowered[idx].upper() + lowered[idx + 1 :]


def sentence_case_ru_headings(html_text: str) -> str:
    def repl(match: re.Match) -> str:
        open_tag, inner, close_tag = match.groups()
        if "<" in inner:
            return match.group(0)
        return f"{open_tag}{sentence_case_ru_heading_text(inner)}{close_tag}"

    return re.sub(r"(<h[1-4]\b[^>]*>)([^<]+)(</h[1-4]>)", repl, html_text)


def normalized_content_row(row: sqlite3.Row | dict) -> dict:
    data = dict(row)
    for key in ("title", "content", "excerpt"):
        if data.get(key):
            data[key] = normalize_rendered_text(str(data[key]))
    return data


def normalized_country_row(row: sqlite3.Row | dict) -> dict:
    data = normalized_content_row(row)
    for key in ("title", "content"):
        if data.get(key):
            data[key] = str(data[key]).replace("2025", "2026")
    return data


def localized_country_context_labels(lang: str) -> dict[str, str]:
    if lang != "ru":
        return {
            "facts_title": "Country Facts For Relocation Planning",
            "capital": "Capital",
            "currency": "Currency",
            "languages": "Languages",
            "internet": "Internet Users",
            "life_expectancy": "Life Expectancy",
            "wb_year": "World Bank Year",
            "facts_note": "Use these facts as planning context, then compare visas, housing and healthcare before making a paid commitment.",
            "explore_next": "Explore Next",
        }
    return {
        "facts_title": "Факты о стране для планирования переезда",
        "capital": "Столица",
        "currency": "Валюта",
        "languages": "Языки",
        "internet": "Пользователи интернета",
        "life_expectancy": "Ожидаемая продолжительность жизни",
        "wb_year": "Год данных World Bank",
        "facts_note": "Используйте эти факты как базовый контекст, а затем уже сравнивайте визы, жильё и медицину до любых платных решений.",
        "explore_next": "Что посмотреть дальше",
    }


RU_COUNTRY_FACT_VALUES = {
    "move-to-thailand": {"capital": "Бангкок", "languages": "тайский"},
    "move-to-malaysia": {"capital": "Куала-Лумпур", "languages": "малайский, английский"},
    "move-to-bali": {"capital": "Джакарта", "languages": "индонезийский"},
    "move-to-vietnam": {"capital": "Ханой", "languages": "вьетнамский"},
    "move-to-taiwan": {"capital": "Тайбэй", "languages": "китайский"},
    "move-to-japan": {"capital": "Токио", "languages": "японский"},
    "move-to-china": {"capital": "Пекин", "languages": "китайский"},
    "move-to-singapore": {"capital": "Сингапур", "languages": "английский, малайский, китайский, тамильский"},
    "move-to-south-korea": {"capital": "Сеул", "languages": "корейский"},
    "move-to-philippines": {"capital": "Манила", "languages": "филиппинский, английский"},
    "move-to-uae": {"capital": "Абу-Даби", "languages": "арабский, английский"},
    "move-to-cambodia": {"capital": "Пномпень", "languages": "кхмерский"},
    "move-to-sri-lanka": {"capital": "Шри-Джаяварденепура-Котте", "languages": "сингальский, тамильский"},
    "move-to-india": {"capital": "Нью-Дели", "languages": "хинди, английский"},
    "move-to-nepal": {"capital": "Катманду", "languages": "непальский"},
    "move-to-laos": {"capital": "Вьентьян", "languages": "лаосский"},
    "move-to-kazakhstan": {"capital": "Астана", "languages": "казахский, русский"},
    "move-to-brunei": {"capital": "Бандар-Сери-Бегаван", "languages": "малайский"},
    "move-to-myanmar": {"capital": "Нейпьидо", "languages": "бирманский"},
    "move-to-uzbekistan": {"capital": "Ташкент", "languages": "узбекский"},
}


def country_facts_for_display(facts: sqlite3.Row | dict | None, slug: str, lang: str) -> dict | sqlite3.Row | None:
    if not facts or lang != "ru":
        return facts
    data = dict(facts)
    data.update(RU_COUNTRY_FACT_VALUES.get(slug, {}))
    return data


@app.route("/")
def home():
    row = page_or_404("__home__")
    return render_page_row(row, breadcrumbs=[])


@app.route("/ru/")
def ru_home():
    source = page_or_404("__home__")
    title, content = localized_simple_page_content("__home__", source["title"], source["content"])
    row = localized_page_dict(slug="ru-home", title=title, content=content, link="/ru/")
    return render_page_row(
        row,
        lang="ru",
        canonical_path="/ru/",
        alternates=localized_page_alternates(en_path="/", ru_path="/ru/"),
        breadcrumbs=[],
    )


@app.route("/countries/")
def countries_index():
    row = page_or_404("countries")
    return render_page_row(row, breadcrumbs=[])


@app.route("/ru/countries/")
def ru_countries_index():
    source = page_or_404("countries")
    title, content = localized_simple_page_content("countries", source["title"], source["content"])
    row = localized_page_dict(slug="ru-countries", title=title, content=content, link="/ru/countries/")
    return render_page_row(
        row,
        lang="ru",
        canonical_path="/ru/countries/",
        alternates=localized_page_alternates(en_path="/countries/", ru_path="/ru/countries/"),
        breadcrumbs=[],
    )


@app.route("/countries/<slug>/")
def country(slug: str):
    source = page_or_404(slug, parent="countries")
    row = normalized_country_row(source)
    facts = one("SELECT * FROM country_facts WHERE slug = ?", (slug,))
    path = local_path(row["link"] or request.path)
    internal_links = internal_links_for_page(row, current_path=path)
    depth_panel_data = content_depth_panel(path, row, lang="en")
    source_panel_data = page_source_panel(path, lang="en")
    quality_panel_data = content_quality_panel(path, row, lang="en")
    schema = [
        breadcrumb_schema([("Countries", "/countries/")], row["title"], path),
        organization_schema(),
        website_schema(),
        country_schema(row, facts, path),
        trust_page_schema(row["title"], path),
    ]
    depth_schema = depth_panel_schema(depth_panel_data, path, lang="en")
    if depth_schema:
        schema.append(depth_schema)
    item_list = item_list_schema(f"Internal links for {strip_html(row['title'])}", internal_links)
    if item_list:
        schema.append(item_list)
    if source_panel_data:
        source_list = item_list_schema(f"Official sources for {strip_html(row['title'])}", source_panel_data["sources"])
        if source_list:
            schema.append(source_list)
    seo = seo_payload(
        title=row["title"],
        description=country_meta_description(row, facts),
        canonical_path=path,
        alternates=localized_page_alternates(en_path=f"/countries/{slug}/", ru_path=f"/ru/countries/{slug}/"),
        schema=schema,
    )
    return render_template(
        "country.html",
        page=row,
        facts=country_facts_for_display(facts, slug, "en"),
        seo=seo,
        breadcrumbs=[("Countries", "/countries/")],
        internal_links=internal_links,
        trust_panel=page_trust_panel(path, lang="en"),
        source_panel=source_panel_data,
        depth_panel=depth_panel_data,
        quality_panel=quality_panel_data,
        labels=localized_country_context_labels("en"),
    )


@app.route("/ru/countries/<slug>/")
def ru_country(slug: str):
    source = page_or_404(slug, parent="countries")
    source = normalized_country_row(source)
    facts = one("SELECT * FROM country_facts WHERE slug = ?", (slug,))
    title = f"Переезд в {ru_country_accusative(slug)}: полный гид 2026"
    content = ru_country_article(slug, facts)
    row = localized_page_dict(slug=f"ru-{slug}", title=title, content=content, link=f"/ru/countries/{slug}/", parent="countries")
    row = polish_ru_data(row)
    row["content"] = sentence_case_ru_headings(row["content"])
    row["content"] = polish_ru_text(row["content"])
    path = f"/ru/countries/{slug}/"
    internal_links = internal_links_for_page(row, current_path=path)
    depth_panel_data = content_depth_panel(path, row, lang="ru")
    source_panel_data = page_source_panel(path, lang="ru")
    quality_panel_data = content_quality_panel(path, row, lang="ru")
    internal_links = polish_ru_data(internal_links)
    depth_panel_data = polish_ru_data(depth_panel_data)
    source_panel_data = polish_ru_data(source_panel_data)
    quality_panel_data = polish_ru_data(quality_panel_data)
    schema = [
        breadcrumb_schema([("Страны", "/ru/countries/")], row["title"], path),
        organization_schema(),
        website_schema(),
        country_schema(source, facts, path),
        trust_page_schema(row["title"], path),
    ]
    depth_schema = depth_panel_schema(depth_panel_data, path, lang="ru")
    if depth_schema:
        schema.append(depth_schema)
    item_list = item_list_schema(f"Internal links for {strip_html(row['title'])}", internal_links)
    if item_list:
        schema.append(item_list)
    if source_panel_data:
        source_list = item_list_schema(f"Official sources for {strip_html(row['title'])}", source_panel_data["sources"])
        if source_list:
            schema.append(source_list)
    seo = seo_payload(
        title=row["title"],
        description=country_meta_description_ru(slug, row["title"], facts),
        lang="ru",
        canonical_path=path,
        alternates=localized_page_alternates(en_path=f"/countries/{slug}/", ru_path=path),
        schema=schema,
    )
    return render_template(
        "country.html",
        page=row,
        facts=country_facts_for_display(facts, slug, "ru"),
        seo=seo,
        breadcrumbs=[("Страны", "/ru/countries/")],
        internal_links=internal_links,
        lang_code="ru",
        trust_panel=polish_ru_data(page_trust_panel(path, lang="ru")),
        source_panel=source_panel_data,
        depth_panel=depth_panel_data,
        quality_panel=quality_panel_data,
        labels=localized_country_context_labels("ru"),
        home_label="Главная",
    )


@app.route("/tools/")
def tools_index():
    row = page_or_404("tools")
    return render_page_row(row, breadcrumbs=[])


@app.route("/ru/tools/")
def ru_tools_index():
    source = page_or_404("tools")
    title, content = localized_simple_page_content("tools", source["title"], source["content"])
    row = localized_page_dict(slug="ru-tools", title=title, content=content, link="/ru/tools/")
    return render_page_row(
        row,
        lang="ru",
        canonical_path="/ru/tools/",
        alternates=localized_page_alternates(en_path="/tools/", ru_path="/ru/tools/"),
        breadcrumbs=[],
    )


@app.route("/tools/<slug>/")
def tool(slug: str):
    row = page_or_404(slug, parent="tools")
    return render_page_row(row,
                           breadcrumbs=[("Tools", "/tools/")])


@app.route("/ru/tools/<slug>/")
def ru_tool(slug: str):
    source = page_or_404(slug, parent="tools")
    title, content = localized_simple_page_content(slug, source["title"], source["content"])
    row = localized_page_dict(slug=f"ru-{slug}", title=title, content=content, link=f"/ru/tools/{slug}/", parent="tools")
    return render_page_row(
        row,
        lang="ru",
        canonical_path=f"/ru/tools/{slug}/",
        alternates=localized_page_alternates(en_path=f"/tools/{slug}/", ru_path=f"/ru/tools/{slug}/"),
        breadcrumbs=[("Инструменты", "/ru/tools/")],
    )


BCM_ARTICLE_STYLE = """
<style>
.bcm-hero{background:linear-gradient(135deg,#0a1628 0%,#1a3a5c 100%);color:#fff;padding:48px 32px;border-radius:16px;text-align:center;margin-bottom:36px}
.bcm-hero .badge{display:inline-block;background:rgba(255,255,255,.15);border:1px solid rgba(255,255,255,.3);color:#fff;font-size:11px;font-weight:700;letter-spacing:1.6px;padding:6px 16px;border-radius:20px;margin-bottom:20px;text-transform:uppercase}
.bcm-hero h1{font-size:clamp(28px,4vw,44px);font-weight:800;margin:0 0 16px;line-height:1.15}.bcm-hero p{font-size:17px;opacity:.9;max-width:760px;margin:0 auto}
.bcm-stats{display:flex;justify-content:center;gap:34px;flex-wrap:wrap;margin-top:26px}.bcm-stats strong{display:block;font-size:28px;color:#5db8f5}.bcm-stats span{font-size:12px;text-transform:uppercase;letter-spacing:1px;opacity:.75}
.bcm-note{background:#fff8e8;border:1px solid #f4c56b;border-radius:10px;padding:18px 22px;margin:28px 0;color:#6b4600}.bcm-table-wrap{overflow-x:auto;margin:28px 0}.bcm-table{width:100%;border-collapse:collapse;font-size:14px}.bcm-table th{background:#0a1628;color:#fff;padding:12px 14px;text-align:left}.bcm-table td{padding:12px 14px;border-bottom:1px solid #e7edf5;vertical-align:top}.bcm-table .rank{font-weight:800;color:#c0392b}
.bcm-country{border:1px solid #e1e8f3;border-radius:12px;padding:28px;margin:28px 0;background:#fff}.bcm-country h2{margin-top:0}.bcm-stats-bar{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;background:#f8fafc;border-radius:8px;padding:16px;margin:18px 0}.bcm-stat-item{text-align:center}.bcm-stat-item .val{display:block;font-size:19px;font-weight:800;color:#c0392b}.bcm-stat-item .lbl{font-size:11px;text-transform:uppercase;letter-spacing:.5px;color:#687385}
.bcm-cols{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin:18px 0}.bcm-pros,.bcm-cons{border-radius:8px;padding:16px}.bcm-pros{background:#f0fdf4}.bcm-cons{background:#fff8f8}.bcm-pros h3,.bcm-cons h3{font-size:14px;text-transform:uppercase;letter-spacing:1px;margin-top:0}.bcm-pros h3{color:#15803d}.bcm-cons h3{color:#b91c1c}.bcm-faq-item{border-bottom:1px solid #e7edf5;padding:18px 0}.bcm-faq-item h3{font-size:18px;margin:0 0 8px}
@media(max-width:700px){.bcm-cols{grid-template-columns:1fr}.bcm-country{padding:20px}.bcm-hero{padding:34px 18px}}
</style>
"""


def cost_of_living_asia_article(lang: str = "en") -> tuple[str, str]:
    if lang == "ru":
        return (
            "Стоимость жизни в Азии в 2026 году: как считать бюджет до переезда",
            """
<style>
.bcm-hero{background:linear-gradient(135deg,#0a1628 0%,#1a3a5c 100%);color:#fff;padding:48px 32px;border-radius:16px;text-align:center;margin-bottom:36px}
.bcm-hero .badge{display:inline-block;background:rgba(255,255,255,.15);border:1px solid rgba(255,255,255,.3);color:#fff;font-size:11px;font-weight:700;letter-spacing:1.6px;padding:6px 16px;border-radius:20px;margin-bottom:20px;text-transform:uppercase}
.bcm-hero h1{font-size:clamp(28px,4vw,44px);font-weight:800;margin:0 0 16px;line-height:1.15}
.bcm-hero p{font-size:17px;opacity:.9;max-width:760px;margin:0 auto}
.bcm-stats{display:flex;justify-content:center;gap:34px;flex-wrap:wrap;margin-top:26px}.bcm-stats strong{display:block;font-size:28px;color:#5db8f5}.bcm-stats span{font-size:12px;text-transform:uppercase;letter-spacing:1px;opacity:.75}
.bcm-note{background:#fff8e8;border:1px solid #f4c56b;border-radius:10px;padding:18px 22px;margin:28px 0;color:#6b4600}
.bcm-table-wrap{overflow-x:auto;margin:28px 0}.bcm-table{width:100%;border-collapse:collapse;font-size:14px}.bcm-table th{background:#0a1628;color:#fff;padding:12px 14px;text-align:left}.bcm-table td{padding:12px 14px;border-bottom:1px solid #e7edf5;vertical-align:top}.bcm-table .rank{font-weight:800;color:#c0392b}
.bcm-country{border:1px solid #e1e8f3;border-radius:12px;padding:28px;margin:28px 0;background:#fff}.bcm-country h2{margin-top:0}.bcm-stats-bar{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;background:#f8fafc;border-radius:8px;padding:16px;margin:18px 0}.bcm-stat-item{text-align:center}.bcm-stat-item .val{display:block;font-size:19px;font-weight:800;color:#c0392b}.bcm-stat-item .lbl{font-size:11px;text-transform:uppercase;letter-spacing:.5px;color:#687385}
.bcm-cols{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin:18px 0}.bcm-pros,.bcm-cons{border-radius:8px;padding:16px}.bcm-pros{background:#f0fdf4}.bcm-cons{background:#fff8f8}.bcm-pros h3,.bcm-cons h3{font-size:14px;text-transform:uppercase;letter-spacing:1px;margin-top:0}.bcm-pros h3{color:#15803d}.bcm-cons h3{color:#b91c1c}
@media(max-width:700px){.bcm-cols{grid-template-columns:1fr}.bcm-country{padding:20px}.bcm-hero{padding:34px 18px}}
</style>
<div class="bcm-hero">
  <div class="badge">Проверено в мае 2026 - бюджет и визовая логика</div>
  <h1>Стоимость Жизни В Азии В 2026 Году</h1>
  <p>Дешёвая аренда сама по себе ничего не решает. Для переезда важнее полный месяц: жильё, депозит, виза, страховка, связь, транспорт, рабочая инфраструктура и запас на ошибку.</p>
  <div class="bcm-stats">
    <div><strong>$700+</strong><span>реалистичный старт</span></div>
    <div><strong>10</strong><span>стран для сравнения</span></div>
    <div><strong>2026</strong><span>обновлённые правила</span></div>
  </div>
</div>
<div class="bcm-note"><strong>Короткий вывод:</strong> Азия может быть доступной, но не вся Азия дешёвая и не каждый дешёвый город подходит для жизни. Если бюджет сходится только при идеальной аренде и без визовых расходов, это не план, а надежда.</div>
<h2>Как Считать Cost Of Living Asia Без Самообмана</h2>
<p>Главная ошибка простая: люди сравнивают страну по цене квартиры. Это удобно, но плохо работает. В Бангкоке можно найти жильё дешевле, чем в Токио, но если вам нужен сильный госпиталь рядом, международная школа, легальная long-stay логика и нормальный район, итоговая сумма быстро растёт. В Хошимине еда и транспорт могут быть очень доступными, но визовый ритм и отсутствие понятного маршрута для долгого проживания меняют картину.</p>
<p>Факт: официальные сайты обычно не публикуют «бюджет экспата». Они публикуют визовые условия, сроки пребывания, требования к страховке, доходу и документам. Значит, стоимость жизни нужно считать в два слоя. Первый слой - редакционная оценка расходов по городу. Второй - официальная проверка: сколько стоит легально оставаться в стране и какие документы нужны, чтобы этот план не развалился.</p>
<h2>Быстрое сравнение: месячный бюджет по странам</h2>
<div class="bcm-table-wrap"><table class="bcm-table">
<thead><tr><th>#</th><th>Страна</th><th>Бюджет solo / месяц</th><th>Что обычно двигает бюджет</th><th>Что проверить по визе</th></tr></thead>
<tbody>
<tr><td class="rank">1</td><td>Вьетнам</td><td>$700-1,300</td><td>Город решает многое: Дананг проще, Хошимин дороже.</td><td>Срок eVisa и понятный ритм продления или выезда.</td></tr>
<tr><td class="rank">2</td><td>Таиланд</td><td>$900-1,800</td><td>Бангкок, Чиангмай и острова дают разные бюджеты.</td><td>DTV, LTR или другой маршрут должны совпадать с реальным сроком stay.</td></tr>
<tr><td class="rank">3</td><td>Малайзия</td><td>$900-1,900</td><td>Куала-Лумпур удобен, Пенанг может быть спокойнее и дешевле.</td><td>DE Rantau, MM2H или рабочий маршрут.</td></tr>
<tr><td class="rank">4</td><td>Индонезия / Бали</td><td>$1,100-2,200</td><td>Популярные туристические районы быстро разгоняют аренду.</td><td>Remote Worker Visa или другой подтверждённый stay permit.</td></tr>
<tr><td class="rank">5</td><td>Тайвань</td><td>$1,400-2,600</td><td>Тайбэй создаёт основное давление; города меньше обычно проще.</td><td>Gold Card или рабочая логика.</td></tr>
<tr><td class="rank">6</td><td>Япония</td><td>$1,800-3,200</td><td>Токио поднимает аренду и повседневные расходы.</td><td>Digital Nomad route даёт шесть месяцев без продления.</td></tr>
</tbody></table></div>
<div class="bcm-country">
<h2>Вьетнам: низкие расходы, но внимательно к stay-логике</h2>
<div class="bcm-stats-bar"><div class="bcm-stat-item"><span class="val">$700-1,300</span><span class="lbl">solo / месяц</span></div><div class="bcm-stat-item"><span class="val">Дананг</span><span class="lbl">более спокойная база</span></div><div class="bcm-stat-item"><span class="val">eVisa</span><span class="lbl">ключевая проверка</span></div></div>
<p>Vietnam часто выглядит как самый рациональный вариант: еда недорогая, интернет в крупных городах нормальный, аренда в Дананге и Ханое может быть мягче, чем в Таиланде или Малайзии. Но это не «переезд без вопросов». Для долгого проживания важен визовый ритм. Если человек работает удалённо и хочет просто протестировать Азию, Вьетнам может быть сильным стартом. Если нужна предсказуемая резиденция на годы, нужно осторожнее.</p>
</div>
<div class="bcm-country">
<h2>Thailand: Сильный Баланс, Но Не Всегда Самый Дешёвый</h2>
<p>Таиланд хорош не потому, что он самый дешёвый. Он хорош балансом: медицина, еда, города, перелёты, expat-среда, выбор жилья. Но Бангкок, Пхукет, Самуи и Чиангмай - разные бюджеты. На практике Таиланд часто выигрывает у более дешёвых стран, если человеку важны госпитали, транспорт, сервисы и возможность быстро решить бытовые вопросы.</p>
<p>Смысл: считать нужно не только rent. Виза, страховка, медицина и район проживания могут сделать «дешёвый Таиланд» совсем не дешёвым. Перед депозитом за квартиру стоит сверить DTV, LTR или другой маршрут на официальных страницах.</p>
</div>
<div class="bcm-country">
<h2>Malaysia: Лучше Для Предсказуемого Городского Быта</h2>
<p>Малайзия часто проигрывает в романтике, но выигрывает в спокойной логике. Английский широко используется, Куала-Лумпур удобен, медицина сильная, инфраструктура понятная. Для семьи или человека, который не хочет каждый день решать бытовые мелочи, это важнее, чем сэкономить ещё $150 в месяц.</p>
<p>Но и здесь нельзя обобщать. DE Rantau подходит не всем, MM2H живёт по своим финансовым требованиям, а туристический сценарий не заменяет долгосрочную стратегию. Если официальный маршрут не совпадает с доходом и документами, красивый бюджет не спасает.</p>
</div>
<div class="bcm-cols">
  <div class="bcm-pros"><h3>Где Cost Of Living Asia Помогает</h3><ul><li>быстро отсеять страны, где бюджет явно не сходится;</li><li>увидеть разницу между «дешево жить» и «реально переехать»;</li><li>сравнить страны до того, как вы платите за жильё и билеты.</li></ul></div>
  <div class="bcm-cons"><h3>Где Нужна Ручная Проверка</h3><ul><li>визы, продления и разрешённая деятельность;</li><li>страховка, медицина, dependants и школьные расходы;</li><li>аренда в конкретном районе и сезонные скачки цен.</li></ul></div>
</div>
<h2>FAQ</h2>
<div class="bcm-faq-item"><h3>Можно Ли Жить В Азии На $1,000 В Месяц?</h3><p>Да, но не везде и не в любом сценарии. Для одного человека это возможно во Вьетнаме, Камбодже, части Таиланда или Малайзии. Для семьи, Токио, Сингапура, дорогих районов Бали или медицински чувствительного сценария - обычно нет.</p></div>
<div class="bcm-faq-item"><h3>Какая Страна В Азии Самая Дешёвая Для Жизни?</h3><p>Если смотреть только на базовые расходы, часто выигрывают Камбоджа, Вьетнам и часть Индии или Непала. Если смотреть на качество инфраструктуры и визовую устойчивость, ответ меняется.</p></div>
<div class="bcm-faq-item"><h3>Почему Официальные Источники Не Дают Точную Стоимость Жизни?</h3><p>Потому что государственные сайты фиксируют правила: визы, сроки, документы, страхование, сборы. Аренда и бытовые расходы зависят от города, района, сезона и личного стандарта жизни.</p></div>
<div class="bcm-faq-item"><h3>Что Проверять Перед Переездом В Первую Очередь?</h3><p>Сначала легальный срок пребывания и возможность продления. Потом доход, страховку, жильё, медицину и город. Если начинать с пляжей и кафе, легко собрать красивый, но слабый план.</p></div>
<div class="bcm-faq-item"><h3>Нужен Ли Запас В Бюджете?</h3><p>Да. Минимум один плохой месяц: депозит, срочный перелёт, медицинский платёж, рост аренды или визовая пауза. Без запаса бюджет выглядит лучше, чем он будет ощущаться в реальности.</p></div>
""",
        )
    return (
        "Cost Of Living In Asia 2026: Real Budgets Before You Move",
        """
<style>
.bcm-hero{background:linear-gradient(135deg,#0a1628 0%,#1a3a5c 100%);color:#fff;padding:48px 32px;border-radius:16px;text-align:center;margin-bottom:36px}
.bcm-hero .badge{display:inline-block;background:rgba(255,255,255,.15);border:1px solid rgba(255,255,255,.3);color:#fff;font-size:11px;font-weight:700;letter-spacing:1.6px;padding:6px 16px;border-radius:20px;margin-bottom:20px;text-transform:uppercase}
.bcm-hero h1{font-size:clamp(28px,4vw,44px);font-weight:800;margin:0 0 16px;line-height:1.15}.bcm-hero p{font-size:17px;opacity:.9;max-width:760px;margin:0 auto}
.bcm-stats{display:flex;justify-content:center;gap:34px;flex-wrap:wrap;margin-top:26px}.bcm-stats strong{display:block;font-size:28px;color:#5db8f5}.bcm-stats span{font-size:12px;text-transform:uppercase;letter-spacing:1px;opacity:.75}
.bcm-note{background:#fff8e8;border:1px solid #f4c56b;border-radius:10px;padding:18px 22px;margin:28px 0;color:#6b4600}.bcm-table-wrap{overflow-x:auto;margin:28px 0}.bcm-table{width:100%;border-collapse:collapse;font-size:14px}.bcm-table th{background:#0a1628;color:#fff;padding:12px 14px;text-align:left}.bcm-table td{padding:12px 14px;border-bottom:1px solid #e7edf5;vertical-align:top}.bcm-table .rank{font-weight:800;color:#c0392b}
.bcm-country{border:1px solid #e1e8f3;border-radius:12px;padding:28px;margin:28px 0;background:#fff}.bcm-country h2{margin-top:0}.bcm-stats-bar{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;background:#f8fafc;border-radius:8px;padding:16px;margin:18px 0}.bcm-stat-item{text-align:center}.bcm-stat-item .val{display:block;font-size:19px;font-weight:800;color:#c0392b}.bcm-stat-item .lbl{font-size:11px;text-transform:uppercase;letter-spacing:.5px;color:#687385}
.bcm-cols{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin:18px 0}.bcm-pros,.bcm-cons{border-radius:8px;padding:16px}.bcm-pros{background:#f0fdf4}.bcm-cons{background:#fff8f8}.bcm-pros h3,.bcm-cons h3{font-size:14px;text-transform:uppercase;letter-spacing:1px;margin-top:0}.bcm-pros h3{color:#15803d}.bcm-cons h3{color:#b91c1c}
@media(max-width:700px){.bcm-cols{grid-template-columns:1fr}.bcm-country{padding:20px}.bcm-hero{padding:34px 18px}}
</style>
<div class="bcm-hero">
  <div class="badge">Updated May 2026 - Budget And Visa Reality</div>
  <h1>Cost Of Living In Asia In 2026</h1>
  <p>Cheap rent is only one line in the spreadsheet. A serious relocation budget includes visa rhythm, deposits, insurance, healthcare, transport, work setup and the cost of leaving if the plan stops working.</p>
  <div class="bcm-stats"><div><strong>$700+</strong><span>realistic start</span></div><div><strong>10</strong><span>countries compared</span></div><div><strong>2026</strong><span>rules checked</span></div></div>
</div>
<div class="bcm-note"><strong>Short answer:</strong> Asia can be affordable, but not every affordable place is a good relocation base. If your budget only works with perfect rent, no medical costs and no visa friction, it is too fragile.</div>
<h2>How To Read Cost Of Living Asia Numbers</h2>
<p>The common mistake is comparing countries by apartment price. It feels practical, but it hides the real decision. Bangkok can be much cheaper than Tokyo, but if you need strong hospitals, an international school, a stable long-stay route and a district where daily life is easy, the monthly number changes. Ho Chi Minh City can be excellent value, yet the stay logic is not the same as a proper residence route.</p>
<p>Official sources rarely publish “expat budgets”. They publish visa rules, stay length, income proof, insurance requirements and application routes. So the budget has to be read in two layers: an editorial living-cost range, then an official feasibility check. The first tells you whether the country belongs on your shortlist. The second tells you whether you can legally and calmly stay there.</p>
<h2>Quick Comparison: Monthly Budget Ranges</h2>
<div class="bcm-table-wrap"><table class="bcm-table"><thead><tr><th>#</th><th>Country</th><th>Solo Monthly Range</th><th>What Usually Decides The Budget</th><th>Visa Check Before Moving</th></tr></thead><tbody>
<tr><td class="rank">1</td><td>Vietnam</td><td>$700-1,300</td><td>Da Nang is easier; Ho Chi Minh City costs more.</td><td>eVisa length and renewal rhythm.</td></tr>
<tr><td class="rank">2</td><td>Thailand</td><td>$900-1,800</td><td>Bangkok, Chiang Mai and islands behave like different markets.</td><td>DTV, LTR or another route must match the stay.</td></tr>
<tr><td class="rank">3</td><td>Malaysia</td><td>$900-1,900</td><td>Kuala Lumpur buys comfort; Penang can be calmer.</td><td>DE Rantau, MM2H or employment logic.</td></tr>
<tr><td class="rank">4</td><td>Indonesia / Bali</td><td>$1,100-2,200</td><td>Tourist districts inflate rent fast.</td><td>Remote worker or stay permit route.</td></tr>
<tr><td class="rank">5</td><td>Taiwan</td><td>$1,400-2,600</td><td>Taipei is the pressure point; smaller cities are easier.</td><td>Gold Card or employment route.</td></tr>
<tr><td class="rank">6</td><td>Japan</td><td>$1,800-3,200</td><td>Tokyo raises housing and daily friction.</td><td>Digital Nomad is six months with no extension.</td></tr>
</tbody></table></div>
<div class="bcm-country"><h2>Vietnam: Low Cost, But The Stay Logic Matters</h2><div class="bcm-stats-bar"><div class="bcm-stat-item"><span class="val">$700-1,300</span><span class="lbl">solo/month</span></div><div class="bcm-stat-item"><span class="val">Da Nang</span><span class="lbl">easier base</span></div><div class="bcm-stat-item"><span class="val">eVisa</span><span class="lbl">key check</span></div></div><p>Vietnam is often the strongest value play: food is cheap, internet in major cities is workable, and Da Nang or Hanoi can cost much less than Thailand or Malaysia. But this is not an automatic long-term move. For a remote worker testing Asia, Vietnam can be a clean starting point. For someone needing multi-year stability, the visa rhythm needs a sober look before any housing commitment.</p></div>
<div class="bcm-country"><h2>Thailand: Strong Balance, Not Always The Cheapest</h2><p>Thailand wins because it is balanced, not because it is always the lowest-cost choice. Healthcare, food, airports, serviced apartments, coworking and expat infrastructure reduce friction. Bangkok, Phuket, Koh Samui and Chiang Mai are different budgets. A cheap Thai plan can become expensive if the visa route, insurance and neighbourhood are chosen late.</p></div>
<div class="bcm-country"><h2>Malaysia: Good For Predictable City Life</h2><p>Malaysia often looks less dramatic than Thailand or Bali, but it is practical. English is widely used, Kuala Lumpur is comfortable, healthcare is strong and the infrastructure is easy to understand. For families or people who hate daily friction, that can matter more than saving another $150 a month. Still, DE Rantau, MM2H and employment routes are different paths, not interchangeable labels.</p></div>
<div class="bcm-cols"><div class="bcm-pros"><h3>When The Numbers Help</h3><ul><li>screen countries before paying for flights or housing;</li><li>separate cheap living from a realistic relocation route;</li><li>compare cities after visa feasibility is clear.</li></ul></div><div class="bcm-cons"><h3>What Needs Manual Checking</h3><ul><li>stay length, extension and permitted work;</li><li>insurance, healthcare, dependants and school costs;</li><li>district-level rent and seasonal price jumps.</li></ul></div></div>
<h2>FAQ</h2>
<div class="bcm-faq-item"><h3>Can You Live In Asia On $1,000 A Month?</h3><p>Yes, in selected cities and with a lean setup. It is realistic for some solo scenarios in Vietnam, Cambodia, parts of Thailand or Malaysia. It is usually weak for families, Tokyo, Singapore, premium Bali areas or people with medical constraints.</p></div>
<div class="bcm-faq-item"><h3>What Is The Cheapest Country In Asia To Live In?</h3><p>If you only compare basic living costs, Cambodia, Vietnam and parts of India or Nepal often look strongest. If you include healthcare, infrastructure and visa stability, the answer changes.</p></div>
<div class="bcm-faq-item"><h3>Why Do Official Sources Not Give Exact Living Costs?</h3><p>Government pages publish rules: visas, fees, stay length, documents and insurance. Rent and daily expenses move by city, district, season and lifestyle.</p></div>
<div class="bcm-faq-item"><h3>What Should You Check First?</h3><p>Start with legal stay length and extension logic. Then check income proof, insurance, housing, healthcare and the city you would actually live in.</p></div>
<div class="bcm-faq-item"><h3>Do You Need A Budget Buffer?</h3><p>Yes. One bad month can include a deposit, urgent flight, medical bill, rent increase or visa disruption. Without a buffer, the plan looks better than it will feel.</p></div>
""",
    )


def japan_vs_taiwan_article(lang: str = "en") -> tuple[str, str]:
    if lang == "ru":
        return (
            "Япония или Тайвань для переезда в 2026 году: визы, бюджет и реальность",
            BCM_ARTICLE_STYLE + """
<div class="bcm-hero"><div class="badge">Обновлено в мае 2026 - Japan vs Taiwan</div><h1>Япония или Тайвань для переезда в 2026 году</h1><p>Если выбирать только сердцем, Япония часто победит. Если выбирать по визе, сроку, деньгам и документам, картина становится сложнее. Japan Digital Nomad Visa и Taiwan Gold Card решают разные задачи.</p><div class="bcm-stats"><div><strong>6 месяцев</strong><span>Japan Digital Nomad Visa</span></div><div><strong>1-3 года</strong><span>Taiwan Gold Card</span></div><div><strong>NT$160k</strong><span>частый salary-фильтр</span></div></div></div>
<div class="bcm-note"><strong>Короткий вывод:</strong> Япония лучше как короткий, дорогой и очень качественный тест страны. Тайвань сильнее, если вам нужен более длинный горизонт, право работать и вы реально проходите по профессиональной квалификации Gold Card. Это не спор «какая страна красивее». Это вопрос: какой официальный маршрут выдерживает ваш профиль.</div>
<h2>Japan vs Taiwan: что важно понять сразу</h2>
<p>У Японии сильный бренд. Токио, Осака, Киото, транспорт, безопасность, сервис - всё это легко превращается в желание переехать. Но официальный digital nomad route Японии специально сделан коротким. На странице <a href="https://www.mofa.go.jp/ca/fna/pagewe_000001_00046.html" rel="nofollow noopener" target="_blank">Ministry of Foreign Affairs of Japan</a> указано: срок пребывания 6 месяцев, продление не предоставляется. Там же прописаны документы по доходу и страховке.</p>
<p>Практический смысл простой: Japan Digital Nomad Visa - это не мягкий вход в резиденцию. Это легальный способ пожить и работать удалённо из Японии ограниченный срок. Хороший способ проверить страну, районы, рабочий ритм и бытовую реальность. Плохой способ строить план «поживу полгода, а потом как-нибудь останусь».</p>
<p>Тайвань устроен иначе. Официальная страница <a href="https://goldcard.nat.gov.tw/en/about/" rel="nofollow noopener" target="_blank">Taiwan Employment Gold Card</a> описывает Gold Card как 4-in-1 card: resident visa, work permit, Alien Resident Certificate и re-entry permit на срок 1-3 года. Это уже не короткая nomad-витрина, а профессиональный маршрут для людей, которые могут доказать квалификацию.</p>
<h2>Сравнение Японии и Тайваня по главным параметрам</h2>
<div class="bcm-table-wrap"><table class="bcm-table"><thead><tr><th>Критерий</th><th>Япония</th><th>Тайвань</th><th>Что это значит на практике</th></tr></thead><tbody>
<tr><td>Главный маршрут</td><td>Digital Nomad / Designated Activities</td><td>Employment Gold Card</td><td>Это разные типы визовой логики, их нельзя сравнивать как две версии одной nomad-визы.</td></tr>
<tr><td>Срок</td><td>6 месяцев, без продления</td><td>1-3 года по Gold Card</td><td>Тайвань сильнее для долгого горизонта, Япония - для короткого качественного stay.</td></tr>
<tr><td>Доход / квалификация</td><td>Годовой доход JPY 10 млн или выше</td><td>Категории Gold Card, часто salary или профессиональные доказательства</td><td>Обе страны требуют документов, а не просто желания жить в Азии.</td></tr>
<tr><td>Работа</td><td>Удалённая работа на зарубежный контур</td><td>Open work permit в рамках Gold Card</td><td>Тайвань даёт больше свободы на рынке труда, если карта одобрена.</td></tr>
<tr><td>Семья</td><td>Spouse / child route есть, но привязан к короткому сроку</td><td>Dependants возможны по правилам Gold Card</td><td>Для семьи Тайвань часто практичнее, но документы нужно сверять отдельно.</td></tr>
<tr><td>Бюджет</td><td>Обычно выше, особенно Токио</td><td>Обычно мягче, кроме дорогих районов Тайбэя</td><td>Дешевле не значит проще: всё упирается в статус и документы.</td></tr>
</tbody></table></div>
<h2>Japan Digital Nomad Visa: где сильная сторона, а где ловушка</h2>
<p>Сильная сторона Японии - предсказуемость короткого сценария. Если у вас есть подтверждаемый высокий доход, удалённая работа, страховка и понимание, что срок ограничен, маршрут честный. Он подходит человеку, который хочет пожить в Японии полгода, поработать удалённо, проверить повседневную жизнь и не строить иллюзию долгой резиденции.</p>
<p>Официальная страница MOFA указывает годовой доход JPY 10 million or more и страховое покрытие для medical treatment of injury or illness на сумму JPY 10 million or more. Это не мелкая формальность. Если доход нестабилен, страховка слабая или документы трудно объяснить, Япония перестаёт быть простой.</p>
<p>Ловушка в том, что Японию легко выбрать эмоционально. Человек сначала думает о районе в Токио, еде, поездах и безопасности. А потом выясняется, что срок всего 6 месяцев, продления нет, а семейная логистика упирается в те же рамки. Для короткого опыта - отлично. Для переезда на годы - нет, если не искать другой статус.</p>
<h2>Taiwan Gold Card: сильнее для профессионального переезда, но не для всех</h2>
<p>Taiwan Gold Card выглядит менее романтично, зато она гораздо ближе к настоящей релокации. Карта объединяет право на работу, проживание, визу и re-entry. На практике это значит: если вы проходите по квалификации, Тайвань даёт больше пространства для нормальной жизни, работы, аренды и планирования.</p>
<p>Но Gold Card нельзя называть простой визой для всех удалёнщиков. Это профессиональный фильтр. На официальной странице по salary qualification указано, что заявитель должен предоставить CV, proof of employment и один из документов, подтверждающих среднюю месячную зарплату не ниже NT$160,000. Там же отдельно сказано, что bank receipts from account balance, cryptocurrency, stocks и property income не могут использоваться как proof. Источник: <a href="https://goldcard.nat.gov.tw/en/faq/how-do-i-meet-the-salary-requirements-of-the-gold-card-application/" rel="nofollow noopener" target="_blank">Taiwan Gold Card salary requirements</a>.</p>
<p>Практически это важно. Если у вас сильная зарплатная история, понятный работодатель, налоговые документы или профессиональная категория, Тайвань может быть очень сильным вариантом. Если доход есть, но он разбросан по крипте, дивидендам, наличным переводам или неформальным контрактам, путь может быть сложнее, чем кажется.</p>
<h2>Кому лучше подойдёт Япония</h2>
<p>Япония лучше человеку, который не пытается превратить short stay в долгую эмиграцию. Например: удалённый специалист с высоким доходом хочет провести 6 месяцев в Токио, Осаке или Фукуоке, проверить быт, поработать в другом часовом поясе и вернуться или дальше выбирать маршрут. В таком сценарии ограничение не мешает. Оно даже помогает: рамки ясные, ожидания честные.</p>
<p>Япония хуже, если вам нужна резиденция, школа для детей, долгий контракт аренды, местная работа или план на 2-3 года. Тут digital nomad route не закрывает задачу. Нужны другие основания: работа, бизнес, учёба, family route или иной статус. Их нужно изучать отдельно, а не додумывать поверх Digital Nomad Visa.</p>
<h2>Кому лучше подойдёт Тайвань</h2>
<p>Тайвань лучше для специалистов, которым нужен не просто красивый опыт, а рабочая и резидентская логика вместе. Tech, finance, science, digital, education, law, culture, architecture и другие категории Gold Card могут быть релевантны, если есть документы. Не впечатление о себе как о «сильном специалисте», а доказательства: зарплата, опыт, достижения, контракты, налоговые формы.</p>
<p>Тайвань хуже, если вы ищете самую простую страну для жизни в Азии, не хотите собирать документы или не проходите по профессиональным критериям. В таком случае лучше смотреть Таиланд, Малайзию, Вьетнам или другие маршруты, где entry logic может быть мягче. Тайвань хорош, но он не обязан подходить каждому.</p>
<h2>Бюджет: Japan vs Taiwan без красивых иллюзий</h2>
<p>По бытовым расходам Тайвань обычно мягче. Тайбэй может быть дорогим, но всё равно часто проще, чем Токио, если сравнивать аренду, питание, транспорт и повседневную жизнь. В Японии качество высокое, но за него платишь: жильё, депозиты, страховка, мебель, транспорт, первый месяц, район. Особенно если хочется жить не «как можно дешевле», а нормально.</p>
<p>Но решать только по бюджету нельзя. Дешевле жить на Тайване не значит легче получить Gold Card. Дороже жить в Японии не значит, что Япония хуже. Вопрос в совпадении: срок, документы, доход, семья, работа, город и запас денег. Если один из этих пунктов не сходится, страна может нравиться сколько угодно - план всё равно слабый.</p>
<div class="bcm-cols"><div class="bcm-pros"><h3>Япония подходит</h3><ul><li>для короткого premium stay на 6 месяцев;</li><li>для людей с подтверждаемым доходом JPY 10 млн+ в год;</li><li>для тех, кто не рассчитывает на продление;</li><li>для проверки страны перед более серьёзным маршрутом.</li></ul></div><div class="bcm-cons"><h3>Тайвань подходит</h3><ul><li>для квалифицированных специалистов;</li><li>для горизонта 1-3 года;</li><li>для тех, кому нужна работа и резидентская логика вместе;</li><li>для людей с чистыми salary / qualification документами.</li></ul></div></div>
<h2>Какие официальные источники проверить перед решением</h2>
<p>Для Японии сначала открывайте <a href="https://www.mofa.go.jp/ca/fna/pagewe_000001_00046.html" rel="nofollow noopener" target="_blank">MOFA Digital Nomad page</a> и страницу <a href="https://www.moj.go.jp/isa/applications/status/designatedactivities53_00001.html" rel="nofollow noopener" target="_blank">Immigration Services Agency</a>. Там важны срок, no extension, income proof, insurance и activity.</p>
<p>Для Тайваня начинайте с <a href="https://goldcard.nat.gov.tw/en/about/" rel="nofollow noopener" target="_blank">официального объяснения Gold Card</a>, затем проверьте <a href="https://goldcard.nat.gov.tw/en/application/" rel="nofollow noopener" target="_blank">application information</a> и отдельные FAQ по квалификации. Если вы идёте по зарплате, salary FAQ обязателен.</p>
<h2>FAQ</h2>
<div class="bcm-faq-item"><h3>Japan Digital Nomad Visa можно продлить?</h3><p>По официальной странице MOFA срок указан как 6 месяцев, и прямо сказано, что продление не предоставляется. Планировать продление как обычный сценарий нельзя.</p></div>
<div class="bcm-faq-item"><h3>Taiwan Gold Card это digital nomad visa?</h3><p>Нет в прямом смысле. Это профессиональный маршрут 4-in-1: work permit, resident visa, ARC и re-entry permit. Он может подойти удалённому специалисту, но только если профиль проходит требования Gold Card.</p></div>
<div class="bcm-faq-item"><h3>Что дешевле: Япония или Тайвань?</h3><p>Обычно Тайвань дешевле и мягче по бюджету, особенно если сравнивать не премиальные районы. Но бюджет не заменяет визовую пригодность.</p></div>
<div class="bcm-faq-item"><h3>Что лучше для семьи?</h3><p>Тайвань часто практичнее из-за более длинного горизонта и dependants-логики Gold Card. Но семейные документы, страховку, школу и медицину нужно проверять отдельно. Японский digital nomad route для семьи тоже привязан к короткому сроку.</p></div>
<div class="bcm-faq-item"><h3>Что выбрать: Japan vs Taiwan?</h3><p>Если нужен короткий качественный опыт и вы проходите японские требования - Япония. Если нужен горизонт на годы, право работать и вы проходите Gold Card - Тайвань. Если не проходите ни один маршрут, лучше сравнить другие страны Азии, а не подгонять факты под желание.</p></div>
""",
        )
    return (
        "Japan vs Taiwan For Expats In 2026: Visa, Cost And Long-Stay Reality",
        BCM_ARTICLE_STYLE + """
<div class="bcm-hero"><div class="badge">Updated May 2026 - Japan vs Taiwan</div><h1>Japan vs Taiwan For Expats In 2026</h1><p>Both countries are strong, but they solve different problems. Japan is a short, strict digital nomad route. Taiwan is usually better for professionals who can actually qualify for the Gold Card.</p><div class="bcm-stats"><div><strong>6 mo</strong><span>Japan Digital Nomad</span></div><div><strong>1-3 yr</strong><span>Taiwan Gold Card</span></div><div><strong>2026</strong><span>rules checked</span></div></div></div>
<div class="bcm-note"><strong>Short answer:</strong> do not choose Japan vs Taiwan by mood alone. Japan is better for a limited high-quality stay. Taiwan is stronger if you need a longer legal horizon and your professional profile fits the Gold Card.</div>
<h2>Quick Verdict: Japan vs Taiwan For Expats</h2>
<p>Japan wins emotionally for many people. Tokyo, Osaka, Kyoto, transport, service and safety are easy to love. But Japan's digital nomad route is deliberately narrow: six months, remote work, high income proof and medical insurance. The MOFA page states a six-month period of stay and says no extension will be granted. In practice, this is not a residence path.</p>
<p>Taiwan is less theatrical, but often more practical. The Employment Gold Card combines a work permit, residence permit, visa and re-entry permit. The official Gold Card portal also says holders can stay for up to three years. But it is not a casual digital nomad visa. It is a skilled-professional route, and the documents matter.</p>
<h2>Side-By-Side Comparison</h2>
<div class="bcm-table-wrap"><table class="bcm-table"><thead><tr><th>Factor</th><th>Japan</th><th>Taiwan</th><th>Practical Meaning</th></tr></thead><tbody>
<tr><td>Best fit</td><td>Short premium stay</td><td>Professional relocation</td><td>Check the legal horizon before lifestyle.</td></tr>
<tr><td>Main route</td><td>Digital Nomad / Designated Activities</td><td>Employment Gold Card</td><td>Different legal logic, not interchangeable labels.</td></tr>
<tr><td>Stay length</td><td>6 months, no extension</td><td>Usually 1-3 years</td><td>Taiwan is stronger beyond a half-year test.</td></tr>
<tr><td>Income / qualification</td><td>JPY 10 million annual income requirement</td><td>Category-based qualification, often salary or expertise evidence</td><td>Both need documents, not just preference.</td></tr>
<tr><td>Family</td><td>Spouse or child route exists with documents</td><td>Family options depend on Gold Card rules</td><td>Family planning needs separate verification.</td></tr>
</tbody></table></div>
<h2>Where Japan Is Stronger</h2>
<p>Japan is stronger as a short, high-quality base. If your income is clear, your work is remote, your insurance meets the requirement and you are not pretending that six months will quietly become several years, the route is clean. Six months can still be valuable: test districts, work rhythm, language friction, healthcare, family logistics and whether the country fits you in real life.</p>
<p>Japan is weak if the hidden plan is permanent relocation. The official no-extension language is not a small detail. If the real goal is years, then employment, business, study or another status has to be researched separately. Stretching the digital nomad label beyond the rule is bad planning.</p>
<h2>Where Taiwan Is Stronger</h2>
<p>Taiwan is stronger for a professional relocation scenario. The Gold Card is not just “a visa to live abroad”. It is built around skill, category, salary, professional evidence or another qualification route. If the profile fits, Taiwan gives a wider runway: work authorization, residence, visa and re-entry in one structure.</p>
<p>The practical reading is simple. Taiwan is better if you are a provable specialist. If your qualification is vague, do not build the move on hope. Check the Gold Card first, then compare Taipei, Taichung, Kaohsiung, rent and lifestyle.</p>
<div class="bcm-cols"><div class="bcm-pros"><h3>Japan Fits</h3><ul><li>a short premium stay of up to six months;</li><li>people with clear high income proof;</li><li>remote workers who do not need extension.</li></ul></div><div class="bcm-cons"><h3>Taiwan Fits</h3><ul><li>skilled professionals with documents;</li><li>a one-to-three-year horizon;</li><li>people who need work and residence logic together.</li></ul></div></div>
<h2>FAQ</h2>
<div class="bcm-faq-item"><h3>Can Japan Digital Nomad Visa Be Extended?</h3><p>The MOFA page states a six-month period of stay and says no extension will be granted. Do not plan around an extension unless official rules change.</p></div>
<div class="bcm-faq-item"><h3>Is Taiwan Gold Card A Digital Nomad Visa?</h3><p>Not exactly. It is a skilled-professional route combining work authorization, residence, visa and re-entry. A casual remote worker without qualifying evidence may not fit.</p></div>
<div class="bcm-faq-item"><h3>Which Is Cheaper: Japan Or Taiwan?</h3><p>Taiwan is usually easier on the budget, especially outside the most expensive Taipei districts. Japan is typically heavier on rent and daily friction, especially in Tokyo.</p></div>
<div class="bcm-faq-item"><h3>Which Is Better For Families?</h3><p>Taiwan often has the stronger long-horizon logic through the Gold Card, but family rights and documents still need separate checks. Japan has a spouse or child route for the digital nomad path, but it follows the same short stay logic.</p></div>
<div class="bcm-faq-item"><h3>How Should You Choose Japan vs Taiwan?</h3><p>Choose Japan for a short, high-quality stay. Choose Taiwan if you qualify professionally and need a longer legal runway. If the visa does not fit, lifestyle is secondary.</p></div>
""",
    )


COMPARE_ARTICLE_BRIEFS = {
    "thailand-vs-vietnam": {
        "en_title": "Thailand vs Vietnam For Expats In 2026: Cost, Visas And Daily Life",
        "ru_title": "Таиланд или Вьетнам для переезда в 2026 году: визы, бюджет и быт",
        "en_h1": "Thailand vs Vietnam For Expats In 2026",
        "ru_h1": "Таиланд или Вьетнам для переезда в 2026 году",
        "a": "Thailand",
        "b": "Vietnam",
        "a_ru": "Таиланд",
        "b_ru": "Вьетнам",
        "en_verdict": "Thailand is the safer all-round relocation base. Vietnam is usually cheaper and can be excellent for testing Southeast Asia, but it has weaker long-stay clarity for many expat profiles.",
        "ru_verdict": "Таиланд сильнее как сбалансированная база для переезда. Вьетнам чаще дешевле и хорош для теста Юго-Восточной Азии, но long-stay логика для многих профилей слабее.",
        "en_a": "Thailand wins when you need healthcare, airports, city choice, islands, expat services and a more developed relocation ecosystem. The DTV and LTR routes still need official checks, but Thailand gives more structured options than a simple short visitor stay.",
        "en_b": "Vietnam wins on value. Da Nang, Hanoi and Ho Chi Minh City can give strong internet, food, energy and lower monthly costs. The risk is treating a convenient eVisa rhythm as a long-term relocation plan.",
        "ru_a": "Таиланд выигрывает, когда важны медицина, аэропорты, выбор городов, острова, expat-сервисы и более развитая инфраструктура для переезда. DTV и LTR всё равно нужно проверять по официальным источникам, но выбор маршрутов шире.",
        "ru_b": "Вьетнам выигрывает ценой. Дананг, Ханой и Хошимин могут дать хороший интернет, еду, энергию города и более низкий месяц. Риск в том, что удобную eVisa начинают читать как долгосрочный план.",
        "official_en": "Check Thailand e-Visa and Thailand.go.th for DTV logic; check Vietnam Immigration for eVisa duration and entry rules.",
        "official_ru": "По Таиланду проверяйте Thailand e-Visa и Thailand.go.th для DTV; по Вьетнаму - Vietnam Immigration для срока eVisa и правил въезда.",
    },
    "malaysia-vs-vietnam": {
        "en_title": "Malaysia vs Vietnam For Expats In 2026: Comfort, Cost And Visa Fit",
        "ru_title": "Малайзия или Вьетнам для переезда в 2026 году: комфорт, бюджет и визы",
        "en_h1": "Malaysia vs Vietnam For Expats In 2026",
        "ru_h1": "Малайзия или Вьетнам для переезда в 2026 году",
        "a": "Malaysia",
        "b": "Vietnam",
        "a_ru": "Малайзия",
        "b_ru": "Вьетнам",
        "en_verdict": "Malaysia is usually better for families, English-speaking daily life and predictable city comfort. Vietnam is better when budget and a flexible test stay matter more than long-term structure.",
        "ru_verdict": "Малайзия чаще лучше для семьи, английского в быту и предсказуемого городского комфорта. Вьетнам лучше, если важнее бюджет и гибкий тест страны, а не долгосрочная структура.",
        "en_a": "Malaysia is practical rather than dramatic: Kuala Lumpur and Penang offer English, healthcare, malls, airports and a softer landing. DE Rantau can fit digital professionals, but the official route and documents still decide the plan.",
        "en_b": "Vietnam is sharper on cost and energy. It can be a strong remote-work base for a few months, especially in Da Nang. It is weaker if the real goal is family relocation or a multi-year stay with clean legal predictability.",
        "ru_a": "Малайзия практична, а не эффектна: Куала-Лумпур и Пенанг дают английский, медицину, торговые центры, аэропорты и более мягкий вход. DE Rantau может подойти digital professionals, но документы решают всё.",
        "ru_b": "Вьетнам сильнее по цене и энергии. Он хорошо работает как база на несколько месяцев, особенно Дананг. Слабее - если цель семья, школа или multi-year stay с понятной легальной логикой.",
        "official_en": "Check MDEC and Malaysia Immigration for DE Rantau context; check Vietnam Immigration for eVisa rules.",
        "official_ru": "По Малайзии проверяйте MDEC и Immigration Department; по Вьетнаму - официальный eVisa портал иммиграции.",
    },
    "singapore-vs-hong-kong": {
        "en_title": "Singapore vs Hong Kong For Expats In 2026: Career, Cost And Talent Routes",
        "ru_title": "Сингапур или Гонконг для переезда в 2026 году: карьера, стоимость и talent routes",
        "en_h1": "Singapore vs Hong Kong For Expats In 2026",
        "ru_h1": "Сингапур или Гонконг для переезда в 2026 году",
        "a": "Singapore",
        "b": "Hong Kong",
        "a_ru": "Сингапур",
        "b_ru": "Гонконг",
        "en_verdict": "Singapore is cleaner for high-income regional careers and corporate stability. Hong Kong is stronger for people tied to finance, China-facing business and the Top Talent Pass profile.",
        "ru_verdict": "Сингапур понятнее для high-income карьеры, региональных штаб-квартир и корпоративной стабильности. Гонконг сильнее для finance, China-facing business и профилей под Top Talent Pass.",
        "en_a": "Singapore is expensive, but it is also orderly: infrastructure, safety, schools, air links and corporate hiring are unusually strong. The ONE Pass is not for average earners; it is a high-salary talent route.",
        "en_b": "Hong Kong is also expensive, but the value proposition is different: finance, legal services, China access, dense urban life and talent admission routes. Housing pressure is the main practical shock.",
        "ru_a": "Сингапур дорогой, но очень упорядоченный: инфраструктура, безопасность, школы, перелёты и корпоративный рынок сильные. ONE Pass - маршрут не для среднего дохода, а для top talent.",
        "ru_b": "Гонконг тоже дорогой, но смысл другой: finance, legal services, доступ к Китаю, плотная городская жизнь и talent admission routes. Главный шок - жильё.",
        "official_en": "Check Singapore MOM for ONE Pass and Hong Kong Immigration for Top Talent Pass rules.",
        "official_ru": "По Сингапуру проверяйте MOM ONE Pass, по Гонконгу - Immigration Department и Top Talent Pass Scheme.",
    },
    "uae-vs-qatar": {
        "en_title": "UAE vs Qatar For Expats In 2026: Remote Work, Business And Gulf Cost Reality",
        "ru_title": "ОАЭ или Катар для переезда в 2026 году: работа, бизнес и реальные расходы",
        "en_h1": "UAE vs Qatar For Expats In 2026",
        "ru_h1": "ОАЭ или Катар для переезда в 2026 году",
        "a": "UAE",
        "b": "Qatar",
        "a_ru": "ОАЭ",
        "b_ru": "Катар",
        "en_verdict": "UAE is stronger for remote-work residence, business setup, city choice and international services. Qatar can work for employment-led relocation, but it is less flexible as a general remote-worker base.",
        "ru_verdict": "ОАЭ сильнее для remote-work residence, бизнеса, выбора городов и международных сервисов. Катар может подойти при рабочем контракте, но как общая база для удалёнщика он менее гибкий.",
        "en_a": "The UAE has clearer public routes for working outside the UAE while living there, plus Dubai and Abu Dhabi offer deep expat infrastructure. The trade-off is cost pressure and the need to keep paperwork clean.",
        "en_b": "Qatar is smaller and more employment-centered. Doha can be comfortable and safe, but the relocation case is strongest when a job, employer or official entry route is already clear.",
        "ru_a": "У ОАЭ понятнее публичная логика residence для работы outside the UAE, плюс Дубай и Абу-Даби дают сильную expat-инфраструктуру. Минусы - высокая стоимость и требовательность к документам.",
        "ru_b": "Катар меньше и сильнее привязан к employment-сценарию. Доха может быть комфортной и безопасной, но релокация лучше работает, когда уже есть работа, работодатель или понятный официальный route.",
        "official_en": "Check UAE government and ICP for residence routes; check Hayya and Qatar MOI for Qatar entry logic.",
        "official_ru": "По ОАЭ проверяйте u.ae и ICP; по Катару - Hayya и портал МВД Катара.",
    },
}


def enhanced_compare_article(slug: str, lang: str = "en") -> tuple[str, str] | None:
    data = COMPARE_ARTICLE_BRIEFS.get(slug)
    if not data:
        return None
    if lang == "ru":
        return (
            data["ru_title"],
            BCM_ARTICLE_STYLE + f"""
<div class="bcm-hero"><div class="badge">Обновлено в мае 2026 - Compare</div><h1>{data["ru_h1"]}</h1><p>{data["ru_verdict"]}</p><div class="bcm-stats"><div><strong>{data["a_ru"]}</strong><span>вариант A</span></div><div><strong>vs</strong><span>сравнение</span></div><div><strong>{data["b_ru"]}</strong><span>вариант B</span></div></div></div>
<div class="bcm-note"><strong>Короткий вывод:</strong> {data["ru_verdict"]} Выбирать нужно не по одной цене или эмоции, а по связке: визовый маршрут, срок, работа, медицина, жильё, семья и запас денег.</div>
<h2>Что На Самом Деле Сравнивает Эта Страница</h2>
<p>Сравнение {data["a_ru"]} vs {data["b_ru"]} часто выглядит как спор вкуса: где дешевле, где приятнее климат, где лучше еда, где проще жить. Но для переезда это слишком поверхностно. Сначала нужно понять, на каком легальном основании вы будете находиться в стране, сколько этот сценарий стоит в первый месяц и что произойдёт, когда срок stay закончится.</p>
<p>{data["official_ru"]} Это не формальность. Официальные страницы дают факты: срок, продление, документы, разрешённую деятельность и финансовые требования. Всё остальное - практическая интерпретация.</p>
<h2>Где Сильнее {data["a_ru"]}</h2>
<p>{data["ru_a"]}</p>
<p>Практически это значит: {data["a_ru"]} стоит выбирать, если его сильная сторона совпадает с вашей реальной задачей. Не с мечтой о стране, а с документами, доходом, семьёй и горизонтом. Если вы не проходите по маршруту или бюджет держится только на идеальной аренде, плюс страны быстро теряет вес.</p>
<h2>Где Сильнее {data["b_ru"]}</h2>
<p>{data["ru_b"]}</p>
<p>{data["b_ru"]} может быть лучшим выбором, если вы честно принимаете его ограничения. Дешевле не всегда значит проще, а дороже не всегда значит лучше. Важно, чтобы страна совпадала с вашей работой, сроком проживания и уровнем бытовой устойчивости.</p>
<h2>Decision Table</h2>
<div class="bcm-table-wrap"><table class="bcm-table"><thead><tr><th>Сценарий</th><th>Лучше смотреть</th><th>Почему</th></tr></thead><tbody>
<tr><td>Нужен понятный legal stay</td><td>Зависит от профиля</td><td>Официальный маршрут важнее рейтинга страны.</td></tr>
<tr><td>Главный фактор - бюджет</td><td>{data["b_ru"]}</td><td>Часто второй вариант мягче по расходам, но это нужно сверять городом.</td></tr>
<tr><td>Главный фактор - инфраструктура</td><td>{data["a_ru"]}</td><td>Первый вариант чаще сильнее по сервисам и предсказуемости.</td></tr>
<tr><td>Семья или медицина</td><td>Считать отдельно</td><td>Школы, страховка и больницы быстро меняют ответ.</td></tr>
</tbody></table></div>
<h2>Кому Не Подходит Такое Сравнение</h2>
<p>Оно не подходит тем, кто уже выбрал страну и ищет подтверждение. Тогда любая таблица будет читаться с перекосом. Гораздо полезнее взять два реальных сценария и проверить слабое место: виза, доход, аренда, медицина, семья, налоговая логика или срок.</p>
<h2>FAQ</h2>
<div class="bcm-faq-item"><h3>Что Выбрать: {data["a_ru"]} Или {data["b_ru"]}?</h3><p>{data["ru_verdict"]}</p></div>
<div class="bcm-faq-item"><h3>Можно Ли Решать Только По Стоимости Жизни?</h3><p>Нет. Стоимость важна, но она не заменяет визу, страховку, медицину, работу и право оставаться в стране.</p></div>
<div class="bcm-faq-item"><h3>Какие Источники Проверять?</h3><p>{data["official_ru"]}</p></div>
<div class="bcm-faq-item"><h3>Что Проверить Перед Арендой Жилья?</h3><p>Срок stay, продление, разрешённую деятельность, документы по доходу, страховку, депозит и стоимость выхода из страны.</p></div>
<div class="bcm-faq-item"><h3>Можно Ли Использовать Эту Страницу Как Юридический Совет?</h3><p>Нет. Это редакционный материал для планирования. Перед подачей или оплатой услуг нужно сверять официальный источник.</p></div>
""",
        )
    return (
        data["en_title"],
        BCM_ARTICLE_STYLE + f"""
<div class="bcm-hero"><div class="badge">Updated May 2026 - Compare</div><h1>{data["en_h1"]}</h1><p>{data["en_verdict"]}</p><div class="bcm-stats"><div><strong>{data["a"]}</strong><span>option A</span></div><div><strong>vs</strong><span>comparison</span></div><div><strong>{data["b"]}</strong><span>option B</span></div></div></div>
<div class="bcm-note"><strong>Short answer:</strong> {data["en_verdict"]} The right choice depends on legal stay, work setup, healthcare, housing, family needs and budget buffer, not one attractive feature.</div>
<h2>What This Comparison Actually Decides</h2>
<p>{data["a"]} vs {data["b"]} is not a travel preference question. For relocation, the useful question is which country fits your legal route, monthly budget, first-month setup cost and time horizon. Cheap rent is useful only if the visa and daily life work together.</p>
<p>{data["official_en"]} Official pages give the facts: stay length, extension logic, required documents, permitted activity and financial evidence. The editorial job is to explain what those facts mean in practice.</p>
<h2>Where {data["a"]} Is Stronger</h2>
<p>{data["en_a"]}</p>
<p>In practice, choose {data["a"]} when its main advantage solves your actual constraint. If the route does not fit your income, employer, family or stay length, the country's strengths become less useful.</p>
<h2>Where {data["b"]} Is Stronger</h2>
<p>{data["en_b"]}</p>
<p>{data["b"]} can be the better answer when you accept its limits honestly. Lower cost does not automatically mean easier relocation. Higher infrastructure does not automatically mean a better fit.</p>
<h2>Decision Table</h2>
<div class="bcm-table-wrap"><table class="bcm-table"><thead><tr><th>Scenario</th><th>Look First At</th><th>Why</th></tr></thead><tbody>
<tr><td>Need a clear legal stay route</td><td>Depends on profile</td><td>The official route matters more than the country ranking.</td></tr>
<tr><td>Budget is the main pressure</td><td>{data["b"]}</td><td>The second option is often softer on cost, but city choice still decides.</td></tr>
<tr><td>Infrastructure matters most</td><td>{data["a"]}</td><td>The first option is usually stronger for services and predictability.</td></tr>
<tr><td>Family or healthcare planning</td><td>Check separately</td><td>Schools, insurance and hospitals can reverse the simple answer.</td></tr>
</tbody></table></div>
<h2>Who Should Be Careful</h2>
<p>Be careful if you have already chosen the country emotionally and are only looking for confirmation. The safer method is to test the weak point first: visa, income proof, employer setup, rent, healthcare, family eligibility or the cost of leaving.</p>
<h2>FAQ</h2>
<div class="bcm-faq-item"><h3>Which Is Better: {data["a"]} Or {data["b"]}?</h3><p>{data["en_verdict"]}</p></div>
<div class="bcm-faq-item"><h3>Should I Decide Only By Cost Of Living?</h3><p>No. Cost matters, but it does not replace visa fit, insurance, healthcare, work permission and stay length.</p></div>
<div class="bcm-faq-item"><h3>Which Official Sources Should I Check?</h3><p>{data["official_en"]}</p></div>
<div class="bcm-faq-item"><h3>What Should I Check Before Renting?</h3><p>Stay length, extension logic, permitted activity, income proof, insurance, deposit and exit cost.</p></div>
<div class="bcm-faq-item"><h3>Is This Legal Advice?</h3><p>No. This is editorial planning guidance. Verify the official authority before applying or paying for services.</p></div>
""",
    )


def ru_best_countries_move_article() -> tuple[str, str]:
    return (
        "Лучшие страны Азии для переезда в 2026 году",
        BCM_ARTICLE_STYLE + """
<div class="bcm-hero"><div class="badge">Обновлено в мае 2026 - экспертный гид</div><h1>Лучшие Страны Азии Для Переезда В 2026 Году</h1><p>Выбор страны в Азии начинается не с пляжей и не с рейтингов. Сначала нужно понять бюджет, визовый маршрут, медицину, городскую инфраструктуру и то, насколько страна подходит именно вашему сценарию.</p><div class="bcm-stats"><div><strong>10</strong><span>стран в рейтинге</span></div><div><strong>$600+</strong><span>стартовый бюджет</span></div><div><strong>2026</strong><span>правила проверены</span></div></div></div>
<div class="bcm-note"><strong>Короткий вывод:</strong> лучшей страны для всех нет. Таиланд силён балансом, Малайзия - предсказуемостью, Вьетнам - ценой, Тайвань - профессиональным маршрутом, Япония - качеством короткого пребывания. Ошибка начинается там, где человек выбирает страну по настроению, а визу проверяет потом.</div>
<h2>Быстрое сравнение: лучшие страны для релокации</h2>
<div class="bcm-table-wrap"><table class="bcm-table"><thead><tr><th>#</th><th>Страна</th><th>Бюджет / месяц</th><th>Сильная сторона</th><th>Кому подходит</th></tr></thead><tbody>
<tr><td class="rank">1</td><td>Таиланд</td><td>$900-1,800</td><td>баланс быта, медицины и городов</td><td>удалёнщики, пары, ранняя пенсия</td></tr>
<tr><td class="rank">2</td><td>Малайзия</td><td>$900-1,900</td><td>английский, медицина, городская инфраструктура</td><td>семьи, долгое проживание, спокойная релокация</td></tr>
<tr><td class="rank">3</td><td>Вьетнам</td><td>$700-1,300</td><td>цена и энергия городов</td><td>тест Азии, бюджетная удалённая работа</td></tr>
<tr><td class="rank">4</td><td>Бали / Индонезия</td><td>$1,100-2,200</td><td>сообщество и среда</td><td>креативные специалисты, предприниматели</td></tr>
<tr><td class="rank">5</td><td>Тайвань</td><td>$1,400-2,600</td><td>безопасность и Gold Card</td><td>квалифицированные специалисты</td></tr>
<tr><td class="rank">6</td><td>Япония</td><td>$1,800-3,200</td><td>качество жизни и порядок</td><td>короткое проживание с высоким уровнем сервиса</td></tr>
<tr><td class="rank">7</td><td>Филиппины</td><td>$900-1,700</td><td>английский и пенсионный маршрут</td><td>пенсионеры, англоязычный быт</td></tr>
<tr><td class="rank">8</td><td>Сингапур</td><td>$2,500-5,000+</td><td>карьера и инфраструктура</td><td>люди с высоким доходом, основатели проектов, специалисты</td></tr>
<tr><td class="rank">9</td><td>Камбоджа</td><td>$600-1,100</td><td>низкая стоимость</td><td>ультрабюджет, осторожный план долгого проживания</td></tr>
<tr><td class="rank">10</td><td>ОАЭ</td><td>$2,500-5,000+</td><td>налоговая и бизнес-логика</td><td>предприниматели, высокий доход</td></tr>
</tbody></table></div>
<div class="bcm-country"><h2>1. Таиланд: Лучший Баланс Для Большинства</h2><div class="bcm-stats-bar"><div class="bcm-stat-item"><span class="val">$900+</span><span class="lbl">старт</span></div><div class="bcm-stat-item"><span class="val">DTV / LTR</span><span class="lbl">проверить визу</span></div><div class="bcm-stat-item"><span class="val">Bangkok</span><span class="lbl">главный хаб</span></div></div><p>Таиланд редко выигрывает по одной цифре. Он выигрывает суммой факторов: медицина, перелёты, еда, сервисы, аренда, среда экспатов, острова и большие города. Для многих это самый понятный первый шаг в Азии. Но визовую часть нельзя оставлять на потом. DTV, LTR, пенсионные и другие маршруты работают по разной логике. Если человек хочет жить долго, ему нужно проверить официальный маршрут до аренды квартиры.</p><div class="bcm-cols"><div class="bcm-pros"><h3>Плюсы</h3><ul><li>сильная медицина и инфраструктура;</li><li>много городов под разные бюджеты;</li><li>большое сообщество экспатов и удалённых специалистов.</li></ul></div><div class="bcm-cons"><h3>Минусы</h3><ul><li>острова быстро дорожают;</li><li>визовые маршруты нельзя смешивать;</li><li>Бангкок и Чиангмай дают разный опыт.</li></ul></div></div></div>
<div class="bcm-country"><h2>2. Малайзия: Практичный Вариант Для Семьи И Города</h2><p>Малайзия не всегда выглядит самой яркой, но часто оказывается самой спокойной. В Куала-Лумпуре легче с английским, медициной, торговыми центрами, международной средой и обычной городской жизнью. Пенанг может быть мягче по ритму. Для семьи это часто важнее, чем «самая дешёвая страна». Слабое место - не цена, а совпадение с визовым маршрутом. DE Rantau, MM2H и employment pass не заменяют друг друга.</p></div>
<div class="bcm-country"><h2>3. Вьетнам: Сильная Цена, Но Не Универсальная Резиденция</h2><p>Вьетнам хорош для теста Азии. Дананг, Ханой и Хошимин дают разный баланс цены, работы и быта. Интернет и кафе-среда в крупных городах подходят многим удалёнщикам. Но Вьетнам не стоит продавать себе как «дешёвый Таиланд». Главный вопрос - срок и легальность пребывания. Если нужен стабильный маршрут на несколько лет, Вьетнам требует более осторожного планирования.</p></div>
<div class="bcm-country"><h2>4. Бали: Сильная Среда, Но Бюджет Уже Не Низкий</h2><p>Бали остаётся магнитом для удалённых специалистов, основателей проектов, креативных команд и людей, которым важна среда. Но дешёвым Бали уже нельзя считать автоматически. Чангу, Убуд и Семиньяк живут по своей логике цен. Плюс нужно внимательно смотреть индонезийский визовый маршрут, потому что образ жизни не заменяет легальный статус.</p></div>
<div class="bcm-country"><h2>5. Тайвань: Для Специалистов, Которым Нужен Горизонт</h2><p>Тайвань подходит не всем, но для квалифицированных специалистов может быть одним из самых сильных вариантов. Employment Gold Card объединяет несколько разрешений и может дать более длинный горизонт, чем многие «nomad» визы. Но это не маршрут «для всех удалёнщиков». Нужны документы, категория и подтверждаемая квалификация.</p></div>
<div class="bcm-country"><h2>6. Япония: Отлично На Полгода, Сложнее Для Переезда</h2><p>Япония привлекательна почти всем: порядок, транспорт, безопасность, культура, города. Но digital nomad visa в Японию - короткий и строгий маршрут. Официальные правила говорят о шести месяцах и отсутствии продления. Значит, Япония хороша как качественное короткое пребывание, но не как автоматический путь к резиденции.</p></div>
<h2>Как выбрать подходящую страну в Азии</h2>
<p>Сначала проверьте не страну, а свой сценарий. Один человек с удалённым доходом, семья с детьми, пенсионер, основатель проекта и специалист с оффером - это пять разных решений. Дешёвый город может быть плохим, если там нет нужной медицины. Дорогая страна может быть разумной, если даёт рабочий статус, безопасность и предсказуемость. В Азии особенно важно не путать впечатление от поездки с планом релокации.</p>
<p>Практический порядок такой: срок пребывания, право работать или жить, доход и документы, страхование, город, жильё, школа или медицина, потом образ жизни. Если порядок перевернуть, легко выбрать красивую страну и потом обнаружить, что легального маршрута нет.</p>
<h2>FAQ</h2>
<div class="bcm-faq-item"><h3>Какая Страна Азии Лучшая Для Переезда В 2026 Году?</h3><p>Для большинства первым shortlist остаются Таиланд, Малайзия, Вьетнам, Тайвань и Бали. Но «лучшая» зависит от визы, дохода, семьи, медицины и срока проживания.</p></div>
<div class="bcm-faq-item"><h3>Где В Азии Дешевле Всего Жить?</h3><p>По базовым расходам часто выигрывают Камбоджа, Вьетнам, часть Индии и Непала. Но низкая цена не всегда означает лучший переезд.</p></div>
<div class="bcm-faq-item"><h3>Какая Страна Лучше Для Digital Nomads?</h3><p>Таиланд и Бали сильны по среде, Малайзия - по городскому комфорту, Тайвань - по профессиональному маршруту, Япония - по короткому пребыванию с высоким уровнем сервиса.</p></div>
<div class="bcm-faq-item"><h3>Какая Страна Лучше Для Семьи?</h3><p>Малайзия и Тайвань часто выглядят сильнее из-за инфраструктуры, медицины и предсказуемого быта. Но всё зависит от школы, района и визового маршрута.</p></div>
<div class="bcm-faq-item"><h3>Можно Ли Сначала Приехать Туристом И Решить На Месте?</h3><p>Можно для разведки. Но платить за долгую аренду, перевозить семью или закрывать дела дома лучше только после проверки официального визового маршрута.</p></div>
""",
    )


@app.route("/compare/")
def compare_index():
    row = page_or_404("compare")
    return render_page_row(row, breadcrumbs=[])


@app.route("/compare/<slug>/")
def compare(slug: str):
    row = page_or_404(slug, parent="compare")
    if slug == "japan-vs-taiwan":
        title, content = japan_vs_taiwan_article("en")
        row = {
            "slug": slug,
            "title": title,
            "content": content,
            "parent": "compare",
            "link": f"/compare/{slug}/",
        }
    else:
        enhanced = enhanced_compare_article(slug, "en")
        if enhanced:
            title, content = enhanced
            row = {
                "slug": slug,
                "title": title,
                "content": content,
                "parent": "compare",
                "link": f"/compare/{slug}/",
            }
    return render_page_row(row,
                           breadcrumbs=[("Compare", "/compare/")])


@app.route("/ru/compare/")
def ru_compare_index():
    source = page_or_404("compare")
    row = {
        "slug": "ru-compare",
        "title": "Сравнение стран Азии в 2026 году: визы, расходы и практичность",
        "content": localized_compare_index_content(),
        "parent": None,
        "link": "https://www.marharuta.online/ru/compare/",
    }
    return render_page_row(
        row,
        lang="ru",
        canonical_path="/ru/compare/",
        alternates=localized_page_alternates(en_path="/compare/", ru_path="/ru/compare/"),
        breadcrumbs=[],
        show_internal_links=True,
    )


@app.route("/ru/compare/<slug>/")
def ru_compare(slug: str):
    source = page_or_404(slug, parent="compare")
    translated = one("SELECT title, content FROM pages WHERE slug = ? AND parent = ?", (localized_compare_db_slug(slug), "ru-compare"))
    if translated and strip_html(translated["content"]).strip():
        title = translated["title"]
        content = normalize_ru_compare_content(_localize_internal_links(localized_generic_content(translated["content"]), lang="ru"))
    elif slug == "japan-vs-taiwan":
        title, content = japan_vs_taiwan_article("ru")
    else:
        enhanced = enhanced_compare_article(slug, "ru")
        if enhanced:
            title, content = enhanced
        else:
            title, content = localized_compare_pair_content(slug, translated["title"] if translated else source["title"], source["content"])
    row = localized_page_dict(
        slug=localized_compare_db_slug(slug),
        title=title,
        content=content,
        link=f"/ru/compare/{slug}/",
        parent="ru-compare",
    )
    return render_page_row(
        row,
        lang="ru",
        canonical_path=f"/ru/compare/{slug}/",
        alternates=localized_page_alternates(en_path=f"/compare/{slug}/", ru_path=f"/ru/compare/{slug}/"),
        breadcrumbs=[("Сравнение", "/ru/compare/")],
        show_internal_links=True,
    )


@app.route("/compare-cities/")
def compare_cities():
    row = page_or_404("compare-cities")
    return render_page_row(row, breadcrumbs=[],
                           extra_js="compare_cities")


@app.route("/ru/compare-cities/")
def ru_compare_cities():
    source = page_or_404("compare-cities")
    title, content = localized_simple_page_content("compare-cities", source["title"], source["content"])
    row = localized_page_dict(slug="ru-compare-cities", title=title, content=content, link="/ru/compare-cities/")
    return render_page_row(
        row,
        lang="ru",
        canonical_path="/ru/compare-cities/",
        breadcrumbs=[],
        extra_js="compare_cities",
    )


@app.route("/visas/")
def visas():
    row = page_or_404("visas")
    return render_page_row(row, breadcrumbs=[])


@app.route("/ru/visas/")
def ru_visas():
    source = page_or_404("visas")
    title, content = localized_simple_page_content("visas", source["title"], source["content"])
    row = localized_page_dict(slug="ru-visas", title=title, content=content, link="/ru/visas/")
    return render_page_row(row, lang="ru", canonical_path="/ru/visas/", breadcrumbs=[])


@app.route("/best-countries-in-asia-to-move/")
def best_countries():
    row = page_or_404("best-countries-in-asia-to-move")
    return render_page_row(row, breadcrumbs=[])


@app.route("/ru/best-countries-in-asia-to-move/")
def ru_best_countries():
    title, content = ru_best_countries_move_article()
    row = localized_page_dict(
        slug="ru-best-countries-in-asia-to-move",
        title=title,
        content=content,
        link="/ru/best-countries-in-asia-to-move/",
    )
    return render_page_row(row, lang="ru", canonical_path="/ru/best-countries-in-asia-to-move/", breadcrumbs=[])


@app.route("/cheapest-countries-in-asia/")
def cheapest_countries():
    row = page_or_404("cheapest-countries-in-asia")
    return render_page_row(row, breadcrumbs=[])


@app.route("/ru/cheapest-countries-in-asia/")
def ru_cheapest_countries():
    title, content = ru_cheapest_countries_article()
    row = localized_page_dict(
        slug="ru-cheapest-countries-in-asia",
        title=title,
        content=content,
        link="/ru/cheapest-countries-in-asia/",
    )
    return render_page_row(row, lang="ru", canonical_path="/ru/cheapest-countries-in-asia/", breadcrumbs=[])


@app.route("/move-to-asia/")
def move_to_asia():
    row = page_or_404("move-to-asia")
    return render_page_row(row, breadcrumbs=[])


@app.route("/ru/move-to-asia/")
def ru_move_to_asia():
    source = page_or_404("move-to-asia")
    title, content = localized_simple_page_content("move-to-asia", source["title"], source["content"])
    row = localized_page_dict(slug="ru-move-to-asia", title=title, content=content, link="/ru/move-to-asia/")
    return render_page_row(row, lang="ru", canonical_path="/ru/move-to-asia/", breadcrumbs=[])


@app.route("/digital-nomad-visas-asia/")
def digital_nomad_visas_asia():
    row = page_or_404("digital-nomad-visas-asia")
    return render_page_row(row, breadcrumbs=[])


@app.route("/ru/digital-nomad-visas-asia/")
def ru_digital_nomad_visas_asia():
    source = page_or_404("digital-nomad-visas-asia")
    title, content = localized_simple_page_content("digital-nomad-visas-asia", source["title"], source["content"])
    row = localized_page_dict(
        slug="ru-digital-nomad-visas-asia",
        title=title,
        content=content,
        link="/ru/digital-nomad-visas-asia/",
    )
    return render_page_row(row, lang="ru", canonical_path="/ru/digital-nomad-visas-asia/", breadcrumbs=[])


@app.route("/retire-in-asia/")
def retire_in_asia():
    row = page_or_404("retire-in-asia")
    return render_page_row(row, breadcrumbs=[])


@app.route("/ru/retire-in-asia/")
def ru_retire_in_asia():
    source = page_or_404("retire-in-asia")
    title, content = localized_simple_page_content("retire-in-asia", source["title"], source["content"])
    row = localized_page_dict(slug="ru-retire-in-asia", title=title, content=content, link="/ru/retire-in-asia/")
    return render_page_row(row, lang="ru", canonical_path="/ru/retire-in-asia/", breadcrumbs=[])


@app.route("/cost-of-living-asia/")
def cost_of_living_asia():
    title, content = cost_of_living_asia_article("en")
    row = {
        "slug": "cost-of-living-asia",
        "title": title,
        "content": content,
        "parent": None,
        "link": "/cost-of-living-asia/",
    }
    return render_page_row(row, breadcrumbs=[])


@app.route("/ru/cost-of-living-asia/")
def ru_cost_of_living_asia():
    title, content = cost_of_living_asia_article("ru")
    row = localized_page_dict(slug="ru-cost-of-living-asia", title=title, content=content, link="/ru/cost-of-living-asia/")
    return render_page_row(row, lang="ru", canonical_path="/ru/cost-of-living-asia/", breadcrumbs=[])


@app.route("/guides/")
def guides_index():
    row = page_or_404("guides")
    return render_page_row(row, breadcrumbs=[], show_breadcrumbs=True)


@app.route("/ru/guides/")
def ru_guides_index():
    source = page_or_404("guides")
    title, content = localized_simple_page_content("guides", source["title"], source["content"])
    row = localized_page_dict(slug="ru-guides", title=title, content=content, link="/ru/guides/")
    return render_page_row(row, lang="ru", canonical_path="/ru/guides/", breadcrumbs=[], show_breadcrumbs=True)


@app.route("/guides/<slug>/")
def guide(slug: str):
    row = page_or_404(slug, parent="guides")
    return render_page_row(row, breadcrumbs=[("Guides", "/guides/")])


@app.route("/ru/guides/<slug>/")
def ru_guide(slug: str):
    source = page_or_404(slug, parent="guides")
    title, content = localized_guide_content(slug, source["title"], source["content"])
    row = localized_page_dict(slug=f"ru-{slug}", title=title, content=content, link=f"/ru/guides/{slug}/", parent="guides")
    return render_page_row(
        row,
        lang="ru",
        canonical_path=f"/ru/guides/{slug}/",
        breadcrumbs=[("Гайды", "/ru/guides/")],
    )


def render_blog_index(*, lang: str, page: int = 1):
    is_ru = lang == "ru"
    path = "/ru/blog/" if is_ru else "/blog/"
    query_page = request.args.get("page", type=int)
    if query_page:
        if query_page <= 1:
            return redirect(path, 301)
        return redirect(f"{path}page/{query_page}/", 301)
    page = max(page, 1)
    per_page = 10
    title = "Блог о релокации в Азию" if is_ru else "Asia Relocation Blog"
    description = (
        "Русскоязычные гайды по визам, странам и релокации в Азию на основе официальных источников."
        if is_ru else
        "Guides, comparisons and practical relocation advice for expats moving across Asia."
    )
    total_posts = one("SELECT COUNT(*) AS count FROM posts WHERE lang = ?", (lang,))["count"]
    total_pages = max((total_posts + per_page - 1) // per_page, 1)
    if page > total_pages:
        abort(404)
    posts = many(
        """
        SELECT id, slug, title, excerpt, date, lang
        FROM posts
        WHERE lang = ?
        ORDER BY date DESC, id DESC
        LIMIT ? OFFSET ?
        """,
        (lang, per_page, (page - 1) * per_page),
    )
    if is_ru:
        posts = [polish_ru_data(dict(post)) for post in posts]
    en_path = "/blog/" if page == 1 else f"/blog/page/{page}/"
    ru_path = "/ru/blog/" if page == 1 else f"/ru/blog/page/{page}/"
    alternates = localized_page_alternates(en_path=en_path, ru_path=ru_path)
    canonical_path = path if page == 1 else f"{path}page/{page}/"
    trust_panel = blog_trust_panel(lang=lang)
    depth_panel = blog_depth_panel(lang=lang)
    if is_ru:
        title = polish_ru_text(title)
        description = polish_ru_text(description)
        trust_panel = polish_ru_data(trust_panel)
        depth_panel = polish_ru_data(depth_panel)
    schema_items = [
        breadcrumb_schema([], title, path),
        collection_schema(title, description, canonical_path),
        trust_page_schema(title, canonical_path, page_type="CollectionPage"),
        depth_panel_schema(depth_panel, canonical_path, lang=lang),
        organization_schema(),
        website_schema(),
    ]
    schema_items = [item for item in schema_items if item]
    seo = seo_payload(
        title=title,
        description=description,
        lang=lang,
        canonical_path=canonical_path,
        alternates=alternates,
        schema=schema_items,
    )
    pagination = {
        "page": page,
        "per_page": per_page,
        "total_posts": total_posts,
        "total_pages": total_pages,
        "base_path": path,
        "prev_url": path if page == 2 else f"{path}page/{page - 1}/" if page > 2 else "",
        "next_url": f"{path}page/{page + 1}/" if page < total_pages else "",
    }
    return render_template(
        "blog.html",
        posts=posts,
        seo=seo,
        blog_lang=lang,
        blog_url_prefix="/ru/blog" if is_ru else "/blog",
        blog_title=title,
        blog_intro=description,
        trust_panel=trust_panel,
        depth_panel=depth_panel,
        internal_links=polish_ru_data(internal_links_for_blog(lang)) if is_ru else internal_links_for_blog(lang),
        read_more="Читать" if is_ru else "Read more",
        pagination=pagination,
    )


@app.route("/blog/")
def blog():
    return render_blog_index(lang="en")


@app.route("/blog/page/<int:page>/")
def blog_page(page: int):
    if page <= 1:
        return redirect("/blog/", 301)
    return render_blog_index(lang="en", page=page)


@app.route("/ru/blog/")
def blog_ru():
    return render_blog_index(lang="ru")


@app.route("/ru/blog/page/<int:page>/")
def blog_ru_page(page: int):
    if page <= 1:
        return redirect("/ru/blog/", 301)
    return render_blog_index(lang="ru", page=page)


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


def author_page_content(lang: str) -> tuple[str, str]:
    if lang == "ru":
        return (
            "Редакционная команда Relocate to Asia",
            f"""
<section class="rta-trust-page">
  <h1>Редакционная команда Relocate to Asia</h1>
  <p>Материалы Relocate to Asia готовит редакционная команда, которая работает с визовыми правилами, официальными программами, страновыми данными и практическими сценариями релокации в Азию. Мы не выдаём себя за иммиграционных юристов и не продаём визовые услуги.</p>
  <p>Наша задача другая: аккуратно отделять подтверждённые правила от практической интерпретации. Если официальный источник говорит «6 months» или «no extension», это фиксируется как факт. Если из этого следует, что маршрут плохо подходит для долгого переезда, это уже редакционный вывод, и он должен быть обозначен именно как вывод.</p>
  <h2>Что проверяет команда</h2>
  <ul>
    <li>официальные сроки пребывания, validity, продление и ограничения;</li>
    <li>требования к доходу, работодателю, страховке, депозитам и dependants;</li>
    <li>страницы иммиграционных служб, министерств, консульств и официальных программ;</li>
    <li>расходы, страновые факты и городские сценарии, когда они влияют на решение.</li>
  </ul>
  <h2>Как сообщить об ошибке</h2>
  <p>Если вы нашли устаревшее правило или более точный официальный источник, напишите через страницу <a href="/ru/contact/">контактов и исправлений</a>. Для визовых, финансовых и медицинских страниц это важнее косметики: лучше быстро поправить один факт, чем красиво оставить ошибку.</p>
</section>
""",
        )
    return (
        "Relocate to Asia Editorial Team",
        f"""
<section class="rta-trust-page">
  <h1>Relocate to Asia Editorial Team</h1>
  <p>Relocate to Asia is written and maintained by an editorial team focused on Asian relocation planning, official visa rules, country data and practical decision support. We are not an immigration law firm, and we do not sell visa services.</p>
  <p>The editorial job is to separate confirmed rules from practical interpretation. If an official source says “6 months” or “no extension”, that is treated as a fact. If that makes a route weak for long-term relocation, that is an editorial interpretation and should be presented as such.</p>
  <h2>What The Team Checks</h2>
  <ul>
    <li>official stay duration, validity, renewal and extension limits;</li>
    <li>income, employer, insurance, deposit and dependant requirements;</li>
    <li>immigration, ministry, consular and official program pages;</li>
    <li>cost, country and city data where it affects relocation decisions.</li>
  </ul>
  <h2>Corrections</h2>
  <p>If you find an outdated rule or a better official source, use the <a href="/contact/">contact and corrections page</a>. On visa, cost and healthcare pages, a corrected fact matters more than a polished paragraph.</p>
</section>
""",
    )


def contact_page_content(lang: str) -> tuple[str, str]:
    if lang == "ru":
        return (
            "Контакты и исправления",
            f"""
<section class="rta-trust-page">
  <h1>Контакты и исправления</h1>
  <p>Если вы нашли устаревшую визовую информацию, битую ссылку, неточную цифру или официальный источник, который лучше подтверждает правило, напишите нам. Для сайта о визах, расходах и релокации это не формальность, а часть доверия.</p>
  <div class="rta-note"><strong>Email:</strong> <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a></div>
  <h2>Что лучше указать в письме</h2>
  <ul>
    <li>URL страницы на Relocate to Asia;</li>
    <li>какой факт кажется устаревшим или неточным;</li>
    <li>ссылку на официальный источник, если он есть;</li>
    <li>дату, когда вы проверяли правило.</li>
  </ul>
  <p>Мы не консультируем по индивидуальным заявкам и не можем сказать, одобрят ли конкретную визу. Но если правило на сайте устарело, его нужно исправить.</p>
</section>
""",
        )
    return (
        "Contact And Corrections",
        f"""
<section class="rta-trust-page">
  <h1>Contact And Corrections</h1>
  <p>If you found outdated visa information, a broken link, an inaccurate figure or a better official source, tell us. For a site covering visas, costs and relocation decisions, corrections are not cosmetic. They are part of trust.</p>
  <div class="rta-note"><strong>Email:</strong> <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a></div>
  <h2>What To Include</h2>
  <ul>
    <li>the Relocate to Asia page URL;</li>
    <li>the fact that appears outdated or inaccurate;</li>
    <li>the official source link, if available;</li>
    <li>the date you checked the rule.</li>
  </ul>
  <p>We do not provide individual immigration advice and cannot predict whether an application will be approved. But if a rule on the site is outdated, it should be corrected.</p>
</section>
""",
    )


@app.route("/authors/")
def authors():
    title = "Authors And Editorial Review"
    content = """
<section class="rta-trust-page">
  <h1>Authors And Editorial Review</h1>
  <p>Relocate to Asia uses an editorial team model. Visa and relocation pages are written, edited and checked against official public sources before publication where possible.</p>
  <div class="rta-linkhub-grid">
    <a class="rta-linkhub-card" href="/authors/editorial-team/"><h3>Relocate to Asia Editorial Team</h3><p>Author, editor and fact-checking role for relocation guides.</p></a>
    <a class="rta-linkhub-card" href="/how-we-verify-data/"><h3>How We Verify Data</h3><p>Source standards, official references and update process.</p></a>
  </div>
</section>
"""
    page = {"title": title, "content": content, "link": "/authors/"}
    return render_page_row(page, breadcrumbs=[], extra_schema=trust_page_schema(title, "/authors/", page_type="CollectionPage"))


@app.route("/ru/authors/")
def ru_authors():
    title = "Авторы и редакционная проверка"
    content = """
<section class="rta-trust-page">
  <h1>Авторы и редакционная проверка</h1>
  <p>Relocate to Asia работает по редакционной модели. Визовые и релокационные материалы пишутся, редактируются и по возможности сверяются с официальными публичными источниками до публикации.</p>
  <div class="rta-linkhub-grid">
    <a class="rta-linkhub-card" href="/ru/authors/editorial-team/"><h3>Редакционная команда Relocate to Asia</h3><p>Автор, редактор и fact-checking role для гайдов по релокации.</p></a>
    <a class="rta-linkhub-card" href="/ru/how-we-verify-data/"><h3>Как мы проверяем данные</h3><p>Стандарты источников, официальные ссылки и процесс обновления.</p></a>
  </div>
</section>
"""
    page = {"title": title, "content": content, "link": "/ru/authors/"}
    return render_page_row(page, lang="ru", canonical_path="/ru/authors/", breadcrumbs=[], extra_schema=trust_page_schema(title, "/ru/authors/", page_type="CollectionPage"))


@app.route("/authors/editorial-team/")
def editorial_team_author():
    title, content = author_page_content("en")
    page = {"title": title, "content": content, "link": "/authors/editorial-team/"}
    return render_page_row(page, breadcrumbs=[("Authors", "/authors/")], extra_schema=editorial_team_schema("en"))


@app.route("/ru/authors/editorial-team/")
def ru_editorial_team_author():
    title, content = author_page_content("ru")
    page = {"title": title, "content": content, "link": "/ru/authors/editorial-team/"}
    return render_page_row(page, lang="ru", canonical_path="/ru/authors/editorial-team/", breadcrumbs=[("Авторы", "/ru/authors/")], extra_schema=editorial_team_schema("ru"))


@app.route("/contact/")
def contact():
    title, content = contact_page_content("en")
    page = {"title": title, "content": content, "link": "/contact/"}
    return render_page_row(page, breadcrumbs=[], extra_schema=trust_page_schema(title, "/contact/", page_type="ContactPage"))


@app.route("/ru/contact/")
def ru_contact():
    title, content = contact_page_content("ru")
    page = {"title": title, "content": content, "link": "/ru/contact/"}
    return render_page_row(page, lang="ru", canonical_path="/ru/contact/", breadcrumbs=[], extra_schema=trust_page_schema(title, "/ru/contact/", page_type="ContactPage"))




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

TRUST_PAGES_RU = {
    "about": {
        "title": "О проекте Relocate to Asia",
        "description": "Кто публикует Relocate to Asia и как сайт помогает сравнивать страны Азии, визы и реальные расходы на переезд.",
        "content": """
<section class="rta-trust-page">
  <h1>О проекте Relocate to Asia</h1>
  <p>Relocate to Asia — это редакционный проект о переезде в Азию для тех, кто сравнивает страны, города, визы и практические расходы. Сайт не продаёт визы и не подменяет собой юридическую консультацию. Наша задача проще и полезнее: дать человеку нормальную опору до того, как он потратит деньги на подачу, перелёт или жильё.</p>
  <p>Мы делаем упор на факты, официальные правила и практические компромиссы. Не на красивую картинку, а на то, что реально влияет на решение.</p>
  <h2>Что мы публикуем</h2>
  <ul>
    <li>Сравнения стран и городов для экспатов и удалённых специалистов.</li>
    <li>Визовые и long-stay гайды на основе официальных источников.</li>
    <li>Материалы о расходах, образе жизни и реальных ограничениях при переезде по Азии.</li>
    <li>Английские и русские версии там, где перевод действительно помогает читателю.</li>
  </ul>
</section>
""",
    },
    "editorial-policy": {
        "title": "Редакционная политика",
        "description": "Как Relocate to Asia исследует, пишет и обновляет материалы о визах, странах и переезде.",
        "content": """
<section class="rta-trust-page">
  <h1>Редакционная политика</h1>
  <p>Relocate to Asia публикует практические материалы для планирования переезда, а не юридические инструкции. В визовых статьях в приоритете официальные государственные сайты, консульские страницы, иммиграционные порталы и страницы самих программ. Вторичные источники можно использовать для контекста, но не вместо того органа, который публикует правило.</p>
  <h2>Наши стандарты</h2>
  <ul>
    <li>Использовать официальные источники для сроков, eligibility, продления и условий подачи.</li>
    <li>Разделять подтверждённый факт и редакционный вывод.</li>
    <li>По возможности указывать месяц и год проверки.</li>
    <li>Ставить nofollow на внешние официальные ссылки.</li>
    <li>Переписывать или обновлять страницу, если правило изменилось или появился более точный официальный источник.</li>
  </ul>
  <p>Перед подачей документы и правила всегда нужно перепроверять на официальной странице. Иммиграционные требования могут меняться без предупреждения.</p>
</section>
""",
    },
    "how-we-verify-data": {
        "title": "Как мы проверяем данные",
        "description": "Как Relocate to Asia проверяет визовые правила, страновые факты и сравнительные материалы.",
        "content": """
<section class="rta-trust-page">
  <h1>Как мы проверяем данные</h1>
  <p>В визовых и long-stay гайдах блок источников должен вести на официальные страницы: сайты иммиграции, министерств, консульств или самих государственных программ. Для ключевых цифр мы берём короткие подтверждённые формулировки, а затем отдельно объясняем, что они значат на практике.</p>
  <h2>Что мы проверяем</h2>
  <ul>
    <li>Кто является официальным источником по конкретной визе или программе.</li>
    <li>Базовые цифры: срок пребывания, валидность, доход, fee или deposit, если это указано в источнике.</li>
    <li>Упоминаются ли прямо local work, продление, dependants или смена статуса.</li>
    <li>Не попадают ли внутренние API и редакционная инфраструктура в публичный блок источников.</li>
    <li>Есть ли предупреждение там, где официальный источник что-то не подтверждает напрямую.</li>
  </ul>
</section>
""",
    },
}


@app.route("/about/")
def about():
    page = {"title": TRUST_PAGES["about"]["title"], "content": TRUST_PAGES["about"]["content"], "link": "/about/"}
    return render_page_row(page, breadcrumbs=[], extra_schema=trust_page_schema(page["title"], "/about/", page_type="AboutPage"))


@app.route("/ru/about/")
def ru_about():
    page = {"title": TRUST_PAGES_RU["about"]["title"], "content": TRUST_PAGES_RU["about"]["content"], "link": "/ru/about/"}
    return render_page_row(page, lang="ru", canonical_path="/ru/about/", breadcrumbs=[], extra_schema=trust_page_schema(page["title"], "/ru/about/", page_type="AboutPage"))


@app.route("/editorial-policy/")
def editorial_policy():
    page = {"title": TRUST_PAGES["editorial-policy"]["title"], "content": TRUST_PAGES["editorial-policy"]["content"], "link": "/editorial-policy/"}
    return render_page_row(page, breadcrumbs=[], extra_schema=trust_page_schema(page["title"], "/editorial-policy/"))


@app.route("/ru/editorial-policy/")
def ru_editorial_policy():
    page = {
        "title": TRUST_PAGES_RU["editorial-policy"]["title"],
        "content": TRUST_PAGES_RU["editorial-policy"]["content"],
        "link": "/ru/editorial-policy/",
    }
    return render_page_row(page, lang="ru", canonical_path="/ru/editorial-policy/", breadcrumbs=[], extra_schema=trust_page_schema(page["title"], "/ru/editorial-policy/"))


@app.route("/how-we-verify-data/")
def how_we_verify_data():
    page = {"title": TRUST_PAGES["how-we-verify-data"]["title"], "content": TRUST_PAGES["how-we-verify-data"]["content"], "link": "/how-we-verify-data/"}
    return render_page_row(page, breadcrumbs=[], extra_schema=trust_page_schema(page["title"], "/how-we-verify-data/"))


@app.route("/methodology/")
def methodology_redirect():
    return redirect("/how-we-verify-data/", 301)


@app.route("/ru/how-we-verify-data/")
def ru_how_we_verify_data():
    page = {
        "title": TRUST_PAGES_RU["how-we-verify-data"]["title"],
        "content": TRUST_PAGES_RU["how-we-verify-data"]["content"],
        "link": "/ru/how-we-verify-data/",
    }
    return render_page_row(page, lang="ru", canonical_path="/ru/how-we-verify-data/", breadcrumbs=[], extra_schema=trust_page_schema(page["title"], "/ru/how-we-verify-data/"))


@app.route("/ru/methodology/")
def ru_methodology_redirect():
    return redirect("/ru/how-we-verify-data/", 301)


def sitemap_paths() -> list[tuple[str, str]]:
    en_post_count = one("SELECT COUNT(*) AS count FROM posts WHERE lang = 'en'")["count"]
    ru_post_count = one("SELECT COUNT(*) AS count FROM posts WHERE lang = 'ru'")["count"]
    per_page = 10
    paths: list[tuple[str, str]] = [
        ("/", "daily"),
        ("/ru/", "daily"),
        ("/countries/", "weekly"),
        ("/ru/countries/", "weekly"),
        ("/tools/", "monthly"),
        ("/ru/tools/", "monthly"),
        ("/compare/", "weekly"),
        ("/ru/compare/", "weekly"),
        ("/compare-cities/", "monthly"),
        ("/ru/compare-cities/", "monthly"),
        ("/visas/", "weekly"),
        ("/ru/visas/", "weekly"),
        ("/best-countries-in-asia-to-move/", "monthly"),
        ("/ru/best-countries-in-asia-to-move/", "monthly"),
        ("/cheapest-countries-in-asia/", "monthly"),
        ("/ru/cheapest-countries-in-asia/", "monthly"),
        ("/move-to-asia/", "monthly"),
        ("/ru/move-to-asia/", "monthly"),
        ("/digital-nomad-visas-asia/", "monthly"),
        ("/ru/digital-nomad-visas-asia/", "monthly"),
        ("/retire-in-asia/", "monthly"),
        ("/ru/retire-in-asia/", "monthly"),
        ("/cost-of-living-asia/", "monthly"),
        ("/ru/cost-of-living-asia/", "monthly"),
        ("/guides/", "weekly"),
        ("/ru/guides/", "weekly"),
        ("/blog/", "daily"),
        ("/ru/blog/", "daily"),
        ("/about/", "monthly"),
        ("/ru/about/", "monthly"),
        ("/authors/", "monthly"),
        ("/ru/authors/", "monthly"),
        ("/authors/editorial-team/", "monthly"),
        ("/ru/authors/editorial-team/", "monthly"),
        ("/contact/", "monthly"),
        ("/ru/contact/", "monthly"),
        ("/editorial-policy/", "monthly"),
        ("/ru/editorial-policy/", "monthly"),
        ("/how-we-verify-data/", "monthly"),
        ("/ru/how-we-verify-data/", "monthly"),
    ]
    for page_num in range(2, max((en_post_count + per_page - 1) // per_page, 1) + 1):
        paths.append((f"/blog/page/{page_num}/", "daily"))
    for page_num in range(2, max((ru_post_count + per_page - 1) // per_page, 1) + 1):
        paths.append((f"/ru/blog/page/{page_num}/", "daily"))
    for row in many("SELECT link FROM pages WHERE link IS NOT NULL AND link != ''"):
        link = row["link"]
        if link.startswith(SITE_URL):
            link = link.removeprefix(SITE_URL) or "/"
        paths.append((link, "monthly"))
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
    alternate_map.update(compare_pair_map())
    alternate_map["/blog/"] = [
        {"lang": "en", "url": absolute_url("/blog/")},
        {"lang": "ru", "url": absolute_url("/ru/blog/")},
        {"lang": "x-default", "url": absolute_url("/blog/")},
    ]
    alternate_map["/ru/blog/"] = alternate_map["/blog/"]
    en_post_count = one("SELECT COUNT(*) AS count FROM posts WHERE lang = 'en'")["count"]
    ru_post_count = one("SELECT COUNT(*) AS count FROM posts WHERE lang = 'ru'")["count"]
    per_page = 10
    total_paginated = max(
        max((en_post_count + per_page - 1) // per_page, 1),
        max((ru_post_count + per_page - 1) // per_page, 1),
    )
    for page_num in range(2, total_paginated + 1):
        alternates = localized_page_alternates(
            en_path=f"/blog/page/{page_num}/",
            ru_path=f"/ru/blog/page/{page_num}/",
        )
        alternate_map[f"/blog/page/{page_num}/"] = alternates
        alternate_map[f"/ru/blog/page/{page_num}/"] = alternates
    urls = []
    for path, changefreq in sitemap_paths():
        alternates = alternate_map.get(path) or default_page_alternates(path) or []
        links = "".join(
            f"<xhtml:link rel=\"alternate\" hreflang=\"{escape(item['lang'])}\" href=\"{escape(item['url'])}\" />"
            for item in alternates
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
    is_ru = request.path.startswith("/ru/")
    lang = "ru" if is_ru else "en"
    en_path = "/"
    ru_path = "/ru/"
    seo = seo_payload(
        title="Страница не найдена" if is_ru else "Page Not Found",
        description=(
            "Страница не найдена. Используйте навигацию Relocate to Asia, чтобы перейти к странам, визам, сравнениям, инструментам и гайдам."
            if is_ru else
            "The page could not be found. Use Relocate to Asia navigation to browse countries, visas, comparisons, tools and relocation guides."
        ),
        lang=lang,
        canonical_path=request.path,
        alternates=localized_page_alternates(en_path=en_path, ru_path=ru_path),
    )
    seo["meta_robots"] = "noindex,follow"
    return render_template("404.html", seo=seo, lang_code=lang), 404


if __name__ == "__main__":
    app.run(debug=True)
