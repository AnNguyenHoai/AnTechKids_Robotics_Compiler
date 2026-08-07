def task1():
    while True:
        if read_ultrasonic() > 10:
            set_mp3_play(1)
        else:
            set_light_sensor_led(1, 1)
task1()