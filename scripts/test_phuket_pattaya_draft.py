"""Checks for the unpublished Phuket-vs-Pattaya article."""
import hashlib
import json
from pathlib import Path
import re
import sys
import unittest

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import preview_phuket_pattaya_draft as preview
import publish_phuket_pattaya_ru as publisher
from technical_audit import Document


class PhuketPattayaDraftTests(unittest.TestCase):
    def setUp(self):
        self.row = preview.draft_row()
        self.published = json.loads(preview.DRAFT.read_text(encoding="utf-8"))
        self.client = preview.site.app.test_client()
        self.db_hash = hashlib.sha256(preview.site.DB_PATH.read_bytes()).hexdigest()

    def tearDown(self):
        self.assertEqual(self.db_hash, hashlib.sha256(preview.site.DB_PATH.read_bytes()).hexdigest())

    def test_preview_is_private(self):
        self.assertEqual(self.row["status"], "draft")
        self.assertEqual(self.row["date"], "")
        for path in ["/sitemap.xml", "/ru/blog/", "/feed.xml"]:
            self.assertNotIn(preview.PREVIEW_PATH, self.client.get(path).get_data(as_text=True))

    def test_public_article_and_idempotent_publish(self):
        self.assertEqual(self.published["status"], "published")
        self.assertEqual(self.published["date"], "2026-10-23")
        path = f"/ru/blog/{self.published['slug']}/"
        body = self.client.get(path).get_data(as_text=True)
        self.assertIn("application/ld+json", body)
        self.assertNotIn('content="noindex,nofollow"', body)
        self.assertIn(path, self.client.get("/sitemap.xml").get_data(as_text=True))
        self.assertIn(path, self.client.get("/ru/blog/").get_data(as_text=True))
        self.assertFalse(publisher.publish(preview.site.DB_PATH))

    def test_render_and_sources(self):
        response = self.client.get(preview.PREVIEW_PATH)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["X-Robots-Tag"], "noindex, nofollow")
        body = response.get_data(as_text=True)
        page = Document(body)
        self.assertEqual(sum(tag == "h1" for tag, _ in page.tags), 1)
        self.assertIn("Не опубликовано", body)
        self.assertIn('content="noindex,nofollow"', body)
        self.assertNotIn("application/ld+json", body)
        self.assertIn("География, сезонность и транспорт", body)
        panel = preview.site.article_source_panel_for_post(self.row, lang="ru")
        self.assertEqual(len(panel["sources"]), 5)
        self.assertEqual(len(page.ids), len(set(page.ids)))
        self.assertIn('class="table-scroll"', body)

    def test_metadata_body_and_links(self):
        self.assertTrue(50 <= len(self.row["seo_title"]) <= 65)
        self.assertTrue(140 <= len(self.row["meta_description"]) <= 165)
        self.assertIsNone(re.search(r"<(?:h1|script|style)\b", self.row["content"], re.I))
        for tag, attrs in Document(self.row["content"]).tags:
            href = attrs.get("href", "") if tag == "a" else ""
            if href.startswith("http"):
                self.assertTrue({"nofollow", "noopener"} <= set(attrs.get("rel", "").split()))
            elif href.startswith("/"):
                self.assertEqual(self.client.get(href).status_code, 200, href)


if __name__ == "__main__":
    unittest.main()
