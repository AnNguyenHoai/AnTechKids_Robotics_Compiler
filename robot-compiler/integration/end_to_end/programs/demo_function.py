# integration/end_to_end/programs/demo_function.py
import rcu

def move_forward():
    rcu.SetMoveRun("forward", 80)
    rcu.SetMoveStop()

move_forward()