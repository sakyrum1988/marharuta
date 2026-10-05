"""
Syncs country data into country_facts table in content.db.

Sources:
  World Bank API — population, surface area and socioeconomic indicators.
  Previously imported country names, capitals and currencies are preserved.

Run manually or add to Render build:
  python sync_countries.py
"""
from __future__ import annotations

import sqlite3
import math
from datetime import datetime, timezone
from pathlib import Path

import requests

DB_PATH = Path(__file__).resolve().parent / "content.db"
TIMEOUT  = 12  # seconds per request

# page slug → ISO 3166-1 alpha-2
COUNTRIES: dict[str, str] = {
    "move-to-thailand":    "TH",
    "move-to-malaysia":    "MY",
    "move-to-bali":        "ID",
    "move-to-vietnam":     "VN",
    "move-to-taiwan":      "TW",
    "move-to-singapore":   "SG",
    "move-to-japan":       "JP",
    "move-to-south-korea": "KR",
    "move-to-philippines": "PH",
    "move-to-cambodia":    "KH",
    "move-to-myanmar":     "MM",
    "move-to-laos":        "LA",
    "move-to-india":       "IN",
    "move-to-sri-lanka":   "LK",
    "move-to-china":       "CN",
    "move-to-uae":         "AE",
    "move-to-nepal":       "NP",
    "move-to-brunei":      "BN",
    "move-to-uzbekistan":  "UZ",
    "move-to-kazakhstan":  "KZ",
    "move-to-georgia": "GE",
    "move-to-portugal": "PT",
    "move-to-spain": "ES",
    "move-to-germany": "DE",
    "move-to-poland": "PL",
    "move-to-mexico": "MX",
    "move-to-colombia": "CO",
    "move-to-turkey": "TR",
}

# World Bank indicator codes → column name
WB_INDICATORS: dict[str, str] = {
    "NY.GDP.PCAP.CD": "gdp_per_capita",   # GDP per capita (current USD)
    "IT.NET.USER.ZS": "internet_pct",      # Internet users (% population)
    "FP.CPI.TOTL.ZG": "inflation",         # Inflation, consumer prices (annual %)
    "SL.UEM.TOTL.ZS": "unemployment",      # Unemployment (% total labour force)
    "SP.DYN.LE00.IN": "life_expectancy",   # Life expectancy at birth (years)
    "SP.POP.TOTL": "population",
    "AG.SRF.TOTL.K2": "area",
}


# ── Schema ────────────────────────────────────────────────────────────────────

def init_table(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS country_facts (
            slug            TEXT PRIMARY KEY,
            iso2            TEXT NOT NULL,
            name            TEXT,
            capital         TEXT,
            currency_code   TEXT,
            currency_name   TEXT,
            languages       TEXT,
            population      INTEGER,
            flag_svg        TEXT,
            timezone        TEXT,
            region          TEXT,
            gdp_per_capita  REAL,
            internet_pct    REAL,
            inflation       REAL,
            unemployment    REAL,
            life_expectancy REAL,
            wb_year         TEXT,
            updated_at      TEXT
        )
    """)
    columns = {r[1] for r in conn.execute('PRAGMA table_info(country_facts)')}
    additions = {"area": "REAL", "wb_checked_at": "TEXT"}
    additions.update({f"{field}_year": "TEXT" for field in WB_INDICATORS.values()})
    for name, kind in additions.items():
        if name not in columns:
            conn.execute(f'ALTER TABLE country_facts ADD COLUMN {name} {kind}')
    conn.commit()






# ── World Bank: latest non-empty observation per country and indicator ───────

def fetch_wb_bulk() -> dict[str, dict]:
    results = {code: {} for code in COUNTRIES.values()}
    codes = ";".join(results)
    for indicator, field in WB_INDICATORS.items():
        try:
            response = requests.get(
                f"https://api.worldbank.org/v2/country/{codes}/indicator/{indicator}",
                params={"format": "json", "mrnev": 1, "per_page": 300},
                timeout=(5, 30),
            )
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, list) or len(payload) != 2 or not isinstance(payload[1], list):
                raise ValueError("Unexpected World Bank response")
            if int(payload[0].get("pages", 1)) > 1:
                raise ValueError("Incomplete World Bank response: pagination required")
            count = 0
            for entry in payload[1]:
                code = (entry.get("country") or {}).get("id")
                value, year = entry.get("value"), str(entry.get("date", ""))
                if code not in results or isinstance(value, bool) or not isinstance(value, (int, float)):
                    continue
                if not math.isfinite(value) or not year.isdigit() or len(year) != 4:
                    continue
                if field != "inflation" and value < 0:
                    continue
                if field in {"internet_pct", "unemployment"} and value > 100:
                    continue
                if year < results[code].get(f"{field}_year", ""):
                    continue
                results[code][field] = int(value) if field == "population" else round(value, 2)
                results[code][f"{field}_year"] = year
                count += 1
            print(f"{indicator}: {count} observations")
        except (requests.RequestException, ValueError, TypeError, KeyError) as error:
            print(f"{indicator}: unavailable ({error}); keeping saved observations")
    return results


def save_observations(conn: sqlite3.Connection, observations: dict[str, dict]) -> int:
    """Merge validated fields; a failed or partial request never erases a row."""
    now = datetime.now(timezone.utc).isoformat()
    count = 0
    for slug, code in COUNTRIES.items():
        cursor = conn.execute("SELECT * FROM country_facts WHERE iso2 = ?", (code,))
        row = cursor.fetchone()
        existing = dict(zip([d[0] for d in cursor.description], row)) if row else {}
        incoming = observations.get(code, {})
        updates = {}
        for field in WB_INDICATORS.values():
            value, year = incoming.get(field), incoming.get(f"{field}_year")
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                continue
            if not isinstance(year, str) or len(year) != 4 or not year.isdigit():
                continue
            if field != "inflation" and value < 0:
                continue
            if field in {"internet_pct", "unemployment"} and value > 100:
                continue
            if year < (existing.get(f"{field}_year") or ""):
                continue
            updates[field], updates[f"{field}_year"] = value, year
        if not updates:
            continue
        combined = {**existing, **updates}
        # A range is honest when different indicators have different vintages.
        years = sorted({combined.get(f"{f}_year") for f in WB_INDICATORS.values()
                        if f not in {"population", "area"} and combined.get(f"{f}_year")})
        if years:
            updates["wb_year"] = years[0] if years[0] == years[-1] else f"{years[0]}–{years[-1]}"
        updates["wb_checked_at"] = now
        if existing:
            assignments = ", ".join(f"{field} = ?" for field in updates)
            conn.execute(f"UPDATE country_facts SET {assignments} WHERE slug = ?", (*updates.values(), existing["slug"]))
        else:
            values = {"slug": slug, "iso2": code, **updates}
            fields = ", ".join(values)
            placeholders = ", ".join("?" for _ in values)
            conn.execute(f"INSERT INTO country_facts ({fields}) VALUES ({placeholders})", tuple(values.values()))
        count += 1
    conn.commit()
    return count


def main() -> None:
    observations = fetch_wb_bulk()
    if not any(observations.values()):
        raise SystemExit("No valid observations received; database left unchanged")
    # Keep a recoverable copy before schema migration or data updates.
    backup_dir = DB_PATH.parent / ".backups"
    backup_dir.mkdir(exist_ok=True)
    backup = backup_dir / ("content-before-api-sync-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f") + ".db")
    if DB_PATH.exists():
        with sqlite3.connect(f"file:{DB_PATH.as_posix()}?mode=ro", uri=True) as source:
            with sqlite3.connect(backup) as target:
                source.backup(target)
    with sqlite3.connect(DB_PATH) as conn:
        init_table(conn)
        count = save_observations(conn, observations)
    print(f"Updated {count} countries. Backup: {backup}")


if __name__ == "__main__":
    main()
