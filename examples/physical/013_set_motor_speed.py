import rcu
import _thread

def task():
    # Move forward for 2 seconds
    rcu.SetMoveSpeed(100, 60)
    rcu.SetWaitForTime(2.0)
    rcu.SetMoveSpeed(0, 0)

    # # Move backward for 1 second
    # rcu.SetMoveSpeed(-70, -70)
    # rcu.SetWaitForTime(1.0)
    # rcu.SetMoveSpeed(0, 0)

    # # Rotate left (differential)
    # rcu.SetMoveSpeed(-70, 70)
    # rcu.SetWaitForTime(1.0)
    # rcu.SetMoveSpeed(0, 0)

    # # Rotate right
    # rcu.SetMoveSpeed(70, -70)
    # rcu.SetWaitForTime(1.0)
    # rcu.SetMoveSpeed(0, 0)

    # # Differential steering
    # rcu.SetMoveSpeed(70, 100)
    # rcu.SetWaitForTime(1.0)
    # rcu.SetMoveSpeed(0, 0)

_thread.start_new_thread(task, ())
while 1:
    pass