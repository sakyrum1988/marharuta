"""Regression tests for cache expiration, FAQ markup and asset versioning."""
import hashlib
import html
import re
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlencode

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app as site


class TechnicalRegressionTests(unittest.TestCase):
    def test_seo_title_preserves_meaning_instead_of_truncating_for_brand(self):
        titles = (
            'Cost Of Living In Asia 2026: Real Relocation Budgets',
            'Бали или Таиланд: где дешевле жить и что выбрать',
            'Таиланд или Малайзия: сравнение расходов и виз',
        )
        with site.app.test_request_context('/'):
            for title in titles:
                with self.subTest(title=title):
                    payload = site.seo_payload(title=title)
                    self.assertTrue(payload['page_title'].startswith(title))
                    self.assertNotIn('...', payload['page_title'])
            self.assertEqual(site.seo_payload(title=site.SITE_NAME)['page_title'], site.SITE_NAME)
            branded = 'About | ' + site.SITE_NAME
            self.assertEqual(site.seo_payload(title=branded)['page_title'], branded)
            self.assertEqual(site.seo_payload(title='About')['page_title'], branded)

    def setUp(self):
        site._PAGE_CACHE.clear()
        self.client = site.app.test_client()

    def tearDown(self):
        site._PAGE_CACHE.clear()

    def test_cache_hits_do_not_extend_original_expiration(self):
        with patch.object(site.time, 'monotonic', return_value=1000):
            first = self.client.get('/about/')
        self.assertEqual(first.status_code, 200)
        self.assertEqual(site._PAGE_CACHE['/about/'][2], 1000)
        with patch.object(site.time, 'monotonic', return_value=1500):
            hit = self.client.get('/about/')
        self.assertEqual(hit.headers['X-Cache'], 'HIT')
        self.assertEqual(hit.headers['Age'], '500')
        self.assertEqual(site._PAGE_CACHE['/about/'][2], 1000)
        with patch.object(site.time, 'monotonic', return_value=1601):
            fresh = self.client.get('/about/')
        self.assertNotIn('X-Cache', fresh.headers)
        self.assertEqual(site._PAGE_CACHE['/about/'][2], 1601)

    def test_warm_cache_does_not_bypass_canonical_host_redirect(self):
        self.client.get('/about/')
        response = self.client.get('/about/?ref=test', base_url='https://marharuta.online')
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.location, 'https://www.marharuta.online/about/?ref=test')

    def test_query_requests_do_not_overwrite_cached_page(self):
        self.client.get('/blog/')
        cached = site._PAGE_CACHE['/blog/']
        self.client.get('/blog/?page=2')
        self.assertEqual(site._PAGE_CACHE['/blog/'], cached)

    def test_blog_search_paginates_and_preserves_query(self):
        for path, query in (('/blog/', 'visa'), ('/ru/blog/', 'виза')):
            with self.subTest(path=path):
                first = self.client.get(path, query_string={'q': query})
                second = self.client.get(path, query_string={'q': query, 'page': 2})
                self.assertEqual(first.status_code, 200)
                self.assertEqual(second.status_code, 200)
                first_body = html.unescape(first.get_data(as_text=True))
                second_body = html.unescape(second.get_data(as_text=True))
                self.assertEqual(first_body.count('<article class="rta-journal-story'), 10)
                self.assertGreater(second_body.count('<article class="rta-journal-story'), 0)
                self.assertLessEqual(second_body.count('<article class="rta-journal-story'), 10)
                self.assertIn('page=2', first_body)
                search_url = path + '?' + urlencode({'q': query})
                self.assertIn(search_url + '&page=2', first_body)
                self.assertIn(f'rel="prev" href="{search_url}"', second_body)
                self.assertIn('noindex,follow', second_body)
                first_slugs = set(re.findall(r'<h3><a href="([^"]+)"', first_body))
                second_slugs = set(re.findall(r'<h3><a href="([^"]+)"', second_body))
                self.assertFalse(first_slugs & second_slugs)
                self.assertEqual(self.client.get(path, query_string={'q': query, 'page': 999}).status_code, 404)

    def test_blog_search_prioritizes_title_matches(self):
        body = self.client.get('/blog/', query_string={'q': 'visa'}).get_data(as_text=True)
        titles = re.findall(r'<h3><a href="[^"]+">(.*?)</a></h3>', body, re.S)
        self.assertGreater(len(titles), 1)
        self.assertIn('visa', html.unescape(re.sub(r'<[^>]+>', '', titles[0])).casefold())

    def test_faq_supports_old_and_new_class_tokens(self):
        for css_class in ('faq-item', 'rta-depth-faq-item', 'other rta-depth-faq-item compact'):
            with self.subTest(css_class=css_class):
                schema = site.faq_schema_from_html(
                    f'<div class="{css_class}"><h3 id="q">A &amp; B?</h3><p class="answer"><strong>An</strong> answer.</p></div>', lang='en')
                self.assertEqual(schema['mainEntity'][0]['name'], 'A & B?')
                self.assertEqual(schema['mainEntity'][0]['acceptedAnswer']['text'], 'An answer.')
        self.assertIsNone(site.faq_schema_from_html('<div class="not-faq-item"><h3>Q</h3><p>A</p></div>', lang='en'))

    def test_details_faq_accepts_attributes(self):
        schema = site.faq_schema_from_html('<details class="faq" open><summary id="q">Q?</summary><p>A.</p></details>', lang='en')
        self.assertEqual(schema['mainEntity'][0]['name'], 'Q?')

    def test_stylesheet_url_tracks_actual_content(self):
        digest = hashlib.sha256((site.APP_DIR / 'static/css/site.css').read_bytes()).hexdigest()[:12]
        body = self.client.get('/').get_data(as_text=True)
        self.assertIn(f'/static/css/site.css?v={digest}', body)

    def test_sitemap_only_claims_lastmod_when_date_is_known(self):
        sitemap = ET.fromstring(self.client.get('/sitemap.xml').data)
        namespace = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        entries = {
            node.find('s:loc', namespace).text: node
            for node in sitemap.findall('s:url', namespace)
        }
        homepage = entries[f'{site.SITE_URL}/']
        self.assertIsNone(homepage.find('s:lastmod', namespace))

        post = site.one("SELECT slug, date, lang FROM posts WHERE date IS NOT NULL ORDER BY date DESC LIMIT 1")
        prefix = '/blog' if post['lang'] == 'en' else '/ru/blog'
        post_url = f"{site.SITE_URL}{prefix}/{post['slug']}/"
        post_lastmod = entries[post_url].find('s:lastmod', namespace)
        self.assertIsNotNone(post_lastmod)
        self.assertEqual(post_lastmod.text, str(post['date'])[:10])

    def test_no_phantom_country_in_either_table_of_contents(self):
        for path in ('/cheapest-countries-in-asia/', '/ru/cheapest-countries-in-asia/'):
            body = self.client.get(path).get_data(as_text=True)
            self.assertNotIn('href="#myanmar"', body)
            self.assertIn('<strong>9</strong>', body)

    def test_ga4_tag_is_present_once_on_production_host_only(self):
        production = self.client.get('/?ga-test=1', base_url='https://www.marharuta.online')
        production_body = production.get_data(as_text=True)
        tag_url = 'https://www.googletagmanager.com/gtag/js?id=G-QET2HP459Y'
        self.assertEqual(production_body.count(tag_url), 1)
        self.assertEqual(production_body.count("gtag('config', \"G-QET2HP459Y\")"), 1)

        local = self.client.get('/?ga-test=1', base_url='http://127.0.0.1:5001')
        self.assertNotIn('googletagmanager.com/gtag/js', local.get_data(as_text=True))

    def test_csp_allows_ga4_script_and_collection_hosts(self):
        response = self.client.get('/?ga-test=1', base_url='https://www.marharuta.online')
        csp = response.headers['Content-Security-Policy']
        self.assertIn('script-src', csp)
        self.assertIn('https://www.googletagmanager.com', csp)
        self.assertIn('https://www.google-analytics.com', csp)

    def test_new_destinations_are_complete_and_bilingual(self):
        for path, country, catalog_path in (
            ('/countries/move-to-georgia/', 'Georgia', '/countries/'),
            ('/ru/countries/move-to-georgia/', 'Грузия', '/ru/countries/'),
            ('/countries/move-to-turkey/', 'Türkiye', '/countries/'),
            ('/ru/countries/move-to-turkey/', 'Турция', '/ru/countries/'),
            ('/countries/move-to-kyrgyzstan/', 'Kyrgyzstan', '/countries/'),
            ('/ru/countries/move-to-kyrgyzstan/', 'Кыргызстан', '/ru/countries/'),
            ('/countries/move-to-armenia/', 'Armenia', '/countries/'),
            ('/ru/countries/move-to-armenia/', 'Армения', '/ru/countries/'),
            ('/countries/move-to-azerbaijan/', 'Azerbaijan', '/countries/'),
            ('/ru/countries/move-to-azerbaijan/', 'Азербайджан', '/ru/countries/'),
            ('/countries/move-to-qatar/', 'Qatar', '/countries/'),
            ('/ru/countries/move-to-qatar/', 'Катар', '/ru/countries/'),
            ('/countries/move-to-saudi-arabia/', 'Saudi Arabia', '/countries/'),
            ('/ru/countries/move-to-saudi-arabia/', 'Саудовская Аравия', '/ru/countries/'),
            ('/countries/move-to-oman/', 'Oman', '/countries/'),
            ('/ru/countries/move-to-oman/', 'Оман', '/ru/countries/'),
            ('/countries/move-to-bahrain/', 'Bahrain', '/countries/'),
            ('/ru/countries/move-to-bahrain/', 'Бахрейн', '/ru/countries/'),
            ('/countries/move-to-kuwait/', 'Kuwait', '/countries/'),
            ('/ru/countries/move-to-kuwait/', 'Кувейт', '/ru/countries/'),
            ('/countries/move-to-jordan/', 'Jordan', '/countries/'),
            ('/ru/countries/move-to-jordan/', 'Иордания', '/ru/countries/'),
            ('/countries/move-to-lebanon/', 'Lebanon', '/countries/'),
            ('/ru/countries/move-to-lebanon/', 'Ливан', '/ru/countries/'),
            ('/countries/move-to-israel/', 'Israel', '/countries/'),
            ('/ru/countries/move-to-israel/', 'Израиль', '/ru/countries/'),
            ('/countries/move-to-iran/', 'Iran', '/countries/'),
            ('/ru/countries/move-to-iran/', 'Иран', '/ru/countries/'),
            ('/countries/move-to-yemen/', 'Yemen', '/countries/'),
            ('/ru/countries/move-to-yemen/', 'Йемен', '/ru/countries/'),
            ('/countries/move-to-syria/', 'Syria', '/countries/'),
            ('/ru/countries/move-to-syria/', 'Сирия', '/ru/countries/'),
            ('/countries/move-to-iraq/', 'Iraq', '/countries/'),
            ('/ru/countries/move-to-iraq/', 'Ирак', '/ru/countries/'),
        ):
            with self.subTest(path=path):
                response = self.client.get(path)
                body = response.get_data(as_text=True)
                self.assertEqual(response.status_code, 200)
                self.assertIn(country, body)
                self.assertIn('2026', body)
                self.assertIn('rta-source-panel', body)
                english_path = path.removeprefix('/ru')
                self.assertIn(english_path, body)
                catalog = self.client.get(catalog_path).get_data(as_text=True)
                self.assertIn(path, catalog)


if __name__ == '__main__':
    unittest.main()
