"""Opt-in Atom discovery experiment. No outbound requests or indexing claims.

INDEXING_PILOT_DIR points to a private prepare-output directory, outside static/.
The directory contains feed.atom and manifest.json from free_indexing_probe.py.
An absent or invalid bundle disables the endpoint and experiment logging.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import ipaddress
import json
import logging
import os
from pathlib import Path
import re
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

from flask import Response, request

ATOM = "{http://www.w3.org/2005/Atom}"
HUB = "https://pubsubhubbub.appspot.com/"
FEED_PATH = "/free-indexing-pilot.atom"
MAX_BYTES = 4_000_000
EVENT = "seokit_indexing_pilot"


def _read_bounded(path: Path) -> bytes:
    with path.open("rb") as stream:
        body = stream.read(MAX_BYTES + 1)
    if len(body) > MAX_BYTES:
        raise ValueError("Pilot artifact is too large")
    return body


def _page_path(url: str, origin: str) -> str:
    if not isinstance(url, str) or len(url) > 2048 or re.search(r"[\s\\\x00-\x1f]", url):
        raise ValueError("Invalid page URL")
    parts = urlsplit(url)
    if (parts.scheme + "://" + parts.netloc != origin or parts.query or parts.fragment
            or not parts.path.startswith("/") or parts.path.startswith("//")):
        raise ValueError("Pilot pages must use the canonical origin without query or fragment")
    return parts.path


def load_bundle(directory: Path, origin: str, static_folder: Path | None) -> dict:
    directory = directory.resolve()
    if static_folder and directory.is_relative_to(static_folder.resolve()):
        raise ValueError("The control manifest must not be published in static/")
    feed = _read_bounded(directory / "feed.atom")
    manifest = json.loads(_read_bounded(directory / "manifest.json"))
    if not isinstance(manifest, dict):
        raise ValueError("Invalid pilot manifest")
    expected = origin + FEED_PATH
    if (manifest.get("version") != 1 or manifest.get("feed_url") != expected
            or manifest.get("hub") != HUB
            or hashlib.sha256(feed).hexdigest() != manifest.get("feed_sha256")):
        raise ValueError("Pilot artifact does not match its manifest")
    rows = manifest.get("entries")
    if not isinstance(rows, list) or not 4 <= len(rows) <= 1000:
        raise ValueError("Invalid pilot sample size")
    paths, treatment = {}, set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Invalid pilot entry")
        path = _page_path(row["url"], origin)
        if path == FEED_PATH or path in paths or row.get("group") not in {"treatment", "control"}:
            raise ValueError("Invalid or duplicate assignment")
        paths[path] = row["group"]
        if row["group"] == "treatment":
            treatment.add(row["url"])
    if len(treatment) < 2 or len(rows) - len(treatment) < 2:
        raise ValueError("Both experiment groups are required")
    if b"<!DOCTYPE" in feed.upper() or b"<!ENTITY" in feed.upper():
        raise ValueError("XML declarations with entities are not supported")
    root = ET.fromstring(feed)
    if root.tag != ATOM + "feed" or root.findtext(ATOM + "id") != expected:
        raise ValueError("Invalid Atom feed")
    links = [(item.get("rel"), item.get("href")) for item in root.findall(ATOM + "link")]
    if sorted(links) != sorted([("self", expected), ("hub", HUB)]):
        raise ValueError("Unexpected feed links")
    entries = root.findall(ATOM + "entry")
    ids = [item.findtext(ATOM + "id") for item in entries]
    if len(ids) != len(treatment) or set(ids) != treatment:
        raise ValueError("Feed entries differ from the treatment group")
    for entry in entries:
        links = entry.findall(ATOM + "link")
        if (len(links) != 1 or links[0].get("rel") != "alternate"
                or links[0].get("href") != entry.findtext(ATOM + "id")):
            raise ValueError("Unexpected entry links")
    return {"body": feed, "url": expected, "paths": paths,
            "experiment": manifest["feed_sha256"][:16]}


def public_ip(value: str | None) -> str | None:
    try:
        address = ipaddress.ip_address(value or "")
    except ValueError:
        return None
    return str(address) if address.is_global and not address.is_multicast else None


def client_ip(environ: dict, *, render_edge: bool) -> tuple[str | None, str]:
    """Never trust arbitrary X-Forwarded-For or change application-wide ProxyFix.

    Render's public edge overwrites CF-Connecting-IP. Trust it only after explicit
    deployment opt-in, on Render, with the observed loopback proxy peer. Unknown
    topologies remain unverified instead of guessing an IP out of a header chain.
    """
    peer = environ.get("REMOTE_ADDR", "")
    if render_edge:
        try:
            loopback = ipaddress.ip_address(peer).is_loopback
        except ValueError:
            loopback = False
        if loopback:
            address = public_ip(environ.get("HTTP_CF_CONNECTING_IP"))
            return address, "render_cf_connecting_ip" if address else "missing_edge_ip"
        return None, "untrusted_proxy_peer"
    address = public_ip(peer)
    return address, "direct_socket" if address else "unverified_proxy"


def claimed_agent(user_agent: str) -> str:
    # Names are claims, not an identity check. Do not log the raw, untrusted UA.
    if re.search(r"\bGooglebot/", user_agent, re.I):
        return "googlebot"
    if "Feedfetcher-Google" in user_agent:
        return "feedfetcher"
    if "Google-InspectionTool" in user_agent:
        return "inspection_tool"
    if "SEOKit-Free-Indexing-Research/" in user_agent:
        return "research_probe"
    return "other"


def register_indexing_pilot(app, origin="https://www.marharuta.online"):
    bundle = None
    directory = app.config.get("INDEXING_PILOT_DIR", os.getenv("INDEXING_PILOT_DIR"))
    if directory:
        try:
            bundle = load_bundle(Path(directory), origin,
                                 Path(app.static_folder) if app.static_folder else None)
        except (OSError, ValueError, KeyError, TypeError, ET.ParseError):
            # Bad experiment setup must neither disclose files nor break the site.
            app.logger.warning("Indexing pilot disabled: invalid private artifact bundle")
    app.extensions["indexing_pilot"] = {"enabled": bundle is not None}
    render_edge = (os.getenv("RENDER") == "true"
                   and os.getenv("INDEXING_PILOT_TRUST_RENDER_EDGE") == "1")
    logger = logging.getLogger("seokit.indexing_pilot")
    if bundle and not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False

    def serve_feed():
        if not bundle:
            return Response("Not found\n", status=404, headers={"Cache-Control": "no-store"})
        response = Response(bundle["body"], content_type="application/atom+xml; charset=utf-8")
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Link"] = f'<{bundle["url"]}>; rel="self", <{HUB}>; rel="hub"'
        return response

    app.add_url_rule(FEED_PATH, "free_indexing_pilot", serve_feed, methods=["GET"])

    @app.after_request
    def observe_pilot(response):
        if not bundle or request.method not in {"GET", "HEAD"}:
            return response
        group = "feed" if request.path == FEED_PATH else bundle["paths"].get(request.path)
        if not group:
            return response
        agent = claimed_agent(request.headers.get("User-Agent", ""))
        address, source = client_ip(request.environ, render_edge=render_edge)
        # Minimize personal data: IPs only for requests claiming a relevant crawler.
        if agent not in {"googlebot", "feedfetcher", "inspection_tool"}:
            address, source = None, "not_collected"
        record = {"event": EVENT, "experiment": bundle["experiment"],
                  "observed_at": datetime.now(timezone.utc).isoformat(),
                  "path": request.path, "group": group, "method": request.method,
                  "status": response.status_code, "claimed_agent": agent,
                  "client_ip": address, "ip_source": source,
                  "identity": "unverified", "indexing": "not_measured"}
        logger.info(json.dumps(record, ensure_ascii=True, separators=(",", ":")))
        return response
