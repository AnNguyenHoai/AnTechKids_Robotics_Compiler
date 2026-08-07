import rcu

count = 0
while count < 20:
    raw = rcu.GetTraceV2I2CData(1)
    
    # Test Left (mask == 4)
    if raw == 1:
        rcu.Set3CLed(1, 1)
    else:
        rcu.Set3CLed(1, 0)
    
    rcu.SetWaitForTime(0.05)
    count +=1