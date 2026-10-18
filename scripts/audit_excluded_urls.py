"""Read-only HTTP and optional Search Console inspection of the 15 audit URLs.

Usage: python scripts/audit_excluded_urls.py --gsc-root D:/GSC --output report.json
Credentials are handled by the existing local GSC client, never serialized.
URL Inspection returns Google's last indexed crawl, NOT a live test.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from html.parser import HTMLParser
import json
from pathlib import Path
import sys
from urllib.robotparser import RobotFileParser
import xml.etree.ElementTree as ET

import requests

SITE = "https://www.marharuta.online"
PATHS = [
    "/ru/countries/move-to-sri-lanka/", "/ru/countries/move-to-nepal/",
    "/compare/malaysia-vs-vietnam/", "/countries/move-to-cambodia/",
    "/ru/blog/uae-virtual-work-visa-2026/", "/ru/countries/move-to-india/",
    "/ru/blog/indonesia-e33g-remote-worker-visa-2026/",
    "/ru/blog/india-e-tourist-visa-2026/", "/blog/cambodia-evisa-visa-e-2026/",
    "/ru/blog/yaponiya-digital-nomad-visa-2026/",
    "/blog/thailand-ltr-remote-workers-2026/", "/countries/move-to-sri-lanka/",
    "/blog/japan-digital-nomad-visa-2026/", "/compare/uae-vs-qatar/",
    "/ru/blog/singapore-one-pass-2026/",
]


class Metadata(HTMLParser):
    def __init__(self):
        super().__init__()
        self.canonical = []
        self.robots = []
        self.h1_count = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "link" and "canonical" in attrs.get("rel", "").split():
            self.canonical.append(attrs.get("href", ""))
        if tag == "meta" and attrs.get("name", "").lower() in {"robots", "googlebot"}:
            self.robots.append(attrs.get("content", ""))
        if tag == "h1":
            self.h1_count += 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gsc-root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    robots_response = requests.get(SITE + "/robots.txt", timeout=30)
    robots_response.raise_for_status()
    robots = RobotFileParser()
    robots.parse(robots_response.text.splitlines())
    sitemap_response = requests.get(SITE + "/sitemap.xml", timeout=30)
    sitemap_response.raise_for_status()
    sitemap = {node.text for node in ET.fromstring(sitemap_response.content).iter()
               if node.tag.endswith("}loc")}

    def check(path):
        url = SITE + path
        result = {"url": url, "robots_googlebot_allowed": robots.can_fetch("Googlebot", url),
                  "in_sitemap": url in sitemap}
        try:
            response = requests.get(url, timeout=30)
            doc = Metadata()
            doc.feed(response.text)
            result.update(status=response.status_code, final_url=response.url,
                          canonical=doc.canonical, meta_robots=doc.robots,
                          x_robots_tag=response.headers.get("X-Robots-Tag", ""),
                          h1_count=doc.h1_count)
        except requests.RequestException as exc:
            result["http_error"] = type(exc).__name__
        return result

    rows = list(ThreadPoolExecutor(max_workers=4).map(check, PATHS))
    if args.gsc_root:
        sys.path.insert(0, str(args.gsc_root.resolve()))
        from app.config import Settings
        from app.gsc_client import GSCClient
        settings = Settings.from_env()
        client = GSCClient.from_service_account(settings.credentials_path, SITE + "/")
        fields = ("verdict", "coverageState", "robotsTxtState", "indexingState",
                  "lastCrawlTime", "pageFetchState", "googleCanonical", "userCanonical")
        for row in rows:
            try:
                result = client.inspect_url(row["url"])["inspectionResult"]["indexStatusResult"]
                row["google_last_crawl"] = {key: result[key] for key in fields if key in result}
            except Exception as exc:
                row["gsc_error"] = type(exc).__name__
            print(json.dumps(row, ensure_ascii=True), flush=True)
    report = {"checked_at": datetime.now(timezone.utc).isoformat(),
              "robots_txt": robots_response.text, "sitemap_url_count": len(sitemap),
              "note": "HTTP checks are current; Google URL Inspection is historical, not a live test.",
              "urls": rows}
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Checked {len(rows)} URLs. Report: {args.output}")


if __name__ == "__main__":
    main()
