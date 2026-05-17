import requests

# ================= CẤU HÌNH =================
SERVER_URL = "http://127.0.0.1:8000"
STUDENT_ID = "B21DCCN629"
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
        
        # 2. Reset (Phòng trường hợp đang code giữa chừng bị lỗi chạy lại chặn mất điểm)
        print("Đang gửi yêu cầu Reset...")
        res_reset = requests.post(
            f"{SERVER_URL}/api/v1/competition/reset",
            headers=HEADERS
        )
        print("🔄 Đã tự động Reset trạng thái thi trên Server:", res_reset.json())

    except Exception as e:
        print("❌ Lỗi luồng Đăng ký/Reset:", e)

if __name__ == "__main__":
    register_server()