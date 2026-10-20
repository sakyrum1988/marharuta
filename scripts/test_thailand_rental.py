"""Checks for the rental article, publication safety and rendered SEO."""
from contextlib import closing
import html
import json
from pathlib import Path
import re
import sqlite3
import sys
import tempfile
import unittest
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app as site
from publish_thailand_rental_ru import article, publish
from technical_audit import Document


class ThailandRentalTests(unittest.TestCase):
    def setUp(self):
        site._PAGE_CACHE.clear()
        self.client = site.app.test_client()
        self.item = article()

    def test_publication_is_idempotent_and_preserves_existing_rows(self):
        with tempfile.TemporaryDirectory() as temporary:
            database = Path(temporary) / "content.db"
            with closing(sqlite3.connect(database)) as connection, connection:
                connection.execute("CREATE TABLE posts (id INTEGER PRIMARY KEY,slug TEXT,title TEXT,content TEXT,excerpt TEXT,date TEXT,lang TEXT,link TEXT)")
                connection.execute("INSERT INTO posts VALUES (1,'keep','Keep','Body','Excerpt','2026-01-01','en','/blog/keep/')")
            self.assertTrue(publish(database))
            self.assertFalse(publish(database))
            with closing(sqlite3.connect(database)) as connection, connection:
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM posts").fetchone()[0], 2)
                self.assertEqual(connection.execute("SELECT title FROM posts WHERE id=1").fetchone()[0], "Keep")
                connection.execute("UPDATE posts SET title='User edit' WHERE slug=?", (self.item["slug"],))
            with self.assertRaises(RuntimeError):
                publish(database)

    def test_public_article_metadata_and_discovery(self):
        path = self.item["link"]
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        doc = Document(body)
        self.assertEqual(len(re.findall(r"<h1\b", body)), 1)
        self.assertIn("<title>" + self.item["title"], body)
        self.assertIn(f'content="{html.escape(self.item["meta_description"], quote=True)}"', body)
        self.assertIn(f'href="{site.SITE_URL}{path}"', body)
        self.assertIn('datetime="2026-10-20"', body)
        self.assertNotIn("noindex", body)
        self.assertNotIn("Редакционный предпросмотр", body)
        self.assertEqual(len(doc.ids), len(set(doc.ids)))
        self.assertIn(path, self.client.get("/ru/blog/").get_data(as_text=True))
        self.assertIn(path, self.client.get("/sitemap.xml").get_data(as_text=True))
        self.assertEqual(self.client.get("/blog/" + self.item["slug"] + "/").status_code, 404)

    def test_schema_and_actual_sources_match(self):
        body = self.client.get(self.item["link"]).get_data(as_text=True)
        schemas = []
        for raw in re.findall(r'<script type="application/ld\+json">(.*?)</script>', body, re.S):
            data = json.loads(raw)
            schemas.extend(data if isinstance(data, list) else [data])
        post = next(schema for schema in schemas if schema.get("@type") == "BlogPosting")
        self.assertEqual(post["datePublished"], "2026-10-20")
        self.assertEqual(len(post["citation"]), 3)
        self.assertTrue(all("www.ocpb.go.th/" in citation["url"] for citation in post["citation"]))
        panel = site.article_source_panel_for_post(self.item, lang="ru")
        self.assertEqual(len(panel["sources"]), 3)
        self.assertEqual(panel["checks"], [])
        self.assertEqual(body.count('class="rta-source-panel"'), 1)

    def test_links_and_anchors_resolve(self):
        body = self.client.get(self.item["link"]).get_data(as_text=True)
        doc = Document(body)
        for tag, attrs in doc.tags:
            href = attrs.get("href", "")
            if tag != "a":
                continue
            if href.startswith("#"):
                self.assertIn(href[1:], doc.ids)
            elif href.startswith("/") and not href.startswith("//"):
                self.assertLess(self.client.get(urlsplit(href).path).status_code, 400)

    def test_clean_body_and_transparent_example(self):
        body = self.item["content"]
        self.assertNotRegex(body.lower(), r"<(?:h1|style|script)\b")
        self.assertIn('class="table-scroll"', body)
        self.assertIn('tabindex="0"', body)
        for value in ("60 000 THB", "25 000 THB", "65 000 THB", "55 000 THB"):
            self.assertIn(value, body)
        self.assertEqual(20000 + 40000, 60000)
        self.assertEqual(20000 + 3500 + 700 + 800, 25000)
        self.assertEqual(25000 + 40000, 65000)
        self.assertEqual(60000 - 5000, 55000)
        self.assertNotIn("24 часа", body)
        self.assertIn("не личные расходы автора", body)


if __name__ == "__main__":
    unittest.main()
