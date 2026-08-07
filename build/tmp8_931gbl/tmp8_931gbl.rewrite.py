def task():
    for i in range(3):
        set_light_sensor_led(1, 1)
        wait(2000)
        set_light_sensor_led(1, 0)
        wait(1000)
task()
while 1:
    pass