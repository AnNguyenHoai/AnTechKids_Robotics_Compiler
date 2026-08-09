def task1():
    turn_right(45)
    wait(500)
    stop()
    set_motor_speed(50, 50)
    if read_ultrasonic() < 30:
        turn_left(50)
        wait(500)
        stop()
        forward(50)
        wait(1000)
        stop()
task1()