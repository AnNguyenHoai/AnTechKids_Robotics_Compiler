import rcu

while True:
    dist = rcu.GetUltrasound(1)

    if dist < 20:
        rcu.Set3CLed(1, 1)
    else:
        rcu.Set3CLed(1, 0)

    rcu.SetWaitForTime(0.2)
