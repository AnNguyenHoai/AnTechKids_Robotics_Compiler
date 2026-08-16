while True:
    dist = read_ultrasonic()
    if dist < 20:
        set_3c_led(1, 0)
        stop()
    else:
        forward(50)
    wait(100)