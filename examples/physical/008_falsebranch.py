import rcu
import _thread

def task1():
    speed = 30
    threshold = 50

    if speed > threshold:
        rcu.SetMoveRunSecond("forward", 50, 1)
    else:
        rcu.SetMoveRunSecond("backward", 50, 1)

_thread.start_new_thread(task1, ())

while 1:
    pass