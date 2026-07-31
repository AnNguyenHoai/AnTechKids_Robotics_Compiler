import rcu
import _thread

def robot_initialize():
    """Hàm khởi tạo cấu hình ban đầu cho robot"""
    # Khởi tạo bánh xe: Bánh trái cổng 1, bánh phải cổng 2, đảo chiều bánh trái
    rcu.SetMoveInitialize(1, 2, "left_reversal")
    # Bật đèn cảm biến dò line ở cổng 1
    rcu.SetLightSensorLed(1, 1) 

def task_timer_actions():
    """Luồng 1: Thực hiện các hành động di chuyển theo thời gian quy định"""
    print("Luồng 1: Bắt đầu chuỗi hành động định thời...")
    
    # Tiến 50% tốc độ trong 1 giây
    rcu.SetMoveRunSecond("forward", 50, 1)
    
    # Tiến theo góc quay bánh xe 360 độ
    rcu.SetMoveRunAngle("forward", 50, 360)
    
    # Chạy vòng lặp nhấp nháy đèn hoặc chờ đợi
    for count in range(5):
        rcu.Set3CLed(1, 1) # Bật LED màu
        rcu.SetWaitForTime(0.5)
        rcu.Set3CLed(1, 0) # Tắt LED màu
        rcu.SetWaitForTime(0.5)

def task_line_tracking():
    """Luồng 2: Liên tục quét cảm biến và chạy dò line bám vạch"""
    print("Luồng 2: Hệ thống dò line đã kích hoạt.")
    
    while True:
        # Đọc giá trị từ mắt đọc cảm biến line (Cổng I2C số 1, mắt số 1)
        # Giả sử giá trị > 50 là vạch đen (hoặc nền trắng tùy cấu hình)
        sensor_value = rcu.GetTraceV2I2CChxState(1, 1)
        
        if sensor_value > 50:
            # Thực hiện thuật toán bám vạch cơ bản với tốc độ 70
            rcu.line_basis(70)
        else:
            # Nếu lệch vạch, tự động chạy bám line theo thời gian ngắn để tìm lại vạch
            rcu.line_millisecond(60, 200)
            
        # Thao tác kiểm tra ngã tư: Nếu gặp vạch cắt ngang thì dừng lại
        # rcu.line_intersection_stop(70, 17)
        
        rcu.SetWaitForTime(0.02) # Tránh nghẽn CPU của RCU

# ==================== CHƯƠNG TRÌNH CHÍNH ====================

# 1. Chạy cấu hình robot
robot_initialize()

# 2. Kích hoạt đa luồng xử lý song song hai nhiệm vụ
_thread.start_new_thread(task_timer_actions, ())
_thread.start_new_thread(task_line_tracking, ())

# 3. Vòng lặp vô hạn giữ chương trình luôn chạy
while 1:
    rcu.SetWaitForTime(1)
