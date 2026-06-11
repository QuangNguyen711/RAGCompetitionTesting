import requests

# ================= CẤU HÌNH =================
SERVER_URL = "http://127.0.0.1:8000"  # IP Server Ban tổ chức
STUDENT_ID = "B21DCCN001"             # Mã sinh viên
LOCAL_PORT = 3636
LOCAL_URL = f"http://127.0.0.1:{LOCAL_PORT}"

HEADERS = {"X-Student-ID": STUDENT_ID}

def reset_server():
    try:
        # Reset (Phòng trường hợp đang code giữa chừng bị lỗi chạy lại chặn mất điểm)
        print("Đang gửi yêu cầu Reset...")
        res_reset = requests.post(
            f"{SERVER_URL}/api/v1/competition/reset",
            headers=HEADERS
        )
        print("🔄 Đã tự động Reset trạng thái thi trên Server:", res_reset.json())

    except Exception as e:
        print("❌ Lỗi luồng Reset:", e)

if __name__ == "__main__":
    reset_server()