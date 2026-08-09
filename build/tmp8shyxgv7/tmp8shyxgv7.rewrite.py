while True:
    dist = read_ultrasonic()
    if dist < 30:
        stop()
    else:
        set_motor_speed(80, 90)
    wait(100)