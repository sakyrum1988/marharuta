"""Fix RU compare pages: better badge styling, flags in hero, TOC, remove switch buttons."""
import re
import sqlite3

DB = r"D:\python-sas\content.db"

FLAGS = {
    "ru-thailand-vs-malaysia":  ("🇹🇭", "Таиланд", "🇲🇾", "Малайзия"),
    "ru-bali-vs-thailand":      ("🇮🇩", "Бали",    "🇹🇭", "Таиланд"),
    "ru-japan-vs-taiwan":       ("🇯🇵", "Япония",  "🇹🇼", "Тайвань"),
    "ru-thailand-vs-vietnam":   ("🇹🇭", "Таиланд", "🇻🇳", "Вьетнам"),
    "ru-malaysia-vs-vietnam":   ("🇲🇾", "Малайзия","🇻🇳", "Вьетнам"),
    "ru-singapore-vs-hong-kong":("🇸🇬", "Сингапур","🇭🇰", "Гонконг"),
    "ru-uae-vs-qatar":          ("🇦🇪", "ОАЭ",     "🇶🇦", "Катар"),
}

NEW_CSS = """\
<style>
.rucmp{max-width:1040px;margin:0 auto;padding:20px 0 46px}
.rucmp-hero{background:linear-gradient(135deg,#0d1f3c 0%,#1a3a6c 50%,#0d3320 100%);color:#fff;padding:48px 32px;border-radius:16px;text-align:center;margin-bottom:36px;box-shadow:0 18px 44px rgba(13,31,60,.18)}
.rucmp-badge{display:inline-block;background:rgba(255,255,255,.15);border:1px solid rgba(255,255,255,.3);font-size:11px;font-weight:700;letter-spacing:2px;padding:6px 16px;border-radius:20px;margin-bottom:18px;text-transform:uppercase}
.rucmp-hero h1{font-size:clamp(24px,4vw,42px);font-weight:800;margin:0 0 12px;line-height:1.18;color:#fff!important}
.rucmp-hero p{font-size:16px;opacity:.86;max-width:640px;margin:0 auto;line-height:1.7}
.rucmp-flags{display:flex;justify-content:center;align-items:center;gap:24px;margin:28px 0 8px;flex-wrap:wrap}
.rucmp-flag-box{text-align:center}
.rucmp-flag-box .flag{font-size:52px;display:block;line-height:1}
.rucmp-flag-box .name{font-size:13px;font-weight:700;margin-top:6px;opacity:.9}
.rucmp-vs{font-size:26px;font-weight:900;opacity:.45}
.rucmp-toc{background:#f0f4ff;border-left:4px solid #1a3a6c;border-radius:8px;padding:20px 26px;margin-bottom:32px}
.rucmp-toc h3{margin:0 0 10px;font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:#555}
.rucmp-toc ol{margin:0;padding-left:20px;column-count:2;column-gap:32px}
.rucmp-toc li{margin-bottom:5px}
.rucmp-toc a{color:#1a3a6c;text-decoration:none;font-weight:500;font-size:14px}
.rucmp-toc a:hover{text-decoration:underline}
@media(max-width:580px){.rucmp-toc ol{column-count:1}}
.rucmp-note{background:#fff7e8;border:1px solid #f0c976;border-radius:12px;padding:16px 18px;margin:0 0 28px;color:#7a5700;line-height:1.65}
.rucmp-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px;margin:26px 0 34px}
.rucmp-card{background:#fff;border:1px solid #dbe5f1;border-radius:14px;padding:20px;box-shadow:0 8px 24px rgba(15,34,66,.05)}
.rucmp-card h3{margin:0 0 8px;color:#0f2242;font-size:22px;line-height:1.25}
.rucmp-card p{margin:0;color:#4a5b70;line-height:1.68}
.rucmp-section{margin:34px 0}
.rucmp-section h2{margin:0 0 14px;color:#0f2242;font-size:clamp(22px,3vw,32px);line-height:1.18;padding-bottom:10px;border-bottom:2px solid #eef2f8}
.rucmp-section p{color:#334155;line-height:1.8;margin:0 0 14px}
.rucmp-list{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;margin:20px 0;padding:0}
.rucmp-list li{list-style:none;background:#f8fbff;border:1px solid #dbe5f1;border-radius:12px;padding:14px 16px;color:#334155;line-height:1.65}
.rucmp-list strong{color:#0f2242}
.rucmp-links{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;margin:22px 0 10px}
.rucmp-link{display:block;background:#fff;border:1px solid #dbe5f1;border-radius:12px;padding:18px;text-decoration:none;box-shadow:0 8px 20px rgba(15,34,66,.05)}
.rucmp-link:hover{transform:translateY(-2px);border-color:#b8cbe4;box-shadow:0 14px 28px rgba(15,34,66,.1)}
.rucmp-link h3{margin:0 0 8px;color:#0f2242;font-size:17px}
.rucmp-link p{margin:0;color:#516274;line-height:1.6}
.rucmp-faq details{background:#fff;border:1px solid #dbe5f1;border-radius:12px;padding:16px 18px;margin-bottom:12px}
.rucmp-faq summary{cursor:pointer;font-weight:800;color:#0f2242}
.rucmp-faq p{margin:10px 0 0;color:#334155}
.rucmp-all-link{display:inline-block;margin-top:22px;padding:9px 16px;border:1px solid rgba(255,255,255,.35);border-radius:8px;color:rgba(255,255,255,.85);font-size:13px;font-weight:600;text-decoration:none;transition:background .15s}
.rucmp-all-link:hover{background:rgba(255,255,255,.12)}
@media(max-width:820px){.rucmp-grid,.rucmp-list,.rucmp-links{grid-template-columns:1fr}.rucmp-hero{padding:32px 18px}.rucmp-hero p{font-size:15px}}
</style>"""


def slugify_heading(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-zа-яёa-z0-9\s-]", "", text)
    text = re.sub(r"\s+", "-", text)
    return text[:40]


def extract_headings(content: str) -> list[str]:
    return re.findall(r"<h2[^>]*>(.*?)</h2>", content, re.DOTALL)


def add_ids_to_sections(content: str, headings: list[str]) -> str:
    for h in headings:
        slug = slugify_heading(re.sub(r"<[^>]+>", "", h))
        pattern = r'(<section class="rucmp-section">)(\s*<h2[^>]*>' + re.escape(h) + r'</h2>)'
        content = re.sub(pattern, f'<section class="rucmp-section" id="{slug}">\\2', content, count=1)
    return content


def build_toc(headings: list[str]) -> str:
    items = []
    for h in headings:
        clean = re.sub(r"<[^>]+>", "", h).strip()
        slug = slugify_heading(clean)
        items.append(f'<li><a href="#{slug}">{clean}</a></li>')
    return (
        '<div class="rucmp-toc">'
        '<h3>Содержание</h3>'
        f'<ol>{"".join(items)}</ol>'
        '</div>'
    )


def build_flags(slug: str) -> str:
    f1_emoji, f1_name, f2_emoji, f2_name = FLAGS[slug]
    return (
        '<div class="rucmp-flags">'
        f'<div class="rucmp-flag-box"><span class="flag">{f1_emoji}</span><span class="name">{f1_name}</span></div>'
        '<span class="rucmp-vs">VS</span>'
        f'<div class="rucmp-flag-box"><span class="flag">{f2_emoji}</span><span class="name">{f2_name}</span></div>'
        '</div>'
    )


def transform(slug: str, content: str) -> str:
    # 1. Replace <style> block
    content = re.sub(r"<style>.*?</style>", NEW_CSS, content, flags=re.DOTALL)

    # 2. Remove .rucmp-switch buttons from hero
    content = re.sub(r'<div class="rucmp-switch">.*?</div>', "", content, flags=re.DOTALL)

    # 3. Add flags after <h1>...</h1> inside .rucmp-hero
    flags_html = build_flags(slug)
    content = re.sub(r"(<h1[^>]*>.*?</h1>)", r"\1" + flags_html, content, count=1, flags=re.DOTALL)

    # 4. Add TOC after the hero div (before .rucmp-note or first .rucmp-section)
    headings = extract_headings(content)
    headings_clean = [h for h in headings if "Что посмотреть" not in h and "Частые вопросы" not in h]
    toc = build_toc(headings_clean)

    # Insert TOC after closing </div> of .rucmp-hero
    # The hero ends with </div>, we find the pattern after rucmp-hero content
    # Insert before .rucmp-note or before first .rucmp-section
    toc_inserted = False
    if '<div class="rucmp-note">' in content:
        content = content.replace('<div class="rucmp-note">', toc + '\n<div class="rucmp-note">', 1)
        toc_inserted = True
    if not toc_inserted:
        content = re.sub(
            r'(<section class="rucmp-section")',
            toc + r'\n\1',
            content, count=1
        )

    # 5. Add section IDs
    content = add_ids_to_sections(content, headings)

    # 6. Add "all comparisons" subtle link — after the hero's <p>, before </div></div> closing
    all_link = '<a class="rucmp-all-link" href="/ru/compare/">&#8592; Все сравнения на русском</a>'
    # The hero ends: ...description </p></div><div class="rucmp-toc"> or </p></div><div class="rucmp-note">
    content = re.sub(
        r'(</p>)(</div>)(\s*<div class="rucmp-(?:toc|note)")',
        r"\1" + all_link + r"\2\3",
        content, count=1, flags=re.DOTALL
    )

    return content


def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT slug, content FROM pages WHERE parent = 'ru-compare' ORDER BY slug"
    ).fetchall()

    for row in rows:
        slug = row["slug"]
        if slug not in FLAGS:
            print(f"SKIP {slug} (no flags defined)")
            continue
        original = row["content"]
        updated = transform(slug, original)
        conn.execute(
            "UPDATE pages SET content = ? WHERE slug = ? AND parent = 'ru-compare'",
            (updated, slug)
        )
        print(f"Updated {slug}: {len(original)} -> {len(updated)} chars")

    conn.commit()
    conn.close()
    print("Done.")


if __name__ == "__main__":
    main()
