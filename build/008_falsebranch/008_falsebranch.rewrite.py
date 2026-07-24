def task1():
    speed = 30
    threshold = 50
    if speed > threshold:
        forward(50)
        wait(1000)
        stop()
    else:
        backward(50)
        wait(1000)
        stop()
task1()
while 1:
    pass