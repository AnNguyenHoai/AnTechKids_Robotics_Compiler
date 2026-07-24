# integration/end_to_end/programs/demo_turn.py
import rcu
rcu.SetMoveRun("left", 60)
rcu.SetMoveStop()
rcu.SetMoveRun("right", 60)
rcu.SetMoveStop()