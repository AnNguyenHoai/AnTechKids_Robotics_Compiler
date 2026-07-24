import rcu
import _thread

def task1():
    rcu.SetMoveRunSecond("forward", 50, 1)
    rcu.SetMoveRunSecond("left", 50, 1)
    rcu.SetMoveRunSecond("forward", 50, 1)
    rcu.SetMoveRunSecond("right", 50, 1)
    rcu.SetMoveRunSecond("backward", 50, 1)

_thread.start_new_thread(task1, ())

while 1:
    pass