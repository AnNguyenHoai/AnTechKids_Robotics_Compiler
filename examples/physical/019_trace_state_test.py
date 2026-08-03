import rcu

while True:
    if rcu.GetTraceV2I2CState(1, 1):  # center line
        rcu.Set3CLed(1, 0)
    else:
        rcu.Set3CLed(1, 1)
    rcu.SetWaitForTime(0.1)