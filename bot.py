import os
import requests

# Điền URL nguồn M3U thực tế của bạn vào đây
TARGET_URLS = [
    "https://s8tv011.com/", 
]

OUTPUT_FILE = "sport.m3u"

def fetch_and_build_sport_playlist():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    valid_entries = []

    for url in TARGET_URLS:
        try:
            print(f"Đang kết nối tới: {url}")
            response = requests.get(url, headers=headers, timeout=20)
            print(f"Mã phản hồi từ server (Status code): {response.status_code}")
            
            if response.status_code == 200:
                content = response.text
                lines = content.splitlines()
                print(f"Tổng số dòng đọc được từ nguồn: {len(lines)}")
                
                # Quét file theo từng cặp dòng: #EXTINF và Link ngay bên dưới
                i = 0
                while i < len(lines) - 1:
                    line = lines[i].strip()
                    if line.startswith("#EXTINF:"):
                        extinf_line = line
                        next_line = lines[i+1].strip()
                        
                        # Kiểm tra dòng tiếp theo có phải link http không
                        if next_line.startswith("http") and not next_line.startswith("#"):
                            # Tạm thời LẤY TẤT CẢ các link tìm thấy trước để kiểm tra (bỏ qua bước lọc rác tạm thời)
                            valid_entries.append((extinf_line, next_line))
                            i += 2
                            continue
                    i += 1
            else:
                print(f"Lỗi: Không truy cập được trang, mã lỗi {response.status_code}")
        except Exception as e:
            print(f"Đã xảy ra lỗi ngoại lệ: {e}")

    # Xây dựng nội dung file sport.m3u
    m3u_lines = ["#EXTM3U"]

    if valid_entries:
        print(f"Thành công! Đã gom được {len(valid_entries)} luồng.")
        for extinf, link in valid_entries:
            m3u_lines.append(extinf)
            m3u_lines.append(link)
    else:
        print("CẢNH BÁO: Không tìm thấy luồng hợp lệ nào!")

    # Ghi ra file sport.m3u
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(m3u_lines) + "\n")

    print(f"Đã cập nhật file {OUTPUT_FILE} xong!")

if __name__ == "__main__":
    fetch_and_build_sport_playlist()
