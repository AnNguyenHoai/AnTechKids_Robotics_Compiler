# VM Control-Latency Corrective Scope

This corrective change addresses software latency and observer effects proven by source audit after the September 25, 2026 real-robot failure report.

Included:

- dual work/time VM slice scheduling;
- reactive-chain scheduling regression gates;
- observer-safe VM qualification telemetry;
- redundant diagnostic line-read removal;
- time-based line-loss confirmation and restored bounded steering authority;
- shorter bounded recovery phase;
- exact dual-budget physical evidence identity and documentation.

Not claimed as complete:

- final scheduler/PID/recovery calibration;
- approved latency thresholds;
- electrical H-bridge brake/coast tuning;
- mechanical stopping-distance acceptance;
- six-scenario physical qualification.

Those items remain evidence-driven work under #325/#312. No physical measurement is fabricated or inferred from host tests.
