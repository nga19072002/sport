import os
import re
import requests

# Thay thế bằng trang web hoặc API nguồn cung cấp định dạng m3u chuẩn của bạn
TARGET_URLS = [
    "https://s8tv011.com/",
    "https://biaomtv22.com/"
]

OUTPUT_FILE = "sport.m3u"

# Từ khóa ưu tiên hoặc bộ lọc bóng đá/thể thao
FOOTBALL_KEYWORDS = [
    "vs", "live", "bongda", "football", "soccer", "tructiep", 
    "tran", "cup", "league", "premier", "champions", "laliga"
]

EXCLUDE_KEYWORDS = [
    "ads", "advert", "banner", "promo", "trailer", "highlight"
]

def is_valid_match(extinf_line):
    """Kiểm tra xem dòng thông tin trận đấu có hợp lệ và không phải quảng cáo"""
    text = extinf_line.lower()
    
    # Nếu chứa từ khóa rác/quảng cáo -> Loại
    for bad in EXCLUDE_KEYWORDS:
        if bad in text:
            return False
            
    # Nếu chứa từ khóa trận đấu (ví dụ có chữ 'vs') -> Nhận
    for good in FOOTBALL_KEYWORDS:
        if good in text:
            return True
            
    return False

def fetch_and_build_sport_playlist():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    valid_entries = [] # Lưu các cặp (EXTINF, Link) hợp lệ

    for url in TARGET_URLS:
        try:
            print(f"Đang quét nguồn: {url}")
            response = requests.get(url, headers=headers, timeout=20)
            if response.status_code == 200:
                content = response.text
                lines = content.splitlines()
                
                # Quét file theo từng cặp dòng: #EXTINF và Link ngay bên dưới
                i = 0
                while i < len(lines) - 1:
                    line = lines[i].strip()
                    if line.startswith("#EXTINF:"):
                        extinf_line = line
                        next_line = lines[i+1].strip()
                        
                        # Kiểm tra xem dòng tiếp theo có phải là link stream m3u8/ts/mp4 không
                        if next_line.startswith("http") and not next_line.startswith("#"):
                            # Lọc xem có phải trận đấu thật không
                            if is_valid_match(extinf_line):
                                valid_entries.append((extinf_line, next_line))
                            i += 2
                            continue
                    i += 1
        except Exception as e:
            print(f"Lỗi khi xử lý {url}: {e}")

    # Xây dựng nội dung file sport.m3u chuẩn
    m3u_lines = ["#EXTM3U"]

    if valid_entries:
        print(f"Lọc thành công {len(valid_entries)} trận đấu thể thao thực tế.")
        for extinf, link in valid_entries:
            m3u_lines.append(extinf)
            m3u_lines.append(link)
    else:
        print("Không tìm thấy trận đấu nào phù hợp sau khi lọc.")

    # Ghi ra file sport.m3u
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(m3u_lines) + "\n")

    print(f"Đã cập nhật file {OUTPUT_FILE} thành công!")

if __name__ == "__main__":
    fetch_and_build_sport_playlist()
