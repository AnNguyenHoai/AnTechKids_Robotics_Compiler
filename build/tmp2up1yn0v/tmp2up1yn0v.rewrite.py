while True:
    dist = read_ultrasonic()
    if dist < 20:
        stop()
    else:
        forward(80)
    wait(100)