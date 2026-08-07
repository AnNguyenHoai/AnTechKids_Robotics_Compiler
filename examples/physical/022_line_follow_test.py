import rcu

while True:
    if rcu.GetTraceV2I2CData(1) == 2:   # 100
        rcu.Set3CLed(1, 1)
    else:
        rcu.Set3CLed(1, 0)

    rcu.SetWaitForTime(0.05)