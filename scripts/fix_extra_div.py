"""Remove the extra </div> between hero and rucmp-note."""
import re
import sqlite3

DB = r"D:\python-sas\content.db"


def fix(content: str) -> str:
    # Remove orphaned </div> between hero's </div> and rucmp-note/toc
    return re.sub(
        r'(</div>)(</div>)(\s*<div class="rucmp-(?:note|toc)">)',
        r'\1\3',
        content, count=1
    )


def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT slug, content FROM pages WHERE parent = 'ru-compare'"
    ).fetchall()
    for row in rows:
        slug = row["slug"]
        updated = fix(row["content"])
        if updated != row["content"]:
            conn.execute(
                "UPDATE pages SET content = ? WHERE slug = ? AND parent = 'ru-compare'",
                (updated, slug)
            )
            print(f"Fixed {slug}")
        else:
            print(f"No change: {slug}")
    conn.commit()
    conn.close()
    print("Done.")


if __name__ == "__main__":
    main()
