import rcu
import _thread

def task1():
    rcu.SetMoveRun("forward", 50)
    rcu.SetMoveStop()

_thread.start_new_thread(task1, ())

while 1:
    pass