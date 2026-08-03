import rcu

while True:
    if rcu.GetTraceV2I2CChxState(1, 1):
        rcu.SetMp3Play(1)  # beep when center line detected
    rcu.SetWaitForTime(0.2)