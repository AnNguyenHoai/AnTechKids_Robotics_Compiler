# integration/end_to_end/programs/demo_if.py
import rcu
speed = 80
if speed > 50:
    rcu.SetMoveRun("forward", speed)
else:
    rcu.SetMoveRun("backward", 30)
rcu.SetMoveStop()