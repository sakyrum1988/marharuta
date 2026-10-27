"""Insert or refresh the researched relocation guide hubs."""

from pathlib import Path
import sqlite3


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "content.db"
GUIDE_DIR = ROOT / "content" / "guides"

GUIDES = {
    "safety": "Safety in Asia: How to Choose a Country and City",
    "housing-rent": "Renting in Asia: A Safe Housing Guide for Expats",
    "culture-language": "Culture and Language in Asia: A Practical Moving Guide",
    "jobs-business": "Jobs and Business in Asia: Legal Routes for Expats",
    "healthcare": "Healthcare in Asia: Insurance and Hospital Planning",
    "banking": "Banking in Asia: Accounts, KYC and International Transfers",
    "driving-transport": "Driving and Transport in Asia: Licences, Safety and City Choice",
    "taxes": "Taxes in Asia for Expats: Residence, Income and Filing",
}

COMPARE_PAGES = {
    "cost-of-living": "Compare Cost of Living in Asia: Cities, Budgets and Setup Costs",
    "rankings": "Asian Country and City Rankings: Choose by Relocation Priorities",
    "safest-countries": "Safest Countries in Asia in 2026: A Relocation-Focused Ranking",
}

OTHER_PAGES = (
    ("country-finder", "Country Finder for Moving to Asia", "tools", "/tools/country-finder/", ROOT / "content" / "tools" / "country-finder-en.html"),
    ("residency-citizenship", "Residency and Citizenship in Asia: Compare the Routes", "visas", "/visas/residency-citizenship/", ROOT / "content" / "visas" / "residency-citizenship-en.html"),
    ("move-to-hong-kong", "Moving to Hong Kong: Visas, Work and Costs", "countries", "/countries/hong-kong/", ROOT / "content" / "countries" / "move-to-hong-kong-en.html"),
    ("work-visas", "Work Visas in Asia: Compare Employer-Sponsored Routes", "visas", "/visas/work/", ROOT / "content" / "visas" / "work-visas-en.html"),
    ("long-stay", "Long-Stay Visas in Asia: Compare the Real Routes", "visas", "/visas/long-stay/", ROOT / "content" / "visas" / "long-stay-en.html"),
    ("student", "Student Visas in Asia: Admission, Work Rights and Costs", "visas", "/visas/student/", ROOT / "content" / "visas" / "student-en.html"),
)


def main() -> None:
    with sqlite3.connect(DB_PATH) as connection:
        for slug, title in GUIDES.items():
            content = (GUIDE_DIR / f"{slug}-en.html").read_text(encoding="utf-8")
            link = f"/guides/{slug}/"
            existing = connection.execute(
                "SELECT id FROM pages WHERE slug = ? AND parent = 'guides'", (slug,)
            ).fetchone()
            if existing:
                connection.execute(
                    "UPDATE pages SET title = ?, content = ?, link = ? WHERE id = ?",
                    (title, content, link, existing[0]),
                )
            else:
                connection.execute(
                    "INSERT INTO pages (slug, title, content, parent, link) VALUES (?, ?, ?, 'guides', ?)",
                    (slug, title, content, link),
                )
        for slug, title in COMPARE_PAGES.items():
            for lang, parent in (("en", "compare"), ("ru", "ru-compare")):
                db_slug = slug if lang == "en" else f"ru-{slug}"
                content_path = ROOT / "content" / "compare" / f"{slug}-{lang}.html"
                content = content_path.read_text(encoding="utf-8")
                page_title = title
                if lang == "ru":
                    page_title = {
                        "cost-of-living": "Сравнение стоимости жизни в Азии: города и полный бюджет",
                        "rankings": "Рейтинг стран и городов Азии для переезда",
                        "safest-countries": "Самые безопасные страны Азии в 2026 году",
                    }[slug]
                link = f"/{'ru/' if lang == 'ru' else ''}compare/{slug}/"
                existing = connection.execute(
                    "SELECT id FROM pages WHERE slug = ? AND parent = ?", (db_slug, parent)
                ).fetchone()
                if existing:
                    connection.execute(
                        "UPDATE pages SET title = ?, content = ?, link = ? WHERE id = ?",
                        (page_title, content, link, existing[0]),
                    )
                else:
                    connection.execute(
                        "INSERT INTO pages (slug, title, content, parent, link) VALUES (?, ?, ?, ?, ?)",
                        (db_slug, page_title, content, parent, link),
                    )
        for slug, title, parent, link, source_path in OTHER_PAGES:
            content = source_path.read_text(encoding="utf-8")
            existing = connection.execute(
                "SELECT id FROM pages WHERE slug = ? AND parent = ?", (slug, parent)
            ).fetchone()
            if existing:
                connection.execute(
                    "UPDATE pages SET title = ?, content = ?, link = ? WHERE id = ?",
                    (title, content, link, existing[0]),
                )
            else:
                connection.execute(
                    "INSERT INTO pages (slug, title, content, parent, link) VALUES (?, ?, ?, ?, ?)",
                    (slug, title, content, parent, link),
                )
        connection.commit()


if __name__ == "__main__":
    main()
