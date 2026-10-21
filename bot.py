import os
import re
from playwright.sync_api import sync_playwright

OUTPUT_FILE = "sport.m3u"
TARGET_URL = "https://s8tv011.com/"

def capture_m3u8_links():
    m3u8_links = set()

    print("Đang khởi tạo trình duyệt Playwright...")
    try:
        with sync_playwright() as p:
            # Khởi chạy Chromium headless
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()

            # Lắng nghe kết nối mạng tìm file .m3u8 hoặc .ts
            def handle_request(request):
                url = request.url
                if ".m3u8" in url or ".ts" in url:
                    print(f"[Bắt được link]: {url}")
                    m3u8_links.add(url)

            page.on("request", handle_request)

            print(f"Đang truy cập: {TARGET_URL}")
            page.goto(TARGET_URL, timeout=45000, wait_until="domcontentloaded")
            page.wait_for_timeout(8000) # Đợi 8s cho JS/Video load
            browser.close()
    except Exception as e:
        print(f"Cảnh báo trong quá trình duyệt web: {e}")

    # Xây dựng nội dung file M3U
    m3u_lines = ["#EXTM3U"]
    if m3u8_links:
        print(f"Tìm thấy {len(m3u8_links)} link stream!")
        for idx, link in enumerate(sorted(m3u8_links), start=1):
            extinf = f'#EXTINF:-1 tvg-logo="https://s8tv011.com/favicon.ico" group-title="S8TV Live", ⚽ S8TV Match {idx}'
            m3u_lines.append(extinf)
            m3u_lines.append(link)
    else:
        print("Không tìm thấy link .m3u8 nào, ghi dữ liệu giữ chân file...")
        m3u_lines.append('#EXTINF:-1 tvg-logo="https://s8tv011.com/favicon.ico" group-title="S8TV Live", ⚽ S8TV Stream Pending')
        m3u_lines.append("https://example.com/stream.m3u8")

    # BẮT BUỘC GHI FILE
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(m3u_lines) + "\n")

    print(f"Đã ghi thành công file {OUTPUT_FILE}!")

if __name__ == "__main__":
    capture_m3u8_links()
