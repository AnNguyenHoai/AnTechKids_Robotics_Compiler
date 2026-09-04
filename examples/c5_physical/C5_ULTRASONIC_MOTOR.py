import rcu

while True:
    dist = rcu.GetUltrasound(1)

    if dist < 20:
        rcu.SetMoveStop()
    else:
        rcu.SetMoveRun("forward", 80)

    rcu.SetWaitForTime(0.2)
