import os
import re
import requests

TARGET_URLS = [
    "https://s8tv011.com/",
    # Bạn có thể thêm các trang web khác vào đây
]

OUTPUT_FILE = "sport.m3u"

def fetch_and_build_sport_playlist():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }

    all_playlist_blocks = []
    found_streams = set()

    for url in TARGET_URLS:
        try:
            print(f"Đang kết nối tới: {url}")
            response = requests.get(url, headers=headers, timeout=20)
            
            if response.status_code == 200:
                content = response.text
                lines = content.splitlines()
                
                # Quét qua nội dung file nguồn để gom nhóm các dòng thuộc về một trận đấu
                i = 0
                while i < len(lines):
                    line = lines[i].strip()
                    
                    # Nếu tìm thấy dòng bắt đầu bằng #EXTINF
                    if line.startswith("#EXTINF:"):
                        extinf_line = line
                        opt_vlccopt = ""
                        opt_exthttp = ""
                        stream_link = ""
                        
                        # Kiểm tra các dòng kế tiếp xem có chứa các thẻ phụ hay link stream không
                        j = i + 1
                        while j < len(lines) and not lines[j].strip().startswith("#EXTINF:"):
                            sub_line = lines[j].strip()
                            if sub_line.startswith("#EXTVLCOPT:"):
                                opt_vlccopt = sub_line
                            elif sub_line.startswith("#EXTHTTP:"):
                                opt_exthttp = sub_line
                            elif sub_line.startswith("http") and not sub_line.startswith("#"):
                                stream_link = sub_line
                                break
                            j += 1
                        
                        # Nếu bắt được link stream hợp lệ và chưa bị trùng
                        if stream_link and stream_link not in found_streams:
                            found_streams.add(stream_link)
                            
                            # Gom nhóm đầy đủ các dòng cấu trúc lại
                            block = [extinf_line]
                            if opt_vlccopt:
                                block.append(opt_vlccopt)
                            if opt_exthttp:
                                block.append(opt_exthttp)
                            block.append(stream_link)
                            
                            all_playlist_blocks.append(block)
                            
                        # Nhảy cóc qua các dòng đã xử lý
                        i = j
                    else:
                        i += 1
            else:
                print(f"Lỗi: Không truy cập được trang, mã lỗi {response.status_code}")
        except Exception as e:
            print(f"Lỗi khi cào dữ liệu từ {url}: {e}")

    # Xây dựng nội dung file sport.m3u hoàn chỉnh
    m3u_lines = ["#EXTM3U"]

    if all_playlist_blocks:
        print(f"Thành công! Đã giữ lại đầy đủ thông tin cho {len(all_playlist_blocks)} trận đấu.")
        for block in all_playlist_blocks:
            m3u_lines.extend(block)
    else:
        print("CẢNH BÁO: Không tìm thấy định dạng luồng hợp lệ nào từ nguồn.")

    # Ghi ra file sport.m3u
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(m3u_lines) + "\n")

    print(f"Đã cập nhật xong file {OUTPUT_FILE}!")

if __name__ == "__main__":
    fetch_and_build_sport_playlist()
