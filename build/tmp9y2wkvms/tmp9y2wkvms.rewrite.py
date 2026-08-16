while True:
    dist = read_ultrasonic()
    if dist < 20:
        turn_left(70)
        wait(500)
        stop()
    else:
        forward(100)
    wait(100)