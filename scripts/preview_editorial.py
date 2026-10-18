"""Loopback-only preview of an unpublished article; never writes content.db."""
import argparse
import html
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import app as site

DRAFT = ROOT / "content/drafts/skolko-deneg-nuzhno-dlya-pereezda-v-tailand-ru.json"


def draft_row():
    row = json.loads(DRAFT.read_text(encoding="utf-8"))
    row["content"] = (DRAFT.parent / row["content_file"]).read_text(encoding="utf-8")
    row["link"] = f"/ru/blog/{row['slug']}/"
    return row


@site.app.get('/ru/_editorial-preview/thailand-first-month/')
def preview():
    return site.render_post_row(draft_row(), lang="ru", preview=True)


@site.app.get('/_editorial-preview/qa/<int:width>/<name>/')
def responsive_preview(width, name):
    paths = {
        "bali": "/ru/compare/bali-vs-thailand/",
        "malaysia": "/ru/compare/thailand-vs-malaysia/",
        "article": "/ru/_editorial-preview/thailand-first-month/",
    }
    if width not in {1280, 820, 390} or name not in paths:
        site.abort(404)
    # The iframe's actual layout viewport is width; scaling only fits the QA
    # canvas on a smaller screen. This route exists only in this local script.
    scale = min(1, 960 / width)
    anchor = site.request.args.get('anchor', '')
    allowed_anchors = {'', 'cost', 'visas', 'example', 'before-payment'}
    if anchor not in allowed_anchors:
        site.abort(400)
    with site.app.test_client() as client:
        body = client.get(paths[name]).get_data(as_text=True)
    if anchor:
        body = body.replace('</body>', '<script>addEventListener("load",()=>document.getElementById(' + json.dumps(anchor) + ')?.scrollIntoView())</script></body>')
    return site.Response(f'''<!doctype html><html lang="ru"><meta charset="utf-8">
        <meta name="robots" content="noindex,nofollow"><title>QA {name} {width}px</title>
        <style>body{{margin:12px;background:#e8ece9;font:14px sans-serif}}
        iframe{{border:1px solid #aaa;width:{width}px;height:{int(1100/scale)}px;
        transform:scale({scale});transform-origin:top left}}</style>
        <p>Локальная проверка: {name} · viewport {width}px · масштаб {scale:g}</p>
        <iframe title="Редакционный предпросмотр" srcdoc="{html.escape(body, quote=True)}"></iframe></html>''',
        headers={'X-Robots-Tag': 'noindex, nofollow'})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=5088)
    args = parser.parse_args()
    site.app.run(host='127.0.0.1', port=args.port, debug=False, use_reloader=False)
