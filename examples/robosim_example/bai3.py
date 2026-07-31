import rcu
import _thread

# --- CẤU HÌNH CỔNG VÀ BIẾN ---
SERVO_PORT = 1
SERVO_OPEN = 40
SERVO_CLOSE = 120
ARM_MOTOR_PORT = 3

def robot_initialize():
    """Khởi tạo cấu hình ban đầu"""
    rcu.SetMoveInitialize(1, 2, "left_reversal")
    rcu.SetLightSensorLed(1, 1) # Bật đèn cảm biến dò line
    rcu.SetServo(SERVO_PORT, SERVO_OPEN) # Mở sẵn tay gắp
    rcu.Set3CLed(1, 0) # Tắt đèn LED màu
    print("Hệ thống sa bàn phân loại đã sẵn sàng!")

def gripper_pick():
    """Hành động gắp vật"""
    rcu.SetMoveStop()
    rcu.SetMotorStraightAngle(ARM_MOTOR_PORT, 1, -40, 500) # Hạ tay
    rcu.SetWaitForTime(0.5)
    rcu.SetServo(SERVO_PORT, SERVO_CLOSE) # Kẹp vật
    rcu.SetWaitForTime(0.8)
    rcu.SetMotorStraightAngle(ARM_MOTOR_PORT, 1, 40, 500) # Nâng tay
    rcu.SetWaitForTime(0.5)

def gripper_drop():
    """Hành động thả vật"""
    rcu.SetMoveStop()
    rcu.SetMotorStraightAngle(ARM_MOTOR_PORT, 1, -40, 500) # Hạ tay
    rcu.SetWaitForTime(0.5)
    rcu.SetServo(SERVO_PORT, SERVO_OPEN) # Nhả vật
    rcu.SetWaitForTime(0.8)
    rcu.SetMotorStraightAngle(ARM_MOTOR_PORT, 1, 40, 500) # Thu tay về
    rcu.SetWaitForTime(0.5)

def mission_sorting():
    """Luồng xử lý sa bàn phân loại vật thể"""
    rcu.SetWaitForTime(2)
    
    # --- CHẶNG 1: DÒ LINE ĐẾN TRẠM KIỂM TRA & GẮP VẬT ---
    print("Đang di chuyển đến trạm kiểm tra vật thể...")
    # Robot bám vạch tốc độ 70 đến khi gặp ngã tư nơi đặt vật thể
    rcu.line_intersection_stop(70, 17) 
    
    # Thực hiện gắp vật thể lên trước
    gripper_pick()
    
    # --- CHẶNG 2: ĐỌC CẢM BIẾN ĐỂ PHÂN LOẠI ---
    print("Đang quét kiểm tra thuộc tính vật thể...")
    # Đọc giá trị cảm biến tại cổng 1, mắt số 2 (giả định đây là vị trí đọc màu/vách riêng)
    sensor_check = rcu.GetTraceV2I2CChxState(1, 2)
    
    # Thiết lập điều kiện phân loại (Ví dụ: giá trị > 60 là Vật Loại A, ngược lại là Loại B)
    if sensor_check > 60:
        print("Phát hiện: Vật thể Loại A -> Di chuyển sang khu vực bên TRÁI")
        rcu.Set3CLed(1, 1) # Bật LED màu hiển thị trạng thái A (Ví dụ: Đỏ/Xanh)
        
        # Rẽ trái tại ngã tư để vào làn đường A
        rcu.line_turn_encounterline(70, 20, 1) 
        rcu.SetWaitForTime(0.5)
        
        # Tiếp tục dò line trên làn đường A cho đến ngã tư kết thúc của Thùng A
        rcu.line_intersection_stop(70, 17)
        
        # Thả vật vào Thùng A
        gripper_drop()
        
    else:
        print("Phát hiện: Vật thể Loại B -> Di chuyển sang khu vực bên PHẢI")
        rcu.Set3CLed(1, 2) # Bật LED màu hiển thị trạng thái B
        
        # Rẽ phải tại ngã tư để vào làn đường B
        rcu.line_turn_encounterline(70, 20, 2) 
        rcu.SetWaitForTime(0.5)
        
        # Tiếp tục dò line trên làn đường B cho đến ngã tư kết thúc của Thùng B
        rcu.line_intersection_stop(70, 17)
        
        # Thả vật vào Thùng B
        gripper_drop()

    # --- CHẶNG 3: HOÀN THÀNH ---
    print("Đã phân loại xong! Dừng robot.")
    rcu.SetMoveStop()

# ==================== KHỞI CHẠY CHƯƠNG TRÌNH ====================
robot_initialize()

# Chạy luồng phân loại độc lập
_thread.start_new_thread(mission_sorting, ())

# Vòng lặp duy trì mạch chạy
while 1:
    rcu.SetWaitForTime(1)
