# H26-G — Unified E2E / Cross-Runtime Test Oracle

## Purpose

H26-G introduces a runtime-neutral semantic oracle for the Golden Path.

The oracle does not replace the production compiler, VM, firmware, or RobotAPI. It defines a common representation of observable robot side effects so that multiple runtime adapters can be compared against the same expected behavior.

## Golden Path under test

```text
RoboSim source
    ↓
frontend rewrite
    ↓
production compiler
    ↓
ISA adapter / binary encoder
    ↓
binary loader
    ↓
runtime
    ↓
hardware telemetry
    ↓
H26-G semantic trace
    ↓
canonical expected trace
```

This is an additional validation layer. Existing production behavior is unchanged.

## Semantic trace

The oracle currently normalizes hardware telemetry into these stable events:

- `motor(left, right)`
- `led(port, state)`
- `delay_ms(milliseconds)`
- `read_ultrasonic`
- `read_line(channel)`
- `read_touch(port)`
- `read_light(channel)`
- `read_color`

A runtime implementation may expose different internal names or data structures. Its adapter only needs to produce the same semantic events.

## Why this is a contract

The expected trace is intentionally independent of:

- numeric opcode values;
- compiler instruction layout;
- binary encoding details;
- VM program-counter behavior;
- runtime class names.

A test therefore fails when observable robot behavior changes, even if the implementation remains internally valid.

## Current adapter

H26-G exercises the existing Python compiler → binary → Python VM path and converts `MockHardware.log` into the semantic trace.

This proves the oracle itself and the current Golden Path against it. It does not claim physical ESP32 execution.

## Future cross-runtime use

Future runtime adapters can feed the same oracle from:

- the ESP32 firmware runtime;
- a simulator;
- another VM implementation.

Physical and firmware execution remain separate acceptance gates. H26-G does not claim that an ESP32 run occurred.

## Validation

Run:

```text
python tests/h26_g/run_h26_g.py
```

The repository-level `run_all_tests.py` also invokes the H26-G runner.

A successful H26-G run means the current host E2E behavior matches the canonical semantic traces covered by this task.

## Non-goals

- no compiler output changes;
- no opcode renumbering;
- no VM dispatch changes;
- no firmware changes;
- no physical hardware claim;
- no automatic acceptance of one runtime's output merely because another runtime produced it.

Future cross-runtime integrations must continue comparing against the same semantic oracle rather than comparing implementation-specific logs directly.
