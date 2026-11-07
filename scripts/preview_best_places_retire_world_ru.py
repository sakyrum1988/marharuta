"""Loopback-only preview of the unpublished Russian retirement article."""
import argparse
import html
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import app as site

DRAFT = ROOT / "content/drafts/luchshie-strany-dlya-pensionerov-ru.json"


def draft_row():
    row = json.loads(DRAFT.read_text(encoding="utf-8"))
    row["content"] = (DRAFT.parent / row["content_file"]).read_text(encoding="utf-8")
    row["link"] = f"/ru/blog/{row['slug']}/"
    return row


@site.app.get("/_editorial-preview/luchshie-strany-pensionerov/")
def preview():
    return site.render_post_row(draft_row(), lang="ru", preview=True)


@site.app.get("/_editorial-preview/luchshie-strany-pensionerov/<int:width>/")
def responsive_preview(width):
    if width not in {1280, 820, 390}:
        site.abort(404)
    with site.app.test_client() as client:
        body = client.get("/_editorial-preview/luchshie-strany-pensionerov/").get_data(as_text=True)
    scale = min(1, 960 / width)
    return site.Response(
        f'''<!doctype html><html lang="ru"><meta charset="utf-8">
        <meta name="robots" content="noindex,nofollow"><title>QA RU retirement article {width}px</title>
        <style>body{{margin:12px;background:#e8ece9;font:14px sans-serif}}
        iframe{{border:1px solid #aaa;width:{width}px;height:{int(1600/scale)}px;
        transform:scale({scale});transform-origin:top left}}</style>
        <p>Editorial preview: {width}px viewport</p>
        <iframe title="Editorial preview" srcdoc="{html.escape(body, quote=True)}"></iframe></html>''',
        headers={"X-Robots-Tag": "noindex, nofollow"},
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=5093)
    args = parser.parse_args()
    site.app.run(host="127.0.0.1", port=args.port, debug=False, use_reloader=False)
