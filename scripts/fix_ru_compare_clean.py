"""
Clean up duplicate additions, then re-apply once correctly.
Run this ONCE to fix all ru-compare pages.
"""
import re
import sqlite3

DB = r"D:\python-sas\content.db"

FLAGS_MAP = {
    "ru-thailand-vs-malaysia":   ("\U0001f1f9\U0001f1ed", "Таиланд",  "\U0001f1f2\U0001f1fe", "Малайзия"),
    "ru-bali-vs-thailand":       ("\U0001f1ee\U0001f1e9", "Бали",     "\U0001f1f9\U0001f1ed", "Таиланд"),
    "ru-japan-vs-taiwan":        ("\U0001f1ef\U0001f1f5", "Япония",   "\U0001f1f9\U0001f1fc", "Тайвань"),
    "ru-thailand-vs-vietnam":    ("\U0001f1f9\U0001f1ed", "Таиланд",  "\U0001f1fb\U0001f1f3", "Вьетнам"),
    "ru-malaysia-vs-vietnam":    ("\U0001f1f2\U0001f1fe", "Малайзия", "\U0001f1fb\U0001f1f3", "Вьетнам"),
    "ru-singapore-vs-hong-kong": ("\U0001f1f8\U0001f1ec", "Сингапур", "\U0001f1ed\U0001f1f0", "Гонконг"),
    "ru-uae-vs-qatar":           ("\U0001f1e6\U0001f1ea", "ОАЭ",      "\U0001f1f6\U0001f1e6", "Катар"),
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


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    text = re.sub(r"\s+", "-", text)
    return text[:40]


def strip_tags(html: str) -> str:
    return re.sub(r"<[^>]+>", "", html)


# ── Step 1: remove all previously added elements ──────────────────────────────

def remove_div_block(content: str, class_name: str) -> str:
    """Remove all <div class="class_name">...</div> blocks, handling nested divs."""
    marker = f'<div class="{class_name}">'
    while marker in content:
        start = content.find(marker)
        if start == -1:
            break
        depth = 0
        i = start
        while i < len(content):
            if content[i:i+4] == "<div":
                depth += 1
            elif content[i:i+6] == "</div>":
                depth -= 1
                if depth == 0:
                    content = content[:start] + content[i+6:]
                    break
            i += 1
        else:
            break  # malformed HTML, stop
    return content


def remove_added_elements(content: str) -> str:
    content = remove_div_block(content, "rucmp-flags")
    content = remove_div_block(content, "rucmp-toc")
    content = remove_div_block(content, "rucmp-switch")
    # Remove orphaned VS+flag fragments (residual from bad previous runs)
    content = re.sub(r'<span class="rucmp-vs">.*?</span>', "", content, flags=re.DOTALL)
    content = re.sub(r'<div class="rucmp-flag-box">.*?</div>', "", content, flags=re.DOTALL)
    # Remove all-link anchors
    content = re.sub(r'<a class="rucmp-all-link"[^>]*>.*?</a>', "", content, flags=re.DOTALL)
    # Remove section IDs we may have added
    content = re.sub(r'<section class="rucmp-section" id="[^"]*">', '<section class="rucmp-section">', content)
    return content


# ── Step 2: apply all improvements once cleanly ───────────────────────────────

def build_flags(slug: str) -> str:
    f1_emoji, f1_name, f2_emoji, f2_name = FLAGS_MAP[slug]
    return (
        '<div class="rucmp-flags">'
        f'<div class="rucmp-flag-box"><span class="flag">{f1_emoji}</span><span class="name">{f1_name}</span></div>'
        '<span class="rucmp-vs">VS</span>'
        f'<div class="rucmp-flag-box"><span class="flag">{f2_emoji}</span><span class="name">{f2_name}</span></div>'
        '</div>'
    )


def build_toc(headings: list[str]) -> str:
    skip = {"Что посмотреть дальше", "Частые вопросы"}
    items = []
    for h in headings:
        clean = strip_tags(h).strip()
        if clean in skip:
            continue
        slug = slugify(clean)
        items.append(f'<li><a href="#{slug}">{clean}</a></li>')
    if not items:
        return ""
    return (
        '<div class="rucmp-toc">'
        '<h3>Содержание</h3>'
        f'<ol>{"".join(items)}</ol>'
        '</div>'
    )


def add_section_ids(content: str, headings: list[str]) -> str:
    for h in headings:
        clean = strip_tags(h).strip()
        slug = slugify(clean)
        pattern = r'(<section class="rucmp-section">)(\s*' + re.escape(f'<h2>{clean}</h2>') + r')'
        content = re.sub(pattern, f'<section class="rucmp-section" id="{slug}">\\2', content, count=1)
    return content


def transform(slug: str, content: str) -> str:
    # 1. Clean <style>
    content = re.sub(r"<style>.*?</style>", NEW_CSS, content, flags=re.DOTALL)

    # 2. Strip previously added elements (idempotent cleanup)
    content = remove_added_elements(content)

    # 3. Add flags after first <h1>...</h1>
    flags_html = build_flags(slug)
    if flags_html:
        content = re.sub(r"(<h1[^>]*>.*?</h1>)", r"\1" + flags_html, content, count=1, flags=re.DOTALL)

    # 4. Add TOC — right before first .rucmp-section (after hero+note)
    headings = re.findall(r"<h2>(.*?)</h2>", content)
    toc = build_toc(headings)
    if toc:
        if '<div class="rucmp-note">' in content:
            # after note
            content = re.sub(
                r'(</div>)(\s*<section class="rucmp-section")',
                r"\1\n" + toc + r"\n\2",
                content, count=1
            )
        else:
            # before first section
            content = content.replace(
                '<section class="rucmp-section">',
                toc + '\n<section class="rucmp-section">',
                1
            )

    # 5. Add section IDs
    content = add_section_ids(content, headings)

    # 6. Add subtle all-comparisons link at bottom of hero
    all_link = '<a class="rucmp-all-link" href="/ru/compare/">&#8592; Все сравнения</a>'
    # Place it right before the closing </div> of .rucmp-hero
    # The hero ends with the <p> description, then </div>
    # We look for </p></div> just before </section> or note/toc
    content = re.sub(
        r"(</p>\s*)(</div>)(\s*(?:<div class=\"rucmp-(?:note|toc)\">|<section))",
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
        if slug not in FLAGS_MAP:
            print(f"SKIP {slug}")
            continue
        original = row["content"]
        updated = transform(slug, original)
        conn.execute(
            "UPDATE pages SET content = ? WHERE slug = ? AND parent = 'ru-compare'",
            (updated, slug)
        )
        print(f"OK {slug}: {len(original)} -> {len(updated)} chars")

    conn.commit()
    conn.close()
    print("Done.")


if __name__ == "__main__":
    main()
