import rcu
import _thread

def task1():
    rcu.SetMoveRunSecond("left", 80, 1)

_thread.start_new_thread(task1, ())

while 1:
    pass