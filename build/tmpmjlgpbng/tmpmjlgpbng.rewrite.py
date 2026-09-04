while True:
    dist = read_ultrasonic()
    if dist > 20:
        stop()
        set_3c_led(1, 0)
    else:
        forward(20)
        set_3c_led(1, 1)
    wait(200)