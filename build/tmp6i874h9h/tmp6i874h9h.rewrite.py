stop()
for i in range(3000):
    dist = read_ultrasonic()
    if dist > 0:
        set_3c_led(1, 1)
    elif dist == -1:
        set_3c_led(1, 1)
    else:
        set_3c_led(1, 0)
    wait(200)