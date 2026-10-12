"""S5/01: manual motor command test. Use on a raised chassis first."""
import rcu
rcu.SetMoveSpeed(60, 60)
rcu.SetWaitForTime(2)
rcu.SetMoveStop()
rcu.SetWaitForTime(0.5)
rcu.SetMoveSpeed(40, 70)
rcu.SetWaitForTime(1)
rcu.SetMoveStop()
rcu.SetWaitForTime(0.5)
rcu.SetMoveSpeed(0, 70)
rcu.SetWaitForTime(1)
rcu.SetMoveStop()
