"""Checks for the local-only editorial preview, without network or DB writes."""
import hashlib
from pathlib import Path
import re
import sys
import unittest

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import preview_weather_draft as preview
from technical_audit import Document


class WeatherDraftTests(unittest.TestCase):
    def setUp(self):
        self.row = preview.draft_row()
        self.client = preview.site.app.test_client()
        self.db_hash = hashlib.sha256(preview.site.DB_PATH.read_bytes()).hexdigest()

    def tearDown(self):
        self.assertEqual(self.db_hash, hashlib.sha256(preview.site.DB_PATH.read_bytes()).hexdigest())

    def test_preview_is_not_listed(self):
        self.assertEqual(self.row["status"], "draft")
        self.assertEqual(self.row["date"], "")
        for path in ["/sitemap.xml", "/ru/blog/", "/feed.xml"]:
            self.assertNotIn(preview.PREVIEW_PATH, self.client.get(path).get_data(as_text=True))

    def test_preview_semantics_and_sources(self):
        response = self.client.get(preview.PREVIEW_PATH)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["X-Robots-Tag"], "noindex, nofollow")
        body = response.get_data(as_text=True)
        page = Document(body)
        self.assertEqual(sum(tag == "h1" for tag, _ in page.tags), 1)
        self.assertIn("Не опубликовано", body)
        self.assertIn('content="noindex,nofollow"', body)
        self.assertNotIn('application/ld+json', body)
        self.assertNotIn("thaievisa", body)
        self.assertNotIn("Destination Thailand Visa", body)
        self.assertIn("Климат и прогноз", body)
        self.assertEqual(len(preview.site.article_source_panel_for_post(self.row, lang="ru")["sources"]), 6)
        self.assertEqual(len(page.ids), len(set(page.ids)))
        self.assertIn('class="table-scroll"', body)
        for tag, attrs in page.tags:
            if tag == "a" and attrs.get("href", "").startswith("#"):
                self.assertIn(attrs["href"][1:], page.ids)

    def test_metadata_and_body(self):
        self.assertTrue(50 <= len(self.row["seo_title"]) <= 65)
        self.assertTrue(140 <= len(self.row["meta_description"]) <= 165)
        self.assertIsNone(re.search(r"<(?:h1|script|style)\b", self.row["content"], re.I))
        for tag, attrs in Document(self.row["content"]).tags:
            if tag == "a" and attrs.get("href", "").startswith("http"):
                self.assertTrue({"nofollow", "noopener"} <= set(attrs.get("rel", "").split()))
            elif tag == "a" and attrs.get("href", "").startswith("/"):
                self.assertEqual(self.client.get(attrs["href"]).status_code, 200, attrs["href"])


if __name__ == "__main__":
    unittest.main()
