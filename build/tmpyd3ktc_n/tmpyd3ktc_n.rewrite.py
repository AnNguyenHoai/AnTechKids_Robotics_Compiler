while True:
    dist = read_ultrasonic()
    if dist < 30:
        stop()
    else:
        set_motor_speed(80, 100)
    wait(100)