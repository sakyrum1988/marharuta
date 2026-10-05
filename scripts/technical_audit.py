"""Crawl the actual sitemap and validate local links, assets and SEO contracts.

Runs without network access or extra dependencies: python scripts/technical_audit.py
"""
from collections import Counter, defaultdict
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit, unquote
import json
import re
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app as site


class Document(HTMLParser):
    def __init__(self, body):
        super().__init__(convert_charrefs=True)
        self.tags = []
        self.ids = []
        self.json_blocks = []
        self.in_json = False
        self.feed(body)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.tags.append((tag, attrs))
        if attrs.get('id'):
            self.ids.append(attrs['id'])
        if tag == 'script' and attrs.get('type') == 'application/ld+json':
            self.in_json = True
            self.json_blocks.append('')

    def handle_endtag(self, tag):
        if tag == 'script':
            self.in_json = False

    def handle_data(self, data):
        if self.in_json:
            self.json_blocks[-1] += data


def audit():
    client = site.app.test_client()
    responses, documents = {}, {}
    failures = []
    references = defaultdict(set)
    titles, descriptions = defaultdict(list), defaultdict(list)
    ns = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
    sitemap = ET.fromstring(client.get('/sitemap.xml').data)
    urls = [n.text for n in sitemap.findall('s:url/s:loc', ns)]
    if len(urls) != len(set(urls)):
        failures.append('Sitemap contains duplicate URLs')

    def get(path):
        if path not in responses:
            responses[path] = client.get(path)
        return responses[path]

    def doc(path):
        if path not in documents:
            documents[path] = Document(get(path).get_data(as_text=True))
        return documents[path]

    for url in urls:
        path = urlsplit(url).path
        response = get(path)
        if response.status_code != 200:
            failures.append(f'{path}: sitemap status {response.status_code}')
            continue
        page = doc(path)
        body = response.get_data(as_text=True)
        title = re.search(r'<title>(.*?)</title>', body, re.S)
        if not title or not title.group(1).strip():
            failures.append(f'{path}: missing title')
        else:
            titles[title.group(1).strip()].append(path)
        meta_descriptions = [a.get('content', '').strip() for t, a in page.tags if t == 'meta' and a.get('name') == 'description']
        if len(meta_descriptions) != 1 or not meta_descriptions[0]:
            failures.append(f'{path}: expected one nonempty meta description')
        else:
            descriptions[meta_descriptions[0]].append(path)
        duplicates = [key for key, count in Counter(page.ids).items() if count > 1]
        if duplicates:
            failures.append(f'{path}: duplicate IDs {duplicates}')
        canonical = [a.get('href') for t, a in page.tags if t == 'link' and a.get('rel') == 'canonical']
        if canonical != [url]:
            failures.append(f'{path}: canonical {canonical}, expected {url}')
        if sum(t == 'h1' for t, a in page.tags) != 1:
            failures.append(f'{path}: expected one H1')
        for raw in page.json_blocks:
            try:
                json.loads(raw)
            except ValueError:
                failures.append(f'{path}: invalid JSON-LD')
        for tag, attrs in page.tags:
            if tag == 'meta' and attrs.get('name') == 'robots' and 'noindex' in attrs.get('content', ''):
                failures.append(f'{path}: sitemap URL is noindex')
            if tag == 'img' and 'alt' not in attrs:
                failures.append(f'{path}: image without alt: {attrs.get("src")}')
            ref = attrs.get('href') if tag in ('a', 'link') else attrs.get('src') if tag in ('script', 'img', 'iframe') else None
            if tag == 'meta' and attrs.get('property') == 'og:image':
                ref = attrs.get('content')
            if not ref:
                continue
            target = urlsplit(urljoin(url, ref))
            if target.netloc not in ('www.marharuta.online', 'marharuta.online'):
                continue
            local = target.path or '/'
            if target.query:
                local += '?' + target.query
            references[(local, unquote(target.fragment))].add(path)
            if tag == 'link' and attrs.get('hreflang'):
                other = doc(target.path)
                reciprocal = any(t == 'link' and a.get('rel') == 'alternate' and a.get('href') == url for t, a in other.tags)
                if not reciprocal:
                    failures.append(f'{path}: non-reciprocal hreflang {ref}')

    for (path, fragment), sources in references.items():
        response = get(path)
        source = ', '.join(sorted(sources)[:3])
        if response.status_code != 200:
            failures.append(f'{path}: linked status {response.status_code} (from {source})')
        elif fragment and 'text/html' in response.content_type and fragment not in doc(path).ids:
            failures.append(f'{path}#{fragment}: missing anchor (from {source})')

    for label, values in [('title', titles), ('description', descriptions)]:
        for paths in values.values():
            if len(paths) > 1:
                failures.append(f'Duplicate {label}: {paths}')

    for path, expected in [('/not-a-real-page/', 404), ('/ru/not-a-real-page/', 404), ('/uk/old-article/', 410)]:
        response = get(path)
        if response.status_code != expected or b'noindex' not in response.data:
            failures.append(f'{path}: invalid error status/indexing')

    print(f'Sitemap pages: {len(urls)}; unique local requests: {len(responses)}; link/anchor targets: {len(references)}')
    for failure in failures:
        print(f'- {failure}')
    print(f'Technical audit: {len(failures)} failures')
    return int(bool(failures))


if __name__ == '__main__':
    raise SystemExit(audit())
