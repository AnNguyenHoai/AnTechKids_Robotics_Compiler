def task():
    set_motor_speed(100, 60)
    wait(2000)
    set_motor_speed(0, 0)
task()
while 1:
    pass