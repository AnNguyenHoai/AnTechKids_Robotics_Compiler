while True:
    dist = read_ultrasonic()
    if dist > 20:
        set_3c_led(1, 1)
    else:
        set_3c_led(1, 0)
    wait(200)