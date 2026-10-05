"""Journal and article presentation regression checks (no network required)."""
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app as site
from editorial import prepare_article, reading_minutes
from technical_audit import Document


class EditorialTests(unittest.TestCase):
    def setUp(self):
        site._PAGE_CACHE.clear()
        self.client = site.app.test_client()

    def test_removes_balanced_hero_and_keeps_article_anchors(self):
        source = '<style>.fc-hero{color:red}</style>\n<div class="fc-hero"><div><span>Badge</span></div><h2>Old title</h2></div><section id="facts"><h2>Facts</h2><p>Keep this.</p></section>'
        body, toc = prepare_article(source)
        self.assertNotIn('Old title', body)
        self.assertIn('<section id="facts">', body)
        self.assertIn('Keep this.', body)
        self.assertEqual(toc, [{'id': 'reading-section-1', 'title': 'Facts'}])

    def test_heading_ids_are_unique_and_existing_ids_are_preserved(self):
        body, toc = prepare_article('<div id="reading-section-1"></div><h2>A</h2><h2 id="original">B &amp; C</h2>')
        self.assertEqual(toc[0]['id'], 'reading-section-2')
        self.assertEqual(toc[1], {'id': 'original', 'title': 'B & C'})
        self.assertEqual(len(Document(body).ids), len(set(Document(body).ids)))

    def test_every_post_has_one_visible_title_and_working_toc(self):
        for post in site.many('SELECT slug, lang FROM posts'):
            path = ('/ru' if post['lang'] == 'ru' else '') + '/blog/' + post['slug'] + '/'
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                page = Document(response.get_data(as_text=True))
                headings = [a for t, a in page.tags if t == 'h1']
                self.assertEqual(len(headings), 1)
                self.assertNotIn('sr-only', headings[0].get('class', ''))
                self.assertTrue(any(t == 'aside' and a.get('class') == 'rta-reading-nav' for t, a in page.tags))
                for tag, attrs in page.tags:
                    if tag == 'a' and attrs.get('href', '').startswith('#reading-section-'):
                        self.assertIn(attrs['href'][1:], page.ids)

    def test_search_finds_posts_beyond_first_page(self):
        body = self.client.get('/blog/', query_string={'q': 'Malaysia for Digital Nomads'}).get_data(as_text=True)
        self.assertIn('href="/blog/malaysia-digital-nomad-guide-2026/"', body)
        self.assertIn('content="noindex,follow"', body)
        self.assertIn('href="https://www.marharuta.online/blog/"', body)

    def test_russian_search_is_case_insensitive(self):
        body = self.client.get('/ru/blog/', query_string={'q': 'МАЛАЙЗИЯ'}).get_data(as_text=True)
        self.assertIn('href="/ru/blog/malaysia-dlya-digital-nomads-2026/"', body)

    def test_empty_and_escaped_search(self):
        body = self.client.get('/ru/blog/', query_string={'q': '<script>alert(1)</script>'}).get_data(as_text=True)
        self.assertIn('Ничего не найдено', body)
        self.assertNotIn('<script>alert(1)</script>', body)
        self.assertIn('&lt;script&gt;', body)

    def test_articles_precede_editorial_help(self):
        body = self.client.get('/ru/blog/').get_data(as_text=True)
        self.assertLess(body.index('rta-journal-story'), body.index('rta-journal-method'))
        self.assertEqual(len(re.findall('<article class="rta-journal-story', body)), 10)
        self.assertIn('aria-current="page"', body)

    def test_reading_time_ignores_css_and_script(self):
        self.assertEqual(reading_minutes('<style>' + 'x ' * 600 + '</style><p>' + 'word ' * 420 + '</p>'), 2)

    def test_article_tables_keep_readable_columns(self):
        page = self.client.get('/ru/blog/uae-virtual-work-visa-2026/').get_data(as_text=True)
        self.assertGreaterEqual(page.count('class="table-scroll"'), 2)
        css = (Path(__file__).resolve().parents[1] / 'static' / 'css' / 'editorial.css').read_text(encoding='utf-8')
        self.assertIn('.table-scroll > table', css)
        self.assertIn('min-width: 760px', css)
        self.assertIn('word-break: normal', css)
        self.assertIn('overflow-wrap: normal', css)


if __name__ == '__main__':
    unittest.main()
