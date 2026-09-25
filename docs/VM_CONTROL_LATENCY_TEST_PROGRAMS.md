# VM Control-Latency Reproduction Programs

These source programs reproduce the physical behaviors that triggered the corrective audit. Keep them unchanged when comparing before/after firmware behavior.

## Line basis at 20 ms cadence

```python
import rcu

while True:
    rcu.line_basis(60)
    rcu.SetWaitForTime(0.02)
```

## Direct line-state stop

```python
import rcu


def task1():
    rcu.SetMoveSpeed(70, 70)
    while True:
        if rcu.GetTraceV2I2CState(1, 2):
            rcu.SetMoveStop()


task1()
```

The first program is primarily sensitive to line-controller cadence, steering authority and recovery timing. The second bypasses `LineFollower` and is primarily useful for sensor/VM/branch/actuator response plus separate mechanical stopping-distance observation.
