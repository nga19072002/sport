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
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()

            # Lắng nghe kết nối mạng
            def handle_request(request):
                url = request.url.lower()
                
                # BỘ LỌC CHUẨN XÁC:
                # 1. Phải chứa đuôi .m3u8 (luồng video chính) hoặc chứa từ khóa stream/live
                # 2. KHÔNG lấy các tệp linh tinh như .png, .jpg, .css, .js, .ico, hoặc các đoạn ts quá ngắn
                is_valid_ext = ".m3u8" in url or "playlist" in url or "index" in url
                is_junk = any(ext in url for ext in [".png", ".jpg", ".jpeg", ".css", ".js", ".ico", ".woff", ".json"])
                
                if is_valid_ext and not is_junk:
                    print(f"[Bắt được link chuẩn]: {request.url}")
                    m3u8_links.add(request.url)

            page.on("request", handle_request)

            print(f"Đang truy cập: {TARGET_URL}")
            page.goto(TARGET_URL, timeout=45000, wait_until="domcontentloaded")
            
            # Đợi lâu hơn một chút (15 giây) để trang web load và kích hoạt player video
            page.wait_for_timeout(15000)
            browser.close()
    except Exception as e:
        print(f"Lỗi khi duyệt web: {e}")

    # Xây dựng nội dung file M3U
    m3u_lines = ["#EXTM3U"]
    if m3u8_links:
        print(f"Tìm thấy {len(m3u8_links)} link luồng chính xác!")
        for idx, link in enumerate(sorted(m3u8_links), start=1):
            extinf = f'#EXTINF:-1 tvg-logo="https://s8tv011.com/favicon.ico" group-title="S8TV Live", ⚽ S8TV Match Stream {idx}'
            m3u_lines.append(extinf)
            m3u_lines.append(link)
    else:
        print("Không tìm thấy link .m3u8 hợp lệ nào.")
        m3u_lines.append('#EXTINF:-1 tvg-logo="https://s8tv011.com/favicon.ico" group-title="S8TV Live", ⚽ Stream Pending')
        m3u_lines.append("https://example.com/stream.m3u8")

    # Ghi file sport.m3u
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(m3u_lines) + "\n")

    print(f"Đã cập nhật file {OUTPUT_FILE} thành công!")

if __name__ == "__main__":
    capture_m3u8_links()
