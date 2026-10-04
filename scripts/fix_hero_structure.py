"""
Fix the hero structure: move the description <p> back inside .rucmp-hero
and remove stray extra </div> tags.
"""
import re
import sqlite3

DB = r"D:\python-sas\content.db"


def fix_hero(content: str) -> str:
    # Pattern: hero closing </div> followed immediately by </div> and <p>
    # This happens when a previous script accidentally pushed <p> outside the hero.
    # Move it back: close hero AFTER the <p>.

    # First, remove any all-link that ended up outside the hero
    content = re.sub(r'<a class="rucmp-all-link"[^>]*>.*?</a>', "", content, flags=re.DOTALL)

    # The hero should be: <div class="rucmp-hero">...flags...</div>
    # followed by: <p>description</p>
    # We want: <div class="rucmp-hero">...flags...<p>description</p></div>

    # Find the hero div end and check if <p> is right after
    # Pattern: hero content ends with </div> (for flags or badge),
    # then 1-2 extra </div>, then <p>
    content = re.sub(
        r'(</div>)(\s*</div>\s*)(</div>)(\s*<p[^>]*>)',
        r'\1\3\4',  # remove the middle extra </div>
        content, count=1
    )

    # Now: <div class="rucmp-flags">...</div></div><p>...
    # We need to move <p>...</p> inside the hero before its </div>
    # Pattern: flags closing </div>, then hero </div>, then <p>.....</p>
    def move_p_inside(m):
        flags_close = m.group(1)   # </div> closing rucmp-flags
        hero_close = m.group(2)    # </div> closing rucmp-hero
        p_tag = m.group(3)         # <p>...</p>
        # Put p INSIDE hero: ...flags</div><p>...</p></div>
        return flags_close + p_tag + hero_close

    content = re.sub(
        r'(</div>)(</div>)(<p[^>]*>.*?</p>)',
        move_p_inside,
        content, count=1, flags=re.DOTALL
    )

    # Add all-link after the description <p>, before hero </div>
    # Pattern: <p>description</p></div><div class="rucmp-note"> OR <div class="rucmp-toc">
    all_link = '<a class="rucmp-all-link" href="/ru/compare/">&#8592; Все сравнения</a>'
    content = re.sub(
        r'(</p>)(</div>)(\s*<div class="rucmp-(?:note|toc)">)',
        r'\1' + all_link + r'\2\3',
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
        original = row["content"]
        updated = fix_hero(original)
        if updated != original:
            conn.execute(
                "UPDATE pages SET content = ? WHERE slug = ? AND parent = 'ru-compare'",
                (updated, slug)
            )
            print(f"Fixed {slug}: {len(original)} -> {len(updated)}")
        else:
            print(f"No change: {slug}")

    conn.commit()
    conn.close()
    print("Done.")


if __name__ == "__main__":
    main()
