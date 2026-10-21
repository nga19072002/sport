import os
import re
import requests

# 1. Các URL nguồn bạn muốn quét link thể thao
TARGET_URLS = [
    "https://khoga.live/",
    "https://90phutzaf.tv/"
]

OUTPUT_FILE = "sport.m3u"

def fetch_and_build_m3u():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    found_links = set()

    # Quét từng trang nguồn
    for url in TARGET_URLS:
        try:
            print(f"Đang cào dữ liệu từ: {url}")
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                # Regex tìm tất cả các đường dẫn kết thúc bằng .m3u hoặc .m3u8
                pattern = r'https?://[^\s<>"]+?\.(?:m3u8?)(?:\?[^\s<>"]*)?'
                matches = re.findall(pattern, response.text, re.IGNORECASE)
                for link in matches:
                    found_links.add(link)
        except Exception as e:
            print(f"Lỗi khi cào {url}: {e}")

    if not found_links:
        print("Không tìm thấy link .m3u / .m3u8 mới nào.")
        return

    print(f"Tìm thấy tổng cộng {len(found_links)} link duy nhất.")

    # Tạo nội dung cho file sport.m3u chuẩn IPTV
    m3u_lines = ["#EXTM3U\n"]
    
    for idx, link in enumerate(sorted(found_links), start=1):
        # Tạo metadata cho từng kênh
        info_line = f'#EXTINF:-1 tvg-id="sport_{idx}" group-title="Sports", Sport Channel {idx}'
        m3u_lines.append(info_line)
        m3u_lines.append(link)

    # Ghi đè lại file sport.m3u mới nhất
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(m3u_lines) + "\n")

    print(f"Đã cập nhật thành công file {OUTPUT_FILE}!")

if __name__ == "__main__":
    fetch_and_build_m3u()
