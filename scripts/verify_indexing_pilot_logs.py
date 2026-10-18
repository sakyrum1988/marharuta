"""Check recent pilot Googlebot claims against Google's current public IP list.

Reads local logs; only Google's public range document is fetched. No log data,
client addresses or site URLs are transmitted. A matched crawl is NOT indexing.
Older than 24h requires a contemporary range snapshot, not this current-list tool.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import ipaddress
import json
from pathlib import Path
import sys
from urllib.request import urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from indexing_pilot import EVENT, public_ip

SOURCE = "https://developers.google.com/crawling/ipranges/common-crawlers.json"
MAX_BYTES = 2_000_000


def parse_ranges(raw):
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("Invalid Google IP document")
    prefixes = data["prefixes"]
    if not isinstance(prefixes, list) or not 1 <= len(prefixes) <= 10000:
        raise ValueError("Invalid Google IP list")
    networks = []
    for item in prefixes:
        if not isinstance(item, dict):
            raise ValueError("Invalid Google IP entry")
        cidr = item.get("ipv4Prefix") or item.get("ipv6Prefix")
        network = ipaddress.ip_network(cidr, strict=True)
        if not network.is_global or network.prefixlen < (16 if network.version == 4 else 32):
            raise ValueError("Unexpectedly broad or non-public crawler range")
        networks.append(network)
    return networks


def classify(record, networks, *, now):
    result = {"path": record.get("path"), "group": record.get("group"),
              "experiment": record.get("experiment"), "observed_at": record.get("observed_at"),
              "status": record.get("status"), "identity": "unverified",
              "indexing": "not_measured"}
    if record.get("claimed_agent") != "googlebot":
        return {**result, "identity": "not_a_googlebot_claim"}
    try:
        observed = datetime.fromisoformat(record["observed_at"])
        if observed.tzinfo is None or not -300 <= (now - observed).total_seconds() <= 86400:
            return {**result, "identity": "requires_contemporary_range_snapshot"}
    except (ValueError, KeyError, TypeError):
        return {**result, "identity": "invalid_observation_time"}
    address = public_ip(record.get("client_ip"))
    if not address or record.get("ip_source") not in {"render_cf_connecting_ip", "direct_socket"}:
        return {**result, "identity": "no_trusted_client_ip"}
    matched = any(ipaddress.ip_address(address) in net for net in networks)
    return {**result, "identity": "googlebot_ip_match" if matched else "not_in_current_google_ranges"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", type=Path, required=True)
    args = parser.parse_args()
    try:
        # Validate local input before making a network request. Parse only our
        # structured event lines, allowing a Render/logger prefix before the JSON.
        records = []
        with args.log.open(encoding="utf-8") as stream:
            for line in stream:
                if len(line) > 16384:
                    raise ValueError("Oversized log line")
                marker = line.find('{"event":"' + EVENT + '"')
                if marker >= 0:
                    record = json.loads(line[marker:])
                    if record.get("event") == EVENT:
                        records.append(record)
                if len(records) > 100000:
                    raise ValueError("Log is too large")
        if not records:
            raise ValueError("No pilot event records")
        with urlopen(SOURCE, timeout=20) as response:
            if response.status != 200 or response.geturl() != SOURCE:
                raise ValueError("Unexpected Google IP list response")
            raw = response.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError("Oversized Google IP list")
        networks = parse_ranges(raw)
        now = datetime.now(timezone.utc)
        print(json.dumps({"range_source": SOURCE, "range_sha256": hashlib.sha256(raw).hexdigest(),
                          "checked_at": now.isoformat(),
                          "results": [classify(row, networks, now=now) for row in records]},
                         ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({"status": "verification_failed", "error_type": type(error).__name__}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
