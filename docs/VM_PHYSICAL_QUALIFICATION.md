# VM-RT J Physical Robot Qualification

Tracking: #312, parent #302
Baseline: `main@18875d500bb64f4ff4a495f8915795af4f8a02f8` (merged #311 / PR #323)

## Purpose

This runbook defines the evidence required to qualify cooperative VM responsiveness on a real ESP32 robot. Host fixtures validate the tooling only; they are not physical qualification evidence and cannot approve production thresholds.

## Qualification firmware

Build the diagnostic-only profile:

```text
python -m platformio run -d robot-platform -e esp32dev_vm_qualification
```

The profile inherits the production `esp32dev` configuration and adds only:

```text
-DVM_RESPONSIVENESS_DIAGNOSTICS=1
```

The normal production profile remains unchanged.

## Required metadata per run

Create a JSON metadata file containing at least:

```json
{
  "schema_version": 1,
  "evidence_kind": "physical_robot",
  "physical_robot": true,
  "scenario": "line_follow_recovery",
  "hardware": "robot-id / board revision / sensor revision / motor driver",
  "profile": "esp32dev_vm_qualification",
  "firmware_commit": "<exact git sha>",
  "program_identity": "<source/bytecode identity>",
  "slice_configuration": {"max_work_units": 4},
  "failures_or_outliers": [],
  "thresholds": null
}
```

Do not set `physical_robot=true` for synthetic or desktop-generated telemetry.

## Required scenarios

Run each scenario with an exact program/bytecode identity and retain the raw serial capture.

1. **Line following and recovery** — continuous line follow plus forced deviation/recovery. Capture line snapshot age, read count, slice timing, slowest work unit and any visible steering lag.
2. **Intersection behavior** — where the hardware/course supports it, exercise intersection stop/turn behavior and confirm the pending operation progresses across slices without starving platform services.
3. **Ultrasonic decision loop** — repeatedly sample distance, make a decision and update motor output. Record the sensor→decision→motor observation using the available telemetry plus an external timestamp/video/logic-analyzer reference when end-to-end timing is required.
4. **Timed wait/movement** — exercise `Wait` and timed movement while another platform service remains active. Verify pending state spans slices and the VM continues only after completion.
5. **Long-running/forever loop** — run long enough to establish a useful timing distribution, not just a single sample. Confirm repeated bounded slices and continuing network/diagnostic service.
6. **Stop/abort while pending** — issue stop while a cooperative wait/line/timed operation is pending. Record `stop_latency_us`, pending owner/opcode before stop, and motor/output state after stop.

## Capture

Save the serial output to a text/JSONL file. Lines not containing VM telemetry are allowed; the parser ignores them. Each accepted telemetry record must have `type="vm_rt"` and the full VM-RT H field set.

Generate a normalized report:

```text
python tools/vm_rt_qualification.py \
  --telemetry artifacts/vm-rt/<run>/serial.jsonl \
  --metadata artifacts/vm-rt/<run>/metadata.json \
  --output artifacts/vm-rt/<run>/qualification-report.json
```

The report records:

- slice count and termination reason distribution;
- slice duration p50/p95/p99/max;
- indivisible work-unit p50/p95/p99/max;
- top slowest work units with owning PC;
- line-snapshot age distribution and physical-read evidence;
- observed stop/abort latency distribution;
- hardware/profile/firmware/program/slice metadata;
- operator-recorded failures and outliers.

## Sensor → decision → motor evidence

Current VM telemetry directly measures scheduler and snapshot timing, not the complete electrical sensor-to-motor path. For scenarios where end-to-end sensor→decision→motor latency is required, correlate the JSONL timestamps/evidence with a physical observation source such as logic analyzer, GPIO marker, or frame-accurate video. Do not label `sliceDurationUs` alone as end-to-end actuator latency.

## Threshold approval

`docs/VM_RESPONSIVENESS_THRESHOLDS.json` intentionally contains `null` thresholds and status `UNAPPROVED_PENDING_PHYSICAL_EVIDENCE`.

Only populate thresholds after the required physical scenarios have enough samples to identify normal distributions and worst observed outliers. A threshold change must reference the qualification report(s) that justify it. The slice budget must not be changed from the current value solely to make a test pass.

## Exit checklist for #312

- [ ] All required scenarios executed on physical robot.
- [ ] Raw JSONL and metadata retained for each run.
- [ ] Qualification report generated for each run.
- [ ] Sensor→decision→motor evidence captured where applicable.
- [ ] Stop/abort latency measured while pending.
- [ ] Longest indivisible work-unit outliers reviewed by PC/opcode.
- [ ] Any budget change justified by measured evidence.
- [ ] `VM_RESPONSIVENESS_THRESHOLDS.json` populated from evidence and approved.
- [ ] Host VM-RT gates remain green.

Until these boxes have physical evidence, #312 should remain open even if the qualification tooling PR is merged.
