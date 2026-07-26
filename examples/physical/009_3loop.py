import rcu
import _thread

def task1():
    for i in range(3):
        rcu.SetMoveRunSecond("forward", 150, 0.5)

_thread.start_new_thread(task1, ())

while 1:
    pass