# H23-D — Line Response Latency Trace

Purpose: measure the synchronous software path from Line5 sampling to motor-output submission.

Enable with:

```text
line diag on
```

Disable/status:

```text
line diag off
line diag status
```

The diagnostic emits a record only when the canonical 5-bit Line5 mask changes.

Example:

```text
[LINE-RESPONSE] t=123456us mask=0x04 prev=--- loop=20110us | sensor=142us control=31us output=18us total=191us | cmd L=50 R=50
```

Fields:

- `loop`: time between consecutive `RobotAPI::LineBasis()` calls.
- `sensor`: `GetTraceRaw(1)` duration.
- `control`: `LineFollower::update()` duration.
- `output`: `setMotorsDirect()` duration, including mapping and low-level motor submission.
- `total`: sensor acquisition start through motor-output submission.
- `mask`: canonical 5-bit mask, bit4..bit0 = FL/L/C/R/FR.

Interpretation:

- large `loop` => VM/API invocation cadence is slow;
- large `sensor` => sensor acquisition is slow;
- large `control` => line algorithm is slow;
- large `output` => motor software path is slow;
- small `total` with poor physical tracking => investigate actuator/mechanical response rather than software latency.

This diagnostic measures software response and motor-command submission only. It does not measure physical motor acceleration, wheel inertia, chassis motion, or sensor optical response.

## V2-TEST-005 measurement protocol

The performance comparison must use the same procedure for both baselines:

1. V1 direct GPIO Line5 baseline.
2. V2 MCP23017 Line5 implementation.
3. Enable `line diag on`.
4. Exercise the same physical track transitions and comparable control-loop conditions.
5. Capture serial output containing `[LINE-RESPONSE]` records.
6. Collect enough mask-change events to represent center, small deviation, strong deviation, lost/reacquire, and intersection transitions.
7. Parse both logs with:

```bash
python tools/line_response_report.py v1.log --label v1-direct-gpio --csv v1.csv
python tools/line_response_report.py v2.log --label v2-mcp23017 --csv v2.csv
```

The report computes, for each timing field:

- sample count;
- minimum;
- median;
- p95;
- maximum;
- mean.

The first physical V1/V2 measurement must be retained as release evidence.

## Acceptance-threshold rule

No latency acceptance threshold is defined in software source-of-truth yet.

The first physical comparison must be reviewed before freezing a threshold. The parser therefore deliberately emits:

```json
"acceptance_threshold": null,
"pass_fail": "NOT_EVALUATED"
```

Software tests must not invent a threshold or mark performance PASS/FAIL without hardware evidence.

After the first approved hardware measurement, update V2-TEST-005 with:

- measured V1 distribution;
- measured V2 distribution;
- approved metric(s), for example p95 `sensor_us` and/or `total_us`;
- frozen acceptance threshold;
- board/firmware versions and test conditions.
