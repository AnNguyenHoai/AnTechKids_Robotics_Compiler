def task1():
    while True:
        if read_touch(1):
            rcu.SetMoveSpeed(50, 50)
task1()