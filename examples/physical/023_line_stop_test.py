import rcu

rcu.SetMoveRun("forward", 50)
rcu.SetWaitForTime(1)
rcu.line_stop()  # should stop motors