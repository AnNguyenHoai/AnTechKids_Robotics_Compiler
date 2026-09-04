import rcu

rcu.SetMoveRun("forward", 50)
rcu.line_follow(50)
rcu.SetWaitForTime(2)
rcu.line_stop()
