def task1():
    set_3c_led(1, 3)
    set_3c_led(2, 3)
    wait(5000)
    set_mp3_play(1)
    forward(80)
    wait(10000)
    stop()
task1()