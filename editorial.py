"""Presentation helpers for imported articles; original database HTML is preserved."""
import html
import math
import re
from html.parser import HTMLParser


def plain_text(value):
    value = re.sub(r'<(style|script)\b[^>]*>.*?</\1>', '', value or '', flags=re.S | re.I)
    return ' '.join(html.unescape(re.sub(r'<[^>]+>', ' ', value)).split())


def reading_minutes(content):
    return max(1, math.ceil(len(plain_text(content).split()) / 210))


def article_topic(post, lang):
    text = (post['slug'] + ' ' + post['title']).casefold()
    if any(word in text for word in ('visa', 'evisa', 'hayya', 'eta-', 'vizy', 'виз', 'въезд')):
        return 'Визы и документы' if lang == 'ru' else 'Visas & documents'
    if any(word in text for word in ('cost', 'budget', 'бюджет', 'стоимость')):
        return 'Бюджет переезда' if lang == 'ru' else 'Moving costs'
    return 'Жизнь за границей' if lang == 'ru' else 'Life abroad'


class ImportedPanels(HTMLParser):
    """Locate balanced presentation wrappers without reserializing article HTML."""
    classes = {'fc-hero', 'art-hero', 'article-hero', 'rta-hero-card', 'fc-toc', 'art-toc', 'article-toc'}
    void = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}

    def __init__(self, source):
        super().__init__(convert_charrefs=False)
        self.source = source
        self.offsets = [0]
        for line in source.splitlines(keepends=True):
            self.offsets.append(self.offsets[-1] + len(line))
        self.stack, self.ranges = [], []
        self.start = None
        self.feed(source)

    def source_offset(self):
        line, column = self.getpos()
        return self.offsets[line - 1] + column

    def handle_starttag(self, tag, attrs):
        if tag in self.void:
            return
        if self.start is None and self.classes.intersection(dict(attrs).get('class', '').split()):
            self.start = self.source_offset()
            self.stack = [tag]
        elif self.start is not None:
            self.stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        pass

    def handle_endtag(self, tag):
        if self.start is None or tag not in self.stack:
            return
        index = len(self.stack) - 1 - self.stack[::-1].index(tag)
        del self.stack[index:]
        if not self.stack:
            self.ranges.append((self.start, self.source.index('>', self.source_offset()) + 1))
            self.start = None


def prepare_article(content):
    """Replace imported mastheads/TOCs with one accessible template-owned version."""
    panels = ImportedPanels(content)
    for start, end in reversed(panels.ranges):
        content = content[:start] + content[end:]
    toc = []
    ids = set(re.findall(r'\bid=["\']([^"\']+)', content))

    def heading(match):
        attrs, inner = match.groups()
        existing = re.search(r'\bid=["\']([^"\']+)', attrs)
        if existing:
            anchor = existing.group(1)
        else:
            number = len(toc) + 1
            anchor = f'reading-section-{number}'
            while anchor in ids:
                number += 1
                anchor = f'reading-section-{number}'
            ids.add(anchor)
            attrs += f' id="{anchor}"'
        toc.append({'id': anchor, 'title': plain_text(inner)})
        return f'<h2{attrs}>{inner}</h2>'

    return re.sub(r'<h2\b([^>]*)>(.*?)</h2>', heading, content, flags=re.S | re.I), toc
