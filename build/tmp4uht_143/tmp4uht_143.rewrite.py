while True:
    dist = read_ultrasonic()
    if dist < 10:
        set_3c_led(1, 1)
        forward(0)
    else:
        forward(80)
        set_3c_led(1, 0)
    wait(100)