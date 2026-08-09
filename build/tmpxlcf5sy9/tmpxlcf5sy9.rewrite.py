while True:
    dist = read_ultrasonic()
    if dist < 30:
        stop()
    else:
        forward(90)
    wait(100)