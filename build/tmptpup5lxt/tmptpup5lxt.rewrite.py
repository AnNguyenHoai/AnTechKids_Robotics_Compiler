while True:
    dist = read_ultrasonic()
    if dist < 20:
        stop()
    else:
        forward(100)
    wait(100)