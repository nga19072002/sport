
#!/usr/bin/env python3
"""Fetch football fixtures from API-Football and update matches.json."""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

API_URL = "https://v3.football.api-sports.io/fixtures"
API_KEY = os.environ.get("API_FOOTBALL_KEY", "").strip()
OUTPUT = Path("matches.json")
TZ = ZoneInfo("Asia/Ho_Chi_Minh")


def fail(message):
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


if not API_KEY:
    fail("Missing GitHub Actions secret API_FOOTBALL_KEY.")

today = datetime.now(TZ).date()
dates = [today, today + timedelta(days=1)]
matches = []

for match_date in dates:
    params = urlencode({
        "date": match_date.isoformat(),
        "timezone": "Asia/Ho_Chi_Minh",
    })
    request = Request(
        f"{API_URL}?{params}",
        headers={
            "x-apisports-key": API_KEY,
            "Accept": "application/json",
            "User-Agent": "FootballTV-MatchesUpdater/1.0",
        },
    )

    try:
        with urlopen(request, timeout=30) as response:
            data = json.load(response)
    except HTTPError as exc:
        fail(f"API returned HTTP {exc.code}. Check API key and plan.")
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        fail(f"Could not read API response: {exc}")

    if data.get("errors"):
        fail(f"API-Football error: {data['errors']}")

    for item in data.get("response", []):
        fixture = item.get("fixture", {})
        teams = item.get("teams", {})
        home = teams.get("home", {}).get("name", "")
        away = teams.get("away", {}).get("name", "")

        if not home or not away:
            continue

        status_info = fixture.get("status", {})
        status_code = status_info.get("short", "")
        status_text = status_info.get("long", "")

        # Keep watchUrl empty until an authorized viewing URL is available.
        matches.append({
            "home": home,
            "away": away,
            "kickoff": fixture.get("date", ""),
            "status": status_text or status_code or "Chưa rõ trạng thái",
            "watchUrl": "",
        })

# Do not overwrite the existing file if the API returns no fixtures.
if not matches:
    fail("API returned no fixtures for today and tomorrow; keeping existing matches.json.")

# Remove duplicate fixture entries.
unique = {}
for match in matches:
    key = (match["home"], match["away"], match["kickoff"])
    unique[key] = match

matches = sorted(unique.values(), key=lambda item: item["kickoff"])

new_content = json.dumps(matches, ensure_ascii=False, indent=2) + "\n"
old_content = OUTPUT.read_text(encoding="utf-8") if OUTPUT.exists() else ""

if new_content == old_content:
    print(f"No changes; {len(matches)} fixtures already current.")
else:
    OUTPUT.write_text(new_content, encoding="utf-8")
    print(f"Updated matches.json with {len(matches)} fixtures.")
