import requests

# ================= CẤU HÌNH =================
SERVER_URL = "http://127.0.0.1:8000"  # IP Server Ban tổ chức
STUDENT_ID = "B21DCCN001"             # Mã sinh viên
LOCAL_PORT = 3636
LOCAL_URL = f"http://127.0.0.1:{LOCAL_PORT}"

HEADERS = {"X-Student-ID": STUDENT_ID}

def register_server():
    try:
        # 1. Đăng ký URL
        print("Đang gửi yêu cầu đăng ký URL...")
        res = requests.post(
            f"{SERVER_URL}/api/v1/competition/register",
            json={"server_url": LOCAL_URL},
            headers=HEADERS
        )
        print("\n✅ Đã đăng ký Server URL thành công:", res.json())

    except Exception as e:
        print("❌ Lỗi luồng Đăng ký:", e)

if __name__ == "__main__":
    register_server()