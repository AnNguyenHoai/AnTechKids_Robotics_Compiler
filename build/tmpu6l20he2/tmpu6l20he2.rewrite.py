while True:
    dist = read_ultrasonic()
    if dist < 20:
        set_3c_led(1, 1)
        stop()
    else:
        set_3c_led(1, 0)
        forward(80)
    wait(200)