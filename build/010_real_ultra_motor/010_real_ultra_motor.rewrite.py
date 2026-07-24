VAR_distance = 0

def task1():
    global VAR_distance
    VAR_distance = rcu.GetUltrasound(1)
    if VAR_distance < 20:
        forward(50)
        wait(1000)
        stop()
    else:
        backward(50)
        wait(1000)
        stop()
task1()