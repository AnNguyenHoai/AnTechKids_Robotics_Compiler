while True:
    dist = read_ultrasonic()
    if dist < 20:
        stop()
    else:
        set_motor_speed(80, 93)
    wait(100)