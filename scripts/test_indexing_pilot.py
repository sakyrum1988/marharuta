"""Offline tests: synthetic samples are not evidence of indexing effectiveness."""
from datetime import datetime, timedelta, timezone
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from flask import Flask
import indexing_pilot as pilot
from scripts.verify_indexing_pilot_logs import classify, parse_ranges

ORIGIN = "https://www.marharuta.online"
NOW = datetime(2026, 10, 18, tzinfo=timezone.utc)


def write_bundle(directory):
    rows = [{"url": ORIGIN + path, "group": group} for path, group in (
        ("/about/", "treatment"), ("/editorial-policy/", "treatment"),
        ("/blog/", "control"), ("/ru/blog/", "control"))]
    root = ET.Element(pilot.ATOM + "feed")
    ET.SubElement(root, pilot.ATOM + "id").text = ORIGIN + pilot.FEED_PATH
    ET.SubElement(root, pilot.ATOM + "title").text = "Synthetic fixture"
    ET.SubElement(root, pilot.ATOM + "updated").text = "2026-10-17T00:00:00Z"
    for rel, href in (("self", ORIGIN + pilot.FEED_PATH), ("hub", pilot.HUB)):
        ET.SubElement(root, pilot.ATOM + "link", rel=rel, href=href)
    for row in rows[:2]:
        entry = ET.SubElement(root, pilot.ATOM + "entry")
        ET.SubElement(entry, pilot.ATOM + "id").text = row["url"]
        ET.SubElement(entry, pilot.ATOM + "title").text = "Synthetic fixture"
        ET.SubElement(entry, pilot.ATOM + "updated").text = "2026-10-17T00:00:00Z"
        ET.SubElement(entry, pilot.ATOM + "link", rel="alternate", href=row["url"])
    body = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    manifest = {"version": 1, "feed_url": ORIGIN + pilot.FEED_PATH,
                "hub": pilot.HUB, "feed_sha256": hashlib.sha256(body).hexdigest(), "entries": rows}
    (directory / "feed.atom").write_bytes(body)
    (directory / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return manifest, body


class PilotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name)
        self.manifest, self.body = write_bundle(self.directory)
        self.env = patch.dict(os.environ, {}, clear=True)
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.temp.cleanup()

    def app(self, directory=None):
        app = Flask(__name__)
        app.config["TESTING"] = True
        app.config["INDEXING_PILOT_DIR"] = directory
        pilot.register_indexing_pilot(app, ORIGIN)
        app.add_url_rule("/about/", "about", lambda: "about")
        app.add_url_rule("/blog/", "blog", lambda: "blog")
        return app

    def test_disabled_by_default_without_logging(self):
        app = self.app()
        with patch.object(pilot.logging.getLogger("seokit.indexing_pilot"), "info") as log:
            response = app.test_client().get(pilot.FEED_PATH)
            self.assertEqual(response.status_code, 404)
            log.assert_not_called()
        self.assertFalse(app.extensions["indexing_pilot"]["enabled"])

    def test_exact_feed_bytes_and_head(self):
        client = self.app(str(self.directory)).test_client()
        with patch.object(pilot.logging.getLogger("seokit.indexing_pilot"), "info"):
            response = client.get(pilot.FEED_PATH)
            head = client.head(pilot.FEED_PATH)
        self.assertEqual(response.data, self.body)
        self.assertEqual(response.mimetype, "application/atom+xml")
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        self.assertIn(pilot.HUB, response.headers["Link"])
        self.assertEqual(head.status_code, 200)
        self.assertEqual(head.data, b"")

    def test_no_manifest_route_or_submission_endpoint(self):
        client = self.app(str(self.directory)).test_client()
        self.assertEqual(client.get("/manifest.json").status_code, 404)
        self.assertEqual(client.post(pilot.FEED_PATH).status_code, 405)

    def test_control_urls_not_in_feed(self):
        bundle = pilot.load_bundle(self.directory, ORIGIN, None)
        self.assertNotIn((ORIGIN + "/blog/").encode(), bundle["body"])
        self.assertEqual(bundle["paths"]["/blog/"], "control")

    def test_wrong_hash_fails_closed_without_breaking_site(self):
        (self.directory / "feed.atom").write_bytes(b"wrong")
        with self.assertLogs(level="WARNING"):
            app = self.app(str(self.directory))
        client = app.test_client()
        self.assertEqual(client.get(pilot.FEED_PATH).status_code, 404)
        self.assertEqual(client.get("/about/").status_code, 200)

    def test_sample_manifest_validation(self):
        for change in ("origin", "query", "duplicate", "group", "controls"):
            with self.subTest(change=change):
                manifest, _ = write_bundle(self.directory)
                if change == "origin":
                    manifest["entries"][0]["url"] = "https://other.test/about/"
                elif change == "query":
                    manifest["entries"][0]["url"] += "?token=secret"
                elif change == "duplicate":
                    manifest["entries"][1]["url"] = manifest["entries"][0]["url"]
                elif change == "group":
                    manifest["entries"][0]["group"] = "unknown"
                else:
                    manifest["entries"][2]["group"] = "treatment"
                (self.directory / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
                with self.assertRaises(ValueError):
                    pilot.load_bundle(self.directory, ORIGIN, None)

    def test_rejects_public_manifest_directory(self):
        with self.assertRaises(ValueError):
            pilot.load_bundle(self.directory, ORIGIN, self.directory.parent)

    def test_malformed_manifest_disables_pilot_without_breaking_site(self):
        for manifest in ([], {**self.manifest, "entries": [None] * 4}):
            with self.subTest(manifest=manifest):
                (self.directory / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
                with self.assertLogs(level="WARNING"):
                    app = self.app(str(self.directory))
                self.assertFalse(app.extensions["indexing_pilot"]["enabled"])
                self.assertEqual(app.test_client().get("/about/").status_code, 200)

    def test_rejects_xml_entities_even_with_matching_hash(self):
        body = b'<!DOCTYPE feed [<!ENTITY x "test">]>' + self.body
        self.manifest["feed_sha256"] = hashlib.sha256(body).hexdigest()
        (self.directory / "feed.atom").write_bytes(body)
        (self.directory / "manifest.json").write_text(json.dumps(self.manifest), encoding="utf-8")
        with self.assertRaises(ValueError):
            pilot.load_bundle(self.directory, ORIGIN, None)

    def test_control_in_entry_link_is_rejected(self):
        body = self.body.replace(b'href="https://www.marharuta.online/about/"',
                                 b'href="https://www.marharuta.online/blog/"')
        self.manifest["feed_sha256"] = hashlib.sha256(body).hexdigest()
        (self.directory / "feed.atom").write_bytes(body)
        (self.directory / "manifest.json").write_text(json.dumps(self.manifest), encoding="utf-8")
        with self.assertRaises(ValueError):
            pilot.load_bundle(self.directory, ORIGIN, None)

    def test_logs_both_groups_without_query_cookies_or_auth(self):
        client = self.app(str(self.directory)).test_client()
        with patch.object(pilot.logging.getLogger("seokit.indexing_pilot"), "info") as log:
            for path in ("/about/", "/blog/"):
                client.get(path + "?token=DO_NOT_LOG", headers={
                    "Authorization": "Bearer DO_NOT_LOG", "User-Agent": "Browser DO_NOT_LOG"})
            client.get("/unrelated/")
        self.assertEqual(log.call_count, 2)
        records = [json.loads(call.args[0]) for call in log.call_args_list]
        self.assertEqual({row["group"] for row in records}, {"control", "treatment"})
        self.assertNotIn("DO_NOT_LOG", str(log.call_args_list))
        self.assertTrue(all(row["client_ip"] is None for row in records))
        self.assertTrue(all(row["identity"] == "unverified" for row in records))

    def test_render_header_requires_two_explicit_environment_conditions(self):
        for environment, expected_source in (
            ({"RENDER": "true"}, "unverified_proxy"),
            ({"INDEXING_PILOT_TRUST_RENDER_EDGE": "1"}, "unverified_proxy"),
            ({"RENDER": "true", "INDEXING_PILOT_TRUST_RENDER_EDGE": "1"}, "render_cf_connecting_ip"),
        ):
            with self.subTest(environment=environment), patch.dict(os.environ, environment, clear=True):
                client = self.app(str(self.directory)).test_client()
                with patch.object(pilot.logging.getLogger("seokit.indexing_pilot"), "info") as log:
                    client.get("/about/", headers={"User-Agent": "Googlebot/2.1", "CF-Connecting-IP": "66.249.66.1"})
                self.assertEqual(json.loads(log.call_args.args[0])["ip_source"], expected_source)

    def test_proxy_header_is_not_trusted_for_direct_public_peer(self):
        data = {"REMOTE_ADDR": "1.1.1.1", "HTTP_CF_CONNECTING_IP": "66.249.66.1"}
        self.assertEqual(pilot.client_ip(data, render_edge=True), (None, "untrusted_proxy_peer"))
        self.assertEqual(pilot.client_ip(data, render_edge=False), ("1.1.1.1", "direct_socket"))

    def test_xff_and_invalid_edge_headers_do_not_prove_identity(self):
        for value in ("", "127.0.0.1", "10.0.0.1", "66.249.66.1, 1.1.1.1", "malformed"):
            data = {"REMOTE_ADDR": "127.0.0.1", "HTTP_CF_CONNECTING_IP": value,
                    "HTTP_X_FORWARDED_FOR": "66.249.66.1"}
            self.assertIsNone(pilot.client_ip(data, render_edge=True)[0])

    def test_feedfetcher_and_inspection_are_separate_from_googlebot(self):
        self.assertEqual(pilot.claimed_agent("Feedfetcher-Google"), "feedfetcher")
        self.assertEqual(pilot.claimed_agent("Google-InspectionTool/1.0"), "inspection_tool")
        self.assertEqual(pilot.claimed_agent("Googlebot-Image/1.0"), "other")


class VerificationTests(unittest.TestCase):
    def setUp(self):
        self.networks = [ipaddress.ip_network("66.249.66.0/24")]
        self.record = {"claimed_agent": "googlebot", "client_ip": "66.249.66.1",
                       "ip_source": "render_cf_connecting_ip", "observed_at": NOW.isoformat(),
                       "status": 200, "path": "/example/", "group": "treatment"}

    def check(self):
        return classify(self.record, self.networks, now=NOW)

    def test_match_is_not_an_indexing_result(self):
        result = self.check()
        self.assertEqual(result["identity"], "googlebot_ip_match")
        self.assertEqual(result["indexing"], "not_measured")

    def test_nonmatching_public_ip(self):
        self.record["client_ip"] = "1.1.1.1"
        self.assertEqual(self.check()["identity"], "not_in_current_google_ranges")

    def test_claim_without_trusted_ip_stays_unverified(self):
        self.record["ip_source"] = "x_forwarded_for"
        self.assertEqual(self.check()["identity"], "no_trusted_client_ip")

    def test_old_logs_require_contemporary_evidence(self):
        self.record["observed_at"] = (NOW - timedelta(days=2)).isoformat()
        self.assertEqual(self.check()["identity"], "requires_contemporary_range_snapshot")

    def test_user_triggered_fetch_is_not_search_crawl(self):
        self.record["claimed_agent"] = "feedfetcher"
        self.assertEqual(self.check()["identity"], "not_a_googlebot_claim")

    def test_invalid_ranges_cannot_match_everyone(self):
        for prefixes in ([], [{"ipv4Prefix": "0.0.0.0/0"}], [{"ipv4Prefix": "127.0.0.0/8"}]):
            with self.assertRaises(ValueError):
                parse_ranges(json.dumps({"prefixes": prefixes}))

    def test_malformed_range_document_is_rejected(self):
        for document in ([], {"prefixes": [None]}, {"prefixes": ["66.249.66.0/24"]}):
            with self.assertRaises(ValueError):
                parse_ranges(json.dumps(document))

    def test_ipv4_and_ipv6_range_formats(self):
        ranges = parse_ranges(json.dumps({"prefixes": [
            {"ipv4Prefix": "66.249.66.0/24"}, {"ipv6Prefix": "2001:4860:4801::/48"}]}))
        self.assertEqual(len(ranges), 2)


class SiteIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.directory = Path(cls.temp.name)
        _, cls.body = write_bundle(cls.directory)
        with patch.dict(os.environ, {"INDEXING_PILOT_DIR": str(cls.directory)}, clear=True):
            import app as site
        cls.site = site
        cls.site.app.config["TESTING"] = True

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_real_app_feed_and_normal_routes_with_cache(self):
        client = self.site.app.test_client()
        self.site._PAGE_CACHE.clear()
        with patch.object(pilot.logging.getLogger("seokit.indexing_pilot"), "info") as log:
            self.assertEqual(client.get(pilot.FEED_PATH, base_url=ORIGIN).data, self.body)
            first = client.get("/about/", base_url=ORIGIN)
            second = client.get("/about/", base_url=ORIGIN)
            control = client.get("/blog/", base_url=ORIGIN)
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.headers["X-Cache"], "HIT")
        self.assertEqual(control.status_code, 200)
        self.assertEqual(log.call_count, 4)
        self.assertNotIn(pilot.FEED_PATH, self.site._PAGE_CACHE)

    def test_apex_still_redirects_and_sitemap_unchanged(self):
        client = self.site.app.test_client()
        with patch.object(pilot.logging.getLogger("seokit.indexing_pilot"), "info"):
            response = client.get(pilot.FEED_PATH, base_url="https://marharuta.online")
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.location, ORIGIN + pilot.FEED_PATH)
        self.assertNotIn(pilot.FEED_PATH, client.get("/robots.txt").get_data(as_text=True))
        self.assertNotIn(pilot.FEED_PATH, client.get("/sitemap.xml").get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
