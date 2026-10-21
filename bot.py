"""Playwright-based checker for publicly exposed, authorized M3U/M3U8 links.

Only reads normal page DOM (anchors, video/source elements, and visible text).
It does not intercept network traffic, execute hidden API calls, log in, solve CAPTCHAs,
or bypass access controls. Configure selectors for the source you are authorized to use.
"""
from __future__ import annotations
import csv, json, re, time
from pathlib import Path
from urllib.parse import urljoin, urlparse
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

ROOT = Path(__file__).resolve().parent
CFG = json.loads((ROOT / 'sources.json').read_text(encoding='utf-8'))
BASE_URL = CFG.get('start_url', 'https://s8tv011.com/')
DOMAIN = (urlparse(BASE_URL).hostname or '').lower()
TIMEOUT = int(CFG.get('timeout_ms', 25000))
MAX_MATCH_PAGES = int(CFG.get('max_match_pages', 80))
MAX_LOAD_MORE = int(CFG.get('max_load_more_clicks', 15))
STREAM_RE = re.compile(r'https?://[^\s"\'<>]+?\.m3u8?(?:\?[^\s"\'<>]*)?', re.I)
MATCH_RE = re.compile(r'\b(?:vs?\.?|v\.?|–|—)\b', re.I)
BAD_TERMS = ('banner', 'advert', 'analytics', 'trailer', 'highlight', 'promo')


def clean(s):
    return re.sub(r'\s+', ' ', (s or '')).strip()[:180]


def is_stream(url):
    p = urlparse(url)
    return p.scheme in ('http', 'https') and bool(re.search(r'\.m3u8?(?:$|\?)', p.path + ('?' + p.query if p.query else ''), re.I)) and not any(t in url.lower() for t in BAD_TERMS)


def same_site(url):
    host = (urlparse(url).hostname or '').lower()
    return host == DOMAIN or host.endswith('.' + DOMAIN)


def expand_listing(page):
    # Click only ordinary, visible pagination/load-more controls; stop if the page stops growing.
    labels = re.compile(r'(show more|load more|xem thêm|xem tất cả|tải thêm|more matches)', re.I)
    for _ in range(MAX_LOAD_MORE):
        before = page.locator('body').inner_text(timeout=3000)
        clicked = False
        for loc in [page.get_by_role('button', name=labels), page.get_by_text(labels)]:
            try:
                for i in range(min(loc.count(), 8)):
                    item = loc.nth(i)
                    if item.is_visible(timeout=300):
                        item.click(timeout=1200)
                        page.wait_for_timeout(900)
                        clicked = True
                        break
                if clicked:
                    break
            except Exception:
                continue
        if not clicked:
            break
        after = page.locator('body').inner_text(timeout=3000)
        if len(after) <= len(before):
            break


def collect_matches(page):
    cfg = CFG.get('selectors', {})
    card_sel, title_sel, url_sel = cfg.get('match_card'), cfg.get('match_title'), cfg.get('match_link', 'a[href]')
    rows = []
    if card_sel and title_sel:
        cards = page.locator(card_sel)
        for i in range(min(cards.count(), MAX_MATCH_PAGES * 3)):
            card = cards.nth(i)
            try:
                title = clean(card.locator(title_sel).first.inner_text(timeout=700))
                hrefs = card.locator(url_sel).evaluate_all("els => els.map(a => a.href).filter(Boolean)")
                href = next((u for u in hrefs if same_site(u)), '')
                if title:
                    rows.append({'title': title, 'url': href})
            except Exception:
                pass
    if not rows:
        # Generic fallback: use same-site anchors with match-like labels or match-like parent text.
        data = page.locator('a[href]').evaluate_all("els => els.map(a => ({href:a.href, text:(a.innerText||a.getAttribute('aria-label')||'').trim(), parent:(a.parentElement?.innerText||'').trim().slice(0,260)}))")
        for item in data:
            href = item.get('href', '')
            if not same_site(href) or href.rstrip('/') == BASE_URL.rstrip('/'):
                continue
            title = clean(item.get('text'))
            context = clean(item.get('parent'))
            candidate = title if MATCH_RE.search(title) and len(title) > 5 else context
            if candidate and MATCH_RE.search(candidate) and len(candidate) < 180:
                rows.append({'title': candidate, 'url': href})
    dedup, out = set(), []
    for r in rows:
        key = (r['title'].lower(), r['url'])
        if key not in dedup:
            dedup.add(key); out.append(r)
    return out[:MAX_MATCH_PAGES]


def inspect_page(page):
    """Find stream URLs explicitly present in page DOM or ordinary visible text."""
    found = set()
    try:
        data = page.locator('a[href], video[src], source[src], iframe[src]').evaluate_all(
            "els => els.map(e => ({url:e.href||e.src||e.getAttribute('src')||e.getAttribute('href')||'', text:(e.innerText||e.getAttribute('aria-label')||'').trim()}))")
        for item in data:
            u = item.get('url', '')
            if u and is_stream(urljoin(page.url, u)):
                found.add(urljoin(page.url, u))
        body = page.locator('body').inner_text(timeout=2500)
        # Only links actually rendered as text, not browser network logs or hidden API traffic.
        for u in STREAM_RE.findall(body):
            if is_stream(u): found.add(u)
    except Exception:
        pass
    return sorted(found)


def main():
    results = []
    playlist = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1365, 'height': 900})
        page = context.new_page()
        print(f'Opening {BASE_URL}')
        try:
            page.goto(BASE_URL, wait_until='domcontentloaded', timeout=TIMEOUT)
            try: page.wait_for_load_state('networkidle', timeout=6000)
            except PlaywrightTimeoutError: pass
            page.wait_for_timeout(int(CFG.get('settle_ms', 2500)))
            expand_listing(page)
            matches = collect_matches(page)
        except Exception as e:
            matches = []
            results.append({'match': '(homepage)', 'match_url': BASE_URL, 'status': 'PAGE_ERROR', 'stream_count': 0, 'streams': '', 'note': str(e)[:300]})
        print(f'Found {len(matches)} possible match pages')
        for i, match in enumerate(matches):
            row = {'match': match['title'], 'match_url': match['url'], 'status': 'NO_PUBLIC_M3U8_IN_DOM', 'stream_count': 0, 'streams': '', 'note': ''}
            if not match['url']:
                row['status'] = 'MATCH_PAGE_NOT_FOUND'
                row['note'] = 'No same-site match URL identified from listing DOM.'
                results.append(row); continue
            try:
                detail = context.new_page()
                detail.goto(match['url'], wait_until='domcontentloaded', timeout=TIMEOUT)
                try: detail.wait_for_load_state('networkidle', timeout=5000)
                except PlaywrightTimeoutError: pass
                detail.wait_for_timeout(1200)
                streams = inspect_page(detail)
                detail.close()
                if streams:
                    row['status'] = 'LINK_FOUND_IN_PAGE_DOM'
                    row['stream_count'] = len(streams)
                    row['streams'] = ' ; '.join(streams)
                    for n, stream in enumerate(streams, 1):
                        playlist[stream] = (match['title'], n)
                else:
                    row['note'] = 'No .m3u/.m3u8 URL exposed in normal page DOM. The bot intentionally does not inspect protected network traffic.'
            except Exception as e:
                row['status'] = 'PAGE_ERROR'
                row['note'] = str(e)[:300]
            results.append(row)
            print(f"[{i+1}/{len(matches)}] {row['status']}: {row['match']}")
        context.close(); browser.close()

    with (ROOT / 'matches.csv').open('w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=['match','match_url','status','stream_count','streams','note'])
        writer.writeheader(); writer.writerows(results)
    (ROOT / 'matches.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    # Include diagnostic comments when no public stream URL is exposed in the DOM.
    lines = [
        '#EXTM3U',
        '# Generated by S8TV DOM checker',
        f'# Match pages discovered: {len(matches)}',
        f'# Public .m3u/.m3u8 URLs found: {len(playlist)}',
    ]
    for url, (title, _) in playlist.items():
        safe_title = clean(title).replace(',', ' ')
        lines.extend([f'#EXTINF:-1 group-title="Bóng đá",{safe_title}', url])
    if not playlist:
        lines.append('# No public stream URL was found in the page DOM. See matches.csv and matches.json for per-match status.')
    (ROOT / 'sport.m3u').write_text('\\n'.join(lines) + '\\n', encoding='utf-8')
    print(f'Wrote {len(playlist)} unique public DOM stream URL(s); discovered {len(matches)} possible match page(s).')
    if not playlist:
        print('WARNING: no playable entries were found. Check matches.csv / matches.json for per-match status.')

if __name__ == '__main__':
    main()
