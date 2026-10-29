"""V1-S7 supervised touch test, GPIO36, active-HIGH module only.
Power OFF before rewiring. Initial test with wheels lifted.
If sensor outputs LOW when pressed, do not run this script as-is.
"""
import rcu

while True:
    if rcu.GetTouch(1):
        rcu.SetMoveStop()
    else:
        rcu.SetMoveSpeed(60, 60)
    rcu.SetWaitForTime(0.02)
