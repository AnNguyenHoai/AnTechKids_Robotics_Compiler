VAR_tuong_so = 0

def task1():
    global VAR_tuong_so
    forward(80)
    VAR_tuong_so = 1
    while True:
        if read_ultrasonic() < 25 and VAR_tuong_so == 1:
            turn_left(70)
            wait(600)
            stop()
            VAR_tuong_so += 1
            forward(80)
task1()