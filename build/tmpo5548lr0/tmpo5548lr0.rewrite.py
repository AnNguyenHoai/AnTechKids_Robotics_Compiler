while True:
    dist = read_ultrasonic()
    if dist > 20:
        stop()
        set_3c_led(1, 0)
    elif dist > 0:
        forward(80)
        set_3c_led(1, 1)
    else:
        stop()
        set_3c_led(1, 0)
    wait(200)