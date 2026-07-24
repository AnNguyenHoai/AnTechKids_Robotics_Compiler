# integration/end_to_end/programs/demo_variable.py
import rcu
speed = 60
rcu.SetMoveRun("forward", speed)
rcu.SetMoveStop()