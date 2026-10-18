"""Focused checks for the October title/content refresh (no DB writes)."""
import hashlib
import html
from pathlib import Path
import re
import sys
import unittest
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app as site
from preview_editorial import draft_row
from technical_audit import Document


class SeoSprintTests(unittest.TestCase):
    def setUp(self):
        self.client = site.app.test_client()
        site._PAGE_CACHE.clear()

    def test_comparisons_have_complete_titles_one_hero_and_preserved_anchors(self):
        common = {'quick', 'cost', 'visas', 'healthcare', 'lifestyle', 'internet', 'safety', 'climate', 'verdict', 'faq'}
        for slug, extras in [('bali-vs-thailand', {'nomad', 'longterm'}), ('thailand-vs-malaysia', {'language', 'family'})]:
            with self.subTest(slug=slug):
                response = self.client.get(f'/ru/compare/{slug}/')
                body = response.get_data(as_text=True)
                doc = Document(body)
                title, unused = site.optimize_ru_compare_for_search(slug, '')
                self.assertEqual(response.status_code, 200)
                self.assertIn(f'<title>{html.escape(title)}', body)
                self.assertEqual(len(re.findall(r'<h1\b', body)), 1)
                self.assertNotIn('rta-legacy-comparison-title', body)
                self.assertTrue((common | extras).issubset(set(doc.ids)))
                self.assertEqual(len(doc.ids), len(set(doc.ids)))
                self.assertEqual(body.count('class="table-scroll"'), 2)
                self.assertIn('nofollow', body)
                self.assertIn('Бангкок', body)

    def test_new_article_is_preview_only_and_has_separate_metadata(self):
        before = hashlib.sha256(site.DB_PATH.read_bytes()).hexdigest()
        row = draft_row()
        response = self.client.get('/ru/_editorial-preview/thailand-first-month/')
        body = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(row['seo_title'], body)
        self.assertIn('Редакционный предпросмотр', body)
        self.assertIn('noindex,nofollow', body)
        self.assertNotIn('>Опубликовано', body)
        self.assertNotIn('application/ld+json', body)
        self.assertEqual(len(re.findall(r'<h1\b', body)), 1)
        self.assertIn('class="table-scroll"', body)
        self.assertIn('первого месяца в Бангкоке', body)
        self.assertEqual(self.client.get(row['link']).status_code, 404)
        self.assertNotIn(row['slug'], self.client.get('/sitemap.xml').get_data(as_text=True))
        self.assertEqual(before, hashlib.sha256(site.DB_PATH.read_bytes()).hexdigest())

    def test_internal_links_in_new_materials_resolve(self):
        paths = ['/ru/compare/bali-vs-thailand/', '/ru/compare/thailand-vs-malaysia/', '/ru/_editorial-preview/thailand-first-month/']
        for path in paths:
            body = self.client.get(path).get_data(as_text=True)
            for tag, attrs in Document(body).tags:
                href = attrs.get('href', '')
                if tag == 'a' and href.startswith('/') and not href.startswith('//'):
                    with self.subTest(path=path, href=href):
                        self.assertLess(self.client.get(urlsplit(href).path).status_code, 400)

    def test_budget_arithmetic(self):
        spent = sum([25000, 7000, 20000, 12000, 3000, 3000, 24000, 10000, 5000])
        self.assertEqual(spent, 109000)
        self.assertEqual(spent + 40000 + 40000, 189000)
        self.assertEqual(spent + 40000 + 120000, 269000)
        self.assertEqual(20000 + 12000 + 3000 + 3000 + 24000 // 12, 40000)


if __name__ == '__main__':
    unittest.main()
