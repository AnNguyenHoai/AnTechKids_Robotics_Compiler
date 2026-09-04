VAR_tuong_so = 0

def task1():
    global VAR_tuong_so
    forward(80)
    VAR_tuong_so = 1
    while True:
        if read_ultrasonic() < 15 and VAR_tuong_so == 1:
            turn_left(80)
            wait(400)
            stop()
            VAR_tuong_so += 1
            stop()
task1()