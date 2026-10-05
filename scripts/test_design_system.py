"""Shared layout regressions. These do not substitute for responsive visual QA."""
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import app as site
from technical_audit import Document


class DesignSystemTests(unittest.TestCase):
    def setUp(self):
        site._PAGE_CACHE.clear()
        self.client = site.app.test_client()

    def test_all_related_lists_are_accessible_and_not_repeated_in_planning(self):
        for row in site.many('SELECT * FROM posts'):
            with self.subTest(slug=row['slug'], lang=row['lang']):
                path = site.post_path(row)
                body = self.client.get(path).get_data(as_text=True)
                self.assertIn('<ol class="rta-related-list">', body)
                self.assertNotIn('class="rta-related-card"', body)
                planning_urls = {link['url'] for link in site.internal_links_for_post(row, lang=row['lang'])}
                related_markup = re.search(r'<ol class="rta-related-list">(.*?)</ol>', body, re.S).group(1)
                related_urls = {attrs['href'] for tag, attrs in Document(related_markup).tags if tag == 'a'}
                self.assertGreater(len(related_urls), 0)
                self.assertFalse(planning_urls & related_urls)
                for url in related_urls:
                    self.assertEqual(self.client.get(url).status_code, 200, url)

    def test_theme_and_fonts_are_shared_by_page_families(self):
        paths = ['/', '/ru/', '/ru/blog/', '/ru/countries/', '/ru/countries/move-to-thailand/',
                 '/ru/visas/', '/ru/guides/', '/ru/tools/budget-planner/', '/ru/compare/',
                 '/ru/authors/margarita-yarovenko/']
        for path in paths:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                body = response.get_data(as_text=True)
                styles = [attrs['href'] for tag, attrs in Document(body).tags
                          if tag == 'link' and attrs.get('rel') == 'stylesheet']
                self.assertTrue(any('family=Onest:' in url for url in styles))
                self.assertTrue(styles[-1].startswith('/static/css/editorial.css?v='))
                self.assertFalse(any('Manrope' in url for url in styles))

    def test_mobile_navigation_breakpoints_match(self):
        js = (ROOT / 'static/js/site.js').read_text(encoding='utf-8')
        css = (ROOT / 'static/css/editorial.css').read_text(encoding='utf-8')
        self.assertIn("matchMedia('(max-width: 980px)')", js)
        self.assertIn('@media (max-width: 980px)', css)
        self.assertNotIn("matchMedia('(max-width: 720px)')", js)
        self.assertIn('if (wasOpen) btn.focus()', js)

    def test_home_owns_its_layout_and_uses_local_responsive_artwork(self):
        for prefix in ('', '/ru'):
            body = self.client.get(prefix + '/').get_data(as_text=True)
            doc = Document(body)
            self.assertEqual(sum(tag == 'h1' for tag, attrs in doc.tags), 1)
            self.assertIn('rta-home-premium', body)
            self.assertNotIn('class="rta-page"', body)
            self.assertNotIn('class="rta-hero"', body)
            self.assertIn('countries', doc.ids)
            artwork = [attrs for tag, attrs in doc.tags if tag == 'img' and 'asia-coast-illustration' in attrs.get('src', '')]
            self.assertEqual(len(artwork), 1)
            self.assertIn('640w', artwork[0]['srcset'])
            self.assertEqual(artwork[0]['fetchpriority'], 'high')
            with self.client.get(artwork[0]['src']) as asset_response:
                self.assertEqual(asset_response.status_code, 200)
            for tag, attrs in doc.tags:
                url = attrs.get('href', '')
                if tag == 'a' and url.startswith('/') and not url.startswith('//'):
                    self.assertEqual(self.client.get(url).status_code, 200, url)

    def test_debug_preview_never_reuses_html_or_asset_cache(self):
        old_debug = site.app.debug
        try:
            site.app.debug = True
            for path in ('/ru/', '/static/css/editorial.css?v=preview'):
                for _ in range(2):
                    with self.client.get(path) as response:
                        self.assertEqual(response.headers['Cache-Control'], 'no-store')
                        self.assertNotEqual(response.headers.get('X-Cache'), 'HIT')
            self.assertNotIn('/ru/', site._PAGE_CACHE)
        finally:
            site.app.debug = old_debug

    def test_budget_interface_labels_are_translated_before_generic_words(self):
        body = self.client.get('/ru/tools/budget-planner/').get_data(as_text=True)
        self.assertIn('Посчитать общий бюджет', body)
        for fragment in ('Calculate Итого', 'Итого One-Time', 'Annual Итого', 'First Month Итого', 'Итого you need'):
            self.assertNotIn(fragment, body)

    def test_planning_navigation_uses_existing_localized_pages(self):
        for prefix in ('', '/ru'):
            body = self.client.get(prefix + '/').get_data(as_text=True)
            menu = re.search(r'<div class="rta-dropdown rta-dropdown--wide">(.*?)</div>', body, re.S).group(1)
            links = [attrs['href'] for tag, attrs in Document(menu).tags if tag == 'a']
            self.assertEqual(len(links), 6)
            self.assertIn(prefix + '/move-to-asia/', links)
            self.assertIn(prefix + '/cost-of-living-asia/', links)
            for url in links:
                self.assertEqual(self.client.get(url).status_code, 200, url)


if __name__ == '__main__':
    unittest.main()
