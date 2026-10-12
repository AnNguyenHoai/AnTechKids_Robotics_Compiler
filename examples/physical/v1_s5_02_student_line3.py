"""S5/02: student-authored three-sensor line follower; tune on physical track."""
import rcu
while True:
    left = rcu.GetTraceV2I2CChxState(1, 0)
    center = rcu.GetTraceV2I2CChxState(1, 1)
    right = rcu.GetTraceV2I2CChxState(1, 2)
    if center:
        rcu.SetMoveSpeed(65, 65)
    elif left:
        rcu.SetMoveSpeed(40, 70)
    elif right:
        rcu.SetMoveSpeed(70, 40)
    else:
        rcu.SetMoveStop()
    rcu.SetWaitForTime(0.02)
