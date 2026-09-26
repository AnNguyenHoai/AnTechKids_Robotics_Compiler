# VM Control-Latency Real-Robot Retest Checklist

Use this focused checklist before running the full six-scenario #325 campaign. It does not replace physical qualification.

## Build identity

- Branch/commit: record the exact CI-verified commit SHA.
- Profile for timing capture: `esp32dev_vm_qualification`.
- Scheduler identity: `max_work_units=16`, `max_duration_us=2000`.
- Keep serial capture active until after the VM is stopped so buffered JSONL is emitted.

## Retest A — line basis

Program:

```python
import rcu

while True:
    rcu.line_basis(60)
    rcu.SetWaitForTime(0.02)
```

Record:

- whether the robot can remain on the line over the same course that previously failed;
- visible oscillation/jerk versus missed-line behavior;
- course/surface/battery state;
- JSONL slice/work-unit/snapshot timing after stopping the VM;
- any loss/recovery event that still produces a large excursion.

Do not alter PID/mixer/recovery values during a run without starting a new evidence identity.

## Retest B — direct sensor to stop

Program:

```python
import rcu


def task1():
    rcu.SetMoveSpeed(70, 70)
    while True:
        if rcu.GetTraceV2I2CState(1, 2):
            rcu.SetMoveStop()


task1()
```

Record two different measurements:

1. **software/electrical response** — sensor transition to motor-command/PWM response using logic analyzer/GPIO marker or equivalent reviewed physical timing evidence;
2. **mechanical stopping distance** — distance from the physical detection point to the final resting position.

Do not infer software latency directly from stopping distance. Driver coast/brake behavior, wheel traction, speed and inertia also contribute.

## Pass/fail use

These focused retests are diagnostic acceptance checks for the corrective PR. Even if both look good, keep `VM_RESPONSIVENESS_THRESHOLDS.json` unapproved until all required #325/#312 physical scenarios and external end-to-end timing evidence are complete.
