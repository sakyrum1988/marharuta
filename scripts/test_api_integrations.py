"""Regression checks for API failures and preservation of saved observations."""
import io
import json
import re
import subprocess
import sqlite3
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import sync_countries as sync
import init_db
import app as site


class CountrySyncTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        self.db.row_factory = sqlite3.Row
        sync.init_table(self.db)
        self.db.execute("INSERT INTO country_facts (slug, iso2, capital, population, internet_pct, internet_pct_year, updated_at) VALUES ('move-to-thailand', 'TH', 'Bangkok', 70000000, 88, '2024', 'original')")
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def row(self):
        return dict(self.db.execute("SELECT * FROM country_facts WHERE iso2='TH'").fetchone())

    def test_failure_leaves_entire_row_unchanged(self):
        before = self.row()
        self.assertEqual(sync.save_observations(self.db, {'TH': {}}), 0)
        self.assertEqual(self.row(), before)

    def test_partial_update_preserves_other_fields_and_tracks_year(self):
        sync.save_observations(self.db, {'TH': {'gdp_per_capita': 8000, 'gdp_per_capita_year': '2025'}})
        row = self.row()
        self.assertEqual(row['population'], 70000000)
        self.assertEqual(row['capital'], 'Bangkok')
        self.assertEqual(row['internet_pct'], 88)
        self.assertEqual(row['wb_year'], '2024–2025')
        self.assertEqual(row['updated_at'], 'original')
        self.assertTrue(row['wb_checked_at'])

    def test_older_invalid_observations_do_not_overwrite(self):
        before = self.row()
        sync.save_observations(self.db, {'TH': {'internet_pct': 50, 'internet_pct_year': '2023', 'population': float('nan'), 'population_year': '2025'}})
        self.assertEqual(self.row(), before)

    def test_zero_is_a_valid_observation(self):
        sync.save_observations(self.db, {'TH': {'unemployment': 0, 'unemployment_year': '2025'}})
        self.assertEqual(self.row()['unemployment'], 0)

    def test_invalid_json_yields_no_writes(self):
        response = Mock()
        response.json.side_effect = ValueError('malformed JSON')
        with patch.object(sync.requests, 'get', return_value=response), redirect_stdout(io.StringIO()):
            result = sync.fetch_wb_bulk()
        self.assertFalse(any(result.values()))

    def test_latest_nonempty_and_year_per_field(self):
        def response(url, params, timeout):
            self.assertEqual(params['mrnev'], 1)
            field = sync.WB_INDICATORS[url.rsplit('/', 1)[1]]
            value = 0 if field == 'unemployment' else 50
            result = Mock()
            result.json.return_value = [{'pages': 1}, [{'country': {'id': 'TH'}, 'value': value, 'date': '2024'}]]
            return result
        with patch.object(sync.requests, 'get', side_effect=response), redirect_stdout(io.StringIO()):
            result = sync.fetch_wb_bulk()
        self.assertEqual(result['TH']['unemployment'], 0)
        self.assertEqual(result['TH']['population_year'], '2024')

    def test_country_endpoint_handles_unknown_codes(self):
        with site.app.test_client() as client:
            self.assertEqual(client.get('/api/countries/invalid').status_code, 400)
            self.assertEqual(client.get('/api/countries/ZZ').status_code, 404)
            response = client.get('/api/countries/th')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json['iso2'], 'TH')

    def test_wordpress_import_reports_retired_source(self):
        with patch.object(init_db, 'API', ''):
            with self.assertRaisesRegex(RuntimeError, 'WordPress import is disabled'):
                init_db.fetch_all('pages', 'id')

    def test_rendered_calculators_on_api_failure_and_recovery(self):
        root = Path(__file__).resolve().parents[1]
        pages = []
        with site.app.test_client() as client:
            for lang in ('en', 'ru'):
                for tool in ('cost-calculator', 'budget-planner'):
                    path = ('/ru' if lang == 'ru' else '') + f'/tools/{tool}/'
                    body = client.get(path).get_data(as_text=True)
                    scripts = [script for script in re.findall(r'<script[^>]*>(.*?)</script>', body, re.S) if 'RtaData.rates()' in script]
                    self.assertEqual(len(scripts), 1, path)
                    self.assertNotRegex(scripts[0], r'RATES\[\w+\]\s*\|\|\s*1')
                    pages.append({'path': path, 'lang': lang, 'script': scripts[0]})
        result = subprocess.run(
            ['node', str(root / 'scripts/test_tool_runtime.js')],
            input=json.dumps({'pages': pages, 'shared': (root / 'static/js/data-api.js').read_text(encoding='utf-8')}),
            capture_output=True, text=True, encoding='utf-8', timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
