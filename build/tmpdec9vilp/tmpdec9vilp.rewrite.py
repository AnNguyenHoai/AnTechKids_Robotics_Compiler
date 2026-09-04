VAR_tuong_so = 0

def task1():
    global VAR_tuong_so
    forward(66)
    VAR_tuong_so = 1
    while True:
        if read_ultrasonic() < 15 and VAR_tuong_so == 1:
            turn_left(55)
            wait(400)
            stop()
            VAR_tuong_so += 1
            forward(80)
        if read_ultrasonic() < 15 and VAR_tuong_so == 2:
            turn_right(55)
            wait(400)
            stop()
            VAR_tuong_so += 1
            forward(80)
task1()