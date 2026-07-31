import rcu
import _thread

def robot_initialize():
    """Khởi tạo toàn bộ cấu hình phần cứng"""
    # 1. Khởi tạo hệ thống bánh xe di chuyển (Cổng 1, 2)
    rcu.SetMoveInitialize(1, 2, "left_reversal")
    # 2. Bật đèn cảm biến dò line (Cổng 1, trạng thái 1)
    rcu.SetLightSensorLed(1, 1)
    # 3. Đưa Servo và động cơ góc lái về vị trí xuất phát 90 độ
    rcu.SetServo(1, 90)
    rcu.SetSeeringEngine(1, 90)
    print("Hệ thống tổng hợp đã sẵn sàng!")

def task1():
    """Luồng 1: Chuỗi hành động di chuyển phức hợp định thời"""
    print("Luồng 1 kích hoạt: Thực hiện chuỗi lệnh cấu hình di chuyển...")
    
    # Chạy tiến 1 giây với tốc độ 50
    rcu.SetMoveRunSecond("forward", 50, 1)
    
    # Chạy tiến thêm một khoảng theo góc quay bánh xe 50 độ, tốc độ 50
    rcu.SetMoveRunAngle("forward", 50, 50)
    
    # Cài đặt tốc độ bánh trái và bánh phải lệch nhau để bo cua
    rcu.SetMoveSpeed(50, 50)
    
    # Ra lệnh cho robot chạy tiến liên tục không dừng
    rcu.SetMoveRun("forward", 50)
    
    # Phanh dừng khẩn cấp hệ thống bánh xe
    rcu.SetMoveStop()
    
    # Vòng lặp đếm ngược 10 giây sử dụng hàm đợi của RCU
    for count in range(10):
        rcu.SetWaitForTime(1)
        print("Đang chờ luồng 2 xử lý... Giây thứ:", count + 1)

def task2():
    """Luồng 2: Quét cảm biến, điều khiển cơ cấu phụ và chuỗi thuật toán dò line nâng cao"""
    print("Luồng 2 kích hoạt: Đang kiểm tra điều kiện cảm biến I2C...")
    
    # Kiểm tra trạng thái mắt đọc số 1 của cảm biến line I2C tại cổng 1
    if rcu.GetTraceV2I2CChxState(1, 1) > 50:
        print("Điều kiện thỏa mãn! Bắt đầu chuỗi lệnh điều khiển ngoại vi và dò line...")
        
        while True:
            # --- KHỐI ĐIỀU KHIỂN ĐỘNG CƠ VÀ NGOẠI VI VÒNG LẶP ---
            rcu.SetMotor(1, 50)                      # Chạy động cơ DC cổng 1
            rcu.SetMotorServo(1, 50, 90)             # Điều khiển động cơ kết hợp góc xoay
            rcu.SetMotorStraightAngle(1, 2, 50, 1000)# Chạy thẳng theo góc/thời gian định lượng
            rcu.SetServo(1, 90)                      # Quay Servo cổng 1 góc 90 độ
            rcu.SetSeeringEngine(1, 90)              # Quay động cơ lái góc 90 độ
            rcu.SetSeeringEngineTime(1, 90, 1000)    # Quay động cơ lái góc 90 độ giữ trong 1000ms
            
            rcu.SetLightSensorLed(1, 0)              # Tắt đèn cảm biến để tiết kiệm điện/thay đổi chế độ đọc
            rcu.Set3CLed(1, 1)                       # Bật đèn LED màu tín hiệu
            rcu.SetLizard(1)                         # Kích hoạt thiết bị ngoại vi Lizard (Còi/Cảm biến đặc biệt)
            
            # --- CHUỖI THUẬT TOÁN DÒ LINE PHỨC HỢP (Chạy tuần tự trên sa bàn) ---
            # 1. Dò line tốc độ 70 và dừng lại chính xác tại ngã tư vuông góc (Mã lỗi/Loại vạch: 17)
            rcu.line_intersection_stop(70, 17)
            
            # 2. Dò line trong đúng 1000 mili-giây (1 giây) rồi chuyển sang lệnh tiếp theo
            rcu.line_millisecond(70, 1000)
            rcu.line_millisecond(70, 1000) # Lặp lại lệnh thứ hai theo code mẫu của bạn
            
            # 3. Dò line dựa trên thuật toán xử lý ảnh/bản đồ bit (BMP) góc quét 360
            rcu.line_for_bmp(70, 360)
            
            # 4. Xoay xe rẽ hướng tại chỗ với tốc độ 70, góc 20, khớp vào vạch line tiếp theo (Hướng rẽ: 1)
            rcu.line_turn_encounterline(70, 20, 1)
            
            # 5. Duy trì chế độ dò line cơ bản bám vạch liên tục với tốc độ 70
            rcu.line_basis(70)

# ==================== KHỞI CHẠY CHƯƠNG TRÌNH CHÍNH ====================

# Gọi hàm khởi tạo phần cứng ban đầu
robot_initialize()

# Kích hoạt chạy song song hai luồng nhiệm vụ (Sử dụng đúng cấu trúc đa luồng từ code mẫu)
_thread.start_new_thread(task1, ())
_thread.start_new_thread(task2, ())

# Vòng lặp vô hạn giữ cho chip điều khiển RCU luôn hoạt động không bị tắt chương trình
while 1:
    pass
