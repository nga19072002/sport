import os
import re
import requests

TARGET_URLS = [
    "https://s8tv011.com/",
    
]

OUTPUT_FILE = "sport.m3u"

# Các từ khóa ưu tiên bắt link trận đấu bóng đá / thể thao
FOOTBALL_KEYWORDS = [
    "vs", "live", "bongda", "football", "soccer", "tructiep", 
    "tran", "cup", "league", "premier", "champions", "laliga", "m3u8"
]

EXCLUDE_KEYWORDS = [
    "ads", "banner", "promo", "trailer", "highlight", "news"
]

def fetch_and_build_sport_playlist():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://s8tv011.com/"
    }

    m3u_entries = []
    found_urls = set()

    for url in TARGET_URLS:
        try:
            print(f"Đang kết nối tới: {url}")
            response = requests.get(url, headers=headers, timeout=20)
            print(f"Mã phản hồi từ server (Status code): {response.status_code}")
            
            if response.status_code == 200:
                html_content = response.text
                
                # 1. Tìm tất cả các link m3u8 / stream trực tiếp xuất hiện trong trang S8TV
                stream_pattern = r'https?://[^\s<>"\']+\.m3u8(?:\?[^\s<>"\']*)?'
                streams = re.findall(stream_pattern, html_content, re.IGNORECASE)
                
                # 2. Bắt các thông tin trận đấu (Tên trận, giải đấu) từ HTML
                # Bắt mẫu tên trận đấu dạng "Đội A vs Đội B"
                match_titles = re.findall(r'([A-Za-z0-9\s]+?\s+vs\s+[A-Za-z0-9\s]+)', html_content, re.IGNORECASE)
                
                print(f"Tìm thấy {len(streams)} đường dẫn stream .m3u8!")
                
                for idx, stream_url in enumerate(streams, start=1):
                    if stream_url in found_urls:
                        continue
                    
                    # Kiểm tra loại bỏ link quảng cáo rác
                    if any(bad in stream_url.lower() for bad in EXCLUDE_KEYWORDS):
                        continue

                    found_urls.add(stream_url)

                    # Lấy tên trận đấu nếu quét được, hoặc đặt tên mặc định
                    title = match_titles[idx-1].strip() if idx <= len(match_titles) else f"S8TV Match Stream {idx}"
                    
                    # Tạo cấu trúc #EXTINF chuẩn đẹp có Logo S8TV
                    extinf = f'#EXTINF:-1 tvg-logo="https://s8tv011.com/favicon.ico" group-title="S8TV Sports", ⚽ {title}'
                    m3u_entries.append((extinf, stream_url))
            else:
                print(f"Lỗi: Không truy cập được trang, mã lỗi {response.status_code}")

        except Exception as e:
            print(f"Đã xảy ra lỗi khi cào dữ liệu: {e}")

    # Tạo nội dung danh sách M3U
    m3u_lines = ["#EXTM3U"]

    if m3u_entries:
        print(f"Thành công! Đã tạo được {len(m3u_entries)} luồng phát M3U.")
        for extinf, link in m3u_entries:
            m3u_lines.append(extinf)
            m3u_lines.append(link)
    else:
        print("CẢNH BÁO: Không tìm thấy link luồng .m3u8 trực tiếp nào trên trang web HTML.")

    # Ghi ra file sport.m3u
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(m3u_lines) + "\n")

    print(f"Đã cập nhật file {OUTPUT_FILE} xong!")

if __name__ == "__main__":
    fetch_and_build_sport_playlist()
