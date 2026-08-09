def task1():
    set_motor_speed(80, 100)
    if read_ultrasonic() < 30:
        backward(80)
        wait(3000)
        stop()
task1()