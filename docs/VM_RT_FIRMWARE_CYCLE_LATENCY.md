# VM-RT X — Firmware Control-Cycle Latency

Issue: #380. Parent: #302. Related: #379, #312, #325.

## Problem

`VM_MAX_SLICE_DURATION_US` bounds only `RunSlice()`. It does not bound the age of the line-sensor sample consumed by student code. A reactive program can therefore have a short `GetTraceState -> Stop` VM path while still observing a stale sample if the surrounding firmware cycle is delayed.

## Runtime contract

Normal firmware operation is split into two phases:

1. **Control-critical phase**
   - begin one coherent line snapshot;
   - refresh sensors;
   - update motion state;
   - execute one bounded VM/behavior slice;
   - update diagnostics from the same cached line sample;
   - close the snapshot.
2. **Background phase**
   - consume a bounded number of serial bytes without waiting for a delimiter;
   - service network/OTA/HTTP/discovery cooperatively;
   - update the optional development console.

Serial/network work MUST NOT sit between the fresh line sample and that cycle's VM decision.

## Serial contract

The serial command parser consumes at most 32 bytes per firmware cycle into a bounded 192-byte line buffer. Commands are dispatched only after a newline is received. Oversized input is discarded incrementally. `readStringUntil()` or another timeout-based delimiter wait is forbidden in the normal firmware loop.

## Network contract

Normal network work has a 500 us soft inter-call budget. Arduino/WiFi framework calls are indivisible at this layer, so the budget is checked between Wi-Fi/OTA/HTTP/discovery calls rather than pretending they can be preempted. LAN discovery processes at most one datagram per firmware update.

Once OTA actually starts, the callback stops motors immediately and transfers ownership to OTA. While OTA owns the robot, VM work is suspended and the network update path may run without the normal background budget until completion/reboot.

## Timing evidence

Qualification firmware records timing in RAM; it must not print UART telemetry from the active control path.

The evidence separates:

- firmware-cycle duration;
- physical line-sample period;
- line snapshot timestamp -> completed `GetTraceState` observation;
- line snapshot timestamp -> completed `Stop` Step / PWM submission;
- `GetTraceState` observation -> completed `Stop` Step.

Mechanical stopping distance after PWM zero is a separate physical measurement and must not be reported as software latency.

The additional JSONL records are:

- `type=vm_rt_reactive` — one completed detected-line -> Stop chain;
- `type=vm_rt_cycle_summary` — max/last whole-cycle and line-sample-period observations.

Existing `type=vm_rt` records remain unchanged for compatibility with the qualification parser.

## Qualification boundary

The 500 us network service allowance and existing VM `16 work units / 2000 us` configuration are engineering scheduling ceilings, not approved production responsiveness thresholds. #312/#325 remain open until physical evidence establishes acceptable distributions/outliers and separates software latency from motor-driver/mechanical coast.
