while True:
    dist = read_ultrasonic()
    if dist < 20:
        set_mp3_play(1)
    wait(100)