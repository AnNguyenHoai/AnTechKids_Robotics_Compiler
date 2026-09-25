# VM Control-Latency Corrective Changelog

- Scheduler: work-only `4` -> provisional dual budget `16 work units / 2000 us`.
- Runtime: optional wall-clock RunSlice exit, legacy `Step()` unchanged.
- Telemetry: active per-slice Serial JSON -> RAM ring + post-stop JSON dump.
- Stop observation: one stop-latency sample emitted once, not copied to every buffered slice.
- Line diagnostics: cached-state observer, no additional `TCRT5000::update()`.
- Line loss: three scheduler-dependent zero samples -> 10 ms elapsed-time confirmation.
- Steering baseline: P-only `Kp 1.0 / scale 10` -> P-only `Kp 1.2 / scale 15`.
- Recovery: soft arc `300 ms` -> `120 ms`, bounded recovery speeds retained.
- Qualification: physical metadata/campaign now bind both work and wall-clock scheduler values.
- Approval: physical thresholds remain null and unapproved pending #325/#312 evidence.
