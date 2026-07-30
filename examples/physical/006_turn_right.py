import rcu
import _thread

def task1():
    rcu.SetMoveRunSecond("backward", 70, 1)

_thread.start_new_thread(task1, ())

while 1:
    pass