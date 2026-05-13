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
  <p class="rta-muted">Числа по населению, интернету и macro-показателям взяты из последнего доступного набора World Bank в базе сайта. Год данных: {html.escape(str(year))}.</p>
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
        "retire-in-asia": ("Пенсия в Азии в 2026 году: визы, расходы и медицина", "Пенсионная релокация отличается от remote-work переезда. Здесь важнее медицина, страховка, банковская логика, валюта, dependants и стабильность long-stay маршрута.", [("Philippines SRRV", "Пенсионный маршрут с депозитом и логикой indefinite stay. Подходит не всем, но его стоит сравнить."), ("Малайзия", "Сильна английским, городами и медициной. Важно проверять актуальные условия MM2H."), ("Таиланд", "Сильный lifestyle и медицина в крупных городах, но визовый маршрут нужно проверять отдельно.")]),
        "cost-of-living-asia": ("Стоимость жизни в Азии в 2026 году", "Дешёвая страна не всегда подходит для переезда. Низкая аренда может идти вместе со слабой визовой логикой, дорогой медициной или городом, который не подходит под работу и семью.", [("Считайте полный месяц", "Аренда, еда, транспорт, связь, страховка, coworking, медицина и непредвиденные расходы."), ("Отделяйте старт от жизни", "Депозит, перелёты, визы и первый месяц часто ломают красивый бюджет."), ("Сравнивайте города", "Бангкок и Чиангмай, Куала-Лумпур и Пенанг, Бали и Джакарта — это разные бюджеты.")]),
        "visas": ("Визы Азии в 2026 году: long-stay, digital nomad и пенсионные маршруты", "Страну лучше выбирать после проверки визы. Иначе можно влюбиться в направление, которое не совпадает с вашим доходом, сроком stay, семьёй или типом работы.", [("Remote work", "Проверяйте, разрешена ли удалённая работа и где должен находиться работодатель."), ("Long-stay", "Смотрите срок, продление, доход, депозиты и dependants."), ("Retirement", "Медицина и стабильность часто важнее минимальной стоимости жизни.")]),
        "best-countries-in-asia-to-move": ("Лучшие страны Азии для переезда в 2026 году", "Лучшей страны для всех нет. Есть страна, которая совпадает с вашим бюджетом, визой, работой, семьёй и терпимостью к бытовым компромиссам.", [("Таиланд", "Сильный lifestyle, медицина и выбор городов. Визовый маршрут нужно подбирать аккуратно."), ("Малайзия", "Хороший английский, инфраструктура и long-stay логика для части профилей."), ("Тайвань", "Сильная безопасность, медицина и профессиональные маршруты.")]),
        "cheapest-countries-in-asia": ("Самые дешёвые страны Азии для жизни в 2026 году", "Дешевизна полезна только тогда, когда не ломает визу, медицину, интернет и качество жилья. Бюджет нужно считать вместе с рисками.", [("Вьетнам", "Часто силён по повседневным расходам, но long-stay логику нужно проверять отдельно."), ("Камбоджа", "Может быть бюджетной, но медицина и инфраструктура требуют осторожности."), ("Бали / Индонезия", "Бюджет зависит от района и lifestyle. Визовый маршрут нельзя оставлять на потом.")]),
    }
    data = hubs.get(slug)
    if not data:
        return None
    title, intro, cards = data
    card_html = "\n".join(f'<div class="rta-linkhub-card"><h3>{html.escape(card_title)}</h3><p>{html.escape(text)}</p></div>' for card_title, text in cards)
    return f"""
<section class="rta-article">
  <div class="rta-hero-card">
    <span class="rta-pill">Гид 2026</span>
    <h1>{html.escape(title)}</h1>
    <p>{html.escape(intro)}</p>
  </div>
  <h2>Короткий вывод</h2>
  <p>Начинайте не с эмоции, а с ограничения, которое может сломать план: виза, срок stay, подтверждение дохода, медицина, семья или бюджет. Когда это совпадает, страна уже становится реальным кандидатом.</p>
  <div class="rta-linkhub-grid">{card_html}</div>
  <h2>Как принимать решение</h2>
  <p>Сначала проверьте легальный маршрут. Потом посчитайте полный бюджет: стартовые расходы, месячную жизнь, страховку, депозиты и emergency fund. После этого сравнивайте города, районы и lifestyle.</p>
  <p>Если маршрут не подходит по документам, лучше узнать это сразу. Хорошая страна с неподходящей визой всё равно не становится хорошим планом.</p>
  <h2>Что открыть дальше</h2>
  <p>Используйте страновые страницы, визовый гид, сравнение стран и калькулятор стоимости жизни. Эти страницы работают вместе: одна показывает правила, другая деньги, третья бытовые компромиссы.</p>
</section>
"""


def ru_guide_article(slug: str, title: str) -> str | None:
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
    ]
    return replace_many(content, replacements)


def localized_country_content(slug: str, title: str, content: str) -> tuple[str, str]:
    content = localized_generic_content(content)
    forms = COUNTRY_FORMS_RU.get(slug)
    if forms:
        nominative, accusative, prep = forms
        facts = one("SELECT * FROM country_facts WHERE slug = ?", (slug,))
        return f"Переезд в {accusative}: гид по стране 2026", ru_country_article(slug, facts)
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
                ("From the buzzing capital Bangkok to the laid-back digital nomad capital of Chiang Mai, and the beach lifestyle of Phuket — Thailand offers multiple distinct environments to suit different lifestyles and budgets.", "У Таиланда нет одного единственного сценария. Бангкок, Чиангмай и Пхукет — это три очень разные модели жизни, и именно в этом страна часто выигрывает: можно подбирать среду под свой ритм, бюджет и тип работы."),
                ("Thailand has significantly expanded its long-term visa options in recent years. Here&#8217;s a breakdown of the most relevant visas for expats and digital nomads:", "За последние годы Таиланд заметно расширил выбор long-stay маршрутов. Ниже — те визы, которые чаще всего реально имеют смысл для expats и удалёнщиков."),
                ("Most digital nomads start with METV (multiple-entry tourist visa) while researching long-term options. The LTR Visa is the best path for those earning $80k+ remotely.", "Многие digital nomads начинают с METV, пока изучают долгий сценарий. LTR уже имеет смысл там, где есть сильный удалённый доход и понятный профиль под официальный маршрут."),
                ("Thailand&#8217;s cost of living varies significantly between cities. Bangkok is more expensive than Chiang Mai, but both remain affordable compared to Western standards.", "Стоимость жизни в Таиланде сильно зависит от города. Бангкок ощутимо дороже Чиангмая, но оба варианта всё ещё остаются доступнее многих западных сценариев."),
                ("Typical monthly expenses in Chiang Mai: rent $300–600, food $200–400, transport $50–100, entertainment $100–200. Bangkok adds roughly 30–40% to these figures.", "Типичный месячный сценарий в Чиангмае — это аренда $300–600, еда $200–400, транспорт $50–100 и досуг $100–200. Бангкок обычно добавляет к этим цифрам ещё примерно 30–40%."),
            ],
        }
        content = replace_many(content, slug_specific.get(slug, []))
        ru_title = f"Переезд в {accusative}: полный гид 2026"
    else:
        ru_title = title
    return ru_title, content


def localized_simple_page_content(slug: str, title: str, content: str) -> tuple[str, str]:
    content = localized_generic_content(content)
    title = RU_STATIC_TITLES.get(slug, title)
    hub_content = ru_hub_content(slug)
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
        r"The инструмент сравнения стран puts.*?data-driven choice\.",
        "Инструмент сравнения ставит две страны рядом по 15+ метрикам, чтобы решение было не на ощущениях.",
        content,
    )
    content = content.replace("Southeast and East Asia", "Юго-Восточной и Восточной Азии")
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


def render_page_row(row: sqlite3.Row | dict, **kwargs):
    breadcrumbs = kwargs.get("breadcrumbs", [])
    lang = kwargs.get("lang", "ru" if request.path.startswith("/ru/") else "en")
    path = local_path(kwargs.get("canonical_path") or (row["link"] if "link" in row.keys() and row["link"] else request.path))
    slug = row["slug"] if "slug" in row.keys() else request.path.strip("/")
    schema = [
        breadcrumb_schema(breadcrumbs, row["title"], path),
        organization_schema(),
        website_schema(),
    ]
    internal_links = internal_links_for_page(row, current_path=path)
    faq_schema = faq_schema_from_html(row["content"], lang=lang)
    if faq_schema:
        schema.append(faq_schema)
    item_list = item_list_schema(f"Internal links for {strip_html(row['title'])}", internal_links)
    if item_list:
        schema.append(item_list)
    if path in {"/compare/", "/compare-cities/", "/tools/cost-calculator/", "/tools/budget-planner/"}:
        schema.append(web_application_schema(row["title"], path, row["content"]))
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
        article_seo_panel=post_seo_panel(row, lang=lang),
        related_posts=related_posts(row),
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
        alternates=localized_page_alternates(en_path=f"/countries/{slug}/", ru_path=f"/ru/countries/{slug}/"),
        schema=schema,
    )
    return render_template(
        "country.html",
        page=row,
        facts=facts,
        seo=seo,
        breadcrumbs=[("Countries", "/countries/")],
        internal_links=internal_links,
        labels=localized_country_context_labels("en"),
    )


@app.route("/ru/countries/<slug>/")
def ru_country(slug: str):
    source = page_or_404(slug, parent="countries")
    facts = one("SELECT * FROM country_facts WHERE slug = ?", (slug,))
    title, content = localized_country_content(slug, source["title"], source["content"])
    row = localized_page_dict(slug=f"ru-{slug}", title=title, content=content, link=f"/ru/countries/{slug}/", parent="countries")
    path = f"/ru/countries/{slug}/"
    internal_links = internal_links_for_page(row, current_path=path)
    schema = [
        breadcrumb_schema([("Страны", "/ru/countries/")], row["title"], path),
        organization_schema(),
        website_schema(),
        country_schema(source, facts, path),
    ]
    item_list = item_list_schema(f"Internal links for {strip_html(row['title'])}", internal_links)
    if item_list:
        schema.append(item_list)
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
        facts=facts,
        seo=seo,
        breadcrumbs=[("Страны", "/ru/countries/")],
        internal_links=internal_links,
        lang_code="ru",
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


@app.route("/compare/")
def compare_index():
    row = page_or_404("compare")
    return render_page_row(row, breadcrumbs=[])


@app.route("/compare/<slug>/")
def compare(slug: str):
    row = page_or_404(slug, parent="compare")
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
    row = page_or_404(localized_compare_db_slug(slug), parent="ru-compare")
    return render_page_row(
        row,
        lang="ru",
        canonical_path=f"/ru/compare/{slug}/",
        alternates=localized_page_alternates(en_path=f"/compare/{slug}/", ru_path=f"/ru/compare/{slug}/"),
        breadcrumbs=[("Сравнение", "/ru/compare/")],
        show_internal_links=False,
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
    source = page_or_404("best-countries-in-asia-to-move")
    title, content = localized_simple_page_content("best-countries-in-asia-to-move", source["title"], source["content"])
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
    source = page_or_404("cheapest-countries-in-asia")
    title, content = localized_simple_page_content("cheapest-countries-in-asia", source["title"], source["content"])
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
    row = page_or_404("cost-of-living-asia")
    return render_page_row(row, breadcrumbs=[])


@app.route("/ru/cost-of-living-asia/")
def ru_cost_of_living_asia():
    source = page_or_404("cost-of-living-asia")
    title, content = localized_simple_page_content("cost-of-living-asia", source["title"], source["content"])
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
    en_path = "/blog/" if page == 1 else f"/blog/page/{page}/"
    ru_path = "/ru/blog/" if page == 1 else f"/ru/blog/page/{page}/"
    alternates = localized_page_alternates(en_path=en_path, ru_path=ru_path)
    seo = seo_payload(
        title=title,
        description=description,
        lang=lang,
        canonical_path=path if page == 1 else f"{path}page/{page}/",
        alternates=alternates,
        schema=[breadcrumb_schema([], title, path), collection_schema(title, description, path), organization_schema(), website_schema()],
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
        internal_links=internal_links_for_blog(lang),
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
    return render_page_row(page, breadcrumbs=[])


@app.route("/ru/about/")
def ru_about():
    page = {"title": TRUST_PAGES_RU["about"]["title"], "content": TRUST_PAGES_RU["about"]["content"], "link": "/ru/about/"}
    return render_page_row(page, lang="ru", canonical_path="/ru/about/", breadcrumbs=[])


@app.route("/editorial-policy/")
def editorial_policy():
    page = {"title": TRUST_PAGES["editorial-policy"]["title"], "content": TRUST_PAGES["editorial-policy"]["content"], "link": "/editorial-policy/"}
    return render_page_row(page, breadcrumbs=[])


@app.route("/ru/editorial-policy/")
def ru_editorial_policy():
    page = {
        "title": TRUST_PAGES_RU["editorial-policy"]["title"],
        "content": TRUST_PAGES_RU["editorial-policy"]["content"],
        "link": "/ru/editorial-policy/",
    }
    return render_page_row(page, lang="ru", canonical_path="/ru/editorial-policy/", breadcrumbs=[])


@app.route("/how-we-verify-data/")
def how_we_verify_data():
    page = {"title": TRUST_PAGES["how-we-verify-data"]["title"], "content": TRUST_PAGES["how-we-verify-data"]["content"], "link": "/how-we-verify-data/"}
    return render_page_row(page, breadcrumbs=[])


@app.route("/ru/how-we-verify-data/")
def ru_how_we_verify_data():
    page = {
        "title": TRUST_PAGES_RU["how-we-verify-data"]["title"],
        "content": TRUST_PAGES_RU["how-we-verify-data"]["content"],
        "link": "/ru/how-we-verify-data/",
    }
    return render_page_row(page, lang="ru", canonical_path="/ru/how-we-verify-data/", breadcrumbs=[])


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
