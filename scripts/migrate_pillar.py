"""Migrate 5 simple RU compare pages to use pillar-* classes (same as EN)."""
import sqlite3, re, sys
sys.stdout.reconfigure(encoding="utf-8")

conn = sqlite3.connect("D:/python-sas/content.db")

# Get pillar CSS from EN page
pillar_css_raw = conn.execute("SELECT content FROM pages WHERE slug=?", ("thailand-vs-vietnam",)).fetchone()[0]
css_block = re.search(r"(<style[^>]*>[\s\S]*?</style>)", pillar_css_raw).group(1)

# Common RU strings
badge = "Справочник 2026"
h2_read = "Как читать это сравнение"
h2_start = "С чего начать"
p_common = "Не выбирайте только по образу жизни. Сравните визовый маршрут, бюджет, медицину, подходящий город и необходимый срок пребывания."
card_p = "Откройте гид прежде чем выбирать направление."
faq_h2 = "FAQ"
faq1_q = "Какая страна лучше?"
faq1_a = "Лучшая страна та, которая совпадает с вашим визовым маршрутом, бюджетом и рабочей моделью."
faq2_q = "Стоит ли решать только по цене?"
faq2_a = "Нет. Цена важна, но виза, стабильность пребывания и медицина могут быть важнее."
faq3_q = "Что изучать дальше?"
faq3_a = "Откройте страновые гиды и визовые материалы по ссылкам выше, затем используйте инструмент сравнения."


def make_pillar(ru_h1, ru_hero_p, ru_h2_text, cards):
    cards_html = "".join(
        f'<a class="pillar-card" href="{href}"><h3>{title}</h3><p>{card_p}</p></a>'
        for href, title in cards
    )
    return (
        css_block
        + f'\n<section class="pillar"><div class="pillar-hero"><div class="badge">{badge}</div>'
        + f"<h1>{ru_h1}</h1><p>{ru_hero_p}</p></div>"
        + f"<h2>{h2_read}</h2><p>{ru_h2_text}</p><p>{p_common}</p>"
        + f'<h2>{h2_start}</h2><div class="pillar-grid">{cards_html}</div>'
        + f'<section class="pillar-faq"><h2>{faq_h2}</h2>'
        + f"<details><summary>{faq1_q}</summary><p>{faq1_a}</p></details>"
        + f"<details><summary>{faq2_q}</summary><p>{faq2_a}</p></details>"
        + f"<details><summary>{faq3_q}</summary><p>{faq3_a}</p></details>"
        + "</section></section>"
    )


pages = [
    {
        "ru_slug": "ru-thailand-vs-vietnam",
        "ru_title": "Таиланд или Вьетнам: что лучше для переезда в 2026 году",
        "ru_h1": "Таиланд или Вьетнам: что лучше для переезда в 2026 году",
        "ru_hero_p": "У Таиланда обычно шире экспат-инфраструктура; Вьетнам может быть сильнее по бюджету и для короткого пробного пребывания. Визовый маршрут и выбор города решают больше, чем заголовочная стоимость.",
        "ru_h2_text": "У Таиланда обычно шире экспат-инфраструктура; Вьетнам может быть сильнее по бюджету и для короткого пробного пребывания. Визовый маршрут и выбор города решают больше, чем заголовочная стоимость.",
        "cards": [
            ("/ru/countries/move-to-thailand/", "Переезд в Таиланд"),
            ("/ru/countries/move-to-vietnam/", "Переезд во Вьетнам"),
            ("/blog/thailand-ltr-remote-workers-2026/", "Виза LTR Таиланд"),
            ("/blog/vietnam-evisa-guide-2026/", "Электронная виза Вьетнам"),
        ],
    },
    {
        "ru_slug": "ru-malaysia-vs-vietnam",
        "ru_title": "Малайзия или Вьетнам: что лучше для переезда в 2026 году",
        "ru_h1": "Малайзия или Вьетнам: что лучше для переезда в 2026 году",
        "ru_hero_p": "Малайзия обычно проще для англоязычной городской жизни; Вьетнам может быть дешевле и динамичнее, но требует тщательного планирования виз. Сравнивайте стоимость, комфорт и логику пребывания вместе.",
        "ru_h2_text": "Малайзия обычно проще для англоязычной городской жизни; Вьетнам может быть дешевле и динамичнее, но требует тщательного планирования виз. Сравнивайте стоимость, комфорт и логику пребывания вместе.",
        "cards": [
            ("/ru/countries/move-to-malaysia/", "Переезд в Малайзию"),
            ("/ru/countries/move-to-vietnam/", "Переезд во Вьетнам"),
            ("/blog/malaysia-digital-nomad-guide-2026/", "Гид цифрового номада: Малайзия"),
            ("/blog/vietnam-evisa-guide-2026/", "Электронная виза Вьетнам"),
        ],
    },
    {
        "ru_slug": "ru-singapore-vs-hong-kong",
        "ru_title": "Сингапур или Гонконг: что лучше для переезда в 2026 году",
        "ru_h1": "Сингапур или Гонконг: что лучше для переезда в 2026 году",
        "ru_hero_p": "Сингапур и Гонконг — премиальные профессиональные хабы. Выбор здесь меньше о дешёвой жизни и больше о карьерном профиле, визовом маршруте, налогах, жилье и региональном доступе.",
        "ru_h2_text": "Сингапур и Гонконг — премиальные профессиональные хабы. Выбор здесь меньше о дешёвой жизни и больше о карьерном профиле, визовом маршруте, налогах, жилье и региональном доступе.",
        "cards": [
            ("/ru/countries/move-to-singapore/", "Переезд в Сингапур"),
            ("/ru/countries/move-to-china/", "Переезд в Китай"),
            ("/blog/singapore-one-pass-2026/", "ONE Pass Сингапур"),
            ("/blog/hong-kong-top-talent-pass-2026/", "Top Talent Pass Гонконг"),
        ],
    },
    {
        "ru_slug": "ru-uae-vs-qatar",
        "ru_title": "ОАЭ или Катар: что лучше для переезда в 2026 году",
        "ru_h1": "ОАЭ или Катар: что лучше для переезда в 2026 году",
        "ru_hero_p": "ОАЭ и Катар — хабы Персидского залива с разными маршрутами въезда, рабочими условиями и профилями расходов. Удалённые работники должны проверять подтверждение работы и визовые условия перед выбором.",
        "ru_h2_text": "ОАЭ и Катар — хабы Персидского залива с разными маршрутами въезда, рабочими условиями и профилями расходов. Удалённые работники должны проверять подтверждение работы и визовые условия перед выбором.",
        "cards": [
            ("/ru/countries/move-to-uae/", "Переезд в ОАЭ"),
            ("/ru/visas/", "Гид по визам Азии"),
            ("/blog/uae-virtual-work-visa-2026/", "Виртуальная рабочая виза ОАЭ"),
            ("/blog/qatar-hayya-tourist-visa-2026/", "Виза Hayya Катар"),
        ],
    },
    {
        "ru_slug": "ru-japan-vs-taiwan",
        "ru_title": "Япония или Тайвань: что лучше для переезда в 2026 году",
        "ru_h1": "Япония или Тайвань: что лучше для переезда в 2026 году",
        "ru_hero_p": "Япония сильнее для короткого культурного погружения; Тайвань обычно практичнее для специалистов, подходящих под логику Gold Card. Сравнивайте срок визы, бюджетную нагрузку, язык, медицину и стабильность долгосрочного пребывания.",
        "ru_h2_text": "Япония сильнее для короткого культурного погружения; Тайвань обычно практичнее для специалистов, подходящих под логику Gold Card. Сравнивайте срок визы, бюджетную нагрузку, язык, медицину и стабильность долгосрочного пребывания.",
        "cards": [
            ("/ru/countries/move-to-japan/", "Переезд в Японию"),
            ("/ru/countries/move-to-taiwan/", "Переезд на Тайвань"),
            ("/blog/japan-digital-nomad-visa-2026/", "Виза цифрового номада Япония"),
            ("/blog/taiwan-gold-card-guide-2026/", "Taiwan Gold Card"),
        ],
    },
]

for p in pages:
    content = make_pillar(p["ru_h1"], p["ru_hero_p"], p["ru_h2_text"], p["cards"])
    conn.execute(
        "UPDATE pages SET title=?, content=? WHERE slug=?",
        (p["ru_title"], content, p["ru_slug"]),
    )
    # Verify classes
    import re as re2
    classes = set(re2.findall(r'class="([a-z][a-z-]+)"', content))
    prefixes = sorted(set(c.split("-")[0] + "-" if "-" in c else c for c in classes))
    print(f"Updated {p['ru_slug']}: classes={prefixes}")

conn.commit()
print("Done.")
