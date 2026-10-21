# S8TV DOM checker → M3U + match status

This Playwright bot opens `https://s8tv011.com/`, waits for client-rendered content, tries visible “Show more / Xem thêm” controls, identifies possible same-site match pages from normal DOM links, and checks each match page for `.m3u` / `.m3u8` URLs explicitly exposed in its DOM or visible text.

It writes:
- `sport.m3u`: unique URLs that were visible in the normal page DOM.
- `matches.csv`: match title, page URL, status, link count and notes.
- `matches.json`: same results in JSON.

## Important limitations

- This does **not** capture browser network requests or call hidden APIs.
- It does not log in, solve CAPTCHA, evade paywalls, or bypass access controls.
- A result `NO_PUBLIC_M3U8_IN_DOM` means no stream URL was found in the page DOM; it does not prove that a match has no stream.
- S8TV's HTML may change. If generic match discovery fails, inspect the page's ordinary DOM and fill in `selectors.match_card` and `selectors.match_title` in `sources.json`. These selectors are intentionally blank rather than guessed.
- Only use stream URLs you are authorized to access and redistribute. A link being found does not guarantee it is playable or licensed for redistribution.

## Run locally

```bash
python -m pip install -r requirements.txt
python -m playwright install chromium
python bot.py
```

## GitHub Actions

The workflow runs every 3 hours and can also be started manually under **Actions → Auto update sport playlist → Run workflow**. It commits the three generated output files when they change.


## Why `sport.m3u` may show no channels

If the bot does not find any `.m3u`/`.m3u8` URL exposed in the normal page DOM, there are no playable entries to put in the playlist. This version adds diagnostic comments, but media players do not show comments as channels. Open `matches.csv` or `matches.json` and inspect the `status` and `note` fields. `NO_PUBLIC_M3U8_IN_DOM` means no URL was found in ordinary page DOM; it does not prove that the match has no stream.
