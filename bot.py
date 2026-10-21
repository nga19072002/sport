import html
import json
import re
from urllib.parse import urljoin, urlparse

import requests

# Chỉ dùng với trang/luồng mà bạn có quyền truy cập và phát lại.
TARGET_URLS = [
    "https://s8tv011.com/",
    "https://biaomtv22.com/",
]

OUTPUT_FILE = "sport.m3u"
TIMEOUT = 20
MAX_PAGES_PER_TARGET = 8

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/json,text/plain,*/*",
}

# Bắt URL m3u/m3u8 trong HTML, JSON và JavaScript, kể cả URL có query string.
STREAM_RE = re.compile(
    r"(?:https?:)?//[^\s\"'<>\\]+?\.m3u8?(?:\?[^\s\"'<>\\]*)?"
    r"|(?:/[^\s\"'<>\\]+?\.m3u8?(?:\?[^\s\"'<>\\]*)?)",
    re.IGNORECASE,
)
IFRAME_RE = re.compile(
    r"<iframe\b[^>]*?\bsrc\s*=\s*['\"]([^'\"]+)['\"]",
    re.IGNORECASE,
)
TITLE_RE = re.compile(
    r"([\wÀ-ỹ .'-]{2,70}\s+(?:vs\.?|v\.?|–|—)\s+[\wÀ-ỹ .'-]{2,70})",
    re.IGNORECASE,
)
EXCLUDE_TERMS = ("advert", "banner", "promo", "trailer", "highlight", "analytics")


def normalize_text(text: str) -> str:
    """Chuẩn hóa các URL bị escape trong JavaScript/JSON."""
    text = html.unescape(text)
    text = text.replace(r"\/", "/").replace(r"\u0026", "&")
    text = text.replace(r"\u003A", ":").replace(r"\u003a", ":")
    return text


def fetch_text(session: requests.Session, url: str):
    try:
        response = session.get(url, timeout=TIMEOUT, allow_redirects=True)
        print(f"[{response.status_code}] {response.url}")
        if response.status_code != 200:
            return None, response.url
        return normalize_text(response.text), response.url
    except requests.RequestException as exc:
        print(f"Không tải được {url}: {exc}")
        return None, url


def extract_streams(text: str, page_url: str):
    results = []
    for raw_url in STREAM_RE.findall(text):
        raw_url = raw_url.rstrip("),;]")
        if raw_url.startswith("//"):
            raw_url = "https:" + raw_url
        absolute = urljoin(page_url, raw_url)
        parsed = urlparse(absolute)
        if parsed.scheme not in ("http", "https"):
            continue
        if any(term in absolute.lower() for term in EXCLUDE_TERMS):
            continue
        results.append(absolute)
    return results


def extract_title(text: str, fallback: str):
    # Tìm tên trận trong phần văn bản gần URL nếu có; không ghép theo chỉ số mảng.
    match = TITLE_RE.search(text)
    if match:
        return " ".join(match.group(1).split())[:100]
    return fallback


def collect_from_page(session: requests.Session, start_url: str):
    queue = [start_url]
    visited = set()
    found = []
    base_host = urlparse(start_url).netloc.lower()

    while queue and len(visited) < MAX_PAGES_PER_TARGET:
        page_url = queue.pop(0)
        if page_url in visited:
            continue
        visited.add(page_url)
        print(f"Đang kiểm tra: {page_url}")
        content, final_url = fetch_text(session, page_url)
        if not content:
            continue

        streams = extract_streams(content, final_url)
        title = extract_title(content, f"Sports stream {len(found) + 1}")
        for stream in streams:
            found.append((title, stream, final_url))

        # Theo các iframe cùng website để kiểm tra trang nhúng công khai.
        # Không chạy JavaScript và không vượt sang domain khác.
        for iframe_src in IFRAME_RE.findall(content):
            iframe_url = urljoin(final_url, html.unescape(iframe_src.strip()))
            if urlparse(iframe_url).netloc.lower() == base_host and iframe_url not in visited:
                queue.append(iframe_url)

    return found


def build_playlist():
    session = requests.Session()
    session.headers.update(HEADERS)
    unique_streams = {}

    for target in TARGET_URLS:
        print(f"\n=== Nguồn: {target} ===")
        for title, stream_url, source_page in collect_from_page(session, target):
            if stream_url not in unique_streams:
                unique_streams[stream_url] = (title, source_page)

    lines = ["#EXTM3U"]
    for index, (stream_url, (title, source_page)) in enumerate(unique_streams.items(), 1):
        # Làm sạch ký tự có thể phá định dạng EXTINF.
        title = re.sub(r"[\r\n,]", " ", title).strip() or f"Sports stream {index}"
        group = "Sports"
        lines.append(f'#EXTINF:-1 group-title="{group}",{title}')
        lines.append(stream_url)

    with open(OUTPUT_FILE, "w", encoding="utf-8", newline="\n") as output:
        output.write("\n".join(lines) + "\n")

    print(f"\nĐã ghi {len(unique_streams)} link vào {OUTPUT_FILE}.")
    if not unique_streams:
        print(
            "Không thấy URL .m3u/.m3u8 trong HTML/JSON/iframe tĩnh. "
            "Nếu trang tạo link bằng JavaScript hoặc API sau khi tải, cần xác định "
            "API công khai/được phép đó; regex không thể tự lấy dữ liệu chưa có trong HTML."
        )


if __name__ == "__main__":
    build_playlist()
