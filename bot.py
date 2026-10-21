import os
import re
from playwright.sync_api import sync_playwright

OUTPUT_FILE = "sport.m3u"
TARGET_URL = "https://s8tv011.com/"

def capture_m3u8_links():
    m3u8_links = set()

    with sync_playwright() as p:
        # Khởi chạy trình duyệt Chromium ẩn
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        # Lắng nghe tất cả các kết nối mạng mà trang web gửi ra
        def handle_request(request):
            url = request.url
            if ".m3u8" in url or ".ts" in url:
                print(f"Bắt được link stream: {url}")
                m3u8_links.add(url)

        page.on("request", handle_request)

        try:
            print(f"Đang mở trang web: {TARGET_URL}")
            page.goto(TARGET_URL, timeout=60000, wait_until="networkidle")
            page.wait_for_timeout(10000) # Đợi 10 giây để video/JS tải xong
        except Exception as e:
            print(f"Lỗi khi tải trang: {e}")
        finally:
            browser.close()

    # Tạo nội dung M3U
    m3u_lines = ["#EXTM3U"]
    if m3u8_links:
        for idx, link in enumerate(sorted(m3u8_links), start=1):
            extinf = f'#EXTINF:-1 tvg-logo="https://s8tv011.com/favicon.ico" group-title="S8TV Live", ⚽ S8TV Match {idx}'
            m3u_lines.append(extinf)
            m3u_lines.append(link)
    else:
        print("Không bắt được link .m3u8 nào qua mạng.")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(m3u_lines) + "\n")

    print(f"Đã cập nhật file {OUTPUT_FILE}!")

if __name__ == "__main__":
    capture_m3u8_links()
