import rcu
import _thread

def task1():
    rcu.SetMoveRunSecond("forward", 50, 2)
    rcu.SetMoveStop()

_thread.start_new_thread(task1, ())

while 1:
    pass