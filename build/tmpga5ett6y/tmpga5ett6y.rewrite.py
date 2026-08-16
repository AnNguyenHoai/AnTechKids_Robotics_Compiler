for i in range(10):
    set_mp3_play(1)
    set_3c_led(1, 1)
    set_3c_led(2, 1)
    wait(3)
    set_mp3_play(0)
    set_3c_led(1, 0)
    set_3c_led(2, 0)
    wait(3)