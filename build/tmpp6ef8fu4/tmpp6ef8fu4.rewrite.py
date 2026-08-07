def task1():
    set_3c_led(1, 3)
    set_3c_led(2, 3)
    wait(5000)
    set_mp3_play(1)
    for i in range(5):
        set_mp3_play(1)
        wait(0.5)
task1()