import requests

# ================= CẤU HÌNH =================
SERVER_URL = "http://127.0.0.1:8000"
STUDENT_ID = "B21DCCN629"

HEADERS = {"X-Student-ID": STUDENT_ID}

def trigger_evaluation():
    try:
        print("🚀 Đang gửi yêu cầu Kích hoạt luồng Test đến Server...")
        res_eval = requests.post(
            f"{SERVER_URL}/api/v1/competition/evaluate",
            headers=HEADERS
        )
        print("🎯 Kích hoạt thành công! BTC chuẩn bị gọi vào /upload và /ask của bạn...", res_eval.json())

    except Exception as e:
        print("❌ Lỗi kích hoạt thi:", e)

if __name__ == "__main__":
    trigger_evaluation()