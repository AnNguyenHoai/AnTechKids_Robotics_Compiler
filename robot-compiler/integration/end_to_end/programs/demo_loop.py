# integration/end_to_end/programs/demo_loop.py
import rcu

count = 1
while count > 0:
    rcu.SetMoveRun("forward", 70)
    rcu.SetMoveStop()
    count = count - 1