"""Regression tests for cache expiration, FAQ markup and asset versioning."""
import hashlib
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app as site


class TechnicalRegressionTests(unittest.TestCase):
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


if __name__ == '__main__':
    unittest.main()
