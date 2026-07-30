import rcu

line = rcu.GetTraceV2I2CChxState(1,2)

if line:
    rcu.SetMoveRunSecond("forward",80,1)
else:
    rcu.SetMoveRunSecond("backward",80,1)