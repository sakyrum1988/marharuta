"""Loopback-only preview of the Phuket-vs-Pattaya draft; never writes content.db."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import app as site

DRAFT = ROOT / "content/posts/phuket-ili-pattaya-dlya-zhizni-ru.json"
PREVIEW_PATH = "/ru/_editorial-preview/phuket-or-pattaya/"


def draft_row():
    row = json.loads(DRAFT.read_text(encoding="utf-8"))
    row["content"] = (DRAFT.parent / row["content_file"]).read_text(encoding="utf-8")
    row["link"] = f"/ru/blog/{row['slug']}/"
    row["status"] = "draft"
    row["date"] = ""
    return row


@site.app.get(PREVIEW_PATH)
def preview_phuket_pattaya():
    return site.Response(
        site.render_post_row(draft_row(), lang="ru", preview=True),
        headers={"X-Robots-Tag": "noindex, nofollow"},
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=5093)
    args = parser.parse_args()
    site.app.run(host="127.0.0.1", port=args.port, debug=False, use_reloader=False)
