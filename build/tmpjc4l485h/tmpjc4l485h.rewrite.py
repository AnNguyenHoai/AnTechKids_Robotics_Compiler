obstacle = False
invalid_count = 0
while True:
    dist = read_ultrasonic()
    if dist < 0:
        invalid_count += 1
        if invalid_count >= 5:
            obstacle = True
    else:
        invalid_count = 0
        if dist < 20:
            obstacle = True
        else:
            obstacle = False
    if obstacle:
        set_3c_led(1, 1)
        stop()
    else:
        forward(80)
        set_3c_led(1, 0)
    wait(100)