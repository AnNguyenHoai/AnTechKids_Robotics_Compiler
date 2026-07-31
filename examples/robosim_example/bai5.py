import rcu
import _thread

def robot_initialize():
    """Khởi tạo toàn bộ cấu hình thiết bị"""
    rcu.SetMoveInitialize(1, 2, "left_reversal")
    # Khởi tạo trạng thái ban đầu cho hệ thống đèn và servo
    rcu.SetLightSensorLed(1, 1)    # Bật đèn cảm biến để quét vạch
    rcu.Set3CLed(1, 1)             # Đèn LED màu bật (Màu thứ 1)
    rcu.SetServo(1, 90)            # Đưa Servo 1 về góc trung tâm 90 độ
    rcu.SetSeeringEngine(1, 90)    # Đưa động cơ lái về góc thẳng 90 độ
    print("Hệ thống Đèn và Servo đã được cấu hình tối ưu!")

def task_led_and_hardware_control():
    """Luồng chuyên trách điều khiển Đèn, Còi và các loại Động cơ phụ"""
    print("Luồng 1: Bắt đầu chu kỳ điều khiển thiết bị ngoại vi...")
    
    while True:
        # --- PHẦN 1: TỐI ƯU HÓA ĐIỀU KHIỂN ĐÈN & CÒI (Không để lệnh chạy mù) ---
        rcu.SetLightSensorLed(1, 1)  # Bật đèn LED cảm biến dò line (Trạng thái 1)
        rcu.Set3CLed(1, 1)           # Bật đèn LED màu chế độ 1
        rcu.SetLizard(1)             # Bật còi báo/thiết bị Lizard (Trạng thái 1)
        rcu.SetWaitForTime(0.5)      # BẮT BUỘC: Chờ 0.5 giây để các thiết bị hoạt động
        
        rcu.SetLightSensorLed(1, 0)  # Tắt đèn LED cảm biến để tiết kiệm điện/chuyển chế độ
        rcu.Set3CLed(1, 0)           # Tắt hoặc đổi màu LED 3C (Giả định 0 là tắt hoặc màu khác)
        rcu.SetLizard(0)             # Tắt còi báo Lizard (Nếu không robot sẽ kêu liên tục)
        rcu.SetWaitForTime(0.5)      # Chờ 0.5 giây trước khi vào chu kỳ mới

        # --- PHẦN 2: TỐI ƯU HOÀN THIỆN NHÓM ĐỘNG CƠ / SERVO ---
        # 1. Động cơ DC thông thường (Cổng 1, tốc độ 50)
        rcu.SetMotor(1, 50)          
        rcu.SetWaitForTime(0.5)
        rcu.SetMotor(1, 0)           # Tắt động cơ sau khi chạy xong hành trình
        
        # 2. Động cơ kết hợp Servo (MotorServo) - Cần chạy và chờ hoàn thành góc quét
        rcu.SetMotorServo(1, 50, 45)  # Quay đến góc 45 độ với tốc độ 50
        rcu.SetWaitForTime(1.0)       # Chờ động cơ dịch chuyển đến vị trí 45 độ
        rcu.SetMotorServo(1, 50, 90)  # Quay trở lại góc 90 độ
        rcu.SetWaitForTime(1.0)       # Chờ động cơ trả về vị trí cũ
        
        # 3. Động cơ chạy thẳng theo góc định lượng (Cổng 1, Cổng 2, tốc độ 50, góc 1000)
        rcu.SetMotorStraightAngle(1, 2, 50, 1000)
        rcu.SetWaitForTime(1.5)       # Chờ robot chạy hết số vòng/góc quy định
        
        # 4. Điều khiển Servo góc (Thường dùng cho tay kẹp)
        rcu.SetServo(1, 45)           # Mở tay gắp góc 45 độ
        rcu.SetWaitForTime(0.8)       # Chờ Servo cơ học quay xong
        rcu.SetServo(1, 90)           # Đóng tay gắp góc 90 độ
        rcu.SetWaitForTime(0.8)
        
        # 5. Động cơ góc lái (Steering Engine - Thường dùng cho hệ thống bẻ lái xe ô tô)
        rcu.SetSeeringEngine(1, 60)   # Bẻ lái sang trái góc 60 độ
        rcu.SetWaitForTime(0.5)
        
        # Lệnh tích hợp thời gian: Quay lái góc 90 độ và giữ khóa vị trí trong 1000ms (1 giây)
        rcu.SetSeeringEngineTime(1, 90, 1000)
        rcu.SetWaitForTime(1.2)       # Chờ lệnh định thời của hệ thống chạy xong hoàn toàn

def task_line_tracking():
    """Luồng chuyên trách dò line chạy sa bàn để robot di chuyển liên tục"""
    print("Luồng 2: Hệ thống dò line nâng cao đang quét...")
    
    # Kiểm tra điều kiện cảm biến I2C trước khi cho phép robot chạy tự động
    if rcu.GetTraceV2I2CChxState(1, 1) > 50:
        # Chuỗi di chuyển cơ bản của khung gầm xe (Chassis)
        rcu.SetMoveRunSecond("forward", 50, 1)
        rcu.SetMoveRunAngle("forward", 50, 50)
        rcu.SetMoveSpeed(50, 50)
        rcu.SetMoveRun("forward", 50)
        rcu.SetMoveStop()
        
        # Vòng lặp chạy các thuật toán dò vạch phức hợp tuần tự trên sa bàn
        while True:
            rcu.line_intersection_stop(70, 17)      # Dừng ở ngã tư vuông góc
            rcu.line_millisecond(70, 1000)          # Dò line tính bằng mili-giây
            rcu.line_for_bmp(70, 360)               # Dò line theo bản đồ quét 360
            rcu.line_turn_encounterline(70, 20, 1)  # Rẽ trái khớp vạch
            rcu.line_basis(70)                      # Duy trì bám vạch cơ bản

# ==================== KHỞI CHẠY HỆ THỐNG ĐA LUỒNG ====================
robot_initialize()

# Kích hoạt đồng thời cả 2 luồng để Đèn/Servo phối hợp nhịp nhàng với di chuyển
_thread.start_new_thread(task_led_and_hardware_control, ())
_thread.start_new_thread(task_line_tracking, ())

# Giữ mạch RCU luôn hoạt động
while 1:
    pass
