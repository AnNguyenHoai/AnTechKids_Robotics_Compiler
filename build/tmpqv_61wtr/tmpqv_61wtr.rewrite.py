def robot_initialize():
    """Khởi tạo toàn bộ cấu hình thiết bị"""
    set_move_initialize(1, 2, 'left_reversal')
    set_light_sensor_led(1, 1)
    set_3c_led(1, 1)
    set_servo(1, 90)
    set_seering_engine(1, 90)
    print('Hệ thống Đèn và Servo đã được cấu hình tối ưu!')

def task_led_and_hardware_control():
    """Luồng chuyên trách điều khiển Đèn, Còi và các loại Động cơ phụ"""
    print('Luồng 1: Bắt đầu chu kỳ điều khiển thiết bị ngoại vi...')
    while True:
        set_light_sensor_led(1, 1)
        set_3c_led(1, 1)
        set_lizard(1)
        wait(500)
        set_light_sensor_led(1, 0)
        set_3c_led(1, 0)
        set_lizard(0)
        wait(500)
        set_motor(1, 50)
        wait(500)
        set_motor(1, 0)
        set_motor_servo(1, 50, 45)
        wait(1000)
        set_motor_servo(1, 50, 90)
        wait(1000)
        set_motor_straight_angle(1, 2, 50, 1000)
        wait(1500)
        set_servo(1, 45)
        wait(800)
        set_servo(1, 90)
        wait(800)
        set_seering_engine(1, 60)
        wait(500)
        set_seering_engine_time(1, 90, 1000)
        wait(1200)

def task_line_tracking():
    """Luồng chuyên trách dò line chạy sa bàn để robot di chuyển liên tục"""
    print('Luồng 2: Hệ thống dò line nâng cao đang quét...')
    if read_line(1) > 50:
        forward(50)
        wait(1000)
        stop()
        set_move_run_angle('forward', 50, 50)
        set_motor_speed(50, 50)
        forward(50)
        stop()
        while True:
            line_intersection_stop(70, 17)
            line_millisecond(70, 1000)
            line_for_bmp(70, 360)
            line_turn_encounterline(70, 20, 1)
            line_basis(70)
robot_initialize()
task_led_and_hardware_control()
task_line_tracking()
while 1:
    pass