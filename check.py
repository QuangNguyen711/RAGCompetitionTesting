import requests
import time
from datetime import datetime

# ================= CẤU HÌNH =================
SERVER_URL = "http://127.0.0.1:8000"  # IP Server Ban tổ chức
STUDENT_ID = "B21DCCN001"             # Mã sinh viên
NUM_RUNS = 20                         # Số lần test lặp lại

# Cấu hình thời gian chờ (giây) giữa các lần thi 
# Nếu máy sinh viên của bạn phản hồi siêu tốc thì để thấp, còn không thì tăng lên một chút
DELAY_BETWEEN_RUNS = 2 

HEADERS = {"X-Student-ID": STUDENT_ID}

def run_benchmark():
    print(f"=========================================================")
    print(f"📊 BẮT ĐẦU CHẠY BENCHMARK {NUM_RUNS} LƯỢT CHO SINH VIÊN: {STUDENT_ID}")
    print(f"=========================================================\n")

    start_bench_time = time.time()

    for loop in range(1, NUM_RUNS + 1):
        print(f"🔄 [LƯỢT {loop}/{NUM_RUNS}] - Bắt đầu vào lúc: {datetime.now().strftime('%H:%M:%S')}")
        
        # 1. GỌI ROUTE RESET (Xóa dữ liệu, bốc đề ngẫu nhiên mới)
        try:
            print(f"  └─ 🔄 Đang gửi yêu cầu Reset...")
            res_reset = requests.post(
                f"{SERVER_URL}/api/v1/competition/reset",
                headers=HEADERS
            )
            if res_reset.status_code == 200:
                print(f"  └─ ✅ Reset thành công: {res_reset.json().get('message', 'OK')}")
            else:
                print(f"  └─ ❌ Lỗi Reset (Status {res_reset.status_code}): {res_reset.text}")
                print(f"⏭️ Bỏ qua lượt này do không Reset được.")
                continue
        except Exception as e:
            print(f"  └─ ❌ Lỗi kết nối luồng Reset: {e}")
            continue

        # 2. GỌI ROUTE EVALUATE (Kích hoạt máy BTC đẩy 50 câu về máy SV)
        try:
            print(f"  └─ 🚀 Đang kích hoạt luồng Đánh giá (Evaluate)...")
            res_eval = requests.post(
                f"{SERVER_URL}/api/v1/competition/evaluate",
                json={"document_received": True},
                headers=HEADERS
            )
            if res_eval.status_code == 200:
                eval_data = res_eval.json()
                print(f"  └─ 🎯 Hoàn tất lượt {loop}! Kết quả trả về:")
                print(f"     👉 Message: {eval_data.get('message')}")
                print(f"     👉 Điểm quy đổi hệ 10: {eval_data.get('final_score')}/10")
            else:
                print(f"  └─ ❌ Lỗi Evaluate (Status {res_eval.status_code}): {res_eval.text}")
        except Exception as e:
            print(f"  └─ ❌ Lỗi kết nối luồng Evaluate: {e}")

        # 3. NGHỈ GIỮA CÁC ĐỢT (Tránh nghẽn mạng hoặc quá tải local server)
        if loop < NUM_RUNS:
            print(f"💤 Nghỉ {DELAY_BETWEEN_RUNS} giây trước khi sang lượt tiếp theo...\n")
            time.sleep(DELAY_BETWEEN_RUNS)

    total_duration = time.time() - start_bench_time
    print(f"\n=========================================================")
    print(f"🎉 HOÀN THÀNH TOÀN BỘ {NUM_RUNS} LƯỢT BENCHMARK!")
    print(f"⏱️ Tổng thời gian thực thi: {total_duration:.2f} giây")
    print(f"📂 Bạn có thể kiểm tra file 'question_logs.csv' và gọi route GET '/api/v1/competition/question-stats' để phân tích chi tiết!")
    print(f"=========================================================")

if __name__ == "__main__":
    run_benchmark()