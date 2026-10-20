"""Publication safety and public rendering checks for the approved article."""
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
from publish_thailand_weather_ru import article, publish
from technical_audit import Document


class ThailandWeatherTests(unittest.TestCase):
    def setUp(self):
        site._PAGE_CACHE.clear()
        self.client = site.app.test_client()
        self.item = article()

    def test_safe_additive_migration_and_idempotency(self):
        with tempfile.TemporaryDirectory() as temporary:
            database = Path(temporary) / "content.db"
            with closing(sqlite3.connect(database)) as db, db:
                db.execute("CREATE TABLE posts (id INTEGER PRIMARY KEY,slug TEXT,title TEXT,content TEXT,excerpt TEXT,date TEXT,lang TEXT,link TEXT)")
                db.execute("INSERT INTO posts VALUES (1,'keep','Keep','Body','Excerpt','2026-01-01','en','/blog/keep/')")
            self.assertTrue(publish(database))
            self.assertFalse(publish(database))
            with closing(sqlite3.connect(database)) as db, db:
                self.assertEqual(db.execute("SELECT COUNT(*) FROM posts").fetchone()[0], 2)
                self.assertEqual(db.execute("SELECT title,seo_title,meta_description FROM posts WHERE id=1").fetchone(), ("Keep", None, None))
                db.execute("UPDATE posts SET title='User edit' WHERE slug=?", (self.item["slug"],))
            with self.assertRaises(RuntimeError):
                publish(database)

    def test_metadata_discovery_and_schema(self):
        path = self.item["link"]
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertEqual(len(re.findall(r"<h1\b", body)), 1)
        self.assertIn(self.item["title"], body)
        self.assertIn("<title>" + self.item["seo_title"] + "</title>", body)
        self.assertIn(f'name="description" content="{html.escape(self.item["meta_description"], quote=True)}"', body)
        self.assertIn(f'rel="canonical" href="{site.SITE_URL}{path}"', body)
        self.assertNotIn("noindex", body)
        self.assertNotIn("Редакционный предпросмотр", body)
        self.assertIn('datetime="2026-10-20"', body)
        for discovery in ("/ru/blog/", "/sitemap.xml"):
            self.assertIn(path, self.client.get(discovery).get_data(as_text=True))
        self.assertEqual(self.client.get(f"/blog/{self.item['slug']}/").status_code, 404)
        schemas = []
        for raw in re.findall(r'<script type="application/ld\+json">(.*?)</script>', body, re.S):
            parsed = json.loads(raw)
            schemas.extend(parsed if isinstance(parsed, list) else [parsed])
        schema = next(item for item in schemas if item.get("@type") == "BlogPosting")
        self.assertEqual(schema["datePublished"], self.item["date"])
        self.assertEqual(schema["headline"], self.item["title"])
        self.assertEqual(len(schema["citation"]), 6)
        self.assertEqual(schema["url"], site.SITE_URL + path)

    def test_sources_links_and_readable_table(self):
        panel = site.article_source_panel_for_post(self.item, lang="ru")
        self.assertEqual(len(panel["sources"]), 6)
        self.assertEqual(panel["checks"], [])
        self.assertTrue(all(urlsplit(s["url"]).hostname in
                            {"www.tourismthailand.org", "worldweather.wmo.int", "www.tmd.go.th"}
                            for s in panel["sources"]))
        body = self.client.get(self.item["link"]).get_data(as_text=True)
        self.assertIn("Климат и прогноз", body)
        self.assertNotIn("thaievisa", body)
        self.assertEqual(body.count('class="rta-source-panel"'), 1)
        self.assertIn('class="table-scroll"', body)
        self.assertIn('tabindex="0"', body)
        doc = Document(body)
        self.assertEqual(len(doc.ids), len(set(doc.ids)))
        for tag, attrs in doc.tags:
            href = attrs.get("href", "")
            if tag == "a" and href.startswith("#"):
                self.assertIn(href[1:], doc.ids)
            elif tag == "a" and href.startswith("/") and not href.startswith("//"):
                self.assertLess(self.client.get(urlsplit(href).path).status_code, 400)

    def test_unequal_language_pagination(self):
        for counts, expected_lang, prefix in (
            ({"en": 19, "ru": 21}, "ru", "/ru/blog/"),
            ({"en": 21, "ru": 19}, "en", "/blog/"),
        ):
            alternates = site.blog_page_alternates(3, counts=counts)
            self.assertEqual([item["lang"] for item in alternates], [expected_lang, "x-default"])
            self.assertTrue(all(item["url"] == site.SITE_URL + prefix + "page/3/" for item in alternates))
            self.assertEqual(len(site.blog_page_alternates(2, counts=counts)), 3)
        page = self.client.get("/ru/blog/page/3/")
        self.assertEqual(page.status_code, 200)
        self.assertNotIn('href="https://www.marharuta.online/blog/page/3/"', page.get_data(as_text=True))
        self.assertEqual(self.client.get("/blog/page/3/").status_code, 404)
        sitemap = self.client.get("/sitemap.xml").get_data(as_text=True)
        self.assertIn(site.SITE_URL + "/ru/blog/page/3/", sitemap)
        self.assertNotIn(site.SITE_URL + "/blog/page/3/", sitemap)


if __name__ == "__main__":
    unittest.main()
