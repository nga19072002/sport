# Football TV — GitHub JSON updater starter

This repository starter is designed to update `matches.json` hourly using GitHub Actions.

## Important before enabling automation

This starter does **not** scrape Giovang or ONLive. It only reads a JSON feed URL that you are authorized to access and reuse. Publicly viewable pages are not automatically permission to scrape or redistribute their data. Do not bypass logins, CAPTCHAs, rate limits, or access controls, and do not extract video stream URLs.

## Files

- `matches.json` — sample data; replace only with authorized match data.
- `scripts/update_matches.py` — reads an approved HTTPS JSON feed and normalizes matches.
- `.github/workflows/update-matches.yml` — scheduled workflow (hourly) and manual run.

## Setup on GitHub

1. Create a GitHub repository.
2. Upload all files and folders from this ZIP, preserving their paths.
3. In the repository, open **Settings → Secrets and variables → Actions**.
4. Choose **New repository secret**:
   - Name: `MATCHES_FEED_URL`
   - Value: the HTTPS URL of an authorized JSON feed.
5. Open **Settings → Actions → General** and ensure workflows are allowed to run.
6. Under **Actions**, run **Update football matches** manually to test.
7. Under **Settings → Actions → General → Workflow permissions**, enable read and write permissions if required by your repository policy.

## Expected feed shape

The simplest supported response is a JSON array:

```json
[
  {
    "home": "Team A",
    "away": "Team B",
    "kickoff": "20:30",
    "status": "Scheduled",
    "watchUrl": "https://official.example/match-page"
  }
]
```

It also accepts `{"matches": [...]}` and the alternate keys `homeTeam`, `awayTeam`, `startTime`, and `officialUrl`.

The script intentionally rejects non-HTTPS URLs and leaves the existing file unchanged if it cannot find any valid matches. If the provider's schema is different, adapt the field mapping after reviewing its official documentation and terms.

## Serve JSON to the Android TV app

If the repository is public, the raw file can be read from a URL of this form:

`https://raw.githubusercontent.com/OWNER/REPOSITORY/BRANCH/matches.json`

Replace `OWNER`, `REPOSITORY`, and `BRANCH` with your actual repository details. Configure the Android app to fetch this URL over HTTPS. A public repository exposes the JSON to anyone.

## Limits

- GitHub scheduled workflows are not guaranteed to start at the exact minute.
- The feed URL must be a permitted JSON endpoint; a normal HTML webpage will not work with this starter.
- This is a starter package, not a confirmed integration with Giovang or ONLive.
