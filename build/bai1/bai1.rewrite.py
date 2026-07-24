import _thread

def robot_initialize():
    """Hàm khởi tạo cấu hình ban đầu cho robot"""
    rcu.SetMoveInitialize(1, 2, 'left_reversal')
    rcu.SetLightSensorLed(1, 1)

def task_timer_actions():
    """Luồng 1: Thực hiện các hành động di chuyển theo thời gian quy định"""
    print('Luồng 1: Bắt đầu chuỗi hành động định thời...')
    forward(50)
    wait(1000)
    stop()
    rcu.SetMoveRunAngle('forward', 50, 360)
    for count in range(5):
        rcu.Set3CLed(1, 1)
        wait(0.5)
        rcu.Set3CLed(1, 0)
        wait(0.5)

def task_line_tracking():
    """Luồng 2: Liên tục quét cảm biến và chạy dò line bám vạch"""
    print('Luồng 2: Hệ thống dò line đã kích hoạt.')
    while True:
        sensor_value = rcu.GetTraceV2I2CChxState(1, 1)
        if sensor_value > 50:
            rcu.line_basis(70)
        else:
            rcu.line_millisecond(60, 200)
        wait(0.02)
robot_initialize()
_thread.start_new_thread(task_timer_actions, ())
_thread.start_new_thread(task_line_tracking, ())
while 1:
    wait(1)