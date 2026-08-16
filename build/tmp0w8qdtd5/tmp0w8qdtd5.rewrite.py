while True:
    dist = read_ultrasonic()
    if dist < 30:
        stop()
    else:
        forward(100)
    wait(100)