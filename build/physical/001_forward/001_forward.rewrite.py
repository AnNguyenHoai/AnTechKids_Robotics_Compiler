import _thread

def task1():
    forward(50)
    wait(1000)
    stop()
_thread.start_new_thread(task1, ())
while 1:
    pass