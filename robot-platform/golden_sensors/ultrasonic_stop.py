while True:
    dist = read_ultrasonic()
    if dist < 20:
        stop()
        break
    forward(30)
    wait(100)