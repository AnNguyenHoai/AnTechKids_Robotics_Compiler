while True:
    dist = read_ultrasonic()
    if dist == -1:
        stop()
        set_3c_led(1, 0)
    elif dist < 20:
        stop()
        set_3c_led(1, 0)
    else:
        forward(80)
        set_3c_led(1, 1)
    wait(200)