"""S5/03: five-sensor decision logic (not the autonomous line_basis)."""
import rcu
while True:
    fl = rcu.GetTraceV2I2CChxState(1, 3)
    left = rcu.GetTraceV2I2CChxState(1, 0)
    center = rcu.GetTraceV2I2CChxState(1, 1)
    right = rcu.GetTraceV2I2CChxState(1, 2)
    fr = rcu.GetTraceV2I2CChxState(1, 4)
    if fl and not fr:
        rcu.SetMoveSpeed(0, 75)
    elif fr and not fl:
        rcu.SetMoveSpeed(75, 0)
    elif left and not right:
        rcu.SetMoveSpeed(40, 70)
    elif right and not left:
        rcu.SetMoveSpeed(70, 40)
    elif center:
        rcu.SetMoveSpeed(65, 65)
    else:
        rcu.SetMoveStop()
    rcu.SetWaitForTime(0.02)
