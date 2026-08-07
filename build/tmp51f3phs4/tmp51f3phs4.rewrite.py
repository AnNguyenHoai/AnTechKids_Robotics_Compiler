def task1():
    while True:
        if read_ultrasonic() > 10:
            rcu.SetMp3Suspend()
        else:
            set_light_sensor_led(1, 1)
task1()