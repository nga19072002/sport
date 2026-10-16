#!/usr/bin/env python3
"""
Fetch an authorized JSON feed and write matches.json.

Expected feed shape:
[
  {
    "home": "Home team",
    "away": "Away team",
    "kickoff": "2026-10-16T20:30:00+07:00",
    "status": "Scheduled",
    "watchUrl": "https://official.example/match-page"
  }
]

Only use a feed/API you are authorized to access and reuse.
This script does not scrape websites or extract video stream URLs.
"""
import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

OUTPUT = Path("matches.json")
FEED_URL = os.environ.get("MATCHES_FEED_URL", "").strip()


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def valid_https_url(value: str) -> bool:
    try:
        parsed = urlparse(value)
        return parsed.scheme == "https" and bool(parsed.hostname)
    except ValueError:
        return False


if not FEED_URL or not valid_https_url(FEED_URL):
    fail(
        "Set the MATCHES_FEED_URL GitHub Actions secret to an authorized "
        "HTTPS JSON feed. No website has been scraped."
    )

request = Request(
    FEED_URL,
    headers={
        "Accept": "application/json",
        "User-Agent": "FootballTV-MatchesUpdater/1.0"
    },
)

try:
    with urlopen(request, timeout=25) as response:
        if response.status != 200:
            fail(f"Feed returned HTTP {response.status}")
        raw = json.load(response)
except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
    fail(f"Could not read valid JSON from the configured feed: {exc}")

# Some APIs wrap their list in {"matches": [...]}; accept either format.
if isinstance(raw, dict) and isinstance(raw.get("matches"), list):
    raw = raw["matches"]
if not isinstance(raw, list):
    fail("Unsupported feed format: expected a JSON array or {'matches': [...]}.")

cleaned = []
for item in raw:
    if not isinstance(item, dict):
        continue

    home = str(item.get("home", item.get("homeTeam", ""))).strip()
    away = str(item.get("away", item.get("awayTeam", ""))).strip()
    kickoff = str(item.get("kickoff", item.get("startTime", ""))).strip()
    status = str(item.get("status", "Chưa rõ trạng thái")).strip()
    watch_url = str(item.get("watchUrl", item.get("officialUrl", ""))).strip()

    # A valid fixture must have two teams. Only retain HTTPS viewing/info pages.
    if not home or not away or not valid_https_url(watch_url):
        continue

    cleaned.append({
        "home": home,
        "away": away,
        "kickoff": kickoff or "Chưa rõ giờ",
        "status": status or "Chưa rõ trạng thái",
        "watchUrl": watch_url,
    })

# Keep an empty/invalid feed from accidentally erasing a working list.
if not cleaned:
    fail("No valid matches found; keeping the previous matches.json unchanged.")

new_content = json.dumps(cleaned, ensure_ascii=False, indent=2) + "\n"
old_content = OUTPUT.read_text(encoding="utf-8") if OUTPUT.exists() else ""

if new_content == old_content:
    print(f"No changes; {len(cleaned)} matches already current.")
else:
    OUTPUT.write_text(new_content, encoding="utf-8")
    print(f"Updated matches.json with {len(cleaned)} matches.")
