"""
Syncs country data into country_facts table in content.db.

Sources:
  REST Countries (restcountries.com) — capital, currency, languages, population, flag, timezone
  World Bank API                     — GDP/capita, internet users %, inflation, unemployment, life expectancy

Run manually or add to Render build:
  python sync_countries.py
"""
from __future__ import annotations

import sqlite3
import time
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
}

# World Bank indicator codes → column name
WB_INDICATORS: dict[str, str] = {
    "NY.GDP.PCAP.CD": "gdp_per_capita",   # GDP per capita (current USD)
    "IT.NET.USER.ZS": "internet_pct",      # Internet users (% population)
    "FP.CPI.TOTL.ZG": "inflation",         # Inflation, consumer prices (annual %)
    "SL.UEM.TOTL.ZS": "unemployment",      # Unemployment (% total labour force)
    "SP.DYN.LE00.IN": "life_expectancy",   # Life expectancy at birth (years)
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
    conn.commit()


# ── REST Countries ─────────────────────────────────────────────────────────────

def fetch_rest(iso2: str) -> dict:
    fields = "name,capital,currencies,languages,population,flags,timezones,region"
    try:
        r = requests.get(
            f"https://restcountries.com/v3.1/alpha/{iso2}",
            params={"fields": fields},
            timeout=TIMEOUT,
        )
        r.raise_for_status()
    except Exception as e:
        print(f"    REST Countries error: {e}")
        return {}

    d = r.json()

    currencies = d.get("currencies") or {}
    code  = next(iter(currencies), "")
    cname = currencies.get(code, {}).get("name", "") if code else ""

    langs = list((d.get("languages") or {}).values())
    tzs   = d.get("timezones") or []

    return {
        "name":          d.get("name", {}).get("common", ""),
        "capital":       (d.get("capital") or [""])[0],
        "currency_code": code,
        "currency_name": cname,
        "languages":     ", ".join(langs[:4]),
        "population":    d.get("population") or 0,
        "flag_svg":      (d.get("flags") or {}).get("svg", ""),
        "timezone":      tzs[0] if tzs else "",
        "region":        d.get("region", ""),
    }


# ── World Bank static fallback (source: World Bank Open Data 2022–2023) ───────
# Keys: gdp_per_capita (USD), internet_pct (%), inflation (%), unemployment (%), life_expectancy (years)

WB_STATIC: dict[str, dict] = {
    "TH": {"gdp_per_capita": 7233,  "internet_pct": 85.3, "inflation": 5.9,  "unemployment": 1.1, "life_expectancy": 78.3, "wb_year": "2023"},
    "MY": {"gdp_per_capita": 12364, "internet_pct": 97.4, "inflation": 3.5,  "unemployment": 3.5, "life_expectancy": 76.5, "wb_year": "2023"},
    "ID": {"gdp_per_capita": 4788,  "internet_pct": 66.5, "inflation": 4.2,  "unemployment": 5.3, "life_expectancy": 68.1, "wb_year": "2023"},
    "VN": {"gdp_per_capita": 4163,  "internet_pct": 79.1, "inflation": 3.2,  "unemployment": 2.3, "life_expectancy": 75.6, "wb_year": "2023"},
    "TW": {"gdp_per_capita": 33234, "internet_pct": 90.4, "inflation": 2.5,  "unemployment": 3.5, "life_expectancy": 80.9, "wb_year": "2023"},
    "SG": {"gdp_per_capita": 82808, "internet_pct": 92.0, "inflation": 4.8,  "unemployment": 2.0, "life_expectancy": 83.5, "wb_year": "2023"},
    "JP": {"gdp_per_capita": 32487, "internet_pct": 92.7, "inflation": 3.3,  "unemployment": 2.6, "life_expectancy": 84.3, "wb_year": "2023"},
    "KR": {"gdp_per_capita": 36238, "internet_pct": 97.2, "inflation": 3.6,  "unemployment": 2.7, "life_expectancy": 83.6, "wb_year": "2023"},
    "PH": {"gdp_per_capita": 3984,  "internet_pct": 67.3, "inflation": 6.0,  "unemployment": 4.5, "life_expectancy": 71.0, "wb_year": "2023"},
    "KH": {"gdp_per_capita": 1765,  "internet_pct": 60.3, "inflation": 2.2,  "unemployment": 0.1, "life_expectancy": 70.2, "wb_year": "2022"},
    "MM": {"gdp_per_capita": 1191,  "internet_pct": 39.3, "inflation": 26.0, "unemployment": 2.3, "life_expectancy": 67.1, "wb_year": "2022"},
    "LA": {"gdp_per_capita": 2553,  "internet_pct": 52.3, "inflation": 30.0, "unemployment": 1.4, "life_expectancy": 68.0, "wb_year": "2022"},
    "IN": {"gdp_per_capita": 2694,  "internet_pct": 63.0, "inflation": 6.7,  "unemployment": 4.2, "life_expectancy": 70.2, "wb_year": "2023"},
    "LK": {"gdp_per_capita": 4515,  "internet_pct": 41.0, "inflation": 17.5, "unemployment": 4.7, "life_expectancy": 77.0, "wb_year": "2023"},
    "CN": {"gdp_per_capita": 12720, "internet_pct": 74.4, "inflation": 0.2,  "unemployment": 5.0, "life_expectancy": 78.2, "wb_year": "2023"},
    "AE": {"gdp_per_capita": 44316, "internet_pct": 99.0, "inflation": 3.7,  "unemployment": 2.7, "life_expectancy": 79.1, "wb_year": "2023"},
    "NP": {"gdp_per_capita": 1235,  "internet_pct": 51.2, "inflation": 7.8,  "unemployment": 4.9, "life_expectancy": 71.2, "wb_year": "2023"},
    "BN": {"gdp_per_capita": 37996, "internet_pct": 97.0, "inflation": 0.4,  "unemployment": 5.2, "life_expectancy": 75.3, "wb_year": "2023"},
    "UZ": {"gdp_per_capita": 2256,  "internet_pct": 79.4, "inflation": 11.5, "unemployment": 5.1, "life_expectancy": 74.0, "wb_year": "2023"},
    "KZ": {"gdp_per_capita": 13088, "internet_pct": 90.4, "inflation": 14.6, "unemployment": 4.7, "life_expectancy": 73.2, "wb_year": "2023"},
}


# ── World Bank (bulk, with static fallback) ────────────────────────────────────

def fetch_wb_bulk() -> dict[str, dict]:
    """
    One request per indicator for ALL countries at once (5 requests total).
    Returns {iso2: {col: value, 'wb_year': year}}.
    """
    iso2_list   = list(COUNTRIES.values())
    country_str = ";".join(iso2_list)
    results: dict[str, dict] = {iso2: {} for iso2 in iso2_list}

    for indicator, col in WB_INDICATORS.items():
        print(f"  WB bulk {indicator}...", end=" ", flush=True)
        try:
            r = requests.get(
                f"https://api.worldbank.org/v2/country/{country_str}/indicator/{indicator}",
                params={"format": "json", "mrv": 1, "per_page": 300},
                timeout=30,
            )
            r.raise_for_status()
            payload = r.json()
            if len(payload) < 2 or not payload[1]:
                print("no data")
                continue
            count = 0
            for entry in payload[1]:
                country_id = (entry.get("country") or {}).get("id", "")
                val = entry.get("value")
                if country_id in results and val is not None:
                    if col not in results[country_id]:
                        results[country_id][col] = round(float(val), 2)
                        results[country_id].setdefault(
                            "wb_year", str(entry.get("date", ""))
                        )
                        count += 1
            print(f"{count} values")
        except Exception as e:
            print(f"ERROR: {e}")
        time.sleep(0.5)

    # Fill missing values from static fallback
    missing = [iso2 for iso2, d in results.items() if not d]
    if missing:
        print(f"  Falling back to static data for: {', '.join(missing)}")
        for iso2 in missing:
            results[iso2] = WB_STATIC.get(iso2, {})

    return results


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        init_table(conn)

        # 1. REST Countries — one request per country (fast)
        print("=== REST Countries ===")
        rest_data: dict[str, dict] = {}
        for slug, iso2 in COUNTRIES.items():
            print(f"  [{iso2}]...", end=" ", flush=True)
            rest_data[iso2] = fetch_rest(iso2)
            print(rest_data[iso2].get("capital", "?"))

        # 2. World Bank — bulk (5 requests total, all countries at once)
        print("\n=== World Bank (bulk) ===")
        wb_data = fetch_wb_bulk()

        # 3. Save everything
        print("\n=== Saving ===")
        now = datetime.now(timezone.utc).isoformat()
        for slug, iso2 in COUNTRIES.items():
            rc = rest_data.get(iso2, {})
            wb = wb_data.get(iso2, {})
            conn.execute("""
                INSERT OR REPLACE INTO country_facts (
                    slug, iso2, name, capital,
                    currency_code, currency_name, languages,
                    population, flag_svg, timezone, region,
                    gdp_per_capita, internet_pct, inflation,
                    unemployment, life_expectancy, wb_year, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                slug, iso2,
                rc.get("name"),         rc.get("capital"),
                rc.get("currency_code"), rc.get("currency_name"), rc.get("languages"),
                rc.get("population"),    rc.get("flag_svg"), rc.get("timezone"), rc.get("region"),
                wb.get("gdp_per_capita"), wb.get("internet_pct"), wb.get("inflation"),
                wb.get("unemployment"),   wb.get("life_expectancy"), wb.get("wb_year"),
                now,
            ))
            print(f"  {iso2}: capital={rc.get('capital')}  gdp=${wb.get('gdp_per_capita')}  inet={wb.get('internet_pct')}%")

        conn.commit()
        total = conn.execute("SELECT COUNT(*) FROM country_facts").fetchone()[0]
        print(f"\nDone. country_facts: {total} rows.")


if __name__ == "__main__":
    main()
