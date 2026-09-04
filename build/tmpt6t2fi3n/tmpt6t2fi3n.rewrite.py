VAR_tuong_so = 0

def task1():
    global VAR_tuong_so
    forward(70)
    VAR_tuong_so = 1
    while True:
        if read_ultrasonic() < 25 and VAR_tuong_so == 1:
            turn_left(80)
            wait(400)
            stop()
            VAR_tuong_so += 1
            forward(80)
        if read_ultrasonic() < 25 and VAR_tuong_so == 2:
            turn_right(80)
            wait(400)
            stop()
            VAR_tuong_so += 1
            forward(80)
task1()