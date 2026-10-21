import os
import requests

# Thay đường dẫn này bằng API hoặc trang JSON thực tế của s8tv (nếu bạn bắt được qua F12 -> Network)
TARGET_API_URLS = [
    "https://s8tv011.com/api/matches", # Ví dụ đường dẫn API (cần thay đổi theo API thực tế của web)
]

OUTPUT_FILE = "sport.m3u"

def fetch_from_api():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://s8tv011.com/"
    }

    all_blocks = []

    for url in TARGET_API_URLS:
        try:
            print(f"Đang gọi API: {url}")
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json() # Giả định API trả về dạng JSON chứa danh sách trận
                
                # Duyệt qua danh sách trận đấu trong JSON (cấu trúc tùy thuộc vào API cụ thể của web)
                # Ví dụ mẫu giả định:
                # for match in data.get("matches", []):
                #     title = match.get("title")
                #     stream_link = match.get("stream_url")
                #     logo = match.get("logo")
                
                #     extinf = f'#EXTINF:-1 tvg-logo="{logo}" group-title="S8TV Live", {title}'
                #     all_blocks.append([extinf, stream_link])
                
                pass
            else:
                print(f"Lỗi API, mã phản hồi: {response.status_code}")
        except Exception as e:
            print(f"Lỗi khi gọi API: {e}")

    # Ghi ra file sport.m3u
    m3u_lines = ["#EXTM3U"]
    if all_blocks:
        for block in all_blocks:
            m3u_lines.extend(block)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(m3u_lines) + "\n")

    print(f"Đã cập nhật xong file {OUTPUT_FILE}!")

if __name__ == "__main__":
    fetch_from_api()
