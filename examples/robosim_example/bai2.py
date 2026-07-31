import rcu
import _thread

# --- CẤU HÌNH BIẾN HỆ THỐNG ---
# Giả định góc Servo mở tay gắp là 40 độ, ngậm/gắp vật là 120 độ
SERVO_PORT = 1
SERVO_OPEN = 40
SERVO_CLOSE = 120

# Cổng động cơ cánh tay nâng (nâng lên / hạ xuống)
ARM_MOTOR_PORT = 3

def robot_initialize():
    """Khởi tạo toàn bộ cấu hình robot ban đầu"""
    # Cấu hình bánh xe: Bánh trái cổng 1, bánh phải cổng 2
    rcu.SetMoveInitialize(1, 2, "left_reversal")
    
    # Bật đèn LED cho cảm biến dò line ở cổng 1 để đọc chính xác hơn
    rcu.SetLightSensorLed(1, 1)
    
    # Đưa tay gắp về trạng thái mở sẵn sàng
    rcu.SetServo(SERVO_PORT, SERVO_OPEN)
    print("Robot đã sẵn sàng!")

def gripper_pick():
    """Hành động: Hạ tay -> Gắp vật -> Nâng tay lên"""
    print("Hành động: Đang gắp vật thể...")
    rcu.SetMoveStop() # Dừng di chuyển để gắp chính xác
    
    # 1. Hạ cánh tay xuống (Chạy động cơ cổng 3, tốc độ 40, trong 500ms)
    rcu.SetMotorStraightAngle(ARM_MOTOR_PORT, 1, -40, 500) 
    rcu.SetWaitForTime(0.5)
    
    # 2. Đóng kẹp Servo để giữ vật
    rcu.SetServo(SERVO_PORT, SERVO_CLOSE)
    rcu.SetWaitForTime(0.8)
    
    # 3. Nâng cánh tay lên cao để di chuyển
    rcu.SetMotorStraightAngle(ARM_MOTOR_PORT, 1, 40, 500)
    rcu.SetWaitForTime(0.5)

def gripper_drop():
    """Hành động: Hạ tay -> Thả vật -> Thu tay về"""
    print("Hành động: Đang thả vật thể...")
    rcu.SetMoveStop()
    
    # 1. Hạ cánh tay xuống vị trí thả
    rcu.SetMotorStraightAngle(ARM_MOTOR_PORT, 1, -40, 500)
    rcu.SetWaitForTime(0.5)
    
    # 2. Mở kẹp Servo để nhả vật
    rcu.SetServo(SERVO_PORT, SERVO_OPEN)
    rcu.SetWaitForTime(0.8)
    
    # 3. Thu cánh tay nâng về vị trí ban đầu
    rcu.SetMotorStraightAngle(ARM_MOTOR_PORT, 1, 40, 500)
    rcu.SetWaitForTime(0.5)

def mission_control():
    """Luồng điều khiển chính: Chạy sa bàn, xử lý ngã tư và gắp thả"""
    rcu.SetWaitForTime(2) # Chờ 2 giây trước khi xuất phát
    
    # --- CHẶNG 1: Dò line tiến đến ngã tư thứ nhất để RẼ TRÁI ---
    print("Chặng 1: Bắt đầu dò line tìm ngã tư 1...")
    # Robot dò line bám vạch liên tục với tốc độ 70 cho đến khi chạm vạch cắt ngang (Ngã tư)
    rcu.line_intersection_stop(70, 17) 
    
    print("Gặp ngã tư 1: Thực hiện rẽ TRÁI")
    # Quét quay trái tốc độ 70, gặp vạch line kế tiếp thì khớp (Tham số cuối: 1=Trái, 2=Phải tùy thiết lập firmware)
    rcu.line_turn_encounterline(70, 20, 1) 
    rcu.SetWaitForTime(0.5)

    # --- CHẶNG 2: Đi tiếp đến ngã tư thứ hai để GẮP VẬT ---
    print("Chặng 2: Tiến đến vị trí vật thể...")
    rcu.line_intersection_stop(70, 17)
    
    # Gọi hàm gắp vật đã lập trình phía trên
    gripper_pick()

    # --- CHẶNG 3: Quay đầu hoặc rẽ phải để mang vật về đích ---
    print("Chặng 3: Rẽ PHẢI để mang vật về vùng thả...")
    # Di chuyển nhích qua ngã tư một chút nếu cần, hoặc xoay hướng phải
    rcu.line_turn_encounterline(70, 20, 2)
    rcu.SetWaitForTime(0.5)
    
    # Dò line chặng cuối đến ngã tư kết thúc
    rcu.line_intersection_stop(70, 17)
    
    # Thả vật vào kho / vùng đích
    gripper_drop()
    
    # Kết thúc nhiệm vụ, dừng toàn bộ động cơ
    print("Nhiệm vụ hoàn thành!")
    rcu.Set3CLed(1, 1) # Bật LED xanh báo hiệu chiến thắng
    rcu.SetMoveStop()

# ==================== KHỞI CHẠY CHƯƠNG TRÌNH ====================
robot_initialize()

# Chạy luồng nhiệm vụ độc lập
_thread.start_new_thread(mission_control, ())

# Vòng lặp vô hạn duy trì mạch RCU luôn thức
while 1:
    rcu.SetWaitForTime(1)
