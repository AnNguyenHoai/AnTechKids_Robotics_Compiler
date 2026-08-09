while True:
    dist = read_ultrasonic()
    if dist < 40:
        stop()
    else:
        forward(100)
    wait(100)